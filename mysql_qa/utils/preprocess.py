"""
需求：实现数据的预处理功能：1.分词 2.英文转小写

"""

import jieba

from base.logger import single_logger as logger


def preprocess_text(text):
    """
    数据的预处理
    :param text: 原始的文本，比如用户的query或数据里的question
    :return:    分词和转小写以后的处理结果
    """
    try:
        # 1. 转小写
        text = text.lower()
        # 2. 分词
        words = jieba.lcut(text)
        logger.debug(f'文本预处理成功，原始问题:{text},处理结果:{words}')
        return words
    except Exception as e:
        logger.error(f'转化失败:{text}, error:{e}')
        return []
