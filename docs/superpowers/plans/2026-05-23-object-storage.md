# 对象存储与文档处理系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现对象存储与文档处理系统，支持 MinIO/S3/OSS 三种存储提供商，实现文档切片和向量化

**Architecture:** 采用策略模式实现存储提供商和切片策略的解耦，通过异步任务实现文档处理流水线

**Tech Stack:** Python/FastAPI 后端, Vue3/Element Plus 前端, PostgreSQL/Milvus/对象存储

---

## 文件结构

### 新建文件

```
backend/app/
├── models/
│   └── wiki_storage.py          # WikiFile, WikiChunk, WikiTag, ChunkingRule 模型
├── services/
│   ├── storage_service.py       # 对象存储服务基类
│   ├── storage_providers/       # 存储提供商实现
│   │   ├── __init__.py
│   │   ├── base.py             # BaseStorageProvider 抽象类
│   │   ├── minio_provider.py   # MinIO 实现
│   │   ├── s3_provider.py      # AWS S3 实现
│   │   └── oss_provider.py     # 阿里云 OSS 实现
│   ├── chunking_service.py      # 文档切片服务基类
│   ├── chunking_strategies/     # 切片策略实现
│   │   ├── __init__.py
│   │   ├── base.py             # BaseChunkingStrategy 抽象类
│   │   ├── rule_strategy.py     # 规则切片实现
│   │   └── llm_strategy.py     # LLM 智能切片实现
│   ├── document_processor_service.py  # 文档处理流水线
│   └── tags_service.py          # 标签服务
├── api/
│   ├── storage.py              # 存储 API
│   ├── tags.py                 # 标签 API
│   └── chunking_rules.py       # 切片规则 API

backend/tests/
├── test_storage_service.py      # 存储服务测试
├── test_chunking_service.py     # 切片服务测试
└── test_document_processor.py    # 文档处理测试

frontend/src/
├── api/
│   ├── storage.js              # 存储 API 调用
│   └── tags.js                 # 标签 API 调用
├── views/
│   ├── admin/
│   │   └── TagsManager.vue     # 标签管理页面
│   └── setup/
│       └── ChunkingRules.vue   # 切片规则管理页面
└── i18n/
    ├── zh-CN/
    │   └── storage.js          # 中文存储相关翻译
    └── en-US/
        └── storage.js           # 英文存储相关翻译
```

### 修改文件

```
backend/app/
├── models/
│   ├── __init__.py            # 导出新模型
│   └── wiki.py                # 移除 content 字段，添加 processing_status
├── dal/
│   ├── __init__.py            # 导出新 Repository
│   └── repositories.py        # 添加新 Repository
├── services/
│   ├── __init__.py            # 导出新服务
│   ├── wiki_service.py        # 集成对象存储，更新创建/更新逻辑
│   ├── config_service.py       # 添加 storage 配置分类
│   └── vector_service.py      # 添加额外字段
├── api/
│   ├── __init__.py            # 注册新路由
│   ├── wiki.py                # 添加新端点
│   └── system.py              # 添加存储配置端点

frontend/src/
├── api/
│   ├── wiki.js                # 添加新 API 调用
│   └── system.js              # 添加存储配置 API
├── views/
│   ├── Wiki.vue               # 添加文件上传、标签、处理状态显示
│   └── admin/
│       └── Settings.vue       # 添加存储配置标签页
├── i18n/
│   ├── zh-CN/
│   │   ├── common.js          # 添加存储相关翻译
│   │   └── settings.js        # 添加存储配置翻译
│   └── en-US/
│       ├── common.js          # 添加存储相关翻译
│       └── settings.js        # 添加存储配置翻译
├── router/
│   └── index.js               # 添加新路由
└── stores/
    └── system.js              # 添加存储配置状态
```

---

## 任务列表

### 第一阶段：数据库模型

#### Task 1: 创建 wiki_storage 模型
- 创建 `backend/app/models/wiki_storage.py`
- 更新 `backend/app/models/__init__.py`

#### Task 2: 更新 WikiPage 模型
- 修改 `backend/app/models/wiki.py`
- 移除 content 字段，添加 processing_status 字段

#### Task 3: 创建 DAL Repository
- 修改 `backend/app/dal/repositories.py`
- 添加 WikiFileRepository, WikiChunkRepository, WikiTagRepository, ChunkingRuleRepository

---

### 第二阶段：对象存储服务

#### Task 4: 创建存储提供商基类
- 创建 `backend/app/services/storage_providers/base.py`
- 创建 `backend/app/services/storage_providers/__init__.py`

#### Task 5: 实现存储提供商
- 创建 `backend/app/services/storage_providers/minio_provider.py`
- 创建 `backend/app/services/storage_providers/s3_provider.py`
- 创建 `backend/app/services/storage_providers/oss_provider.py`

#### Task 6: 创建 StorageService
- 创建 `backend/app/services/storage_service.py`
- 修改 `backend/app/services/config_service.py` 添加 storage 配置
- 修改 `backend/app/services/__init__.py`

---

### 第三阶段：文档切片服务

#### Task 7: 创建切片策略基类
- 创建 `backend/app/services/chunking_strategies/base.py`
- 创建 `backend/app/services/chunking_strategies/__init__.py`

#### Task 8: 实现规则切片策略
- 创建 `backend/app/services/chunking_strategies/rule_strategy.py`
- 实现 HeadingChunkingStrategy, ParagraphChunkingStrategy, LengthChunkingStrategy

#### Task 9: 实现 LLM 切片策略
- 创建 `backend/app/services/chunking_strategies/llm_strategy.py`
- 实现 LLMChunkingStrategy

---

### 第四阶段：文档处理服务

#### Task 10: 创建文档处理流水线
- 创建 `backend/app/services/document_processor_service.py`

#### Task 11: 创建标签服务
- 创建 `backend/app/services/tags_service.py`
- 修改 `backend/app/services/__init__.py`

#### Task 12: 创建切片规则服务
- 创建 `backend/app/services/chunking_service.py`
- 修改 `backend/app/services/__init__.py`

---

### 第五阶段：API 层

#### Task 13: 创建 API 端点
- 创建 `backend/app/api/storage.py`
- 创建 `backend/app/api/tags.py`
- 创建 `backend/app/api/chunking_rules.py`
- 修改 `backend/app/api/__init__.py`

#### Task 14: 更新 Wiki API
- 修改 `backend/app/api/wiki.py`
- 添加 content, retry, tags 端点
- 修改 `backend/app/services/wiki_service.py`

#### Task 15: 更新 System API
- 修改 `backend/app/api/system.py`
- 添加存储配置端点

---

### 第六阶段：前端开发

#### Task 16: 创建前端 API 文件
- 创建 `frontend/src/api/storage.js`
- 创建 `frontend/src/api/tags.js`

#### Task 17: 创建标签管理页面
- 创建 `frontend/src/views/admin/TagsManager.vue`

#### Task 18: 更新 Wiki 页面
- 修改 `frontend/src/views/Wiki.vue`
- 添加文件上传、标签、处理状态显示

#### Task 19: 更新 Settings 页面
- 修改 `frontend/src/views/admin/Settings.vue`
- 添加存储配置标签页

---

### 第七阶段：测试和集成

#### Task 20: 编写单元测试
- 创建 `backend/tests/test_storage_service.py`
- 创建 `backend/tests/test_chunking_service.py`
- 创建 `backend/tests/test_document_processor.py`

#### Task 21: 集成测试
- 修改 `backend/tests/conftest.py`
- 运行测试验证

---

## 实施计划完成

共 21 个任务，分为 7 个阶段实施。

