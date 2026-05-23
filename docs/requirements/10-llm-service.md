# 需求文档：LLM 服务

## 1. 需求概述

LLM 服务为系统提供自然语言理解、分类、SQL生成等核心AI能力，支持多提供商架构。

---

## 2. 功能需求

### 2.1 多提供商支持

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| LLM-001 | 支持 OpenAI API | 技术选型 |
| LLM-002 | 支持 Zhipu（智谱）API | 技术选型 |
| LLM-003 | 支持 Deepseek API | 技术选型 |
| LLM-004 | 支持 Ollama 本地部署 | 技术选型 |

### 2.2 核心功能

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| LLM-005 | 聊天对话接口 | README.md 第3节 |
| LLM-006 | 流式聊天接口 | 用户体验 |
| LLM-007 | 文本嵌入向量生成 | README.md 第1节 |
| LLM-008 | 批量嵌入向量生成 | 性能优化 |

### 2.3 意图分类

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| LLM-009 | 用户问题意图分类 | README.md 第3节 |
| LLM-010 | 返回意图类型（PURE_DB/PURE_KB/HYBRID/BOUNDARY） | README.md 第3节 |
| LLM-011 | 返回置信度分数 | README.md 第3节 |
| LLM-012 | 提取实体信息（员工姓名、部门等） | README.md 第3节 |

### 2.4 配置管理

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| LLM-013 | 支持从环境变量加载配置 | 配置需求 |
| LLM-014 | 支持从配置服务动态加载 | 配置需求 |
| LLM-015 | 支持热更新配置 | 运维需求 |

### 2.5 模型参数

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| LLM-016 | 支持配置模型名称 | 技术选型 |
| LLM-017 | 支持配置温度参数（temperature） | 技术选型 |
| LLM-018 | 支持配置最大 token 数 | 技术选型 |

---

## 3. 技术架构

### 3.1 Provider Registry 模式

```
LLMService
    └── ProviderRegistry
            ├── OpenAIProvider
            ├── ZhipuProvider
            ├── DeepseekProvider
            └── OllamaProvider
```

### 3.2 接口规范

| 接口 | 参数 | 返回值 |
|------|------|--------|
| chat | messages, model, temperature, max_tokens | str |
| stream_chat | messages, model, temperature, max_tokens | AsyncGenerator |
| embed | text, model | list[float] |
| embed_batch | texts, model | list[list[float]] |

---

## 4. 非功能需求

| 需求编号 | 需求描述 |
|----------|----------|
| LLM-NFR-001 | API 调用超时时间 < 30000ms |
| LLM-NFR-002 | 支持请求重试机制 |
| LLM-NFR-003 | 嵌入向量维度可配置（默认1536） |
