# 多Agent合作的动态知识库系统

## 项目概述

本项目构建了一个**安全可控、分级授权、自动归类**的多Agent协同动态知识库系统，支持三类异构知识资产的统一管理：
- 制度文件（Wiki）
- 个人会话问答（向量化存储）
- 员工档案（结构化数据库）

## 核心特性

### 1. 安全与权限
- 统一身份认证（JWT）
- 基于RBAC的细粒度权限控制
- SQL注入检测
- 敏感字段脱敏

### 2. Agent架构（最新重构）
| Agent | 职责 |
|-------|------|
| **安全Agent** | SQL注入检测、RBAC鉴权、敏感字段脱敏 |
| **编排Agent** | 意图识别、任务分解、跨Agent协调、结果聚合 |
| **Wiki Agent** | Wiki文档CRUD、全文检索 |
| **轻库Agent** | 员工档案查询、行级安全 |
| **向量Agent** | 向量嵌入、语义搜索 |
| **思维导图Agent** | 导图生成、知识整合 |

### 3. Skill层
| Skill | 能力 |
|-------|------|
| `security-utils` | SQL注入检测、敏感词检测、敏感字段脱敏 |
| `content-classifier` | 内容分类、标签提取、语义聚类、格式优化、文本摘要 |
| `mermaid-renderer` | Mermaid语法生成与渲染 |

### 4. MCP协议
- **内嵌MCP**：自研Agent，注册表管理，低耦合，新增Agent无需改调用代码
- **外源MCP**：支持标准MCP Server，配置化管理

## 技术栈

### 后端
- **框架**：FastAPI
- **数据库**：PostgreSQL（关系型数据）、Milvus（向量数据库）
- **缓存**：Redis
- **权限**：Casbin
- **认证**：Keycloak / OAuth2

### 前端
- **框架**：Vue 3 + Vite
- **UI组件**：Element Plus

## 快速开始

### 1. 启动基础设施
```bash
cd knowledge-platform/infra
docker-compose up -d
```

### 2. 启动后端
```bash
cd knowledge-platform/backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### 3. 启动前端
```bash
cd knowledge-platform/frontend
npm install
npm run dev
```

## 项目结构

```
knowledge-platform/
├── backend/
│   ├── app/
│   │   ├── agents/         # Agent实现
│   │   ├── api/            # API路由
│   │   ├── services/       # 业务服务
│   │   ├── dal/            # 数据访问层
│   │   ├── models/         # ORM模型
│   │   ├── core/           # 核心模块
│   │   ├── skills/         # Skill实现
│   │   └── mcps/           # MCP协议
│   └── tests/
├── frontend/
│   └── src/
│       ├── api/
│       ├── views/
│       └── components/
├── infra/
│   ├── docker-compose.yml
│   └── init-*.sql
└── docs/
    ├── requirements/       # 需求文档
    └── specs/              # 设计文档
```

## 研发规范

1. **后端**：FastAPI + SQLAlchemy (PostgreSQL) + Milvus (向量库) + Redis
2. **前端**：Vue 3 + Element Plus
3. **服务模式**：分层架构 (API → Services → DAL)，依赖注入模式
4. **数据库脚本**：直接创建SQL文件放入 infra 文件夹，禁止使用代码生成

## 文档

- [需求规格说明书](./docs/requirements/requirements-specification.md)
- [架构重构设计文档](./docs/superpowers/specs/2026-05-25-agent-architecture-refactor.md)
- [CLAUDE.md](./CLAUDE.md) - 项目开发指南

## 许可证

MIT
