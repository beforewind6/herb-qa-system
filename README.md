# 🌿 杏林问答 — 中医药知识智能问答系统

> **杏林春暖，橘井泉香** — 基于 RAG + FAQ 双引擎的中医药知识智能问答平台

## 🏥 项目简介

杏林问答是一款面向中医药领域的智能问答系统，集成了 **MySQL FAQ 检索** 与 **RAG（检索增强生成）** 双引擎架构，能够快速、准确地回答中药药性、方剂配伍、中医基础理论、针灸穴位等相关问题。

系统核心功能：
- **FAQ 快速匹配**：基于 BM25 算法的 MySQL 知识库检索，毫秒级响应
- **RAG 深度问答**：结合向量检索与 LLM 生成，提供详尽的专业解答
- **流式输出**：WebSocket 实时流式响应，提升用户体验
- **多轮对话**：MySQL 持久化会话历史，支持上下文连续问答

## 📂 知识分类

| 分类 | 内容范围 |
|------|--------|
| 🌿 **中药基础** | 四气五味、药材功效、配伍禁忌、道地药材 |
| 📜 **方剂学** | 经典方剂组成、功效主治、配伍特点 |
| ☯ **中医基础理论** | 阴阳五行、八纲辨证、气血津液 |
| 📍 **针灸学** | 穴位定位、经络走向、针灸技法 |

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/beforewind6/herb-qa-system.git
cd herb-qa-system

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 MySQL、Redis、Milvus（编辑 config.ini）

# 4. 导入知识库数据
# 将 mysql_qa/data/TCM中药知识问答.csv 导入 MySQL

# 5. 启动服务
python app.py
```

访问 `http://localhost:8080` 即可使用。

## 🛠 技术栈

- **后端**: FastAPI + WebSocket + Uvicorn
- **FAQ 检索引擎**: BM25 + MySQL + Redis 缓存
- **RAG 引擎**: BGE-M3 向量模型 + Milvus 向量库 + Qwen LLM
- **前端**: 原生 HTML/CSS/JS + Markdown 渲染 + 暗色模式
- **数据**: MySQL 持久化 + CSV 知识库

## 📁 项目结构

```
herb-qa-system/
├── app.py                    # FastAPI 主服务
├── new_main.py               # FAQ + RAG 双引擎集成
├── config.ini                # 全局配置
├── base/                     # 基础模块 (配置/日志)
├── mysql_qa/                 # FAQ 引擎
│   ├── data/                 # 知识库 CSV
│   ├── db/                   # MySQL 客户端
│   ├── cache/                # Redis 缓存
│   ├── retrieval/            # BM25 检索
│   └── utils/                # 预处理工具
├── rag_qa/                   # RAG 引擎
│   ├── core/                 # 核心逻辑 (检索/生成/分类)
│   ├── edu_document_loaders/ # 文档加载器
│   └── edu_text_spliter/     # 文本分割器
├── static/
│   └── index.html            # 前端界面
└── requirements.txt          # Python 依赖
```

## 💚 关于杏林

「杏林」典出三国名医董奉，其为人治病不收钱，只令病愈者植杏树数株，日久杏树成林。后世以「杏林春暖」赞誉医家仁心仁术。本项目以此为名，旨在传承与弘扬中医药文化瑰宝。

## 📜 许可证

MIT License
