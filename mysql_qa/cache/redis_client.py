"""
Redis客户端模块

提供Redis缓存操作功能，用于缓存BM25检索器数据和问答对数据，
减少重复计算，提高系统响应速度。
"""

from redis import StrictRedis
from base.config import single_config as config
from base.logger import single_logger as logger

import json


class RedisClient(object):
    """
    Redis客户端类

    封装Redis的常用操作，包括：
    - BM25检索器数据的存取（set_data/get_data）
    - 问答对缓存数据的存取（set_answer/get_answer）
    """

    def __init__(self):
        """
        初始化Redis客户端连接

        Args:
            config: 配置对象，包含Redis连接参数（主机、端口、数据库、密码）
        """
        # 创建StrictRedis客户端实例，使用配置中的连接参数
        self.redis = StrictRedis(host=config.REDIS_HOST
                                 , port=config.REDIS_PORT
                                 , db=config.REDIS_DB
                                 , password=config.REDIS_PASSWORD
                                 , decode_responses=True)

    def delete(self, *keys):
        """删除一个或多个键"""
        return self.redis.delete(*keys)

    def set_data(self, key, value):
        """
        将BM25检索器数据写入Redis缓存

        Args:
            key: 缓存键名
            value: 要缓存的数据（会被序列化为JSON格式存储）
        """
        try:
            # 将Python对象序列化为JSON字符串
            json_str = json.dumps(value, ensure_ascii=False)
            # 写入Redis
            self.redis.set(key, json_str)
            logger.info(f'bm25检索器数据，写入redis成功，key:{key},value:{json_str}')
        except Exception as e:
            logger.error(f'bm25检索器数据，写入redis错误:{e}')


    def get_data(self, key):
        """
        从Redis缓存中读取BM25检索器数据

        Args:
            key: 缓存键名

        Returns:
            反序列化后的数据对象，如果键不存在或发生错误则返回空列表
        """
        try:
            # 从Redis获取数据（返回的是JSON字符串）
            json_str = self.redis.get(key)
            # 如果键不存在，返回空列表
            if json_str is None:
                return []
            # 将JSON字符串反序列化为Python对象
            value = json.loads(json_str)
            logger.info(f'bm25检索器数据，读取redis成功,key:{key},value:{value}')
            return value
        except Exception as e:
            logger.error(f'bm25检索器数据，读取redis错误:{e}')
            return []

    def _build_question_key(self, question):
        """
        构建问答对缓存的键名

        使用统一的前缀格式，便于管理和查询

        Args:
            question: 问题文本

        Returns:
            格式化的Redis键名，格式为：tcmqa:answer:{question}
        """
        return f'tcmqa:answer:{question}'

    def set_answer(self, question, answer):
        """
        将问答对数据写入Redis缓存

        用于缓存已回答的问题，避免重复检索和生成答案

        Args:
            question: 问题文本
            answer: 答案文本
        """
        try:
            # 根据问题构建缓存键名
            key = self._build_question_key(question)
            # 将答案写入Redis
            self.redis.set(key, answer, ex=24 * 3600)
            logger.debug(f'文档对缓存数据，写入redis成功,key:{key},value:{answer}')
        except Exception as e:
            logger.error(f'文档对缓存数据，写入redis错误:{e}')

    def get_answer(self, question):
        """
        从Redis缓存中获取问答对数据

        Args:
            question: 问题文本

        Returns:
            答案文本（bytes类型），如果缓存中不存在或发生错误则返回None
        """
        try:
            # 根据问题构建缓存键名
            key = self._build_question_key(question)
            # 从Redis获取答案
            # answer = self.redis.get(key)
            answer = self.redis.getex(key, ex=24 * 3600)
            # 如果键不存在，记录日志并返回None
            if answer is None:
                logger.debug(f'获取问答对缓存数据失败,question:{question},不存在')
                return None
            logger.debug(f'获取问答对缓存数据成功,question:{question},answer:{answer}')
            return answer
        except Exception as e:
            logger.error(f'获取问答对缓存数据失败:{e}')
            return None


if __name__ == '__main__':
    print(config.MYSQL_USER)
    print(RedisClient().get_answer('Python如何读取CSV文件？'))
