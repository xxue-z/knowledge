"""数据库模块测试"""

import pytest
from pathlib import Path
import sqlite3
import tempfile
import os

from src.db import Database


@pytest.fixture
def db_path():
    """使用测试数据库。"""
    path = Path(__file__).resolve().parent.parent.parent.parent.parent / "interview-exam" / "enterprise-qa-data" / "enterprise.db"
    if not path.exists():
        pytest.skip("测试数据库不存在，请先运行 init_db.sh")
    return str(path)


@pytest.fixture
def db(db_path):
    return Database(db_path)


class TestEmployeeQueries:
    def test_get_employee_by_id(self, db):
        emp = db.get_employee_by_id("EMP-001")
        assert emp is not None
        assert emp["name"] == "张三"
        assert emp["department"] == "研发部"

    def test_get_nonexistent_employee(self, db):
        emp = db.get_employee_by_id("EMP-999")
        assert emp is None

    def test_get_employees_by_department(self, db):
        employees = db.get_employees_by_department("研发部")
        assert len(employees) == 4
        names = {e["name"] for e in employees}
        assert "张三" in names
        assert "李四" in names

    def test_get_manager(self, db):
        manager = db.get_manager("EMP-001")
        assert manager is not None
        assert manager["name"] == "CEO"

    def test_count_employees_by_department(self, db):
        count = db.count_employees_by_department("研发部")
        assert count == 4

    def test_count_employees_product_dept(self, db):
        count = db.count_employees_by_department("产品部")
        assert count == 3


class TestProjectQueries:
    def test_get_projects_by_employee(self, db):
        projects = db.get_projects_by_employee("EMP-001")
        assert len(projects) == 4
        roles = {p["project_id"]: p["role"] for p in projects}
        assert roles["PRJ-001"] == "lead"
        assert roles["PRJ-004"] == "lead"

    def test_get_active_projects(self, db):
        projects = db.get_active_projects()
        assert len(projects) == 2
        ids = {p["project_id"] for p in projects}
        assert "PRJ-001" in ids
        assert "PRJ-003" in ids


class TestAttendanceQueries:
    def test_count_late_attendance_zhangsan(self, db):
        count = db.count_late_attendance("EMP-001", "2026-02")
        assert count == 2

    def test_count_late_attendance_wangwu(self, db):
        count = db.count_late_attendance("EMP-003", "2026-02")
        assert count == 5

    def test_count_late_attendance_no_late(self, db):
        count = db.count_late_attendance("EMP-002", "2026-02")
        assert count == 0


class TestPerformanceQueries:
    def test_get_avg_kpi(self, db):
        avg = db.get_avg_kpi("EMP-001")
        assert avg is not None
        assert avg == 89.25

    def test_get_avg_kpi_wangwu(self, db):
        avg = db.get_avg_kpi("EMP-003")
        assert avg == 80.0

    def test_get_quarterly_kpi(self, db):
        reviews = db.get_quarterly_kpi("EMP-001")
        assert len(reviews) == 4
        assert reviews[0]["quarter"] == 1

    def test_count_projects(self, db):
        count = db.count_projects("EMP-001")
        assert count == 4

    def test_count_projects_wangwu(self, db):
        count = db.count_projects("EMP-003")
        assert count == 1


class TestDatabaseErrors:
    def test_nonexistent_db_path(self):
        with pytest.raises(FileNotFoundError):
            Database("/nonexistent/path/db.sqlite")

    def test_parameterized_query_prevents_injection(self, db):
        # 参数化查询应该安全处理恶意输入
        result = db.query(
            "SELECT * FROM employees WHERE employee_id = ?",
            ("'; DROP TABLE employees; --",),
        )
        assert len(result) == 0
