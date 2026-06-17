import re

with open(r'D:\claude\DealBot\api_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 이모지가 있는 라인 찾기
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if any(ord(c) > 127 for c in line):
        print(f'{i}: {repr(line[:80])}')
