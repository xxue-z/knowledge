"""企业智能问答助手 - 主入口"""

import sys
from pathlib import Path

import yaml

from .db import Database
from .intent import QueryType, classify_intent
from .kb import KnowledgeBase
from .fusion import (
    generate_hybrid_answer,
    generate_pure_db_answer,
    generate_pure_kb_answer,
)


def load_config(config_path: str = None) -> dict:
    """加载配置文件。"""
    if config_path is None:
        config_path = str(Path(__file__).parent.parent / "config.yaml")

    path = Path(config_path)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def answer_question(query: str, db_path: str = None, kb_path: str = None, config_path: str = None) -> str:
    """回答用户问题的主函数。

    Args:
        query: 用户的自然语言问题
        db_path: 数据库路径（优先级高于配置文件）
        kb_path: 知识库路径（优先级高于配置文件）
        config_path: 配置文件路径

    Returns:
        格式化的回答字符串
    """
    # skill 目录作为相对路径基准
    _skill_dir = Path(__file__).resolve().parent.parent
    _project_root = _skill_dir.parent.parent.parent.parent  # interview-exam(56)

    config = load_config(config_path)

    def _resolve(path_str: str) -> str:
        """将相对路径解析为基于 skill 目录的绝对路径。"""
        p = Path(path_str)
        if p.is_absolute():
            return str(p)
        return str((_skill_dir / p).resolve())

    import os
    if db_path is None:
        raw = os.environ.get("ENTERPRISE_QA_DB_PATH") or \
              config.get("database", {}).get("path") or \
              str(_project_root / "interview-exam" / "enterprise-qa-data" / "enterprise.db")
        db_path = _resolve(raw)

    if kb_path is None:
        raw = os.environ.get("ENTERPRISE_QA_KB_PATH") or \
              config.get("knowledge_base", {}).get("root_path") or \
              str(_project_root / "interview-exam" / "enterprise-qa-data" / "knowledge")
        kb_path = _resolve(raw)

    # 初始化数据源
    db = Database(db_path)
    kb = KnowledgeBase(kb_path)

    # 意图识别
    intent = classify_intent(query)

    # 根据意图类型分发处理
    if intent.query_type == QueryType.BOUNDARY:
        if intent.entities.get("reason") == "sql_injection":
            return "检测到不安全的查询内容，请使用自然语言提问。"
        return f"无法理解您的问题：「{query}」，请尝试更具体的表述。"

    if intent.query_type == QueryType.PURE_DB:
        return generate_pure_db_answer(db, intent)

    if intent.query_type == QueryType.PURE_KB:
        return generate_pure_kb_answer(kb, intent)

    if intent.query_type == QueryType.HYBRID:
        return generate_hybrid_answer(db, kb, intent)

    return "无法处理该问题，请重试。"


def main():
    """CLI 入口。"""
    if len(sys.argv) < 2:
        print("用法: python -m src.main '问题内容'")
        sys.exit(1)

    query = sys.argv[1]
    result = answer_question(query)
    print(result)


if __name__ == "__main__":
    main()
