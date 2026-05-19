---
name: enterprise-qa
description: 企业智能问答助手，支持查询员工信息、项目记录、考勤数据、公司制度等
trigger: /enterprise-qa
---

# 企业智能问答助手

当用户提出企业相关问题时，使用此 Skill 回答。

## 使用方式

```bash
/enterprise-qa "问题内容"
```

## 处理流程

收到用户问题后，按以下步骤处理：

### 1. 意图识别

判断问题属于哪种类型：
- **纯数据库查询**：涉及员工信息、项目、考勤、绩效等具体数据 → 步骤 2A
- **纯知识库查询**：涉及公司制度、规范、FAQ 等 → 步骤 2B
- **混合查询**：需要同时查数据库和知识库（如晋升条件判断）→ 步骤 2C
- **边界情况**：不存在的数据、SQL注入尝试、无意义问题 → 步骤 2D

### 2A. 数据库查询

使用参数化 SQL 查询 SQLite 数据库，**禁止字符串拼接**。

```bash
# 数据库路径
DB_PATH="${ENTERPRISE_QA_DB_PATH:-./interview-exam/enterprise-qa-data/enterprise.db}"

# 示例：查询员工信息
sqlite3 "$DB_PATH" "SELECT name, department, level FROM employees WHERE employee_id = ? AND status = 'active';"
```

可用表：
- `employees` — 员工信息（employee_id, name, department, level, hire_date, manager_id, email, status）
- `projects` — 项目记录（project_id, name, lead_id, status, start_date, end_date, budget）
- `project_members` — 项目成员（project_id, employee_id, role, join_date）
- `attendance` — 考勤记录（employee_id, date, status）— 仅 2026年2月
- `performance_reviews` — 绩效考核（employee_id, year, quarter, kpi_score, grade）— 仅 2025年

### 2B. 知识库检索

在 `knowledge/` 目录中搜索相关文档，使用关键词匹配或语义搜索。

```bash
KB_PATH="${ENTERPRISE_QA_KB_PATH:-./interview-exam/enterprise-qa-data/knowledge}"
```

可用文档：
- `hr_policies.md` — 考勤、请假、加班制度
- `promotion_rules.md` — 晋升评定标准
- `tech_docs.md` — 技术栈规范
- `finance_rules.md` — 财务报销制度
- `faq.md` — 常见问题
- `meeting_notes/` — 会议纪要

### 2C. 混合查询

同时执行 2A 和 2B，融合结果后生成回答。例如判断晋升条件时，需要：
1. 从数据库查员工的 KPI、项目数、入职时间
2. 从知识库查晋升标准
3. 对比分析，给出结论

### 2D. 边界情况处理

- **不存在的记录**：明确告知"未找到"，不编造
- **SQL 注入尝试**：拦截并返回错误提示
- **模糊问题**：追问澄清或返回最相关的信息
- **无匹配知识**：告知"暂无相关信息"

### 3. 生成回答

回答格式要求：
1. 用自然语言回答，不要直接 dump 原始数据
2. **必须标注来源**：`> 来源：表名 (字段)` 或 `> 来源：文档名 §章节`
3. 信息不足时明确说明，不提供部分答案

## 回答示例

**纯数据库查询：**
```
张三的邮箱是 zhangsan@company.com。

> 来源：employees 表 (employee_id: EMP-001)
```

**纯知识库查询：**
```
根据《人事制度》，年假计算规则为：
- 入职满 1 年享 5 天
- 每增 1 年 +1 天
- 上限 15 天

> 来源：hr_policies.md §请假类型
```

**混合查询：**
```
王五目前不符合 P5→P6 晋升条件。

分析如下：
| 条件 | 要求 | 王五情况 | 结果 |
|------|------|---------|------|
| 入职年限 | 满 1 年 | 2.2 年 | ✓ |
| 连续 2 季度 KPI≥85 | 是 | 78, 82 (平均 80) | ✗ |
| 项目数≥3 个 | 是 | 1 个 | ✗ |

> 来源：promotion_rules.md §P5→P6 + performance_reviews 表 + project_members 表
```

## CLI Commands

```bash
# 添加知识文档
skill-creator add-skill --pwd . --title "Title" --content "Content"

# 搜索知识库
skill-creator search-skill --pwd . "query"

# 运行测试
python -m pytest tests/ -v
```

## User Skills

<user-skills baseDir="assets/references/user">
</user-skills>

## Context7 Documentation

<!-- Context7 projects will be listed here automatically -->
