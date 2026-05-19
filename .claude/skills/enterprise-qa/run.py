"""企业问答助手 - 独立运行入口，可从任意目录执行"""

import sys
import os

# 确保 src 目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import answer_question

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('用法: python run.py "你的问题"')
        print('示例: python run.py "张三的部门是什么？"')
        sys.exit(1)

    query = sys.argv[1]
    result = answer_question(query)
    print(result)
