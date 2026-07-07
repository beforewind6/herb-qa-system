"""
需求：实现mysql的4个功能：1.insert_csv 2.create_table 3.fetch_all_questions 4. fetch_answer
思路：
1. 初始化MySQL链接connection, cursor
2. 实现建表
3. 实现插入数据
4. 实现拉取所有的问题
5. 实现根据问题获取答案
6. 关闭链接
"""

import pymysql

from base.config import single_config as config
from base.logger import single_logger as logger
import pandas as pd


class MysqlClient:

    def __init__(self):
        try:
            # 获取链接：和mysql进行通信。操作事务相关
            # MySQL连接，这个是一个长连接
            self.connect = pymysql.connect(host=config.MYSQL_HOST
                                           , port=3306
                                           , user=config.MYSQL_USER
                                           ,password=config.MYSQL_PASSWORD
                                           , db=config.MYSQL_DATABASE)
            # 获取游标
            # 游标作用：执行SQL， 获取执行结果
            self.cursor = self.connect.cursor()
            logger.info(f'MySQL连接成功，host:{config.MYSQL_HOST}, db:{config.MYSQL_DATABASE}')
        except Exception as e:
            logger.error(f'MySQL连接失败:{e}')
            raise

    def create_table(self):
        sql = """
             CREATE TABLE IF NOT EXISTS jpkb (
              id INT AUTO_INCREMENT PRIMARY KEY,
              subject_name VARCHAR(100) NOT NULL COMMENT '学科名称',
              question VARCHAR(512) NOT NULL COMMENT '问题',
              answer  VARCHAR(4096) NOT NULL COMMENT '答案'
          ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='JP学科知识问答';
        """
        try:
            self.cursor.execute(sql)
            logger.info('jpkb表创建成功（或已存在）')
        except Exception as e:
            logger.error(f'创建jpkb表失败:{e}')

    def insert_csv(self, csv_file):
        try:
            df = pd.read_csv(csv_file)
            logger.info(f'CSV文件读取成功，共{len(df)}条数据，文件:{csv_file}')

            for index, row in df.iterrows():
                sql = "INSERT INTO jpkb (subject_name, question, answer) VALUES (%s, %s, %s)"
                self.cursor.execute(sql, (row['学科名称'], row['问题'], row['答案']))
            self.connect.commit()
            logger.info(f'CSV数据插入MySQL成功，共{len(df)}条')
        except FileNotFoundError as e:
            logger.error(f'CSV文件不存在:{csv_file}, 错误:{e}')
        except pd.errors.EmptyDataError as e:
            logger.error(f'CSV文件为空:{csv_file}, 错误:{e}')
        except Exception as e:
            logger.error(f'CSV数据插入MySQL失败:{e}')
            # 发生异常时回滚，避免部分数据写入
            try:
                self.connect.rollback()
            except Exception as rollback_err:
                logger.error(f'数据回滚失败:{rollback_err}')
        # 通知 BM25 刷新（通过回调或直接调用）

    def fetch_all_questions(self):
        try:
            sql = "select question from jpkb"
            self.cursor.execute(sql)
            # 数据格式： [(question),(question)], 列表的元素数量 = 数据条数， 一个元组 = 一条记录
            fetchall = self.cursor.fetchall()
            if fetchall:
                # a,_   = (a,b) ; [0]
                questions = [row[0] for row in fetchall]
            else:
                questions = []
            logger.info(f'获取所有问题成功，共{len(questions)}条')
            return questions
        except Exception as e:
            logger.error(f'获取所有问题失败:{e}')
            return []

    def fetch_answer(self, question):
        try:
            sql = "select answer from jpkb where question = %s"
            self.cursor.execute(sql, (question,))
            # tuple
            answer_tuple = self.cursor.fetchone()
            if answer_tuple:
                logger.debug(f'获取答案成功，question:{question}')
                return answer_tuple[0]
            else:
                logger.debug(f'获取答案失败，question:{question}，未找到匹配记录')
                return None
        except Exception as e:
            logger.error(f'获取答案异常，question:{question}, 错误:{e}')
            return None

    def close(self):
        """关闭MySQL连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connect:
                self.connect.close()
            logger.info('MySQL连接已关闭')
        except Exception as e:
            logger.error(f'MySQL连接关闭失败:{e}')

    def update_answer(self, question, new_answer):
      self.cursor.execute(
          "UPDATE jpkb SET answer=%s WHERE question=%s", (new_answer, question))
      self.connection.commit()

    def delete_question(self, question):
      self.cursor.execute("DELETE FROM jpkb WHERE question=%s", (question,))
      self.connection.commit()
if __name__ == '__main__':
    client = MysqlClient()
    # client.create_table()
    client.insert_csv(
        'D:/BaiduNetdiskDownload/integrated_qa_system/mysql_qa/data/JP学科知识问答.csv')
    print(client.fetch_all_questions())
    print(len(client.fetch_all_questions()))
