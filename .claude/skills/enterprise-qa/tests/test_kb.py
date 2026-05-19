"""知识库模块测试"""

import pytest
from pathlib import Path

from src.kb import KnowledgeBase, Document


@pytest.fixture
def kb_path():
    path = Path(__file__).resolve().parent.parent.parent.parent.parent / "interview-exam" / "enterprise-qa-data" / "knowledge"
    if not path.exists():
        pytest.skip("知识库目录不存在")
    return str(path)


@pytest.fixture
def kb(kb_path):
    return KnowledgeBase(kb_path)


class TestKnowledgeBase:
    def test_load_documents(self, kb):
        assert len(kb.documents) == 7

    def test_document_filenames(self, kb):
        filenames = {doc.filename for doc in kb.documents}
        assert "hr_policies.md" in filenames
        assert "promotion_rules.md" in filenames
        assert "tech_docs.md" in filenames
        assert "finance_rules.md" in filenames
        assert "faq.md" in filenames

    def test_search_annual_leave(self, kb):
        results = kb.search("年假怎么计算")
        assert len(results) > 0
        # 应该找到 hr_policies.md
        filenames = {r["filename"] for r in results}
        assert "hr_policies.md" in filenames

    def test_search_late_penalty(self, kb):
        results = kb.search("迟到扣钱")
        assert len(results) > 0

    def test_search_promotion(self, kb):
        results = kb.search("晋升条件 P5 P6")
        assert len(results) > 0
        filenames = {r["filename"] for r in results}
        assert "promotion_rules.md" in filenames

    def test_search_expense(self, kb):
        results = kb.search("报销 差旅 机票")
        assert len(results) > 0
        filenames = {r["filename"] for r in results}
        assert "finance_rules.md" in filenames

    def test_search_meeting_notes(self, kb):
        results = kb.search("全员大会 3月")
        assert len(results) > 0

    def test_search_no_results(self, kb):
        results = kb.search("xyzabc123完全无关的内容")
        # BM25 对纯英文/数字可能仍有低分匹配，验证结果不太高即可
        # 真正无关的查询不应返回高置信度结果
        assert len(results) == 0 or all(r["score"] < 5.0 for r in results)

    def test_get_document(self, kb):
        doc = kb.get_document("hr_policies.md")
        assert doc is not None
        assert doc.filename == "hr_policies.md"

    def test_get_nonexistent_document(self, kb):
        doc = kb.get_document("nonexistent.md")
        assert doc is None


class TestDocument:
    def test_parse_sections(self, kb_path):
        path = Path(kb_path) / "hr_policies.md"
        content = path.read_text(encoding="utf-8")
        doc = Document(path, content)
        assert len(doc.sections) > 0
        titles = [s["title"] for s in doc.sections]
        assert any("考勤" in t or "工作" in t for t in titles)
