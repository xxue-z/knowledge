"""意图识别模块 - 判断用户问题类型"""

import re
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    PURE_DB = "pure_db"          # 纯数据库查询
    PURE_KB = "pure_kb"          # 纯知识库查询
    HYBRID = "hybrid"            # 混合查询
    BOUNDARY = "boundary"        # 边界情况


@dataclass
class Intent:
    query_type: QueryType
    entities: dict[str, str]   # 识别到的实体
    raw_query: str


# SQL 注入检测模式
SQL_INJECTION_PATTERNS = [
    r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b.*\b(FROM|INTO|WHERE|TABLE)\b",
    r"(?i)'(\s)*(OR|AND)\s+\d+\s*=\s*\d+",
    r"(?i)--",
    r"(?i)/\*.*\*/",
    r"(?i);\s*(SELECT|INSERT|UPDATE|DELETE|DROP)",
]

# 知识库关键词映射
KB_KEYWORDS = {
    "hr_policies": ["迟到", "考勤", "请假", "年假", "病假", "事假", "调休", "加班", "工作时间", "打卡", "扣钱", "扣款"],
    "promotion_rules": ["晋升", "升级", "职级", "P4", "P5", "P6", "P7", "P8", "条件", "资格"],
    "tech_docs": ["技术栈", "技术规范", "代码规范", "开发流程", "框架"],
    "finance_rules": ["报销", "差旅", "机票", "酒店", "餐补", "招待费", "财务"],
    "faq": ["远程办公", "体检", "试用期", "五险一金", "打车", "宵夜"],
    "meeting_notes": ["会议", "大会", "全员", "技术同步", "纪要", "最近有什么事", "最近发生"],
}

# 数据库关键词映射
DB_KEYWORDS = {
    "employee": ["邮箱", "部门", "上级", "领导", "入职", "员工", "在职", "离职", "姓名"],
    "project": ["项目", "负责", "在研", "规划中", "已完成", "暂停"],
    "attendance": ["迟到", "考勤", "旷工", "出勤", "请假天数"],
    "performance": ["绩效", "KPI", "kpi", "考核", "评分", "等级", "成绩", "业绩"],
    "count": ["多少人", "几个人", "人数", "几个人"],
}


def detect_sql_injection(query: str) -> bool:
    """检测 SQL 注入尝试。"""
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, query):
            return True
    return False


def extract_employee_id(query: str) -> str | None:
    """从问题中提取员工 ID。"""
    match = re.search(r"EMP-\d+", query)
    return match.group(0) if match else None


def extract_employee_name(query: str) -> str | None:
    """从问题中提取员工姓名。"""
    # 优先匹配已知姓名
    known_names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十", "CEO"]
    for name in known_names:
        if name in query:
            return name
    # 尝试匹配"X某某"模式：常见姓氏 + 1-2个汉字
    common_surnames = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
    match = re.search(rf"([{common_surnames}])([一-鿿]{{1,2}})(?:的|做|是|有|在|负责|参与|出)", query)
    if match:
        return match.group(1) + match.group(2)
    return None


def extract_department(query: str) -> str | None:
    """从问题中提取部门名称。"""
    departments = ["研发部", "产品部", "市场部", "管理层"]
    for dept in departments:
        if dept in query:
            return dept
    return None


def classify_intent(query: str) -> Intent:
    """对用户问题进行意图分类。"""
    # 1. 检测 SQL 注入
    if detect_sql_injection(query):
        return Intent(
            query_type=QueryType.BOUNDARY,
            entities={"reason": "sql_injection"},
            raw_query=query,
        )

    entities: dict[str, str] = {}

    # 提取实体
    emp_id = extract_employee_id(query)
    if emp_id:
        entities["employee_id"] = emp_id

    emp_name = extract_employee_name(query)
    if emp_name:
        entities["employee_name"] = emp_name

    dept = extract_department(query)
    if dept:
        entities["department"] = dept

    # 2. 计算关键词匹配分数
    db_score = 0
    kb_score = 0

    matched_db_categories = set()
    for category, keywords in DB_KEYWORDS.items():
        for kw in keywords:
            if kw in query:
                db_score += 1
                matched_db_categories.add(category)

    matched_kb_categories = set()
    for category, keywords in KB_KEYWORDS.items():
        for kw in keywords:
            if kw in query:
                kb_score += 1
                matched_kb_categories.add(category)

    # 3. 特殊规则：晋升判断是混合查询
    if any(kw in query for kw in ["符合", "晋升", "条件"]) and (
        entities.get("employee_id") or entities.get("employee_name")
    ):
        return Intent(QueryType.HYBRID, entities, query)

    # 4. 特殊规则：迟到涉及扣款 = 混合
    if "迟到" in query and any(kw in query for kw in ["扣钱", "扣款", "制度", "规则"]):
        return Intent(QueryType.HYBRID, entities, query)

    # 5. 模糊问题
    if any(kw in query for kw in ["最近有什么事", "最近发生", "有什么新闻"]):
        return Intent(QueryType.HYBRID, entities, query)

    # 6. 特殊规则：有员工实体 + 考勤相关 = 纯 DB
    if (entities.get("employee_id") or entities.get("employee_name")) and \
       any(kw in query for kw in ["迟到", "考勤", "出勤", "旷工"]):
        if not any(kw in query for kw in ["扣钱", "扣款", "制度", "规则", "怎么算"]):
            return Intent(QueryType.PURE_DB, entities, query)

    # 7. 有员工实体 + KB 关键词 = 混合查询
    if (entities.get("employee_id") or entities.get("employee_name")) and kb_score > 0:
        return Intent(QueryType.HYBRID, entities, query)

    # 8. 根据分数判断
    if db_score > 0 and kb_score > 0:
        return Intent(QueryType.HYBRID, entities, query)
    elif db_score > 0:
        return Intent(QueryType.PURE_DB, entities, query)
    elif kb_score > 0:
        return Intent(QueryType.PURE_KB, entities, query)

    # 7. 如果提取到了员工实体，默认走数据库
    if entities.get("employee_id") or entities.get("employee_name"):
        return Intent(QueryType.PURE_DB, entities, query)

    # 8. 无法判断，标记为边界情况
    return Intent(QueryType.BOUNDARY, entities, query)
