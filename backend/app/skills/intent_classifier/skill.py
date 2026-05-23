import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class IntentClassifierSkill:
    """意图分类 Skill - 判断用户查询是数据库查询还是知识库查询"""

    DB_KEYWORDS = [
        "员工", "人员", "部门", "工号", "入职", "在职", "离职",
        "项目", "负责", "参与", "成员", "负责人",
        "考勤", "迟到", "早退", "打卡", "请假", "加班",
        "绩效", "KPI", "考核", "评分", "等级", "晋升",
        "上级", "下属", "经理", "总监",
        "多少人", "几个人", "统计", "人数",
    ]

    KB_KEYWORDS = [
        "制度", "规定", "政策", "规范", "标准", "流程",
        "年假", "假期", "福利", "薪酬", "工资",
        "报销", "费用", "财务", "发票",
        "技术", "开发", "代码", "API", "架构",
        "FAQ", "常见问题", "怎么", "如何", "为什么",
        "会议", "纪要", "记录", "决议",
        "晋升", "升级", "条件", "要求",
    ]

    SQL_INJECTION_PATTERNS = [
        r"(?i)(union\s+select)",
        r"(?i)(or\s+1\s*=\s*1)",
        r"(?i)(drop\s+table)",
        r"(?i)(--\s*$)",
        r"(?i)(/\*.*\*/)",
        r"(?i)('\s*or\s*')",
    ]

    async def classify(self, question: str) -> dict:
        """分类用户问题意图"""
        if self._detect_sql_injection(question):
            return {
                "intent": "SECURITY_BLOCK",
                "confidence": 1.0,
                "entities": {},
                "keywords": []
            }

        db_score = sum(1 for kw in self.DB_KEYWORDS if kw in question)
        kb_score = sum(1 for kw in self.KB_KEYWORDS if kw in question)

        if self._is_hybrid_intent(question):
            return {
                "intent": "HYBRID",
                "confidence": 0.9,
                "entities": self._extract_entities(question),
                "keywords": []
            }

        if db_score > 0 and kb_score == 0:
            return {
                "intent": "PURE_DB",
                "confidence": min(0.5 + db_score * 0.1, 0.95),
                "entities": self._extract_entities(question),
                "keywords": []
            }
        elif kb_score > 0 and db_score == 0:
            return {
                "intent": "PURE_KB",
                "confidence": min(0.5 + kb_score * 0.1, 0.95),
                "entities": {},
                "keywords": []
            }
        elif db_score > 0 and kb_score > 0:
            return {
                "intent": "HYBRID",
                "confidence": 0.7,
                "entities": self._extract_entities(question),
                "keywords": []
            }

        return {
            "intent": "BOUNDARY",
            "confidence": 0.3,
            "entities": {},
            "keywords": []
        }

    def _detect_sql_injection(self, text: str) -> bool:
        """检测 SQL 注入"""
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text):
                return True
        return False

    def _is_hybrid_intent(self, question: str) -> bool:
        """判断是否为混合意图"""
        hybrid_patterns = [
            (["晋升", "升级"], ["条件", "符合", "要求"]),
            (["迟到", "早退"], ["扣钱", "罚款", "处罚"]),
            (["请假"], ["制度", "规定", "政策"]),
        ]

        for db_kws, kb_kws in hybrid_patterns:
            has_db = any(kw in question for kw in db_kws)
            has_kb = any(kw in question for kw in kb_kws)
            if has_db and has_kb:
                return True

        return False

    def _extract_entities(self, question: str) -> Dict[str, List[str]]:
        """提取实体"""
        entities = {}

        employee_names = self._extract_names(question)
        if employee_names:
            entities["employee_names"] = employee_names

        departments = self._extract_departments(question)
        if departments:
            entities["departments"] = departments

        return entities

    def _extract_names(self, text: str) -> List[str]:
        """提取人名（简单实现）"""
        names = []
        name_patterns = ["张经理", "李总", "王员工", "刘经理", "陈总监"]
        for name in name_patterns:
            if name in text:
                names.append(name)
        return names

    def _extract_departments(self, text: str) -> List[str]:
        """提取部门"""
        departments = ["技术部", "销售部", "市场部", "人事部", "财务部", "产品部"]
        return [dept for dept in departments if dept in text]
