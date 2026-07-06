import logging
import os


from base.config import single_config as config


def get_logger(project_name
               , level=logging.DEBUG
               , file_level=logging.DEBUG
               , console_level=logging.INFO
               , formatter='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(lineno)d - %(message)s'
               , encode='utf-8'
               , mode='a'
               , log_url=config.LOG_FILE):
    """
    团队通用日志打印工具
    :param project_name:     项目名，必填
    :param level:            全局日志级别...
    :param file_level:
    :param console_level:
    :param formatter:
    :param encode:
    :param mode:
    :param log_url:
    :return:
    """

    os.makedirs(os.path.dirname(log_url), exist_ok=True)

    # 创建日志记录器
    logger = logging.getLogger(project_name)
    logger.setLevel(level)  # 设置记录器级别

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)  # 控制台显示INFO及以上级别

    # 创建文件处理器
    file_handler = logging.FileHandler(log_url, mode=mode, encoding=encode)
    file_handler.setLevel(file_level)  # 文件记录DEBUG及以上级别

    # 定义日志格式
    formatter = logging.Formatter(fmt=formatter)

    # 为处理器设置格式
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        # 将处理器添加到记录器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger



single_logger = get_logger('EDU_RAG')
