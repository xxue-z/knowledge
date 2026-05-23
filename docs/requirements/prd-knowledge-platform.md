# 多Agent协作动态知识库系统 - PRD

---

## Problem Statement

企业内部存在三类异构知识资产：制度文件（Wiki）、个人会话问答（非结构化QA历史）、员工档案（考勤、绩效、打卡等结构化数据）。当前面临以下核心问题：

1. **知识孤岛**：三类知识分散存储，缺乏统一检索入口，用户需要在多个系统间切换
2. **权限混乱**：缺乏细粒度的数据权限控制，敏感信息存在泄露风险
3. **知识无序**：文档提交后缺乏自动分类机制，知识库"存而乱"
4. **协作低效**：跨库联合查询（如根据Wiki考勤制度和实际打卡记录计算扣款）需要人工完成
5. **安全隐患**：缺少统一身份认证和权限校验机制

---

## Solution

构建一套**安全可控、分级授权、自动归类**的多Agent协同动态知识库平台，核心能力包括：

1. **统一知识存储**：Wiki引擎 + 向量数据库 + 关系型数据库的异构存储架构
2. **全链路权限防护**：权限管控Agent确保每一次数据访问都经过精细化鉴权
3. **动态知识导航**：预设业务导向的导航树结构，结合自动分类与人工维护
4. **多Agent协作**：路由Agent、协调Agent、审核优化Agent等实现智能问答与跨库查询
5. **可视化输出**：思维导图Agent生成结构化知识图谱

---

## User Stories

### 第一阶段：基础存储与权限骨架

1. As a system administrator, I want to initialize the system with a built-in admin account, so that I can set up the platform on first launch.
2. As an employee, I want to log in with username/password and receive a JWT token, so that I can access the knowledge platform securely.
3. As a developer, I want to use OAuth2.0/LDAP integration for enterprise authentication, so that employees can use their corporate credentials.
4. As an HR manager, I want to manage employee records with row-level security, so that sensitive data like salary is protected.
5. As a content author, I want to create Wiki pages with Markdown support, so that I can document company policies.
6. As a user, I want to search Wiki documents with full-text search, so that I can find relevant policies quickly.
7. As an administrator, I want to set document sensitivity levels (public/internal/confidential/secret), so that access can be controlled.
8. As a QA user, I want to submit questions and get semantic search results from the vector database, so that I can find relevant past conversations.
9. As a department manager, I want to view employee records for my department only, so that I can manage my team effectively.
10. As a security engineer, I want to use Casbin for RBAC/ABAC permission control, so that access policies can be managed centrally.

### 第二阶段：导航与自动分类

11. As an administrator, I want to create a hierarchical knowledge navigation tree with preset categories, so that knowledge can be organized systematically.
12. As a content author, I want the system to automatically recommend navigation categories when submitting documents, so that I don't have to manually classify them.
13. As a user, I want to browse knowledge by navigating the tree structure, so that I can discover related content easily.
14. As an administrator, I want to manually edit/move navigation nodes, so that I can refine the knowledge organization.
15. As a content reviewer, I want to see sensitive word filtering and format correction suggestions, so that I can ensure content quality.
16. As an administrator, I want the system to periodically reclassify documents with low confidence scores, so that the knowledge organization stays accurate.
17. As a user, I want to search for keywords and have results automatically mapped to navigation nodes, so that I can locate information quickly.

### 第三阶段：多Agent协作与跨库查询

18. As a department manager, I want to query "张三本月考勤信息和迟到扣款" and get a combined answer from both attendance records and policy documents, so that I can make informed decisions.
19. As a user, I want the system to automatically route my question to the appropriate Agent (database/knowledge base/hybrid), so that I get accurate answers.
20. As a security engineer, I want the system to detect and block SQL injection attempts, so that the platform is protected from attacks.
21. As a user, I want answers to include source references, so that I can verify the information.
22. As a user without full access, I want to see "permission denied" indicators for restricted content, so that I understand why certain information is unavailable.
23. As an administrator, I want to configure permission policies that can be hot-reloaded, so that policy changes take effect immediately.

### 第四阶段：思维导图与完善

24. As a trainer, I want to generate mind maps from document content, so that I can create training materials.
25. As a user, I want mind maps to respect the knowledge navigation structure, so that the output aligns with the company's knowledge organization.
26. As a content author, I want to see classification suggestions and permission settings when submitting documents, so that I can configure these during submission.
27. As an administrator, I want to view audit logs of user actions, so that I can track system usage.
28. As a user, I want to access the platform from mobile devices with responsive design, so that I can use it on the go.

---

## Implementation Decisions

### Core Module Design (Optimized: 7 Agents + 3 Skills)

#### 1. Business Agents (7)

| Module | Responsibilities | Tech Stack | Notes |
|--------|------------------|------------|-------|
| **Router Agent** | Intent recognition, permission pre-check, SQL injection detection | Python + LLM | Core entry, cannot merge |
| **Permission Agent** | RBAC/ABAC auth, sensitive field masking | Casbin | Core security component, cannot merge |
| **Retrieval Service Layer** | Wiki CRUD + full-text search, Vector embedding + semantic search, Hybrid search | PostgreSQL + Milvus | Wiki Agent + Vector Agent merged |
| **LightDB Agent** | Employee record query, Row-level security | PostgreSQL + RLS | Independent, shares permission service |
| **Content Analysis Agent** | Sensitive word filtering, Format optimization, Auto-classification, Navigation node management | Python + LLM | Review Agent + Navigation Agent merged |
| **Mindmap Agent** | Mindmap generation, Knowledge integration | LLM + Mermaid | Independent |
| **Coordinator Agent** | Composite task decomposition, Cross-database query, Result aggregation | Python | Core orchestration component, cannot merge |

#### 2. Reusable Skills (3)

| Skill Name | Capability | Called By |
|------------|------------|-----------|
| `content-classifier` | Content classification, Tag extraction, Semantic clustering | Content Analysis Agent |
| `mermaid-renderer` | Mermaid syntax generation and rendering | Mindmap Agent |
| `sql-inject-detector` | SQL injection detection and blocking | Router Agent |

#### 3. Agent and Skill Relationship

```
                    ┌─────────────────────────────────────────┐
                    │              Coordinator Agent          │
                    │  (Task Decomposition, Cross-DB Query)    │
                    └─────────────┬───────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Router Agent │      │  Retrieval Svc   │      │   LightDB Agent │
│ (Permission    │      │  (Wiki+Vector)  │      │  (Record Query) │
│  Pre-check)    │      │                 │      │                 │
└───────┬───────┘      └────────┬────────┘      └─────────────────┘
        │                       │
        │             ┌─────────┴─────────┐
        │             │                   │
        ▼             ▼                   ▼
   ┌─────────┐   ┌───────────┐     ┌───────────┐
   │Skill:   │   │ Wiki      │     │ Vector    │
   │sql-     │   │ Full-text │     │ Milvus    │
   │inject-  │   │ Index     │     │           │
   │detector │   └───────────┘     └───────────┘
   └─────────┘
```

**Note**:
- Agents are **system architecture-level business components** responsible for data processing and persistence
- Skills are **AI capability-level reusable tools** called by Agents
- Agents cannot be replaced by Skills; they have different responsibilities but can collaborate

#### 4. Merge Optimization Summary

| Merge Item | Original Modules | Merged Into | Reason |
|------------|------------------|-------------|--------|
| Wiki + Vector | Wiki Agent, Vector Agent | Retrieval Service Layer | Both are "storage + retrieval", reduces data sync, unifies search API |
| Review + Navigation | Review Agent, Navigation Agent | Content Analysis Agent | Both involve content understanding & classification, shares classification model, reduces LLM calls |

### Data Permission Model

- **个人会话**：仅本人及直属上级可见
- **员工档案**：按组织架构树授权，普通员工仅看自己，经理看本部门及下级，HR可看全公司但敏感字段加密
- **Wiki文档**：按页面ACL控制读/写/管理权限
- **知识导航**：部分类目仅特定角色可见（如薪酬制度）

### 技术架构

- **前端**：Vue3 + Vite + Element Plus
- **后端**：FastAPI + SQLAlchemy + AsyncPG
- **认证**：JWT + Keycloak（可选）
- **权限**：Casbin + PostgreSQL Adapter
- **向量存储**：Milvus（REST API）
- **缓存**：Redis
- **LLM**：OpenAI/Zhipu/Deepseek/Ollama（多提供商支持）

---

## Testing Decisions

### 测试策略

1. **单元测试**：对核心 Agent 和 Service 进行单元测试，验证单个组件的功能正确性
2. **集成测试**：测试多 Agent 协作流程，验证跨模块交互
3. **权限测试**：验证不同角色的数据访问权限，确保数据隔离正确
4. **性能测试**：验证系统在高并发下的响应时间和稳定性
5. **安全测试**：测试 SQL 注入防护、敏感数据脱敏等安全功能

### 测试覆盖重点

| 模块 | 测试重点 |
|------|----------|
| 认证模块 | 登录/登出流程、Token验证、密码修改 |
| 权限模块 | 角色鉴权、敏感字段脱敏、权限继承 |
| Wiki模块 | CRUD操作、版本控制、全文检索 |
| 向量模块 | 语义搜索准确性、权限过滤 |
| 导航模块 | 自动分类准确性、权限可见性 |
| 协调模块 | 跨库查询、结果聚合 |

---

## Out of Scope

以下内容不在本PRD范围内：

1. **移动端原生应用**：当前仅支持响应式Web设计，不包含iOS/Android原生应用
2. **实时消息推送**：不包含WebSocket实时消息功能
3. **第三方应用集成**：不包含与OA、CRM等外部系统的深度集成
4. **大数据分析**：不包含知识使用趋势分析等高级分析功能
5. **多租户支持**：当前设计为单租户架构
6. **离线模式**：不支持离线访问功能

---

## Further Notes

### 实施阶段建议

**第一阶段**（基础存储与权限骨架）：
- 搭建Wiki、向量库、轻量库
- 集成登录认证，实现JWT签发与校验
- 设计并实现基本RBAC

**第二阶段**（导航与自动分类）：
- 设计知识导航树结构并开发管理API
- 训练/配置分类Agent
- 开发审核优化Agent

**第三阶段**（多Agent协作与跨库查询）：
- 实现权限Agent的细粒度动态鉴权
- 构建协调Agent，完成跨库复合查询

**第四阶段**（思维导图与完善）：
- 开发思维导图生成Agent
- 增强维护页面，可视化权限设置与分类推荐

### 关键依赖与风险

| 风险项 | 缓解措施 |
|--------|----------|
| Milvus 连接稳定性 | 实现重试机制和健康检查 |
| LLM API 调用成本 | 实现缓存策略，减少重复调用 |
| 权限配置复杂性 | 提供可视化配置界面 |
| 自动分类准确性 | 提供人工确认机制，支持定期重分类 |

### 版本规划

| 版本 | 目标 |
|------|------|
| v1.0 | 基础存储、认证、Wiki功能 |
| v1.1 | 向量搜索、知识导航 |
| v1.2 | 多Agent协作、跨库查询 |
| v1.3 | 思维导图、完整功能 |

---

**文档版本**: v1.0  
**创建日期**: 2026-05-22  
**状态**: 待评审
