# 导入标准库
import json
import os
# 导入 PyTorch
import torch
# 导入日志
import sys
from base.logger import logger
from base.config import config
# 导入numpy
import numpy as np
# 导入 Transformers 库
from transformers import BertTokenizer, BertForSequenceClassification
# TODO 重点：模型训练和预测使用的工具
from transformers import Trainer, TrainingArguments

# 导入train_test_split
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix


"""
意图识别模块，提供如下功能：
1. 数据加载：读取 5000 条 JSON 数据集，包含查询和标签（“通用知识”或“专业咨询”）
2. 模型训练：使用 bert-base-chinese 模型，微调二分类任务，准确率达 90%+
3. 评估优化：直接处理数字标签（0 或 1），生成分类报告和混淆矩阵
4. 预测接口：支持实时分类，集成到 EduRAG 系统。

为了满足以上功能，需要实现以下需求：
1. 初始化方法：初始化预训练的分词器、 预训练的模型。 如果是在线上阶段，主要是负责加载训练好的模型
2. 数据预处理：将查询文本和预测标签转化为模型的输入数据格式
3. 构建数据集：用于模型的训练，适配模型的训练函数
4. 模型训练：基于处理好的数据集划分出来训练集，对模型进行训练
5. 模型评估：在数据集划分出来的验证集，对模型进行评估
6. 模型预测：加载训练好的模型，完成意图识别任务
"""


current_dir = os.path.dirname(os.path.abspath(__file__))
rag_qa_path = os.path.abspath(os.path.dirname(os.path.abspath(current_dir)))
project_root = os.path.abspath(os.path.dirname(os.path.abspath(rag_qa_path)))


class QueryClassifier(object):
    """
    需求：初始化预训练的分词器、 预训练的模型。 如果是在上线阶段，主要是负责加载训练好的模型
    思路步骤：
    1. 获取bert预训练模型所在的目录
    2. 加载预训练分词器
    3. 设置训练设备
    4. 定义标签映射
    5. 尝试加载模型
    """

    def __init__(self, model_path='models/bert_query_classifier'):
        # 加载bert
        self.pre_trained_model_path = f'{rag_qa_path}/models/bert-base-chinese'
        # 模型训练以后保存的位置
        self.model_path = model_path
        # 加载tokenizer(词表)
        # TODO 因为我们项目的微调，没有改变词表，所以对于微调过的模型和没有微调的模型，我们使用的tokenizer没有任何变化
        self.tokenizer = BertTokenizer.from_pretrained(self.pre_trained_model_path)
        # 模型对象
        self.model = None
        # 训练和预测的设备
        # self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.device =  torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.mps.is_available() else "cpu" )

        logger.info(f"使用设备: {self.device}")
        # 定义标签映射 (相当于label的词表)
        self.label_map = {"通用知识": 0, "专业咨询": 1}
        # 加载模型
        self.load_model()

    # TODO 加载模型transformers库高度封装的API
    def load_model(self):
        # 1. 对于训练好的模型
        if os.path.exists(self.model_path):
            self.model = BertForSequenceClassification.from_pretrained(self.model_path)
            self.model.to(self.device)
            logger.info(f"模型加载成功：{self.model_path}")
        else:
            # 2.对于第一次训练模型
            # TODO 加载预训练模型bert-base-chinese，num_labels=2的含义是构建一个2分类的线性层，实现二分类
            self.model = BertForSequenceClassification.from_pretrained(self.pre_trained_model_path, num_labels=2)
            # 把模型的参数移动到设备中
            self.model.to(self.device)
            logger.info("初始化新 BERT 模型")

        # for name, param in self.model.named_parameters():
        #     print(f'param_name --> {name} | shape --> {param.shape}')

    # TODO 这里的保存用的是transformers库高度封装的API
    # 如果使用torch框架保存，只支持模型本体的保存，词表的需要用户自己写代码保存
    def save_model(self):
        # 1. 保存模型本体
        self.model.save_pretrained(self.model_path)
        # 2. 保存的模型的词表。 单词->id映射关系
        self.tokenizer.save_pretrained(self.model_path)
        logger.info(f"保存模型成功：{self.model_path}")

    """
    需求：实现数据预处理，将查询文本和预测标签转化为模型的输入数据格式
    思路步骤：
    1. 接收传入的query数据和分类标签数据
    2. 将查询文本数值化，使用预训练的tokenizer对query进行编码和长度补齐，得到input_ids和attention_mask
    3. 将标签数据数值化
    """

    # TODO 这里我们使用3行处理了数据，但是在实际工作中，这里要复杂得多。一般来讲很少有数据直接可以拿来用
    def preprocess_data(self, texts, labels):
        # texts： [问题1,问题2,...问题n] -> ["解释一下什么是RESTful API。"]
        # labels：[标签1,标签2,...标签n] -> ["通用知识"]
        # ["你是谁","解释一下什么是RESTful API。"]
        # pt: pytorch的缩写。 tf: tensorflow
        # tensor: 张量， 1个数字-常量，1维数组-向量，2维数组-矩阵，3维？ 张量：1~n维数据的统称。
        encodings = self.tokenizer(texts
                                   # 样本是否进行截断
                                   , truncation=True
                                   # 样本是否进行填充
                                   # 填充规则：按照当前的文本中最长的那条进行填充，但是不能超过max_length
                                   , padding=True
                                   # 最大长度
                                   , max_length=128
                                   # pt = pytorch
                                   , return_tensors="pt"
                                   )

        # encodings 字典 -> input_ids , attention_mask , token_types
        # label_map 字典 {'通用知识': 0}

        return encodings, [self.label_map[label] for label in labels]

    """
    需求：实现数据集的构建，用于模型的训练，适配模型的训练函数
    思路步骤：
    1. 预处理的数据化query和label数据
    2. 继承实现Dataset类
        2.1 实现初始化方法
        2.2 实现__getitem__，根据索引拿到对应的数据
        2.3 实现__len__，获取数据集长度
    3. 构建Dataset类并返回
    """

    def create_dataset(self, encodings, labels):
        class Dataset(torch.utils.data.Dataset):
            def __init__(self, encodings, labels):
                self.encodings = encodings
                self.labels = labels

            # 根据索引，获取对应的值
            def __getitem__(self, idx):
                # encodings: { 'input_ids': input_ids, 'attention_mask':attention_mask  }

                # input_ids: tensor[batch_size(有几句话，几条数据)=n, seq_len(一句话多长)=<128]"
                # val[idx]： 第idx条数据的编码以后的id

                item = {key: val[idx] for key, val in self.encodings.items()}

                item["labels"] = torch.tensor(self.labels[idx])
                # tensor[seq_len]
                # TODO item {"labels":第idx条数据的label, "attention_mask":第idx条数据attention_mask, "input_ids":第idx条数据input_ids,"token_type_ids":第idx条数据的token_type_ids}
                return item

            def __len__(self):
                return len(self.labels)

        return Dataset(encodings, labels)

    """
    需求：实现模型的训练方法，基于处理好的数据集划分出来训练集，对模型进行训练
    思路步骤：
    1. 数据预处理
        1.1 加载数据集
        1.2 把数据集划分成8:2的训练集和验证集 
        1.3 把数据进行数值化
        1.4 构建Dataset
    2. 设置训练参数
    3. 初始化Trainer，传入参数、数据集、模型对象等
    4. 开启训练
    5. 保存模型
    6. 评估模型
    """

    def train_model(self, data_file='raining_dataset_hybrid_5000.json'):
        # 保护性代码，确保训练的数据是存在的
        if not os.path.exists(data_file):
            logger.error(f"数据集文件 {data_file} 不存在")
            raise FileNotFoundError(f"数据集文件 {data_file} 不存在")

        # 打开文件作为f变量，最后退出的时候，自动调用close
        with open(data_file, "r", encoding="utf-8") as f:
            data = [json.loads(value) for value in f.readlines()]

        # list[dict{query, label}]

        texts = [item["query"] for item in data]

        labels = [item["label"] for item in data]

        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=0.2, random_state=42
        )

        # preprocess_data ：传入文本，返回张量
        train_encodings, train_labels = self.preprocess_data(train_texts, train_labels)
        val_encodings, val_labels = self.preprocess_data(val_texts, val_labels)

        train_dataset = self.create_dataset(train_encodings, train_labels)
        val_dataset = self.create_dataset(val_encodings, val_labels)

        training_args = TrainingArguments(
            # 设置模型和检查点保存的目录路径
            output_dir="bert_results",
            # 设置最多保存1个检查点文件，超出时自动删除旧的
            save_total_limit=1,
            # 设置训练的总轮数为3轮
            num_train_epochs=3,
            # 设置每个设备（GPU/CPU）上的训练批次大小为8
            per_device_train_batch_size=8,
            # 设置每个设备（GPU/CPU）上的评估批次大小为8
            per_device_eval_batch_size=8,
            # 设置学习率预热步数为500步，训练初期学习率从0逐渐增加到设定值
            warmup_steps=500,
            # 设置权重衰减系数为0.01，用于防止过拟合
            # TODO 使用权重衰减，说明训练的时候用的优化器是adamW
            weight_decay=0.01,
            # 设置日志文件保存的目录路径
            logging_dir="./bert_logs",
            # 设置每10个训练步骤记录一次日志
            logging_steps=10,
            # 设置评估策略为每个epoch结束后进行评估
            evaluation_strategy="epoch",
            # 设置模型保存策略为每个epoch结束后保存
            save_strategy="epoch",
            # 设置训练结束后加载最佳模型而非最后一个模型
            load_best_model_at_end=True,
            # 设置用于判断最佳模型的指标为评估损失
            metric_for_best_model="eval_loss",
            # 禁用FP16混合精度训练，使用FP32精度
            fp16=False,
        )

        # 初始化 Trainer
        trainer = Trainer(
            # 传入要训练的模型实例
            model=self.model,
            # 传入上面定义的训练参数配置
            args=training_args,
            # 传入训练数据集
            train_dataset=train_dataset,
            # 传入验证数据集，用于训练过程中评估模型性能
            eval_dataset=val_dataset,
            # 传入计算评估指标的函数，用于在验证集上计算准确率等指标
            compute_metrics=self.compute_metrics
        )

        # 训练模型
        logger.info("开始训练 BERT 模型...")
        trainer.train()
        self.save_model()

        # 评估模型
        self.evaluate_model(val_texts, val_labels)

    def compute_metrics(self, eval_pred):
        """计算评估指标"""
        # logits：预测权重值 [-1.5, 2.0]
        # labels: 真实值 [0]
        logits, labels = eval_pred
        # TODO: 正常的做法 logits: [-1.5, 2.0] -> softmax归一化 -> [0.2, 0.8] -> argmax
        # TODO: 我们这里省略了softmax，直接取logits: [-1.5, 2.0] 最大值。
        # softmax不会影响数据前后的单调性（logits里面最大值，转成softmax归一化以后得结果，还是最大值）
        # argmax需要的是索引， argmax得到的结果就是：1
        # prediction = 1 , label = 0
        # predictions: [batch_size] -> labels:[batch_size]
        predictions = np.argmax(logits, axis=-1)
        accuracy = (predictions == labels).mean()
        return {"accuracy": accuracy}

    """
       需求：评估模型性能，输出分类报告和混淆矩阵
       思路步骤：
       1. 数据预处理
           1.1 对输入文本进行分词编码（截断/填充至128长度）
           1.2 创建包含编码和标签的Torch数据集
       2. 初始化预测工具
           2.1 创建Trainer实例加载当前模型
       3. 执行预测
           3.1 使用predict方法获取原始预测结果
           3.2 通过argmax解析预测标签，得到概率最大的预测值的标签id(0 ~ 1)
       4. 生成评估报告
           4.1 输出分类报告（含精确率/召回率/F1值）
           4.2 输出混淆矩阵
    """

    def evaluate_model(self, texts, labels):
        """评估模型性能"""
        # 仅对 texts 进行分词，labels 已为数字
        encodings = self.tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=128,
            return_tensors="pt"
        )
        dataset = self.create_dataset(encodings, labels)

        trainer = Trainer(model=self.model)
        predictions = trainer.predict(dataset)
        # predictions : [batch_size=97, 2]
        # np.softmax(predictions.predictions) ->  [-3.1, 2.7 ] /[ 0.3, 0.7 ]
        # argmax操作1维向量，所以我需要给它一个维度，它在哪个维度上去计算最大值 , array[-1]
        # predictions [batch,seq, tag_size=2]
        pred_labels = np.argmax(predictions.predictions, axis=-1)
        true_labels = labels  # 直接使用数字标签

        logger.info("分类报告:")
        logger.info(classification_report(
            true_labels,
            pred_labels,
            target_names=["通用知识", "专业咨询"]
        ))
        logger.info("混淆矩阵:")
        logger.info(confusion_matrix(true_labels, pred_labels))

    """
      需求：根据输入的查询语句预测其类别（通用知识或专业咨询）
          端到端： "Java学费一年多少钱"  -> "专业咨询"
      思路步骤：
      1. 加载模型, 并检查模型的状态
          1.1 验证模型是否已加载，未加载则记录错误并返回默认类别: 0->通用知识，让大模型处理query
      2. 输入数据处理
          2.1 对查询语句进行分词和编码（截断/填充至128长度）
          2.2 将编码数据移动到模型所在的设备
      3. 执行预测
          3.1 在无梯度模式下进行推理
          3.2 获取模型输出并解析预测结果（取logits最大值对应的类别）
      4. 结果映射
          4.1 将数字标签转换为对应的类别名称（0->通用知识，1->专业咨询）
      """

    def predict_category(self, query):
        # 检查模型是否加载
        if self.model is None:
            # 模型未加载，记录错误
            logger.error("模型未训练或加载")
            # 默认返回通用知识
            return "通用知识"
        # 对查询进行编码
        encoding = self.tokenizer(query, truncation=True, padding=True, max_length=128, return_tensors="pt")
        # 将编码移到指定设备
        #
        encoding = {k: v.to(self.device) for k, v in encoding.items()}
        # 不计算梯度，进行预测
        with torch.no_grad():
            # 获取模型输出
            # {"attention_mask":attention_mask, "input_ids":input_ids,"token_type_ids": token_type_ids}
            outputs = self.model(**encoding)
            # 获取预测结果
            prediction = torch.argmax(outputs.logits, dim=1).item()
        # 根据预测结果返回类别
        return "专业咨询" if prediction == 1 else "通用知识"


if __name__ == '__main__':
    from base.config import config
    model = QueryClassifier(model_path='../models/bert_query_classifier')
    path = f'/Users/itheima/Documents/黑马/讲课/就业班/edu-rag/南京1期/学生端/04-代码/00001.项目代码_课上/others/classify_data/model_generic_5000.json'
    train_model = model.train_model(path)

    # texts = []
    # labels = []
    #
    # with open(path, 'r', encoding='utf-8') as f:
    #     lines = f.readlines()
    #     for line in lines:
    #         json_data = json.loads(line)
    #         texts.append(json_data['query'])
    #         labels.append(json_data['label'])
    #
    # encodings, label_ids = model.preprocess_data(texts[:5], labels[:5])
    # print(texts[:5])
    # print(encodings['input_ids'].tolist())
    # print(encodings['attention_mask'].tolist())
    # #
    # dataset = model.create_dataset(encodings, labels)


    test_queries = [
        "AI学科的课程大纲是什么",
        "JAVA课程费用多少？",
        "5*9等于多少？",
        "AI培训有哪些老师？",
        "你是人吗",
        "蒙特卡罗树怎么用在风险投资的",
        "transformers有哪些常用的API",
        "大模型学费多少？",
        "大模型学什么？",
        "python大模型学科和智能应用开发有什么区别？"
    ]
    for query in test_queries:
        category = model.predict_category(query)
        print(f"查询: {query} -> 分类: {category}")

