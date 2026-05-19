"""数据库查询模块 - 安全的参数化 SQLite 查询"""

import sqlite3
from pathlib import Path
from typing import Any


class Database:
    """SQLite 数据库查询封装，所有查询使用参数化 SQL。"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def query(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        """执行参数化查询，返回字典列表。"""
        with self._connect() as conn:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def query_one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        """执行参数化查询，返回单条记录。"""
        results = self.query(sql, params)
        return results[0] if results else None

    # --- 员工相关查询 ---

    def get_employee_by_id(self, employee_id: str) -> dict | None:
        return self.query_one(
            "SELECT * FROM employees WHERE employee_id = ?",
            (employee_id,),
        )

    def get_employees_by_department(self, department: str) -> list[dict]:
        return self.query(
            "SELECT * FROM employees WHERE department = ? AND status = 'active'",
            (department,),
        )

    def get_manager(self, employee_id: str) -> dict | None:
        return self.query_one(
            """SELECT e2.* FROM employees e1
               JOIN employees e2 ON e1.manager_id = e2.employee_id
               WHERE e1.employee_id = ?""",
            (employee_id,),
        )

    def count_employees_by_department(self, department: str) -> int:
        result = self.query_one(
            "SELECT COUNT(*) as cnt FROM employees WHERE department = ? AND status = 'active'",
            (department,),
        )
        return result["cnt"] if result else 0

    # --- 项目相关查询 ---

    def get_projects_by_employee(self, employee_id: str) -> list[dict]:
        return self.query(
            """SELECT p.project_id, p.name, p.status, pm.role
               FROM project_members pm
               JOIN projects p ON pm.project_id = p.project_id
               WHERE pm.employee_id = ?""",
            (employee_id,),
        )

    def get_active_projects(self) -> list[dict]:
        return self.query(
            "SELECT * FROM projects WHERE status = 'active'"
        )

    def get_projects_by_department(self, department: str) -> list[dict]:
        return self.query(
            """SELECT DISTINCT p.project_id, p.name, p.status
               FROM projects p
               JOIN project_members pm ON p.project_id = pm.project_id
               JOIN employees e ON pm.employee_id = e.employee_id
               WHERE e.department = ? AND p.status = 'active'""",
            (department,),
        )

    # --- 考勤相关查询 ---

    def count_late_attendance(self, employee_id: str, month_prefix: str) -> int:
        """统计某月迟到次数。month_prefix 格式: '2026-02'"""
        result = self.query_one(
            """SELECT COUNT(*) as cnt FROM attendance
               WHERE employee_id = ? AND status = 'late' AND date LIKE ?""",
            (employee_id, f"{month_prefix}-%"),
        )
        return result["cnt"] if result else 0

    # --- 绩效相关查询 ---

    def get_avg_kpi(self, employee_id: str) -> float | None:
        result = self.query_one(
            "SELECT AVG(kpi_score) as avg_kpi FROM performance_reviews WHERE employee_id = ?",
            (employee_id,),
        )
        return round(result["avg_kpi"], 2) if result and result["avg_kpi"] else None

    def get_quarterly_kpi(self, employee_id: str) -> list[dict]:
        return self.query(
            """SELECT year, quarter, kpi_score, grade
               FROM performance_reviews
               WHERE employee_id = ?
               ORDER BY year, quarter""",
            (employee_id,),
        )

    def count_projects(self, employee_id: str) -> int:
        result = self.query_one(
            "SELECT COUNT(*) as cnt FROM project_members WHERE employee_id = ?",
            (employee_id,),
        )
        return result["cnt"] if result else 0
