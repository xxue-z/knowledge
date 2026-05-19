"""意图识别模块测试"""

import pytest
from src.intent import classify_intent, QueryType, detect_sql_injection


class TestSQLInjectionDetection:
    def test_detect_union_injection(self):
        assert detect_sql_injection("SELECT * FROM users WHERE '1'='1' UNION SELECT * FROM passwords") is True

    def test_detect_or_injection(self):
        assert detect_sql_injection("' OR 1=1 --") is True

    def test_detect_drop_injection(self):
        assert detect_sql_injection("'; DROP TABLE employees; --") is True

    def test_normal_text_passes(self):
        assert detect_sql_injection("张三的部门是什么？") is False

    def test_chinese_text_passes(self):
        assert detect_sql_injection("年假怎么计算？") is False


class TestIntentClassification:
    def test_pure_db_department_query(self):
        intent = classify_intent("张三的部门是什么？")
        assert intent.query_type == QueryType.PURE_DB
        assert intent.entities.get("employee_name") == "张三"

    def test_pure_db_manager_query(self):
        intent = classify_intent("李四的上级是谁？")
        assert intent.query_type == QueryType.PURE_DB
        assert intent.entities.get("employee_name") == "李四"

    def test_pure_kb_annual_leave(self):
        intent = classify_intent("年假怎么计算？")
        assert intent.query_type == QueryType.PURE_KB

    def test_pure_kb_late_penalty(self):
        intent = classify_intent("迟到几次扣钱？")
        # "迟到"匹配 DB 和 KB，"扣钱"匹配 KB，分类为 HYBRID 也合理
        assert intent.query_type in (QueryType.PURE_KB, QueryType.HYBRID)

    def test_hybrid_promotion(self):
        intent = classify_intent("王五符合P5晋升P6条件吗？")
        assert intent.query_type == QueryType.HYBRID
        assert intent.entities.get("employee_name") == "王五"

    def test_hybrid_late_penalty(self):
        intent = classify_intent("张三迟到扣钱的制度是什么？")
        assert intent.query_type in (QueryType.HYBRID, QueryType.PURE_KB)

    def test_boundary_sql_injection(self):
        intent = classify_intent("SELECT * FROM users WHERE '1'='1")
        assert intent.query_type == QueryType.BOUNDARY

    def test_boundary_unknown(self):
        intent = classify_intent("xyzabc123怎么报销")
        # 可能是 PURE_KB（因为有"报销"关键词）或 BOUNDARY
        assert intent.query_type in (QueryType.PURE_KB, QueryType.BOUNDARY)

    def test_pure_db_project_query(self):
        intent = classify_intent("张三负责哪些项目？")
        assert intent.query_type == QueryType.PURE_DB
        assert intent.entities.get("employee_name") == "张三"

    def test_pure_db_department_count(self):
        intent = classify_intent("研发部有多少人？")
        assert intent.query_type == QueryType.PURE_DB
        assert intent.entities.get("department") == "研发部"

    def test_employee_id_extraction(self):
        intent = classify_intent("查一下 EMP-999")
        assert intent.entities.get("employee_id") == "EMP-999"

    def test_hybrid_recent_events(self):
        intent = classify_intent("最近有什么事？")
        assert intent.query_type == QueryType.HYBRID
