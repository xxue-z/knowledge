# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 研发规范

1. **后端**：FastAPI + SQLAlchemy (PostgreSQL) + Milvus (向量库) + Redis
2. **前端**：Vue 3 + Element Plus
3. **服务模式**：分层架构 (API → Services → DAL)，依赖注入模式
4. **数据库脚本**：直接创建 SQL 文件放入 infra 文件夹，禁止使用代码生成工具

## 项目概述

This repo contains a multi-Agent dynamic knowledge base system (`knowledge-platform/`). The system integrates Wiki documents, vectorized conversation records, and relational employee data with RBAC permissions, knowledge navigation, and mind map generation.

## 架构重构说明

本项目正在进行 Agent 架构重构，从旧的 8 个 Agent 重构为 6 个 Agent：

### 旧架构（待迁移）
- 路由Agent、权限Agent、协调Agent、Wiki Agent、检索服务层、轻库Agent、内容分析Agent、思维导图Agent

### 新架构
- **安全Agent**：SQL注入检测、RBAC鉴权、敏感字段脱敏
- **编排Agent**：意图识别、任务分解、跨Agent协调、结果聚合
- **Wiki Agent**：Wiki文档CRUD、全文检索
- **轻库Agent**：员工档案查询、行级安全
- **向量Agent**：向量嵌入、语义搜索
- **思维导图Agent**：导图生成、知识整合

### Skill 层
- `security-utils`：SQL注入检测、敏感词检测、敏感字段脱敏
- `content-classifier`：内容分类、标签提取、语义聚类、格式优化、文本摘要
- `mermaid-renderer`：Mermaid语法生成与渲染

### MCP 协议
- **内嵌MCP**：自研Agent，注册表管理，低耦合，新增Agent无需改调用代码
- **外源MCP**：支持标准MCP Server，配置化管理

## Repository Structure

```
knowledge-platform/
├── backend/                        # FastAPI 后端
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── config.py               # Pydantic Settings 配置
│   │   ├── api/                    # API 路由
│   │   │   ├── auth.py             # 认证（Keycloak JWT）
│   │   │   ├── wiki.py             # Wiki CRUD + 搜索
│   │   │   ├── qa.py               # 智能问答入口
│   │   │   ├── knowledge.py        # 知识导航管理
│   │   │   ├── admin.py            # 管理后台（审计日志、权限）
│   │   │   ├── storage.py          # 对象存储 API
│   │   │   ├── tags.py             # 标签管理 API
│   │   │   └── chunking_rules.py   # 切片规则 API
│   │   ├── agents/                 # Agent 实现
│   │   │   ├── router/              # 路由Agent（待合并）
│   │   │   ├── coordinator/         # 协调Agent（待合并）
│   │   │   ├── permission/          # 权限Agent（待升级）
│   │   │   ├── wiki_agent/          # Wiki Agent
│   │   │   ├── vector/              # 向量Agent（Milvus）
│   │   │   ├── db_agent/           # 轻库Agent（PostgreSQL）
│   │   │   ├── content_analysis_agent/ # 内容分析Agent（待删除）
│   │   │   └── mindmap_agent/        # 思维导图Agent
│   │   ├── services/               # 业务服务层
│   │   │   ├── wiki_service.py     # Wiki CRUD + 版本历史
│   │   │   ├── vector_service.py   # Milvus 连接 + 向量操作
│   │   │   ├── db_service.py       # 员工档案查询（参数化SQL）
│   │   │   ├── nav_service.py      # 知识导航树 CRUD
│   │   │   ├── llm_service.py      # LLM 调用封装（OpenAI兼容）
│   │   │   ├── storage_service.py  # 对象存储服务
│   │   │   ├── tags_service.py     # 标签管理服务
│   │   │   ├── chunking_service.py # 切片规则服务
│   │   │   ├── chunking_strategies/  # 切片策略实现
│   │   │   │   ├── base.py         # 策略基类
│   │   │   │   ├── rule_strategy.py # 规则切片
│   │   │   │   └── llm_strategy.py  # LLM 语义切片
│   │   │   └── storage_providers/   # 存储提供商实现
│   │   │       ├── base.py         # 存储基类
│   │   │       ├── minio_provider.py
│   │   │       ├── s3_provider.py
│   │   │       └── oss_provider.py
│   │   ├── dal/                    # 数据访问层
│   │   │   └── repositories.py     # Repository 实现
│   │   ├── core/                   # 核心模块
│   │   │   ├── security.py         # JWT 校验（Keycloak公钥）
│   │   │   ├── casbin_policy.py    # Casbin RBAC 策略引擎
│   │   │   └── middleware.py       # 审计日志中间件
│   │   ├── models/                 # SQLAlchemy ORM + Pydantic schemas
│   │   │   ├── wiki_storage.py     # 存储相关模型
│   │   │   └── schemas.py          # Pydantic schemas
│   │   ├── skills/                 # Skill 实现
│   │   │   ├── content_classifier/
│   │   │   ├── mermaid_renderer/
│   │   │   ├── intent_classifier/
│   │   │   ├── registry.py            # Skill 注册表
│   │   │   └── init.py
│   │   ├── mcps/                   # MCP 协议
│   │   │   ├── mcp_protocol/
│   │   │   └── registry/
│   │   └── db/
│   │       └── session.py          # AsyncSession 管理
│   ├── tests/
│   └── requirements.txt
│
├── frontend/                       # Vue3 + Vite + Element Plus 前端
│   └── src/
│       ├── api/                   # API 请求
│       ├── views/                 # 页面组件
│       │   └── admin/             # 管理页面
│       │       ├── Settings.vue    # 系统设置
│       │       └── TagsManager.vue # 标签管理
│       └── i18n/                  # 国际化
├── infra/
│   ├── docker-compose.yml         # PostgreSQL + Milvus + Keycloak + Redis + MinIO
│   ├── init-db.sql               # 数据库初始化脚本
│   ├── init-wiki-storage.sql     # Wiki 存储表初始化脚本
│   └── keycloak/                  # Keycloak realm 配置
└── docs/
    ├── requirements/
    │   └── requirements-specification.md   # 需求规格说明书
    ├── specs/                      # 设计文档
    │   ├── 2026-05-23-object-storage-design.md
    │   └── 2026-05-25-agent-architecture-refactor.md
    └── architecture/
        └── project-structure.md    # 项目结构 Wiki（快速索引）
```

## Key Commands

```bash
# 启动基础设施
cd knowledge-platform/infra && docker compose up -d

# 安装后端依赖
cd knowledge-platform/backend && pip install -r requirements.txt

# 复制环境变量
cp .env.example .env

# 运行后端
cd knowledge-platform/backend && uvicorn app.main:app --reload --port 8000

# 运行测试
cd knowledge-platform/backend && python -m pytest tests/ -v

# 初始化数据库（直接执行 SQL 文件）
psql -h localhost -U knowledge -d knowledge -f infra/init-db.sql
psql -h localhost -U knowledge -d knowledge -f infra/init-wiki-storage.sql
```

## Tech Stack

- **Backend:** Python 3.11+ / FastAPI / SQLAlchemy 2.0 (async) / asyncpg
- **Database:** PostgreSQL 15 (关系数据 + ltree 导航树)
- **Vector DB:** Milvus 2.4
- **Storage:** MinIO / AWS S3 / 阿里云 OSS
- **Auth:** Keycloak 24 (OAuth2/OIDC)
- **Permission:** Casbin (RBAC)
- **LLM:** OpenAI-compatible API
- **Frontend:** Vue3 + Vite + Element Plus + vue-i18n + marked

## Architecture

**分层架构 (API → Services → DAL)：**
```
用户请求 → API 层（请求/响应处理）
         → Services 层（业务逻辑）
         → DAL 层（数据访问）
```

**新 Agent 通信模式（重构中）：**
```
用户请求 → FastAPI 接口
    → 安全Agent（SQL注入检测 + 权限检查
    → 编排Agent（意图识别 + 任务分解
        → 调用内嵌Agent（Wiki / 向量 / 轻库 / 思维导图）
        → 或调用外源MCP Server
        → 结果聚合
    → 返回用户
```

**权限数据流：**
```
JWT Token → 解析 user_id, roles, dept_id
    → Casbin enforcer 校验策略
    → Agent 查询时注入可见数据范围
    → Milvus filter: dept_id IN (visible_depts)
    → SQL WHERE: dept_id IN (visible_depts) AND sensitivity <= clearance
    → 敏感字段脱敏（根据角色）
```

## Database Schema

### 核心表
- **wiki_pages** — Wiki 文档（带 ACL、敏感度分级）
- **wiki_page_versions** — 版本历史
- **employees** — 员工档案（带密级、部门隔离）
- **conversations** — 会话问答记录（向量ID关联 Milvus）
- **knowledge_nav** — 知识导航树（ltree 物化路径）
- **nav_content_links** — 导航节点与内容关联
- **casbin_rule** — Casbin 策略持久化
- **audit_logs** — 操作审计日志

### 存储相关表
- **wiki_files** — Wiki 文件存储记录
- **wiki_chunks** — 文档切片记录
- **wiki_tags** — 标签定义（支持层级）
- **page_tags** — 页面与标签关联
- **chunking_rules** — 切片规则定义

## Documentation

- **需求规格说明书**: `docs/requirements/requirements-specification.md — 详细需求说明
- **架构重构设计**: `docs/specs/2026-05-25-agent-architecture-refactor.md` — Agent 架构重构设计文档
- **存储设计文档**: `docs/specs/2026-05-23-object-storage-design.md` — 对象存储系统设计
- **项目结构 Wiki**: `docs/architecture/project-structure.md` — 完整目录结构、数据流、环境变量参考

## Key Constraints

- All SQL must use parameterized queries (SQLAlchemy ORM) — string concatenation is forbidden.
- Every data access goes through permission check (Casbin RBAC).
- Sensitive fields (salary, phone) are masked based on user role.
- All answers must cite sources.
- All API operations are logged to audit_logs.
- Database scripts should be SQL files in `infra/` folder, not generated by migration tools.
- 分层架构禁止跨层调用（API → Services → DAL）。
- Agent 调用 Skill 应使用统一的 Skill 执行器，避免直接依赖具体 Skill 实现。
