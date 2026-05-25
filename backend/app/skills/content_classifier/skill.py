import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)


class ContentClassifierSkill:
    """内容分类 Skill - 从文本中提取实体和意图"""

    DEFAULT_CATEGORIES = [
        {"name": "制度规范", "keywords": ["制度", "规定", "规范", "流程", "标准"]},
        {"name": "技术文档", "keywords": ["技术", "开发", "API", "代码", "架构"]},
        {"name": "人事信息", "keywords": ["员工", "入职", "离职", "绩效", "考勤"]},
        {"name": "财务相关", "keywords": ["报销", "费用", "薪酬", "工资", "预算"]},
        {"name": "项目管理", "keywords": ["项目", "任务", "进度", "里程碑"]},
        {"name": "会议纪要", "keywords": ["会议", "纪要", "记录", "决议"]},
        {"name": "常见问题", "keywords": ["FAQ", "问题", "解答", "如何", "怎么"]},
        {"name": "其他", "keywords": []}
    ]

    def __init__(self, categories: List[dict] = None):
        self.categories = categories or self.DEFAULT_CATEGORIES

    async def classify(self, text: str, categories: List[dict] = None) -> dict:
        """对文本进行分类"""
        target_categories = categories or self.categories

        scores = []
        for category in target_categories:
            score = sum(1 for kw in category["keywords"] if kw in text)
            scores.append((category["name"], score))

        scores.sort(key=lambda x: x[1], reverse=True)
        top_category = scores[0][0] if scores[0][1] > 0 else "其他"
        confidence = min(0.5 + scores[0][1] * 0.1, 1.0)

        return {
            "category": top_category,
            "confidence": confidence,
            "scores": dict(scores)
        }

    async def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取关键词"""
        keywords = set()
        for category in self.categories:
            for kw in category["keywords"]:
                if kw in text:
                    keywords.add(kw)
        return list(keywords)[:top_k]

    async def detect_sensitive(self, text: str) -> dict:
        """检测敏感词"""
        sensitive_words = [
            "机密", "绝密", "保密", "内部资料",
            "密码", "密钥", "token", "api_key",
            "银行卡", "身份证", "手机号",
            "攻击", "漏洞", "入侵", "黑客"
        ]

        found = [word for word in sensitive_words if word in text]

        return {
            "has_sensitive": len(found) > 0,
            "sensitive_words": found,
            "suggestions": [f"检测到 {len(found)} 个敏感词"] if found else []
        }

    async def format_text(self, text: str) -> str:
        """格式化文本"""
        text = text.strip()
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text

    async def summarize(self, text: str, max_length: int = 200) -> str:
        """文本摘要"""
        if len(text) <= max_length:
            return text
        sentences = re.split(r'[。！？\n]', text)
        summary = []
        current_length = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and current_length + len(sentence) <= max_length:
                summary.append(sentence)
                current_length += len(sentence) + 1
            if current_length >= max_length:
                break
        return '。'.join(summary) + '。'
