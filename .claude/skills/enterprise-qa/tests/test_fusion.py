"""结果融合与回答生成模块测试"""

import pytest
from pathlib import Path

from src.db import Database
from src.kb import KnowledgeBase
from src.intent import classify_intent, QueryType
from src.fusion import (
    generate_pure_db_answer,
    generate_pure_kb_answer,
    generate_hybrid_answer,
    resolve_employee_name,
)


@pytest.fixture
def base_path():
    return Path(__file__).resolve().parent.parent.parent.parent.parent / "interview-exam" / "enterprise-qa-data"


@pytest.fixture
def db(base_path):
    path = base_path / "enterprise.db"
    if not path.exists():
        pytest.skip("测试数据库不存在")
    return Database(str(path))


@pytest.fixture
def kb(base_path):
    path = base_path / "knowledge"
    if not path.exists():
        pytest.skip("知识库不存在")
    return KnowledgeBase(str(path))


class TestPureDBAnswers:
    def test_t01_department(self, db):
        intent = classify_intent("张三的部门是什么？")
        answer = generate_pure_db_answer(db, intent)
        assert "研发部" in answer
        assert "来源" in answer

    def test_t02_manager(self, db):
        intent = classify_intent("李四的上级是谁？")
        answer = generate_pure_db_answer(db, intent)
        assert "CEO" in answer or "EMP-000" in answer

    def test_t06_department_count(self, db):
        intent = classify_intent("研发部有多少人？")
        answer = generate_pure_db_answer(db, intent)
        assert "4" in answer
        assert "研发部" in answer

    def test_t08_late_count(self, db):
        intent = classify_intent("张三2月迟到几次？")
        answer = generate_pure_db_answer(db, intent)
        assert "2" in answer

    def test_t09_nonexistent_employee(self, db):
        intent = classify_intent("查一下 EMP-999")
        answer = generate_pure_db_answer(db, intent)
        assert "未找到" in answer

    def test_email_query(self, db):
        intent = classify_intent("张三的邮箱是什么？")
        answer = generate_pure_db_answer(db, intent)
        assert "zhangsan@company.com" in answer

    def test_project_query(self, db):
        intent = classify_intent("张三负责哪些项目？")
        answer = generate_pure_db_answer(db, intent)
        assert "PRJ-001" in answer
        assert "lead" in answer

    def test_performance_query(self, db):
        intent = classify_intent("张三的绩效怎么样？")
        answer = generate_pure_db_answer(db, intent)
        assert "89.25" in answer or "绩效" in answer


class TestPureKBAnswers:
    def test_t03_annual_leave(self, kb):
        intent = classify_intent("年假怎么计算？")
        answer = generate_pure_kb_answer(kb, intent)
        assert "5 天" in answer or "5天" in answer
        assert "来源" in answer

    def test_t04_late_penalty(self, kb):
        intent = classify_intent("迟到几次扣钱？")
        answer = generate_pure_kb_answer(kb, intent)
        assert "50" in answer


class TestHybridAnswers:
    def test_t07_promotion_evaluation(self, db, kb):
        intent = classify_intent("王五符合P5晋升P6条件吗？")
        answer = generate_hybrid_answer(db, kb, intent)
        assert "不符合" in answer or "不满足" in answer
        assert "来源" in answer

    def test_promotion_zhangsan(self, db, kb):
        intent = classify_intent("张三符合晋升条件吗？")
        answer = generate_hybrid_answer(db, kb, intent)
        assert "来源" in answer


class TestBoundaryCases:
    def test_sql_injection_blocked(self):
        intent = classify_intent("SELECT * FROM users WHERE '1'='1")
        assert intent.query_type == QueryType.BOUNDARY

    def test_unknown_query(self):
        intent = classify_intent("xyzabc123怎么报销")
        assert intent.query_type in (QueryType.PURE_KB, QueryType.BOUNDARY)
