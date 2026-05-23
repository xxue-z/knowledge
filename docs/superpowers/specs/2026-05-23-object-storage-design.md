# 对象存储与文档处理系统设计文档

**日期**：2026-05-23  
**版本**：v1.0  
**状态**：待审核

---

## 1. 概述

### 1.1 项目背景
当前 Wiki 文档内容直接存储在 PostgreSQL 数据库中，存在以下问题：
- 数据库体积膨胀
- 不支持文档版本管理
- 无法高效存储和检索大文档
- 缺少文档切片和向量化能力

### 1.2 目标
- 将文档内容迁移到对象存储
- 支持文档版本管理
- 实现文档切片和向量化
- 支持多种对象存储提供商（MinIO、AWS S3、阿里云 OSS）
- 支持灵活的标签系统
- 实现可配置的文档切片策略

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                           Frontend                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Wiki页面 │  │ 设置页面 │  │ 引导页面 │  │ 标签管理 │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                         API Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Wiki API    │  │ Storage API  │  │  Tags API    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                      Services Layer                              │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │  WikiService     │  │ StorageService   │                     │
│  │  (文档元数据)    │  │  (对象存储操作)  │                     │
│  └──────────────────┘  └──────────────────┘                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              DocumentProcessorService                    │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │         ChunkingStrategy (策略模式)               │   │  │
│  │  │  ┌──────────────┐  ┌──────────────────────┐     │   │  │
│  │  │  │ RuleStrategy │  │  LLMStrategy         │     │   │  │
│  │  │  └──────────────┘  └──────────────────────┘     │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │   TagsService    │  │  ConfigService   │                     │
│  └──────────────────┘  └──────────────────┘                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌──────────┐  ┌────────┐  ┌──────────────┐
   │PostgreSQL│  │ Milvus │  │  对象存储     │
   │ (元数据) │  │(向量)  │  │ (MinIO/S3/OSS)│
   └──────────┘  └────────┘  └──────────────┘
```

### 2.2 分层说明

- **Frontend**：Vue 3 应用，提供 Wiki 编辑、配置、标签管理等界面
- **API Layer**：FastAPI 路由，处理 HTTP 请求
- **Services Layer**：业务逻辑层
  - WikiService：文档元数据管理
  - StorageService：对象存储操作（策略模式支持多种提供商）
  - DocumentProcessorService：文档处理流水线
  - TagsService：标签管理
  - ConfigService：系统配置管理
- **数据层**：
  - PostgreSQL：存储元数据
  - Milvus：存储向量
  - 对象存储：存储文档文件

---

## 3. 数据库设计

### 3.1 表结构

#### 3.1.1 `wiki_pages` 表

```sql
CREATE TABLE wiki_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    parent_id UUID REFERENCES wiki_pages(id),
    sensitivity VARCHAR(20) DEFAULT 'public',
    dept_id VARCHAR(50),
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processing_status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    processing_error TEXT
);

CREATE INDEX idx_wiki_pages_parent ON wiki_pages(parent_id);
CREATE INDEX idx_wiki_pages_slug ON wiki_pages(slug);
CREATE INDEX idx_wiki_pages_sensitivity ON wiki_pages(sensitivity);
CREATE INDEX idx_wiki_pages_status ON wiki_pages(processing_status);
```

#### 3.1.2 `wiki_files` 表

```sql
CREATE TABLE wiki_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID NOT NULL REFERENCES wiki_pages(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(200) NOT NULL,
    file_size INTEGER NOT NULL,
    md5_hash VARCHAR(32) NOT NULL,
    mime_type VARCHAR(100) DEFAULT 'text/markdown',
    is_current BOOLEAN DEFAULT true,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    edit_summary VARCHAR(500)
);

CREATE INDEX idx_wiki_files_page ON wiki_files(page_id);
CREATE INDEX idx_wiki_files_current ON wiki_files(page_id, is_current) WHERE is_current = true;
CREATE UNIQUE INDEX idx_wiki_files_version ON wiki_files(page_id, version);
```

#### 3.1.3 `wiki_chunks` 表

```sql
CREATE TABLE wiki_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES wiki_files(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    start_pos INTEGER NOT NULL,
    end_pos INTEGER NOT NULL,
    text_preview VARCHAR(200),
    vector_id VARCHAR(100) NOT NULL
);

CREATE INDEX idx_wiki_chunks_file ON wiki_chunks(file_id);
CREATE INDEX idx_wiki_chunks_vector ON wiki_chunks(vector_id);
```

#### 3.1.4 `wiki_tags` 表

```sql
CREATE TABLE wiki_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    color VARCHAR(20) DEFAULT '#3B82F6',
    description TEXT,
    parent_id UUID REFERENCES wiki_tags(id),
    sort_order INTEGER DEFAULT 0,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_wiki_tags_parent ON wiki_tags(parent_id);
CREATE INDEX idx_wiki_tags_sort ON wiki_tags(sort_order);
```

#### 3.1.5 `wiki_page_tags` 关联表

```sql
CREATE TABLE wiki_page_tags (
    page_id UUID NOT NULL REFERENCES wiki_pages(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES wiki_tags(id) ON DELETE CASCADE,
    PRIMARY KEY (page_id, tag_id)
);

CREATE INDEX idx_wiki_page_tags_page ON wiki_page_tags(page_id);
CREATE INDEX idx_wiki_page_tags_tag ON wiki_page_tags(tag_id);
```

#### 3.1.6 `chunking_rules` 表

```sql
CREATE TABLE chunking_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    rule_type VARCHAR(20) NOT NULL, -- heading, paragraph, length, custom
    rule_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chunking_rules_active ON chunking_rules(is_active) WHERE is_active = true;
CREATE INDEX idx_chunking_rules_sort ON chunking_rules(sort_order);
```

### 3.2 初始化数据

```sql
-- 初始化切片规则
INSERT INTO chunking_rules (name, description, rule_type, rule_config, sort_order) VALUES
('按标题切片', '按 Markdown 标题（#、##、### 等）进行切片', 'heading', '{"levels": [1, 2, 3]}'::jsonb, 1),
('按段落切片', '按空行分隔的段落进行切片', 'paragraph', '{"min_length": 50}'::jsonb, 2),
('按长度切片', '按固定长度进行切片', 'length', '{"max_tokens": 500, "overlap": 50}'::jsonb, 3);
```

---

## 4. 对象存储设计

### 4.1 支持的提供商
- MinIO（自托管）
- AWS S3
- 阿里云 OSS

### 4.2 文件路径规则

```
/wiki/{page_id}/{file_id}/original.md
/wiki/{page_id}/{file_id}/v{version}.md
```

### 4.3 预签名 URL 有效期
- 上传：15 分钟
- 下载/预览：5 分钟

### 4.4 配置项

在 `system_config` 表中新增 `storage` 分类：

| 配置项 | 类型 | 说明 |
|--------|------|------|
| provider | string | 存储提供商：minio, s3, oss |
| endpoint | string | 服务端点 |
| access_key | string | 访问密钥 |
| secret_key | password | 秘密密钥 |
| bucket | string | 存储桶名称 |
| region | string | 区域（S3/OSS 需要） |
| use_ssl | bool | 是否使用 SSL |

---

## 5. 文档处理流水线

### 5.1 处理流程

```
用户上传/创建文档
        ↓
    保存原始文件到对象存储
        ↓
    保存文件元数据到 PostgreSQL
        ↓
    更新页面状态为 processing
        ↓
    [异步任务] 文档处理
        ├─ 从对象存储读取文件
        ├─ 解析 Markdown（移除图片链接、表格转文本）
        ├─ 使用配置的策略进行切片
        ├─ 生成 Embedding
        ├─ 存入 Milvus 向量库
        └─ 保存切片元数据到 PostgreSQL
        ↓
    更新页面状态为 completed 或 failed
```

### 5.2 切片策略模式

#### 策略接口

```python
class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, text: str, rules: list[ChunkingRule]) -> list[Chunk]:
        pass
```

#### 具体策略

1. **RuleStrategy**：基于规则的切片
   - 按标题切片
   - 按段落切片
   - 按长度切片

2. **LLMStrategy**：基于 LLM 的智能切片

### 5.3 向量库 Schema

Milvus Collection 字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | VARCHAR | 主键 |
| user_id | VARCHAR | 用户 ID |
| dept_id | VARCHAR | 部门 ID |
| sensitivity | VARCHAR | 敏感度 |
| text | VARCHAR(65535) | 切片文本 |
| embedding | FloatVector | 向量 |
| file_id | VARCHAR | 文件 ID |
| chunk_index | INT | 切片索引 |
| tags | JSON | 标签数组 |

---

## 6. API 设计

### 6.1 Wiki API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/wiki/pages | 获取页面列表 |
| GET | /api/wiki/pages/{page_id} | 获取页面详情 |
| POST | /api/wiki/pages | 创建页面 |
| PUT | /api/wiki/pages/{page_id} | 更新页面 |
| DELETE | /api/wiki/pages/{page_id} | 删除页面 |
| GET | /api/wiki/pages/{page_id}/content | 获取页面内容（返回预签名 URL） |
| GET | /api/wiki/pages/{page_id}/download | 下载原始文件 |
| GET | /api/wiki/pages/{page_id}/versions | 获取版本历史 |
| POST | /api/wiki/pages/{page_id}/retry | 重试文档处理 |
| POST | /api/wiki/pages/{page_id}/tags | 添加标签 |
| DELETE | /api/wiki/pages/{page_id}/tags/{tag_id} | 移除标签 |

### 6.2 Storage API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/storage/upload-url | 获取上传预签名 URL |
| GET | /api/storage/download-url/{file_id} | 获取下载预签名 URL |

### 6.3 Tags API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/tags | 获取所有标签（树形结构） |
| GET | /api/tags/{tag_id} | 获取标签详情 |
| POST | /api/tags | 创建标签 |
| PUT | /api/tags/{tag_id} | 更新标签 |
| DELETE | /api/tags/{tag_id} | 删除标签 |

### 6.4 Chunking Rules API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/chunking-rules | 获取所有切片规则 |
| GET | /api/chunking-rules/{rule_id} | 获取规则详情 |
| POST | /api/chunking-rules | 创建规则 |
| PUT | /api/chunking-rules/{rule_id} | 更新规则 |
| DELETE | /api/chunking-rules/{rule_id} | 删除规则 |
| POST | /api/chunking-rules/reorder | 重新排序规则 |

---

## 7. 前端设计

### 7.1 Wiki 页面改动

1. **新增文件上传按钮**
   - 支持拖拽上传
   - 支持点击选择文件
   - 文件类型限制：.md

2. **标签选择器**
   - 支持多选
   - 支持搜索
   - 支持创建新标签

3. **处理状态显示**
   - 处理中：显示加载动画和进度提示
   - 处理失败：显示错误信息和"重试"按钮
   - 处理完成：显示正常内容

4. **版本历史**
   - 显示版本列表
   - 支持查看历史版本
   - 支持恢复历史版本

### 7.2 设置页面改动

新增"对象存储"标签页：
- 存储提供商选择（MinIO/S3/OSS）
- 配置表单
- 测试连接按钮
- 保存配置按钮

### 7.3 引导页面改动

在现有步骤后新增"对象存储配置"步骤。

### 7.4 标签管理页面（新增）

- 树形标签展示
- 支持创建、编辑、删除标签
- 支持拖拽排序
- 支持设置标签颜色

### 7.5 切片规则管理页面（新增）

- 规则列表展示
- 支持创建、编辑、删除规则
- 支持拖拽排序
- 支持启用/禁用规则

---

## 8. 错误处理

### 8.1 对象存储错误
- 连接失败：显示友好提示，提供重试按钮
- 权限错误：提示检查配置
- 存储桶不存在：提示创建存储桶

### 8.2 文档处理错误
- 解析失败：记录错误，页面状态设为 failed
- 切片失败：记录错误，页面状态设为 failed
- 向量化失败：记录错误，页面状态设为 failed

---

## 9. 迁移计划

由于现有数据都是测试数据，采用以下策略：
1. 备份现有数据库（可选）
2. 删除旧表
3. 创建新表
4. 初始化基础数据

---

## 10. 测试计划

### 10.1 单元测试
- StorageService 各实现的测试
- ChunkingStrategy 各策略的测试
- DocumentProcessorService 的测试

### 10.2 集成测试
- 完整的文档上传、处理、检索流程
- 各存储提供商的集成测试

### 10.3 前端测试
- 页面交互测试
- 文件上传测试
- 状态显示测试

---

## 11. 部署计划

1. 数据库迁移：执行 SQL 脚本
2. 部署后端代码
3. 部署前端代码
4. 配置对象存储
5. 初始化切片规则
6. 测试验证

---

## 12. 后续优化方向

1. 支持更多文档格式（.docx、.pdf 等）
2. 支持文档预览（非 Markdown 格式）
3. 实现文档增量更新
4. 支持文档协作编辑
5. 添加文档审批流程

---

**文档结束**
