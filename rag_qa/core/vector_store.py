# 导入 BGE-M3 嵌入函数，用于生成文档和查询的向量表示
from milvus_model.hybrid import BGEM3EmbeddingFunction
# 导入 Milvus 相关类，用于操作向量数据库
from pymilvus import MilvusClient, DataType, AnnSearchRequest, WeightedRanker
# 导入 Document 类，用于创建文档对象
from langchain_core.documents import Document
# 导入 CrossEncoder，用于重排序和 NLI 判断
from sentence_transformers import CrossEncoder
# 导入 hashlib 模块，用于生成唯一 ID 的哈希值
import hashlib
# 导入 time 模块，用于生成时间戳
import time
from base.config import config
from base.logger import logger
import sys
import os
import torch

# core/vector_store.py
# 定义 VectorStore 类，封装向量存储和检索功能

# local_path = os.path.abspath(os.path.dirname(__file__))
# rag_qa_path = os.path.abspath(os.path.dirname(local_path))
# sys.path.insert(0, rag_qa_path)
# project_root = os.path.dirname(rag_qa_path)
# sys.path.insert(0, project_root)

"""
需求：初始化VectorStore
思路步骤：
1. 构造milvus连接相关的参数: host、port、db、collection_name
2. 构造嵌入模型
3. 构造rerank模型
4. 创建或加载milvus集合，保证milvus表存在

"""


class VectorStore:
    # 初始化方法，设置向量存储的基本参数
    def __init__(self,
                 collection_name=config.MILVUS_COLLECTION_NAME,
                 host=config.MILVUS_HOST,
                 port=config.MILVUS_PORT,
                 database=config.MILVUS_DATABASE_NAME):
        # 1. 构造milvus连接相关的参数: host、port、db、collection_name
        # 设置 Milvus 集合名称
        self.collection_name = collection_name
        # 设置 Milvus 主机地址
        self.host = host
        # 设置 Milvus 端口号
        self.port = port
        # 设置 Milvus 数据库名称
        self.database = database
        # 初始化 Milvus 客户端，连接到指定主机和数据库
        # TODO 生产环境需要输入用户名和密码
        self.client = MilvusClient(uri=f"http://{self.host}:{self.port}", db_name=self.database)
        # 设置日志记录器
        self.logger = logger

        # 调用方法创建或加载 Milvus 集合
        self._create_or_load_collection()

        # 2. 构造嵌入模型
        bge_m3_model_path = os.path.join(config.MODELS_DIR, 'bge-m3')

        # 构造bge-m3模型，通过路径加载的方式把模型加载到内存中
        self.embedding_function = BGEM3EmbeddingFunction(
            # 传入模型名: 自动下载； 传入路径:直接加载
            model_name_or_path=bge_m3_model_path
            # f16: 半精度浮点数 这里取false相当于使用fp32
            # TODO 是否开启半精度
            , use_f16=False,
            # 推理（预测）设备
            # TODO 专业卡：A100, H100, A800. 消费卡：RTX4090, RTX5090
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )



        # 3. 构造rerank模型
        # 4. 创建或加载milvus集合，保证milvus表存在

        rerank_model_path = os.path.join(config.MODELS_DIR, 'bge-reranker-large')
        # 初始化 BGE-Reranker 模型，用于重排序检索结果
        # TODO device代表设备： mps:m1系列的mac/ cpu: cpu / cuda: nvidia的gpu。和操作系统无关
        self.reranker = CrossEncoder(rerank_model_path
                                     , device='cuda' if torch.cuda.is_available() else 'cpu')


    """
    需求：实现创建或加载集合方法：检查并创建或加载Milvus集合，定义字段结构和索引参数
    思路步骤：
    1. 判断集合是否存在，若存在则进行加载
    2. 集合不存在，创建新集合
        2.1 定义集合各字段 id、text、dense_vector、sparse_vector、parent_id、 parent_content、source 、timestamp
        2.2 定义索引： 稠密向量索引：dense_vector ， 稀疏向量索引：sparse_vector
    3. 把集合的索引加载到内存中
    """

    # 定义私有方法，创建或加载 Milvus 集合
    def _create_or_load_collection(self):
        # 检查指定集合是否已存在
        # if self.collection_name not in client.list_collections()
        if not self.client.has_collection(self.collection_name):
            # 创建集合 Schema，禁用自动 ID，启用动态字段
            # TODO 主键不使用自增 开启动态字段
            schema = self.client.create_schema(auto_id=False, enable_dynamic_field=True)
            # 添加 ID 字段，作为主键，VARCHAR 类型，最大长度 100
            # TODO id 无序，基于子块的内容生成唯一的id。  (文本1) -> md5 -> (05ff)
            schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=100)
            # 添加子块文本字段，VARCHAR 类型，最大长度 65535
            schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
            # 添加稠密向量字段，FLOAT_VECTOR 类型，维度由嵌入函数指定
            schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=1024)
            # 添加稀疏向量字段，SPARSE_FLOAT_VECTOR 类型
            # TODO 稀疏向量由bge-m3模型生成，和bm25没有任何关系
            schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)
            # 添加父块 ID 字段，VARCHAR 类型，最大长度 100
            schema.add_field(field_name="parent_id", datatype=DataType.VARCHAR, max_length=100)
            # 添加父块内容字段，VARCHAR 类型，最大长度 65535
            # TODO 父块内容
            schema.add_field(field_name="parent_content", datatype=DataType.VARCHAR, max_length=65535)
            # 添加学科类别字段，VARCHAR 类型，最大长度 50
            # TODO 学科，用于过滤
            schema.add_field(field_name="source", datatype=DataType.VARCHAR, max_length=50)
            # 添加时间戳字段，VARCHAR 类型，最大长度 50
            schema.add_field(field_name="timestamp", datatype=DataType.VARCHAR, max_length=50)

            # 创建索引参数对象
            index_params = self.client.prepare_index_params()
            # 为稠密向量字段添加 IVF_FLAT 索引，度量类型为内积 (IP)
            index_params.add_index(
                field_name="dense_vector",
                index_name="dense_index",
                index_type="IVF_FLAT",
                metric_type="IP",
                params={"nlist": 128}
            )
            # 为稀疏向量字段添加 SPARSE_INVERTED_INDEX 索引，度量类型为内积 (IP)
            index_params.add_index(
                field_name="sparse_vector",
                index_name="sparse_index",
                # 稀疏向量最常用的索引类型： 倒排索引（全文检索索引）
                index_type="SPARSE_INVERTED_INDEX",
                metric_type="IP",
                params={"drop_ratio_build": 0.2}
            )

            # 创建 Milvus 集合，应用定义的 Schema 和索引参数
            self.client.create_collection(collection_name=self.collection_name, schema=schema,
                                          index_params=index_params)
            # 记录创建集合的日志
            logger.info(f"已创建集合 {self.collection_name}")
        # 如果集合已存在
        else:
            # 记录加载集合的日志
            logger.info(f"已加载集合 {self.collection_name}")

        # 将集合加载到内存，确保可立即查询
        self.client.load_collection(self.collection_name)

    """
      需求：将分块后的文档转换为向量并存储到Milvus集合
      思路步骤：
      1. 提取文本,从文档对象中提取文本内容
      2. 生成向量,使用BGE-M3模型生成稠密和稀疏向量。
      3. 构造数据，为每篇文档生成唯一ID（MD5哈希）。将向量和元数据组织成字典
      4. 使用upsert操作插入或更新数据
      5. 支持批量处理，避免内存溢出
      """

    # 定义方法，向向量存储添加文档
    def add_documents(self, documents, batch_size=1000):
        """
        :param documents: 分块以后的子块内容 list[Document]
            Document(page_content=正文, metadata={父id、子id、父块内容parent_content、时间戳、路径、学科(source)})
        :param batch_size: 批处理大小，默认1000，可根据内存情况调整
        :return:  None 无返回值
        """
        total_docs = len(documents)
        logger.info(f"开始处理 {total_docs} 个文档，批次大小: {batch_size}")

        # 分批处理文档
        for start_idx in range(0, total_docs, batch_size):
            end_idx = min(start_idx + batch_size, total_docs)
            batch_docs = documents[start_idx:end_idx]

            logger.info(f"正在处理批次 {start_idx // batch_size + 1}/{(total_docs + batch_size - 1) // batch_size}, "
                        f"文档范围: {start_idx}-{end_idx - 1}")

            # 提取当前批次文档的内容列表
            texts = [child_chunk.page_content for child_chunk in batch_docs]

            # 使用 BGE-M3 嵌入函数生成文档的嵌入 ，传入list[str]
            # TODO 对于不同的嵌入模型，因为作者的设计是不一样的，没法统一。对于不同的模型，需要自己去了解对应的数据格式
            # embeddings : 字典类型。 sparse/dense
            # 假设使用text-embedding-v4（阿里） -> [n, 1024] 矩阵, 只有稠密向量

            # TODO：稀疏向量， 关键词对应的词频向量
            # embeddings['sparse'][i].indices = 第i个文档的所有的关键词 返回个一个
            # embeddings['sparse'][i].data = 第i个文档所有的关键词对应的权重

            # TODO：稠密向量， 句子转成的语义向量
            # embeddings['dense'] ->  二维矩阵 [n , 1024] n个子块对应的句子向量，一个句子 -> 1024维的向量

            try:
                embeddings = self.embedding_function(texts)

                # 初始化空列表，用于存储插入的数据
                data = []
                # 遍历当前批次的每个文档，带上索引 i
                for i, child_chunk in enumerate(batch_docs):
                    # 生成文档内容的 MD5 哈希值，作为唯一 ID
                    # hashlib.md5(): python库自带的一个通用的加密算法，能够将一串字符串文本转成一个32位，16进制的数字
                    # md5(x1) -> y1
                    # TODO 基于md5 hash算法，给子块生成一个唯一的id
                    text_hash = hashlib.md5(child_chunk.page_content.encode('utf-8')).hexdigest()

                    # 获取第 i 行的稀疏向量数据
                    sparse_row = embeddings['sparse'][i]
                    # 初始化稀疏向量字典
                    sparse_vector = {}
                    # TODO 示例，实际计算的时候原理类似，但是会有一些算法做了优化
                    # 文本1 -> (单词1=888，单词2=9，单词3=1001 ) 词表大小=2万。 -> {888:1, 9:1, 1001:1} -> 归一化 {888:0.33,9:0.33,1001:0.33}
                    # 获取稀疏向量的非零值索引
                    # col: [888,9,1001]
                    indices = sparse_row.col
                    # 获取稀疏向量的非零值
                    # data: [0.33,0.33,0.33]
                    values = sparse_row.data
                    # 将索引和值配对，填充稀疏向量字典
                    for idx, value in zip(indices, values):
                        sparse_vector[int(idx)] = float(value)

                    # 创建数据字典，包含所有字段
                    data.append({
                        # 通过hash算法生成的唯一ID
                        "id": text_hash,
                        # 子块的原文
                        "text": child_chunk.page_content,
                        # 1024维的稠密向量
                        "dense_vector": embeddings["dense"][i].tolist(),  # 转换为list以确保兼容性
                        # dict类型的稀疏向量
                        "sparse_vector": sparse_vector,
                        # 父块ID
                        "parent_id": child_chunk.metadata["parent_id"],
                        # 父块内容
                        "parent_content": child_chunk.metadata["parent_content"],
                        # 学科
                        "source": child_chunk.metadata.get("source", "unknown"),
                        # 时间戳
                        "timestamp": child_chunk.metadata.get("timestamp", "unknown"),
                    })

                # 检查是否有数据需要插入
                if data:
                    # 使用 upsert 操作插入数据，覆盖重复 ID
                    self.client.upsert(collection_name=self.collection_name, data=data)
                    # 记录插入或更新的文档数量日志
                    logger.info(f"批次完成: 已插入或更新 {len(data)} 个文档 (批次 {start_idx // batch_size + 1})")
                else:
                    logger.warning(f"批次 {start_idx // batch_size + 1} 中没有数据需要插入")

            except Exception as e:
                logger.error(f"处理批次 {start_idx // batch_size + 1} 时发生错误: {str(e)}")
                # 继续处理下一个批次而不是中断整个过程
                continue

        logger.info(f"完成处理 {total_docs} 个文档")

    """
    需求：对输入的query进行混合检索
    思路步骤：
    1. 生成查询向量：使用BGE-M3生成稠密和稀疏向量。
    2. 构造检索请求(混合检索)：
        2.1 构造稠密向量的AnnSearchRequest(列名、limit、查询参数、查询向量、过滤条件)
        2.2 构造稀疏向量的AnnSearchRequest(列名、limit、查询参数、查询向量、过滤条件)
    3. 混合检索： 使用WeightedRanker融合结果，调用hybrid_search()
    4. 重排序（精排），使用CrossEncoder:reranker重新排序父文档
    """

    def hybrid_search_with_rerank(self, query, k=config.RETRIEVAL_K, source_filter=None):
        """
        对输入的query进行混合检索
        :param query: 用户的查询字符串（原始的或者是被改写过的）
        :param k: milvus返回的limit值
        :param source_filter: 学科过滤条件
        :return: 返回父块candidate_m个(上下文)
        """
        # 把query进行embedding， [query]
        # TODO 使用BGE-M3生成 ① 稠密 ②稀疏向量 （文档写入milvus的也执行过同样的操作）,这是为了保证一样的文本转换成向量的数值完全一致
        query_embeddings = self.embedding_function([str(query)])

        # 获得稠密向量
        dense_query_vector = query_embeddings['dense'][0]

        # 获得稀疏向量
        spase_query_vector = {}
        row = query_embeddings['sparse'][0]
        indices = row.col
        values = row.data

        for token_id, value in zip(indices, values):
            spase_query_vector[token_id] = value

        # 支持根据学科过滤的场景
        filter_expr = f'source == "{source_filter}"' if source_filter else ''

        # 构建稠密向量的查询对象
        dense_request = AnnSearchRequest(
            data=[dense_query_vector],
            anns_field='dense_vector',
            # IP：内积
            # nprobe：查询最近的几个簇
            # IVF_FLAT
            param={'metric_type': 'IP', 'params': {'nprobe': 10}},
            limit=k,
            expr=filter_expr
        )

        sparse_request = AnnSearchRequest(
            data=[spase_query_vector],
            anns_field='sparse_vector',
            # 倒排索引， SPARSE_INVERTED_INDEX
            param={'metric_type': 'IP', 'params': {}},
            limit=k,
            expr=filter_expr
        )

        # 权重混合检索排序
        # 0.7: 稠密向量, 句子向量
        # 1.0: 稀疏向量, 稀疏向量给的大
        # TODO：我们用这种方式是因为我们认为稀疏向量（单词+权重）对检索结果影响更大
        ranker = WeightedRanker(0.7, 1.0)

        results = self.client.hybrid_search(
            collection_name=self.collection_name,
            reqs=[dense_request, sparse_request],
            ranker=ranker,
            limit=k,
            output_fields=["text", "parent_id", "parent_content", "source", "timestamp"]
        )[0]

        # milvus的查询结果是二维的结构 [m=1,n=limit]
        # m = 传入了几个查询向量（批量查询几个向量）
        # n = limit ，每个查询返回的topK

        # 拿到检索到的所有的子块
        # _doc_from_hit: 把milvus返回的结果封装成Document对象
        sub_chunks = [self._doc_from_hit(hit['entity']) for hit in results]

        # TODO：通过子块，拿到所有的父块的内容，并进行去重
        parent_docs = self._get_unique_parent_docs(sub_chunks)

        # -----------------------------------到此为止，已经完成了粗排-------------------------------------

        if parent_docs:
            # 如果父块只有一个，进行返回
            if len(parent_docs) < 2:
                return parent_docs
            # 这里的parent_docs其实就是context
            # 如果父块超过一个，需要进行重排序： 基于query 和context的匹配程度做重排序
            # 构造： (query, context) 对
            # TODO 注意：这里的query是用户提出的原始的问题，context是查询到的相关上下文
            # rerank模型的作用就是基于rerank模型，再次计算query和context的相关性
            # pairs = [ [query, contex1], [query, contex2]  ,[query, contex3] ....]
            # pairs = [n ,2] , n = 参与rerank的父块的数量
            pairs = [[query, doc.page_content] for doc in parent_docs]

            # TODO 通过rerank模型， 计算 query 和 context(一个父块) 的分数，相似度
            # scores: [n] ， query和每个父块的相似度分数
            scores = self.reranker.predict(pairs)

            # 排序，按照分数的大小进行倒排。 分数高的排到前面
            # zip: (0.3, 父块1), (0.5,父块2)
            # sorted -> (0.5, 父块2), (0.3,父块1) 。根据元祖的第一个元素进行排序, reverse=True
            # TODO 这里直接做了排序， 可以再增加一个判断score是否大于某个阈值的逻辑。比较有技术含量
            ranked_parent_docs = [doc for _, doc in sorted(zip(scores, parent_docs), reverse=True)]
        else:
            ranked_parent_docs = []
        return ranked_parent_docs[:config.CANDIDATE_M]

        # TODO 最后保留CANDIDATE_M个父块作为最终的context
        # TODO 切片操作[:config.CANDIDATE_M] -> 切片 相当于 只保存列表中下标从0到config.CANDIDATE_M的，[0,3)
        # 长度为 10的 list -> 长度不超过CANDIDATE_M
        # 类比 字符串的sub_string(0, CANDIDATE_M)
        # TODO CANDIDATE_M？ 考虑模型能支持的输入大小
        # 1. 考虑上下文(父块）大小：一个父块1200， 3个父块3600
        # 2. 考虑多轮对话
        # 总之：父块大小 + 多轮对话 + 提示词模板 < 模型上下文大小

        # TODO 注意：这里基于rerank的score排序以后得结果无论和问题的相关性多么小，总是取相对比较大的最大值。
        # TODO 这样会存在一个问题：有可能会查出来和问题完全不相干的。 所以可以在前面增加一个阈值判断

        # 返回CANDIDATE_M条数据
        # ranked_parent_docs: 相似度分数从大到小的10个父块
        # 通过切片的方式，截取前CANDIDATE_M个
        #  ranked_parent_docs[0:config.CANDIDATE_M] -> ranked_parent_docs数组截取下标从0到CANDIDATE_M, [0,CANDIDATE_M)


        # noinspection PyMethodMayBeStatic

    def _doc_from_hit(self, hit):
        """
        把milvus返回的dict格式的子块转成Document格式
        :param hit: milvus返回的子块的各个字段，dict类型
        :return: Document类型的子块
        """
        return Document(
            page_content=hit['text'],
            metadata={
                'source': hit['source'],
                'timestamp': hit['timestamp'],
                'parent_id': hit['parent_id'],
                'parent_content': hit['parent_content']
            }
        )

        # noinspection PyMethodMayBeStatic

    def _get_unique_parent_docs(self, sub_chunks):
        """
        从子块中提取父块，并进行去重
        :param sub_chunks:  从milvus中查询到的所有的子块
        :return:    去重后的父块
        """
        parent_docs = set()
        # 返回值
        unique_parent_docs = []

        for chunk in sub_chunks:
            # 拿到每个子块的父块内容
            parent_content = chunk.metadata.get('parent_content', chunk.page_content)
            # 父块内容非空，且不重复
            if parent_content and parent_content not in parent_docs:
                # 构建一个父块对象，放到返回值集合中
                unique_parent_docs.append(
                    Document(
                        # TODO 需要注意，这里的内容存放的是父块的文本
                        page_content=parent_content
                        , metadata=chunk.metadata
                    )
                )
                # 放到set中，表示已经出现过
                parent_docs.add(parent_content)

        return unique_parent_docs


if __name__ == '__main__':
    # import document_processor
    #
    # documents = document_processor.process_documents(
    #     'D:/BaiduNetdiskDownload/integrated_qa_system/rag_qa/data/ai_data')
    # store = VectorStore()
    # store.add_documents(documents)
    store = VectorStore()
    result = store.hybrid_search_with_rerank("大模型学什么")
    print(result)