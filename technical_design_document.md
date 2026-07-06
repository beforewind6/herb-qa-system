# 问答系统技术设计文档

## 1. 系统概述

### 1.1 系统简介
问答系统是一个基于FastAPI框架开发的智能问答平台，集成了MySQL数据库和RAG（Retrieval-Augmented Generation）技术。系统通过向量检索和大语言模型相结合的方式，为用户提供精准的问答服务。

### 1.2 系统架构
- **架构模式**: 微服务架构
- **开发框架**: FastAPI
- **数据库**: MySQL + Milvus向量数据库
- **模型**: BGE-M3嵌入模型 + BGE-Reranker重排序模型

### 1.3 核心组件
- **API网关**: FastAPI应用层
- **业务逻辑层**: 问答处理逻辑
- **数据访问层**: MySQL和Milvus数据库访问
- **模型服务层**: 嵌入模型和重排序模型
- **会话管理层**: 用户会话管理

## 2. 系统架构设计

### 2.1 整体架构
```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Client    │◄──►│  FastAPI     │◄──►│ IntegratedQA    │
│             │    │   Server     │    │ System          │
└─────────────┘    └──────────────┘    ├─────────────────┤
                                      │ FAQ Module      │
                                      ├─────────────────┤
                                      │ RAG Module      │
                                      └─────────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    ▼                          ▼                          ▼
            ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
            │   MySQL      │         │   Milvus     │         │ Model Files  │
            │   Database   │         │   Vector DB  │         │   Storage    │
            └──────────────┘         └──────────────┘         └──────────────┘
```

### 2.2 技术栈
- **后端框架**: FastAPI 0.104+
- **异步处理**: asyncio, uvicorn
- **数据库**: PyMySQL, SQLAlchemy (MySQL), pymilvus (Milvus)
- **模型库**: milvus_model, sentence_transformers
- **序列化**: Pydantic v2
- **Web协议**: Starlette (WebSocket支持)

### 2.3 部署架构
- **应用服务器**: Uvicorn ASGI服务器
- **端口**: 默认8080
- **并发模型**: 异步非阻塞
- **跨域支持**: CORS中间件

## 3. 模块设计

### 3.1 API接口模块 (app.py)

#### 3.1.1 接口路由设计
```python
# 核心路由映射
GET  /                    # 首页访问
POST /api/create_session  # 创建会话
GET  /api/history/{session_id}     # 查询历史消息
DELETE /api/history/{session_id}   # 清除历史消息
POST /api/query          # 非流式查询
WS   /api/stream         # 流式查询WebSocket
GET  /health             # 健康检查
GET  /api/sources        # 获取学科类别
GET  /static/{path}      # 静态资源服务
```

#### 3.1.2 请求/响应模型设计
```python
# QueryRequest - 查询请求模型
class QueryRequest(BaseModel):
    query: str                    # 查询内容，必填
    source_filter: Optional[str] = None  # 学科过滤，可选
    session_id: Optional[str] = None     # 会话ID，可选

# QueryResponse - 查询响应模型
class QueryResponse(BaseModel):
    answer: str                  # 答案内容
    is_streaming: bool          # 是否流式响应
    session_id: str             # 会话ID
    processing_time: float      # 处理时间
```

#### 3.1.3 WebSocket消息协议设计
```python
# 发送消息格式
{
    "query": "string",           # 查询内容
    "source_filter": "string",   # 学科过滤，可选
    "session_id": "string"       # 会话ID，可选
}

# 接收消息类型
# 开始标志
{
    "type": "start",
    "session_id": "string"
}

# Token数据
{
    "type": "token",
    "token": "string",
    "session_id": "string"
}

# 结束标志
{
    "type": "end",
    "session_id": "string",
    "is_complete": true,
    "processing_time": "float"
}

# 错误消息
{
    "type": "error",
    "error": "string"
}
```

### 3.2 问答处理模块 (new_main.py)

#### 3.2.1 IntegratedQASystem类设计
```python
class IntegratedQASystem:
    def __init__(self):
        self.config = Config()                    # 配置管理
        self.faq = FAQSystem()                   # FAQ系统
        self.vector_store = VectorStore()        # 向量存储
        self.llm_caller = LLMDashScopeCaller()   # LLM调用器
        self.session_manager = SessionManager()  # 会话管理器
    
    def query(self, query, source_filter=None, session_id=None):
        # 主要查询方法，支持流式返回
        pass
    
    def get_session_history(self, session_id):
        # 获取会话历史
        pass
    
    def clear_session_history(self, session_id):
        # 清除会话历史
        pass
```

#### 3.2.2 问答策略设计
- **FAQ优先策略**: 首先尝试从FAQ数据库匹配答案
- **RAG策略**: 匹配度低于阈值(0.85)时启用RAG检索
- **流式输出策略**: RAG查询时采用流式输出提升用户体验

### 3.3 向量存储模块 (vector_store.py)

#### 3.3.1 VectorStore类设计
```python
class VectorStore:
    def __init__(self, collection_name, host, port, database):
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.database = database
        self.client = MilvusClient()                    # Milvus客户端
        self.embedding_function = BGEM3EmbeddingFunction()  # 嵌入模型
        self.reranker = CrossEncoder()                  # 重排序模型
        self.dense_dim = self.embedding_function.dim["dense"]  # 向量维度
    
    def add_documents(self, documents, batch_size=1000):
        # 批量添加文档到向量库
        pass
    
    def hybrid_search_with_rerank(self, query, source_filter=None, top_k=10):
        # 混合搜索并重排序
        pass
```

#### 3.3.2 数据模型设计
```python
# Milvus集合字段设计
{
    "id": VARCHAR(100),           # 主键，文档唯一ID
    "text": VARCHAR(65535),       # 子块文本内容
    "dense_vector": FLOAT_VECTOR, # 稠密向量，维度由embedding_function决定
    "sparse_vector": SPARSE_FLOAT_VECTOR,  # 稀疏向量
    "parent_id": VARCHAR(100),    # 父块ID
    "parent_content": VARCHAR(65535), # 父块内容
    "source": VARCHAR(50),        # 学科类别
    "timestamp": VARCHAR(50)      # 时间戳
}
```

#### 3.3.3 索引策略设计
- **稠密向量索引**: IVF_FLAT索引，metric_type="IP"，nlist=128
- **稀疏向量索引**: SPARSE_INVERTED_INDEX，metric_type="IP"，drop_ratio_build=0.2

### 3.4 会话管理模块

#### 3.4.1 会话数据结构
```python
class SessionData:
    def __init__(self, session_id, created_time, last_active, history):
        self.session_id = session_id      # 会话ID
        self.created_time = created_time  # 创建时间
        self.last_active = last_active    # 最后活跃时间
        self.history = history           # 对话历史列表
```

#### 3.4.2 会话管理策略
- **会话创建**: 自动生成UUID作为会话ID
- **会话存储**: 内存缓存 + 数据库持久化
- **会话清理**: 定期清理过期会话

### 3.5 模型服务模块

#### 3.5.1 嵌入模型服务
- **模型类型**: BGE-M3 (支持dense和sparse向量)
- **模型路径**: 从配置文件读取
- **设备支持**: CPU/GPU自动检测
- **向量维度**: 1024维稠密向量

#### 3.5.2 重排序模型服务
- **模型类型**: BGE-Reranker-Large
- **功能**: 对检索结果进行重排序
- **设备支持**: CPU/GPU自动检测

## 4. 数据库设计

### 4.1 MySQL数据库设计

#### 4.1.1 FAQ表结构
```sql
CREATE TABLE faq (
    id INT PRIMARY KEY AUTO_INCREMENT,
    question TEXT NOT NULL,           -- 问题内容
    answer TEXT NOT NULL,             -- 答案内容
    category VARCHAR(50),             -- 学科类别
    similarity_score FLOAT,           -- 相似度分数
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 4.1.2 会话历史表结构
```sql
CREATE TABLE session_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL, -- 会话ID
    role ENUM('user', 'assistant'),   -- 角色(user/question, assistant/answer)
    content TEXT NOT NULL,            -- 消息内容
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_timestamp (timestamp)
);
```

### 4.2 Milvus向量数据库设计

#### 4.2.1 集合Schema设计
```python
# 集合Schema定义
schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=True)
schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=100)
schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=dense_dim)
schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)
schema.add_field(field_name="parent_id", datatype=DataType.VARCHAR, max_length=100)
schema.add_field(field_name="parent_content", datatype=DataType.VARCHAR, max_length=65535)
schema.add_field(field_name="source", datatype=DataType.VARCHAR, max_length=50)
schema.add_field(field_name="timestamp", datatype=DataType.VARCHAR, max_length=50)
```

## 5. 接口详细设计

### 5.1 RESTful API设计

#### 5.1.1 会话管理接口
```python
# 创建会话
@app.post("/api/create_session")
async def create_session():
    """
    创建新会话
    - 输入: 无
    - 输出: {"session_id": "uuid-string"}
    - 异常: 500服务器错误
    """
    pass

# 查询历史
@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """
    查询会话历史
    - 输入: session_id (path参数)
    - 输出: {"session_id": "...", "history": [...]}
    - 异常: 500查询失败
    """
    pass

# 清除历史
@app.delete("/api/history/{session_id}")
async def clear_history(session_id: str):
    """
    清除会话历史
    - 输入: session_id (path参数)
    - 输出: {"status": "success", "message": "..."}
    - 异常: 500清除失败
    """
    pass
```

#### 5.1.2 问答查询接口
```python
# 非流式查询
@app.post("/api/query")
async def query(request: QueryRequest):
    """
    非流式问答查询
    - 输入: QueryRequest模型
    - 输出: QueryResponse模型
    - 逻辑: 
      1. 检查是否为日常问候
      2. 尝试FAQ匹配(阈值0.85)
      3. 需要RAG时提示使用WebSocket
    """
    pass
```

### 5.2 WebSocket接口设计

#### 5.2.1 流式问答协议
```python
@app.websocket("/api/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket流式问答
    - 协议: WebSocket
    - 消息格式: JSON
    - 流程:
      1. 接收查询请求
      2. 发送开始标志
      3. 流式返回token
      4. 发送结束标志
    """
    pass
```

## 6. 安全设计

### 6.1 认证授权
- **访问控制**: 无用户认证（开放服务）
- **频率限制**: 通过中间件实现请求频率限制
- **权限管理**: 按学科类别进行内容过滤

### 6.2 数据安全
- **数据隔离**: 会话数据按session_id隔离
- **隐私保护**: 不存储用户敏感信息
- **传输安全**: 支持HTTPS部署

### 6.3 输入验证
- **参数校验**: 通过Pydantic模型验证
- **注入防护**: 使用ORM防止SQL注入
- **XSS防护**: 输出内容转义

## 7. 性能设计

### 7.1 性能指标
- **响应时间**: 
  - 非流式查询: ≤ 2秒
  - 流式查询首包: ≤ 1秒
  - 健康检查: ≤ 100毫秒
- **吞吐量**: 并发用户数 ≥ 100
- **资源使用**: 内存使用率 ≤ 80%

### 7.2 性能优化策略
- **向量检索优化**: 使用Milvus混合索引
- **模型推理优化**: GPU加速 + 批处理
- **缓存策略**: 热门问题结果缓存
- **异步处理**: FastAPI异步特性充分利用

### 7.3 批处理设计
- **文档插入**: 支持批量插入，批次大小可配置
- **查询优化**: 向量检索支持top-k参数
- **内存管理**: 分批处理避免内存溢出

## 8. 部署设计

### 8.1 部署架构
- **应用服务器**: Uvicorn + Gunicorn (生产环境)
- **反向代理**: Nginx
- **负载均衡**: 支持多实例部署
- **容器化**: Docker支持

### 8.2 配置管理
```python
# 环境变量配置
HOST = os.getenv('HOST', '0.0.0.0')  # 服务绑定地址
PORT = int(os.getenv('PORT', 8080))   # 服务端口
```

### 8.3 监控设计
- **健康检查**: /health 接口
- **日志记录**: 结构化日志输出
- **性能监控**: 响应时间、错误率监控

## 9. 错误处理设计

### 9.1 异常分类
- **客户端错误**: 请求参数错误、资源不存在
- **服务端错误**: 内部服务错误、数据库连接失败
- **模型错误**: 推理失败、模型加载失败

### 9.2 错误响应格式
```json
{
    "detail": "错误描述信息"
}
```

### 9.3 重试机制
- **数据库连接**: 自动重连机制
- **模型服务**: 超时重试
- **外部API**: 指数退避重试

## 10. 扩展性设计

### 10.1 水平扩展
- **无状态设计**: 服务实例无状态
- **负载均衡**: 支持请求分发
- **数据分片**: Milvus支持数据分片

### 10.2 垂直扩展
- **模块化设计**: 各组件松耦合
- **插件机制**: 支持功能扩展
- **配置驱动**: 通过配置调整行为

## 11. 测试策略

### 11.1 单元测试
- **覆盖率**: ≥ 80%
- **测试框架**: pytest
- **Mock策略**: 模拟外部依赖

### 11.2 集成测试
- **API测试**: 接口功能验证
- **数据流测试**: 端到端数据流转
- **性能测试**: 压力和负载测试

### 11.3 部署测试
- **环境验证**: 部署后功能验证
- **配置测试**: 不同配置下的行为验证
- **回滚测试**: 版本回滚验证