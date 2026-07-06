import time

from openai import OpenAI

from mysql_qa.retrieval.bm25_search import BM25Search
from mysql_qa.db.mysql_client import MysqlClient
from mysql_qa.cache.redis_client import RedisClient

from rag_qa.core.rag_system import RAGSystem
from rag_qa.core.vector_store import VectorStore

from base.config import config
from base.logger import logger

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

    def call_dashscope(self, prompt):
        # 调用 DashScope API
        try:
            # 创建聊天完成请求
            completion = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system",
                     "content": "你是一个有用的助手，能够根据用户输入的Prompt严格执行并返回可靠的结果"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1
            )
            # 返回完成结果
            return completion.choices[
                0].message.content if completion.choices else f"未找到对应的答案，请联系客服: {config.CUSTOMER_SERVICE_PHONE}"
        except Exception as e:
            # 记录 API 调用失败
            logger.error(f"DashScope API 调用失败: {e}")
            # 默认返回直接检索
            return f"未找到对应的答案，请联系客服: {config.CUSTOMER_SERVICE_PHONE}"

    def query(self, query, source_filter=None):
        # 1. 接收用户的query，记录开始时间
        start_time = time.time()
        # 2. 调用BM25Search.query，得到答案和是否需要继续查询RAG系统
        answer, need_rag = self.faq.query(query, threshold=0.85)
        # 3. 如果得到答案，直接返回
        if answer:
            end_time = time.time()
            duration = end_time - start_time
            logger.info("在FAQ模块获取到了答案， 执行时间: {}".format(duration))
            return answer

        logger.info(f"在FAQ模块中未能找到可靠的答案，问题：{query}")

        # 4. 如果没有答案，并且需要继续查询RAG系统，调用RAGSystem.generate_answer得到结果
        if need_rag:
            logger.info(f"尝试查询RAG模块，问题：{query}")
            answer = self.rag.generate_answer(query, source_filter)
            # 5. 统计时长
            end_time = time.time()
            duration = end_time - start_time
            logger.info("在RAG系统中获取到了答案， 执行时间: {}".format(duration))
            return answer
        else:
            end_time = time.time()
            duration = end_time - start_time
            logger.info("未能查询到对应的答案: {}".format(duration))
            return f"用户输入的查询非法，未能查询到对应的答案。请联系客服：{config.CUSTOMER_SERVICE_PHONE}"


if __name__ == '__main__':
    integrated_system = IntegratedQASystem()
    result = integrated_system.query("大模型学科学什么")
    print(result)