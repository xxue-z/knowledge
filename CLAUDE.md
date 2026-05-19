# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概述

这是"企业智能问答助手 Skill 开发"面试笔试题的数据包。候选人需要从零构建一个 Skill，通过同时查询 SQLite 数据库和 Markdown 知识库来回答自然语言问题。不限语言（Python、Node.js、Go 等），Claude Code Skill 或 OpenClaw Skill 均可。

**测试用例的当前日期上下文：** 2026-03-27，时区 Asia/Shanghai。

## 仓库结构

```
interview-exam/
├── enterprise-qa-exam.md          # 说明
└── enterprise-qa-data/
    ├── schema.sql                 # SQLite 表结构（5 张表）
    ├── seed_data.sql              # 测试种子数据（10 名员工、5 个项目、考勤、绩效）
    ├── init_db.sh                 # 从 schema + seed 创建 enterprise.db
    ├── config.yaml.example        # 配置文件模板（数据库路径、知识库路径、LLM 设置）
    └── knowledge/                 # 7 个 Markdown 文档：人事制度、晋升标准、技术规范、财务制度、FAQ、会议纪要
```

## 数据库初始化

```bash
cd interview-exam/enterprise-qa-data
chmod +x init_db.sh
./init_db.sh
```

验证：
```bash
sqlite3 enterprise.db "SELECT name FROM employees WHERE employee_id='EMP-001';"
# 预期输出：张三
```

## 数据库结构（SQLite）

5 张表及索引：
- **employees** — employee_id (主键), name, department, level, hire_date, manager_id, email, status (active/on_leave/resigned)
- **projects** — project_id (主键), name, lead_id (外键→employees), status (planning/active/on_hold/completed), start_date, end_date, budget
- **project_members** — 复合主键 (project_id, employee_id), role (lead/core/contributor), join_date
- **attendance** — id (自增), employee_id (外键), date, status (on_time/late/absent/on_leave)。数据仅覆盖 2026 年 2 月。
- **performance_reviews** — id (自增), employee_id (外键), year, quarter (1-4), kpi_score (0-100), grade (S/A/B/C)。数据仅覆盖 2025 年。

## 配置方式

通过环境变量或 config.yaml 指定数据源路径：
```bash
export ENTERPRISE_QA_DB_PATH="./enterprise.db"
export ENTERPRISE_QA_KB_PATH="./knowledge"
```

## 测试用例（必须全部通过）

| 编号 | 问题 | 预期答案 | 数据来源 |
|------|------|---------|---------|
| T01 | 张三的部门是什么？ | 研发部 | employees |
| T02 | 李四的上级是谁？ | CEO (EMP-000) | employees |
| T03 | 年假怎么计算？ | 满1年5天，每年+1，上限15天 | hr_policies.md |
| T04 | 迟到几次扣钱？ | 4-6次开始扣，50元/次 | hr_policies.md |
| T05 | 张三负责哪些项目？ | PRJ-001(lead), PRJ-004(lead), PRJ-002(core), PRJ-003(contributor) | projects + project_members |
| T06 | 研发部有多少人？ | 4人 | employees |
| T07 | 王五符合P5晋升P6条件吗？ | 不符合 (KPI平均80<85, 项目1个<3个) | DB + promotion_rules.md |
| T08 | 张三2月迟到几次？ | 2次 | attendance |
| T09 | 查一下EMP-999 | 明确告知无此员工 | — |
| T10 | 最近有什么事？ | 追问澄清或返回最近会议/项目 | — |
| T11 | SELECT * FROM users WHERE '1'='1 | 拦截SQL注入 | — |
| T12 | xyzabc123怎么报销 | 告知无相关信息，不编造 | — |

## 评分标准（满分100分）

- **功能分（60分）：** 纯数据库查询 T01-T02 (15)、纯知识库查询 T03-T04 (15)、混合查询 T05-T08 (20)、边界情况 T09-T12 (10)
- **技术分（25分）：** 代码质量 (10)、安全性/参数化SQL (8)、单元测试覆盖率≥80% (7)
- **设计分（15分）：** 可扩展性 (5)、引用标注 (5)、创新性 (5)

## 技术要求

- 意图识别：判断查询类型（纯数据库、纯知识库、混合）
- 必须使用参数化 SQL 查询（禁止字符串拼接——这是明确的扣分项）
- 知识库必须使用索引检索（BM25 或 embedding），不能直接读取整个文件
- 多源结果融合与冲突处理
- 所有回答必须标注来源（表名/字段 或 文档名/章节）
- 核心模块单元测试覆盖率≥80%

## 关键数据速查

| 员工 | 部门 | 职级 | 入职日期 | 2025年平均KPI | 项目数 |
|------|------|------|---------|-------------|-------|
| 张三 EMP-001 | 研发部 | P6 | 2023-06-15 | 89.25 | 4 |
| 李四 EMP-002 | 研发部 | P7 | 2022-03-01 | 93.25 | 4 |
| 王五 EMP-003 | 产品部 | P5 | 2024-01-10 | 80.0 | 1 |
| 赵六 EMP-004 | 产品部 | P6 | 2021-09-20 | 88.75 | 1 |
| 钱七 EMP-005 | 研发部 | P5 | 2025-02-01 | 84.67 | 2 |

部门分布：研发部(4人)、产品部(3人)、市场部(1人)、管理层(1人)。在研项目：PRJ-001、PRJ-003。
