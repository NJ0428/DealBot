import re

with open(r'D:\claude\DealBot\web_crawler.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 각 라인에 있는 """ 개수 확인
for i, line in enumerate(lines, 1):
    count = line.count('"""')
    if count > 0:
        print(f'Line {i}: {count} - {repr(line[:70])}')
