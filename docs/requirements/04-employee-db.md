# 需求文档：员工档案数据库

## 1. 需求概述

员工档案存储于关系数据库，支持精确查询、统计分析和行级安全控制。

---

## 2. 功能需求

### 2.1 员工档案管理

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| EMP-001 | 员工档案 CRUD 操作 | README.md 第1节 |
| EMP-002 | 支持按姓名查询员工 | README.md 第6节 |
| EMP-003 | 支持按工号查询员工 | README.md 第6节 |
| EMP-004 | 支持按部门统计员工数量 | README.md 第1节 |
| EMP-005 | 支持上级/下属关系查询 | README.md 第6节 |

### 2.2 行级安全

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| EMP-006 | 普通员工仅能查看自己的档案 | README.md 第5节 |
| EMP-007 | 经理可查看本部门及下级员工 | README.md 第5节 |
| EMP-008 | HR 可查看全公司但敏感字段加密 | README.md 第5节 |
| EMP-009 | SQL 查询时强制追加 WHERE 条件限定数据范围 | README.md 第4节 |
| EMP-010 | 支持 PostgreSQL RLS（行级安全策略） | README.md 第4节 |

### 2.3 轻库 Agent

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| EMP-011 | 轻库 Agent 执行员工档案条件查询 | README.md 第3节 |
| EMP-012 | 轻库 Agent 执行聚合计算 | README.md 第3节 |
| EMP-013 | 轻库 Agent 强制注入 WHERE 条件限定数据范围 | README.md 第3节 |

### 2.4 敏感字段处理

| 需求编号 | 需求描述 | 来源 |
|----------|----------|------|
| EMP-014 | 薪酬字段对非 HR/管理员脱敏显示 | README.md 第5节 |
| EMP-015 | 手机号字段脱敏显示 | 安全需求 |
| EMP-016 | 密级字段控制数据可见性 | README.md 第4节 |

---

## 3. 数据模型需求

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | Integer | 主键 | 自增ID |
| employee_id | String | 唯一 | 工号 |
| name | String | - | 姓名 |
| department | String | - | 部门名称 |
| dept_id | String | 索引 | 部门ID |
| level | String | - | 职级 |
| hire_date | Date | 可选 | 入职日期 |
| manager_id | String | 可选 | 上级工号 |
| email | String | 可选 | 邮箱 |
| phone | String | 可选 | 手机号（存储加密） |
| salary | Float | 可选 | 薪酬（存储加密） |
| status | String | enum | 在职/离职/试用期 |
| clearance_level | Integer | 默认=1 | 安全密级 |
| created_at | DateTime | - | 创建时间 |
| updated_at | DateTime | - | 更新时间 |

---

## 4. 非功能需求

| 需求编号 | 需求描述 |
|----------|----------|
| EMP-NFR-001 | 档案查询响应时间 < 200ms |
| EMP-NFR-002 | 支持 10000+ 员工记录存储 |
| EMP-NFR-003 | 敏感字段存储加密 |
