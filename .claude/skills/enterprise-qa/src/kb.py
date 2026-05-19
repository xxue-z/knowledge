"""知识库检索模块 - 基于 BM25 的 Markdown 文档检索"""

import re
from pathlib import Path
from typing import Any

import jieba
from rank_bm25 import BM25Okapi


class Document:
    """表示一个知识库文档。"""

    def __init__(self, path: Path, content: str):
        self.path = path
        self.filename = path.name
        self.content = content
        self.sections = self._parse_sections()

    def _parse_sections(self) -> list[dict[str, str]]:
        """将 Markdown 按标题拆分为章节。"""
        sections = []
        current_title = ""
        current_body: list[str] = []

        for line in self.content.split("\n"):
            if line.startswith("#"):
                if current_body:
                    body_text = "\n".join(current_body).strip()
                    if body_text:
                        sections.append({
                            "title": current_title,
                            "body": body_text,
                        })
                current_title = line.lstrip("# ").strip()
                current_body = []
            else:
                current_body.append(line)

        if current_body:
            body_text = "\n".join(current_body).strip()
            if body_text:
                sections.append({
                    "title": current_title,
                    "body": body_text,
                })

        return sections


class KnowledgeBase:
    """Markdown 知识库，使用 BM25 进行检索。"""

    def __init__(self, kb_path: str):
        self.kb_path = Path(kb_path)
        if not self.kb_path.exists():
            raise FileNotFoundError(f"知识库目录不存在: {self.kb_path}")
        self.documents: list[Document] = []
        self._load_documents()
        self._build_index()

    def _load_documents(self):
        """递归加载所有 .md 文件。"""
        for md_file in sorted(self.kb_path.rglob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            self.documents.append(Document(md_file, content))

    def _tokenize(self, text: str) -> list[str]:
        """中文分词。"""
        return list(jieba.cut(text))

    def _build_index(self):
        """构建 BM25 索引。"""
        corpus = []
        self._index_entries: list[dict[str, Any]] = []

        for doc in self.documents:
            for section in doc.sections:
                tokens = self._tokenize(section["body"])
                corpus.append(tokens)
                self._index_entries.append({
                    "filename": doc.filename,
                    "title": section["title"],
                    "body": section["body"],
                    "path": str(doc.path),
                })

        if corpus:
            self._bm25 = BM25Okapi(corpus)
        else:
            self._bm25 = None

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """搜索知识库，返回最相关的章节。"""
        if not self._bm25 or not self._index_entries:
            return []

        query_tokens = self._tokenize(query)
        scores = self._bm25.get_scores(query_tokens)

        scored_results = []
        for i, score in enumerate(scores):
            if score > 0:
                entry = self._index_entries[i].copy()
                entry["score"] = float(score)
                scored_results.append(entry)

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def get_document(self, filename: str) -> Document | None:
        """按文件名获取文档。"""
        for doc in self.documents:
            if doc.filename == filename:
                return doc
        return None
