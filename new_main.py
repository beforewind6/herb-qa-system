import time
import uuid

from openai import OpenAI

from mysql_qa.retrieval.bm25_search import BM25Search
from mysql_qa.db.mysql_client import MysqlClient
from mysql_qa.cache.redis_client import RedisClient

# TODO 改造rag_system
from rag_qa.core.new_rag_system import RAGSystem

from rag_qa.core.vector_store import VectorStore

from base.config import config
from base.logger import logger

import pymysql

"""
需求：实现FAQ和RAG模块的结合，用户输入一个query，返回最终的答案
思路步骤：
1. 接收用户的query，记录开始时间
2. 调用BM25Search.query，得到答案和是否需要继续查询RAG系统
3. 如果得到答案，直接返回
4. 如果没有答案，并且需要继续查询RAG系统，调用RAGSystem.generate_answer得到结果
5. 统计时长
"""


class IntegratedQASystem():
    def __init__(self):
        self.faq = BM25Search(
            mysql_client=MysqlClient()
            , redis_client=RedisClient()
        )
        self.rag = RAGSystem(
            vector_store=VectorStore()
            , llm=self.call_dashscope
        )

        self.client = OpenAI(api_key=config.DASHSCOPE_API_KEY,
                             base_url=config.DASHSCOPE_BASE_URL)

        self.mysql_client = MysqlClient()
        self.logger = logger
        self.config = config

        # TODO 对于有session的版本，在系统初始化的时候，进行建表操作
        self.init_conversation_table()

    def call_dashscope(self, prompt):
        """调用DashScope API生成答案（流式输出）"""
        try:
            # 创建聊天完成请求，启用流式输出
            completion = self.client.chat.completions.create(
                model=self.config.LLM_MODEL,  # 使用配置中的语言模型
                messages=[
                    {"role": "system", "content": "你是一个有用的助手。"},  # 系统提示
                    {"role": "user", "content": prompt},  # 用户输入的提示
                ],
                timeout=30,  # 设置 30 秒超时
                stream=True  # 启用流式输出
            )
            # 初始化收集流式输出的字符串
            collected_content = ""
            # 遍历流式输出的每个 chunk
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta.content:
                    # 获取当前 chunk 的内容
                    content = chunk.choices[0].delta.content
                    # 累积内容
                    collected_content += content
                    # 逐 token 返回，供前端实时显示
                    yield content
            # 返回完整答案
            return collected_content
        except Exception as e:
            # 记录 API 调用失败的错误日志
            self.logger.error(f"LLM调用失败: {e}")
            # 返回错误信息
            return f"错误：LLM调用失败 - {e}"

    def init_conversation_table(self):
        """初始化MySQL中的conversations表，用于存储对话历史"""
        try:
            # 创建 conversations 表，包含会话 ID、问题、答案和时间戳
            self.mysql_client.cursor.execute("""
                                             CREATE TABLE IF NOT EXISTS conversations
                                             (
                                                 id          BIGINT AUTO_INCREMENT PRIMARY KEY,
                                                 session_id  VARCHAR(36)           NOT NULL,
                                                 question    TEXT                  NOT NULL,
                                                 answer      TEXT                  NOT NULL,
                                                 timestamp   DATETIME              NOT NULL,
                                                 _is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                                                 INDEX idx_session_id (session_id)
                                             )
                                             """)
            # 提交数据库事务
            self.mysql_client.connect.commit()
            # 记录表初始化成功的日志
            self.logger.info("对话历史表初始化成功")
        except pymysql.MySQLError as e:
            # 记录表初始化失败的错误日志
            self.logger.error(f"初始化对话历史表失败: {e}")
            # 抛出异常，终止初始化
            raise

    def _fetch_recent_history(self, session_id: str) -> list:
        """获取最近5轮对话历史"""
        try:
            # 执行 SQL 查询，获取最近 5 轮对话
            self.mysql_client.cursor.execute("""
                                             SELECT question, answer
                                             FROM conversations
                                             WHERE session_id = %s
                                               and _is_deleted = FALSE
                                             ORDER BY timestamp DESC
                                             LIMIT %s
                                             """, (session_id, 5))
            # 将查询结果转换为字典列表
            history = [{"question": row[0], "answer": row[1]} for row in self.mysql_client.cursor.fetchall()]
            # 反转结果，按时间正序返回
            # TODO 因为ORDER BY timestamp DESC， 根据时间进行了倒排。但是，我们阅读上下文的时候，需要根据时间顺序正排，所以这里需要反转
            return history[::-1]
        except pymysql.MySQLError as e:
            # 记录查询失败的错误日志
            self.logger.error(f"获取对话历史失败: {e}")
            # 返回空列表
            return []

    def get_session_history(self, session_id: str) -> list:
        """从MySQL获取会话历史"""
        # 调用 _fetch_recent_history 获取对话历史
        return self._fetch_recent_history(session_id)

    def update_session_history(self, session_id: str, question: str, answer: str) -> list:
        """更新会话历史到MySQL，保留最近5轮对话"""
        try:
            # 插入新的对话记录
            self.mysql_client.cursor.execute("""
                                             INSERT INTO conversations (session_id, question, answer, timestamp)
                                             VALUES (%s, %s, %s, NOW())
                                             """, (session_id, question, answer))
            # 获取更新后的对话历史
            history = self._fetch_recent_history(session_id)

            # TODO 对于实际生产场景，用户的行为数据就是数据资产，一般来讲我们不会进行物理删除。

            # 删除超出 5 轮的旧记录
            # TODO：复杂嵌套SQL，从最内层的括号开始看，然后逐渐向外
            # 1. 【取最近5条记录】获取最近5轮对话的ID
            # 2. 【取全集和最近5条记录差集】查询当前会话(session_id)下，id不在 获取最近5轮对话的ID以内的
            # 3. 【删除差集】删除第二步的结果
            # self.mysql_client.cursor.execute("""
            #                                  DELETE
            #                                  FROM conversations
            #                                  WHERE session_id = %s
            #                                    AND id NOT IN (SELECT id
            #                                                   FROM (SELECT id
            #                                                         FROM conversations
            #                                                         WHERE session_id = %s
            #                                                         ORDER BY timestamp DESC
            #                                                         LIMIT %s) AS sub)
            #                                  """, (session_id, session_id, 5))
            # 提交事务
            self.mysql_client.connect.commit()
            # 记录更新成功的日志
            self.logger.info(f"会话 {session_id} 历史更新成功")
            # 返回更新后的历史
            return history
        except pymysql.MySQLError as e:
            # 记录数据库操作失败的错误日志
            self.logger.error(f"更新会话历史失败: {e}")
            # 回滚事务
            self.mysql_client.connect.rollback()
            # 抛出异常
            raise
        except Exception as e:
            # 记录意外错误的日志
            self.logger.error(f"更新会话历史意外错误: {e}")
            # 回滚事务
            self.mysql_client.connect.rollback()
            # 抛出异常
            raise

    def clear_session_history(self, session_id: str) -> bool:
        """清除指定会话历史"""
        try:
            # 删除指定 session_id 的所有对话记录
            # old_sql = """
            #      DELETE
            #      FROM conversations
            #      WHERE session_id = %s \
            #      """

            new_sql = """
                      update conversations
                      set _is_deleted = True
                      WHERE session_id = %s \
                      """
            self.mysql_client.cursor.execute(new_sql, (session_id,))
            # 提交事务
            self.mysql_client.connect.commit()
            # 记录清除成功的日志
            self.logger.info(f"会话 {session_id} 历史已清除")
            # 返回 True 表示成功
            return True
        except pymysql.MySQLError as e:
            # 记录清除失败的错误日志
            self.logger.error(f"清除会话历史失败: {e}")
            # 回滚事务
            self.mysql_client.connect.rollback()
            # 返回 False 表示失败
            return False

    """
    需求：实现FAQ和RAG模块的结合，支持多轮对话和流式输出，用户输入一个query，返回最终的答案
    思路步骤：
    1. 接收用户的query，记录开始时间
    2. 通过session_id获取最近的对话记录 , 如果没有session_id
    3. 调用BM25Search.query，得到答案和是否需要继续查询RAG系统
    4. 如果得到答案，直接返回。 记录对话记录到session_id中
    5. 如果没有答案，并且需要继续查询RAG系统，调用RAGSystem.generate_answer流式得到结果，并记录到session_id中
    6. 统计时长
    """

    def query(self, query, session_id=None, source_filter=None):
        # 1. 接收用户的query，记录开始时间
        start_time = time.time()

        history = self._fetch_recent_history(session_id=session_id) if session_id else []

        # 2. 调用BM25Search.query，得到答案和是否需要继续查询RAG系统
        answer, need_rag = self.faq.query(query, threshold=0.85)
        # 3. 如果得到答案，直接返回
        if answer:
            end_time = time.time()
            duration = end_time - start_time
            logger.info("在FAQ模块获取到了答案， 执行时间: {}".format(duration))
            # 如果在FAQ模块中得到了答案，记录到对话历史
            if session_id:
                self.update_session_history(session_id=session_id, question=query, answer=answer)
            yield answer, True

        logger.info(f"在FAQ模块中未能找到可靠的答案，问题：{query}")

        # 4. 如果没有答案，并且需要继续查询RAG系统，调用RAGSystem.generate_answer得到结果
        if need_rag:
            logger.info(f"尝试查询RAG模块，问题：{query}")
            collected_answer = ''
            for token in self.rag.generate_answer(query, source_filter=source_filter, history=history):
                # 累积答案
                collected_answer += token
                # 逐 token 返回，标记为部分答案
                yield token, False
            # 如果在RAG系统重获取到了答案，记录到对话历史
            if session_id:
                self.update_session_history(session_id=session_id, question=query, answer=collected_answer)
            # 5. 统计时长
            end_time = time.time()
            duration = end_time - start_time
            logger.info("在RAG系统中获取到了答案， 执行时间: {}".format(duration))
            yield '', True
        else:
            end_time = time.time()
            duration = end_time - start_time
            logger.info("未能查询到对应的答案: {}".format(duration))
            yield f"用户输入的查询非法，未能查询到对应的答案。请联系客服：{config.CUSTOMER_SERVICE_PHONE}" , True
