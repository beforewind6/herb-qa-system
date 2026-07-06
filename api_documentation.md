# 问答系统 API 接口文档

## 项目概述
- **项目名称**: 问答系统API
- **项目描述**: 集成MySQL和RAG的智能问答系统
- **基础框架**: FastAPI
- **服务端口**: 默认 8080
- **跨域支持**: 允许所有来源（生产环境需限制）

## 接口列表

### 1. 首页访问
- **接口路径**: `GET /`
- **功能描述**: 根路径重定向到 index.html
- **请求参数**: 无
- **返回值**: 
  - `FileResponse`: 返回 static/index.html 文件
- **说明**: 访问根路径时返回前端页面

### 2. 创建会话
- **接口路径**: `POST /api/create_session`
- **功能描述**: 创建新的会话，生成唯一会话ID
- **请求参数**: 无
- **返回值**: 
  ```json
  {
    "session_id": "string"
  }
  ```
- **说明**: 生成UUID作为会话标识符

### 3. 查询历史消息
- **接口路径**: `GET /api/history/{session_id}`
- **功能描述**: 获取指定会话的历史记录
- **请求参数**:
  - `session_id` (path): 会话ID
- **返回值**: 
  ```json
  {
    "session_id": "string",
    "history": "array"
  }
  ```
- **错误码**:
  - `500`: 获取历史记录失败
- **说明**: 返回指定会话的所有历史记录

### 4. 清除历史消息
- **接口路径**: `DELETE /api/history/{session_id}`
- **功能描述**: 清除指定会话的历史记录
- **请求参数**:
  - `session_id` (path): 会话ID
- **返回值**: 
  ```json
  {
    "status": "success",
    "message": "历史记录已清除"
  }
  ```
- **错误码**:
  - `500`: 清除历史记录失败
- **说明**: 删除指定会话的所有历史记录

### 5. 非流式查询
- **接口路径**: `POST /api/query`
- **功能描述**: 执行非流式的问答查询
- **请求体**:
  ```json
  {
    "query": "string",           // 查询内容，必填
    "source_filter": "string",   // 学科过滤，可选
    "session_id": "string"       // 会话ID，可选
  }
  ```
- **返回值**:
  ```json
  {
    "answer": "string",          // 答案内容
    "is_streaming": "boolean",   // 是否流式响应
    "session_id": "string",      // 会话ID
    "processing_time": "float"   // 处理时间
  }
  ```
- **说明**: 
  - 如果是日常问候，直接返回模板回复
  - 如果需要RAG（阈值低于0.85），提示使用WebSocket接口
  - 否则返回MySQL中的答案

### 6. 流式查询 (WebSocket)
- **接口路径**: `WS /api/stream`
- **功能描述**: 通过WebSocket实现实时流式问答
- **通信协议**: WebSocket
- **发送消息格式**:
  ```json
  {
    "query": "string",           // 查询内容
    "source_filter": "string",   // 学科过滤，可选
    "session_id": "string"       // 会话ID，可选
  }
  ```
- **接收消息类型**:
  - **开始标志**:
    ```json
    {
      "type": "start",
      "session_id": "string"
    }
    ```
  - **Token数据**:
    ```json
    {
      "type": "token",
      "token": "string",
      "session_id": "string"
    }
    ```
  - **结束标志**:
    ```json
    {
      "type": "end",
      "session_id": "string",
      "is_complete": true,
      "processing_time": "float"
    }
    ```
  - **错误消息**:
    ```json
    {
      "type": "error",
      "error": "string"
    }
    ```
- **说明**: 实时返回问答结果，支持流式输出

### 7. 健康检查
- **接口路径**: `GET /health`
- **功能描述**: 检查服务健康状态
- **请求参数**: 无
- **返回值**: 
  ```json
  {
    "status": "healthy"
  }
  ```
- **说明**: 用于监控服务状态

### 8. 获取学科类别
- **接口路径**: `GET /api/sources`
- **功能描述**: 获取系统支持的有效学科类别列表
- **请求参数**: 无
- **返回值**: 
  ```json
  {
    "sources": ["string"]
  }
  ```
- **说明**: 返回系统中所有可用的学科类别

### 9. 静态资源
- **接口路径**: `GET /static/{path}`
- **功能描述**: 提供静态文件服务
- **请求参数**: 
  - `path` (path): 静态文件路径
- **返回值**: 静态文件内容
- **说明**: 服务前端所需的静态资源文件

## 请求模型定义

### QueryRequest
```json
{
  "query": "string",           // 查询内容，必填
  "source_filter": "string",   // 学科过滤，可选
  "session_id": "string"       // 会话ID，可选
}
```

### QueryResponse
```json
{
  "answer": "string",          // 答案内容
  "is_streaming": "boolean",   // 是否流式响应
  "session_id": "string",      // 会话ID
  "processing_time": "float"   // 处理时间
}
```

## 响应状态码

- `200`: 成功
- `500`: 服务器内部错误

## 特殊功能

### 日常问候识别
系统内置了日常问候语识别功能，支持以下类型的问候：
- 问候语: "你好", "您好", "hi", "hello"
- 身份询问: "你是谁", "您是谁", "你叫什么", "你的名字", "who are you"
- 在线确认: "在吗", "在不在", "有人吗"
- 状态询问: "干嘛呢", "你在干嘛", "做什么"

### 学科过滤
支持按学科类别进行内容过滤，可通过 `source_filter` 参数指定特定学科。

## 部署信息

- **启动命令**: `uvicorn app:app --host 0.0.0.0 --port 8080`
- **环境变量**:
  - `HOST`: 服务绑定的主机地址，默认为 `0.0.0.0`
  - `PORT`: 服务端口，默认为 `8080`