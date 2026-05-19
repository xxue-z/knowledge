"""结果融合与回答生成模块"""

from datetime import date

from .db import Database
from .intent import Intent, QueryType
from .kb import KnowledgeBase


# 模拟当前日期 2026-03-27
CURRENT_DATE = date(2026, 3, 27)


def resolve_employee_name(db: Database, name: str) -> dict | None:
    """根据姓名查找员工。"""
    return db.query_one(
        "SELECT * FROM employees WHERE name = ? AND status = 'active'",
        (name,),
    )


def format_db_answer(data: dict | list[dict] | None, source: str) -> str:
    """格式化数据库查询结果为自然语言回答。"""
    if data is None:
        return "未找到相关记录。"
    if isinstance(data, list) and len(data) == 0:
        return "未找到相关记录。"
    return ""  # 由调用方自定义


def generate_pure_db_answer(db: Database, intent: Intent) -> str:
    """处理纯数据库查询。"""
    entities = intent.entities
    query = intent.raw_query

    # 部门人数查询（无需员工实体）
    if any(kw in query for kw in ["多少人", "几个人", "人数"]):
        dept = entities.get("department", "")
        if dept:
            count = db.count_employees_by_department(dept)
            employees = db.get_employees_by_department(dept)
            names = "、".join(e["name"] for e in employees)
            return (
                f"{dept}有 {count} 人：{names}。\n\n"
                f"> 来源：employees 表 (department='{dept}', status='active')"
            )

    # 项目级成绩查询（无需员工实体）
    if "项目" in query and any(kw in query for kw in ["成绩", "绩效", "表现", "好", "优秀"]):
        projects = db.get_active_projects()
        if projects:
            lines = ["在研项目及其负责人绩效：\n"]
            for p in projects:
                lead = db.get_employee_by_id(p["lead_id"])
                lead_name = lead["name"] if lead else p["lead_id"]
                avg_kpi = db.get_avg_kpi(p["lead_id"]) or 0
                lines.append(f"- **{p['name']}**（{p['project_id']}）— 负责人：{lead_name}，平均 KPI：{avg_kpi}")
            lines.append(f"\n> 来源：projects 表 + performance_reviews 表")
            return "\n".join(lines)

    # 查员工基本信息
    employee = None
    if entities.get("employee_id"):
        employee = db.get_employee_by_id(entities["employee_id"])
    elif entities.get("employee_name"):
        employee = resolve_employee_name(db, entities["employee_name"])

    if not employee:
        eid = entities.get("employee_id", "")
        name = entities.get("employee_name", "")
        identifier = eid or name or "未知"
        return f"未找到员工 {identifier} 的记录。"

    emp_id = employee["employee_id"]
    emp_name = employee["name"]

    # 部门查询
    if any(kw in query for kw in ["部门", "哪个部门", "什么部门"]):
        return (
            f"{emp_name}的部门是{employee['department']}。\n\n"
            f"> 来源：employees 表 (employee_id: {emp_id})"
        )

    # 上级查询
    if any(kw in query for kw in ["上级", "领导", "汇报"]):
        manager = db.get_manager(emp_id)
        if manager:
            return (
                f"{emp_name}的上级是{manager['name']}（{manager['employee_id']}）。\n\n"
                f"> 来源：employees 表 (employee_id: {emp_id}, manager_id: {employee['manager_id']})"
            )
        return f"{emp_name}没有上级记录。\n\n> 来源：employees 表 (employee_id: {emp_id})"

    # 邮箱查询
    if "邮箱" in query or "email" in query.lower():
        return (
            f"{emp_name}的邮箱是 {employee['email']}。\n\n"
            f"> 来源：employees 表 (employee_id: {emp_id})"
        )

    # 项目查询
    if any(kw in query for kw in ["项目", "负责"]):
        projects = db.get_projects_by_employee(emp_id)
        if not projects:
            return f"{emp_name}暂无参与项目。\n\n> 来源：project_members 表"
        lines = []
        for p in projects:
            lines.append(f"- {p['name']}（{p['project_id']}）- 角色：{p['role']}")
        return (
            f"{emp_name}参与的项目：\n" + "\n".join(lines) + "\n\n"
            f"> 来源：projects 表 + project_members 表 (employee_id: {emp_id})"
        )

    # 迟到查询
    if "迟到" in query:
        # 推断月份
        month = "2026-02"  # 默认考勤数据所在月
        if "2月" in query or "二月" in query:
            month = "2026-02"
        count = db.count_late_attendance(emp_id, month)
        return (
            f"{emp_name}在 {month} 迟到 {count} 次。\n\n"
            f"> 来源：attendance 表 (employee_id: {emp_id}, date LIKE '{month}-%', status='late')"
        )

    # 绩效查询
    if any(kw in query for kw in ["绩效", "KPI", "kpi", "考核", "业绩", "成绩"]):
        avg_kpi = db.get_avg_kpi(emp_id)
        reviews = db.get_quarterly_kpi(emp_id)
        if avg_kpi is not None:
            lines = [f"{emp_name} 2025年平均KPI：{avg_kpi}"]
            lines.append("\n季度明细：")
            for r in reviews:
                lines.append(f"- {r['year']} Q{r['quarter']}: {r['kpi_score']} 分（{r['grade']}）")
            return (
                "\n".join(lines) + "\n\n"
                f"> 来源：performance_reviews 表 (employee_id: {emp_id})"
            )
        return f"{emp_name}暂无绩效记录。\n\n> 来源：performance_reviews 表"

    # 默认返回员工基本信息
    return (
        f"{emp_name}，{employee['department']}，职级 {employee['level']}，"
        f"入职日期 {employee['hire_date']}。\n\n"
        f"> 来源：employees 表 (employee_id: {emp_id})"
    )


def generate_pure_kb_answer(kb: KnowledgeBase, intent: Intent) -> str:
    """处理纯知识库查询。"""
    query = intent.raw_query
    results = kb.search(query, top_k=3)

    if not results:
        return "暂无相关信息，建议咨询 HR 部门。"

    # 取最相关的结果
    best = results[0]
    source_file = best["filename"]
    section_title = best["title"]

    return (
        f"{best['body']}\n\n"
        f"> 来源：{source_file} §{section_title}"
    )


def generate_hybrid_answer(db: Database, kb: KnowledgeBase, intent: Intent) -> str:
    """处理混合查询。"""
    entities = intent.entities
    query = intent.raw_query

    # 晋升条件判断
    if any(kw in query for kw in ["晋升", "符合", "条件", "升级"]):
        return _evaluate_promotion(db, kb, entities)

    # 迟到 + 扣款规则
    if "迟到" in query and any(kw in query for kw in ["扣钱", "扣款", "制度"]):
        return _answer_late_penalty(db, kb, entities)

    # 模糊问题
    if any(kw in query for kw in ["最近有什么事", "最近发生"]):
        return _answer_recent_events(db, kb)

    # 通用混合：同时查 DB 和 KB
    db_answer = generate_pure_db_answer(db, intent) if entities else ""
    kb_results = kb.search(query, top_k=2)

    parts = []
    if db_answer and "未找到" not in db_answer:
        parts.append(db_answer)
    if kb_results:
        # 只取相关度较高的结果
        for r in kb_results:
            if r["score"] > 2.0:
                parts.append(f"\n{r['body']}\n> 来源：{r['filename']} §{r['title']}")

    return "\n".join(parts) if parts else "暂无相关信息。"


def _evaluate_promotion(db: Database, kb: KnowledgeBase, entities: dict) -> str:
    """评估晋升条件。"""
    employee = None
    if entities.get("employee_id"):
        employee = db.get_employee_by_id(entities["employee_id"])
    elif entities.get("employee_name"):
        employee = resolve_employee_name(db, entities["employee_name"])

    if not employee:
        return "未找到该员工记录，无法评估晋升条件。"

    emp_id = employee["employee_id"]
    emp_name = employee["name"]
    current_level = employee["level"]
    hire_date = employee["hire_date"]

    # 确定目标职级
    level_map = {"P4": "P5", "P5": "P6", "P6": "P7", "P7": "P8"}
    target_level = level_map.get(current_level)
    if not target_level:
        return f"{emp_name}当前职级 {current_level}，无更高职级可晋升。"

    # 查晋升标准
    promotion_doc = kb.get_document("promotion_rules.md")
    if not promotion_doc:
        return "未找到晋升标准文档。"

    # 找到对应职级的标准
    section_key = f"{current_level} → {target_level}"
    promotion_section = None
    for section in promotion_doc.sections:
        if section_key in section["title"] or current_level in section["title"]:
            promotion_section = section
            break

    # 查询数据库
    avg_kpi = db.get_avg_kpi(emp_id) or 0
    project_count = db.count_projects(emp_id)
    reviews = db.get_quarterly_kpi(emp_id)

    # 计算入职年限
    hire = _parse_date(hire_date)
    years_since_hire = (CURRENT_DATE - hire).days / 365.25 if hire else 0

    # 分析各项条件
    conditions = []

    if current_level == "P5":
        # P5→P6: 入职满1年, 连续2季度KPI≥85, 项目≥3
        cond1 = years_since_hire >= 1
        conditions.append(("入职年限", "满 1 年", f"{years_since_hire:.1f} 年", cond1))

        cond2 = _check_consecutive_kpi(reviews, 2, 85)
        kpi_str = ", ".join(str(r["kpi_score"]) for r in reviews[-2:]) if len(reviews) >= 2 else "数据不足"
        conditions.append((f"连续 2 季度 KPI≥85", "是", f"{kpi_str} (平均 {avg_kpi})", cond2))

        cond3 = project_count >= 3
        conditions.append(("项目数≥3 个", "是", f"{project_count} 个", cond3))
    elif current_level == "P6":
        # P6→P7: P6满2年, 连续4季度KPI≥90, 主导项目≥2, 技术突破
        p6_years = years_since_hire  # 简化处理
        cond1 = p6_years >= 2
        conditions.append(("P6 满 2 年", "满 2 年", f"{p6_years:.1f} 年", cond1))

        cond2 = _check_consecutive_kpi(reviews, 4, 90)
        conditions.append(("连续 4 季度 KPI≥90", "是", f"平均 {avg_kpi}", cond2))

        led_projects = db.query(
            "SELECT COUNT(*) as cnt FROM project_members WHERE employee_id = ? AND role = 'lead'",
            (emp_id,),
        )
        lead_count = led_projects[0]["cnt"] if led_projects else 0
        cond3 = lead_count >= 2
        conditions.append(("主导项目≥2 个", "是", f"{lead_count} 个", cond3))
    else:
        # 通用处理
        conditions.append(("入职年限", "满 1 年", f"{years_since_hire:.1f} 年", years_since_hire >= 1))
        conditions.append(("KPI 表现", "≥85", f"{avg_kpi}", avg_kpi >= 85))
        conditions.append(("项目参与", "≥3 个", f"{project_count} 个", project_count >= 3))

    # 判断结果
    all_met = all(c[3] for c in conditions)
    result = "符合" if all_met else "不符合"

    # 构建回答
    lines = [f"{emp_name}目前{'已' if all_met else '不'}符合 {current_level}→{target_level} 晋升条件。\n"]
    lines.append("分析如下：")
    lines.append("| 条件 | 要求 | 实际情况 | 结果 |")
    lines.append("|------|------|---------|------|")
    for name, req, actual, met in conditions:
        lines.append(f"| {name} | {req} | {actual} | {'✓' if met else '✗'} |")

    # 来源标注
    sources = [f"promotion_rules.md §{section_key}"]
    sources.append(f"performance_reviews 表")
    sources.append(f"project_members 表")
    sources.append(f"employees 表 (hire_date: {hire_date})")

    lines.append(f"\n> 来源：{' + '.join(sources)}")

    return "\n".join(lines)


def _answer_late_penalty(db: Database, kb: KnowledgeBase, entities: dict) -> str:
    """回答迟到扣款问题。"""
    employee = None
    if entities.get("employee_id"):
        employee = db.get_employee_by_id(entities["employee_id"])
    elif entities.get("employee_name"):
        employee = resolve_employee_name(db, entities["employee_name"])

    # 查迟到制度
    hr_doc = kb.get_document("hr_policies.md")
    penalty_section = None
    if hr_doc:
        for section in hr_doc.sections:
            if "迟到" in section["title"] or "扣" in section["body"]:
                penalty_section = section
                break

    parts = []
    if employee:
        late_count = db.count_late_attendance(employee["employee_id"], "2026-02")
        parts.append(f"{employee['name']} 2026年2月迟到 {late_count} 次。")

    if penalty_section:
        parts.append(f"\n根据《人事制度》{penalty_section['title']}：")
        parts.append(penalty_section["body"])
        parts.append(f"\n> 来源：hr_policies.md §{penalty_section['title']}")

    if employee:
        parts.append(f"> 来源：attendance 表 (employee_id: {employee['employee_id']})")

    return "\n".join(parts) if parts else "暂无相关迟到和扣款信息。"


def _answer_recent_events(db: Database, kb: KnowledgeBase) -> str:
    """回答最近发生了什么事。"""
    parts = ["以下是最近的相关信息：\n"]

    # 查最近会议
    meeting_notes = kb.search("会议 大会 纪要", top_k=3)
    if meeting_notes:
        parts.append("### 最近会议")
        for note in meeting_notes:
            parts.append(f"- {note['filename']}：{note['title']}")
            # 提取前几行摘要
            summary_lines = note["body"].split("\n")[:3]
            parts.append(f"  {' '.join(line.strip() for line in summary_lines if line.strip())}")

    # 查在研项目
    active_projects = db.get_active_projects()
    if active_projects:
        parts.append("\n### 在研项目")
        for p in active_projects:
            lead = db.get_employee_by_id(p["lead_id"])
            lead_name = lead["name"] if lead else p["lead_id"]
            parts.append(f"- {p['name']}（负责人：{lead_name}）")

    sources = []
    if meeting_notes:
        sources.append("meeting_notes/")
    if active_projects:
        sources.append("projects 表")
    parts.append(f"\n> 来源：{' + '.join(sources)}")

    return "\n".join(parts)


def _parse_date(date_str: str) -> date | None:
    """解析日期字符串。"""
    try:
        parts = date_str.split("-")
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return None


def _check_consecutive_kpi(reviews: list[dict], quarters: int, threshold: float) -> bool:
    """检查最近 N 个季度 KPI 是否连续达标。"""
    if len(reviews) < quarters:
        return False
    recent = reviews[-quarters:]
    return all(r["kpi_score"] >= threshold for r in recent)
