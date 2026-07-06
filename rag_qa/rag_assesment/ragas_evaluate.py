"""
需求：使用RAGAS框架对RAG系统性能进行量化评估
思路步骤：
1. 数据准备：
    1.1 加载JSON格式的评估数据集（含问题/答案/上下文/真实答案。
    1.2 转换为RAGAS要求的Dataset(datasets)格式（question/answer/contexts/ground_truth）
2. 环境配置：
    2.1 LLM: 初始化大语言模型用于指标推理
    2.2 embedding: 配嵌入模型计算语义相似度置
3. 指标选择：
    3.1 忠实度（Faithfulness）：验证答案与上下文的事实一致性
    3.2 答案相关性（Answer Relevancy）：评估答案与问题的匹配度
    3.3 上下文相关性（Context Relevancy）：检测上下文信息的简洁性
    3.4 上下文召回率（Context Recall）：衡量上下文覆盖真实答案的完整性
4. 执行评估：
    4.1 调用evaluate函数并行计算各指标得分
    4.2 集成LLM和嵌入模型实现自动化评分
5. 结果处理：
    5.1 控制台打印多维评分结果
    5.2 转换为DataFrame并持久化为CSV文件
"""
# 导入pandas库，用于数据处理和保存CSV文件
import pandas as pd
# 导入ragas库的evaluate函数，用于执行RAG评估
from ragas import evaluate
# 导入ragas的评估指标，包括忠实度、答案相关性、上下文相关性和上下文召回率
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextRelevance,
    ContextRecall
)
# 导入datasets库的Dataset类，用于构建RAGAS所需的数据格式
# datasets是hugging-face官网数据集的库
# 1. 通用格式（transformers库） 2.内置一些常用的数据集，可以直接下载
from datasets import Dataset

# 导入langchain_openai的聊天模型和dashscope嵌入模型，用于本地模型调用
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings

# 导入json库，用于加载JSON格式的评估数据集
import json
from base.config import config

# 1. 加载生成的数据集
# 使用with语句打开JSON文件，确保文件正确关闭，指定编码为utf-8
with open("rag_evaluate_data.json", "r", encoding="utf-8") as f:
    # 将JSON文件内容加载到data变量中，data为包含多个数据条目的列表
    # loads = load_str
    # json.loads(): 加载的是字符串
    # json.load(): 加载的是文件
    data = json.load(f)

# 2. 转换为RAGAS格式
# 创建字典eval_data，将JSON数据转换为RAGAS要求的字段格式
eval_data = {
    # 提取每个数据条目的question字段，组成问题列表
    "question": [item["question"] for item in data],
    # 提取每个数据条目的answer字段，组成答案列表
    "answer": [item["answer"] for item in data],
    # 提取每个数据条目的context字段，组成上下文列表（每个context为列表）
    "contexts": [item["context"] for item in data],
    # 提取每个数据条目的ground_truth字段，组成真实答案列表
    "ground_truth": [item["ground_truth"] for item in data]
}
# 使用Dataset.from_dict将字典转换为RAGAS所需的Dataset对象
dataset = Dataset.from_dict(eval_data)

# 初始化通义千问模型（使用OpenAI兼容接口）
llm = ChatOpenAI(
    model_name=config.LLM_MODEL,  # 使用qwen-plus模型
    openai_api_base=config.DASHSCOPE_BASE_URL,
    openai_api_key=config.DASHSCOPE_API_KEY,
    temperature=0 # 控制生成结果的随机性
)

# 初始化通义千问嵌入模型
embeddings = DashScopeEmbeddings(
    model="text-embedding-v4",  # 通义千问嵌入模型
    dashscope_api_key=config.DASHSCOPE_API_KEY
)

# 4. 执行评估
# 调用evaluate函数，传入数据集、评估指标、LLM模型和嵌入模型
result = evaluate(
    # 传入转换好的Dataset对象
    dataset=dataset,
    # 指定使用的评估指标列表
    metrics=[
        Faithfulness(),  # 忠实度：答案是否基于上下文
        AnswerRelevancy(),  # 答案相关性：答案与问题的匹配度
        ContextRelevance(),  # 上下文相关性：上下文是否仅包含相关信息
        ContextRecall()  # 上下文召回率：上下文是否包含所有必要信息
    ],
    # 传入配置好的LLM模型
    llm=llm,
    # 传入配置好的嵌入模型
    embeddings=embeddings
)

# 5. 输出并保存结果
# 打印评估结果标题
print("RAGAS评估结果：")
# 打印评估结果，包含各指标的分数
print(result)
# 将评估结果转换为pandas DataFrame，便于保存
result_df = pd.DataFrame([result])
# 将DataFrame保存为CSV文件，文件名为ragas_evaluation_results.csv，不保存索引
result_df.to_csv("ragas_evaluation_results.csv", index=False)
