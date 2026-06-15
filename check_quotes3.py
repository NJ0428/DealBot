import re

with open(r'D:\claude\DealBot\web_crawler.py', 'r', encoding='utf-8') as f:
    content = f.read()

# """ 찾기
pattern = r'\"\"\"'
matches = list(re.finditer(pattern, content))

print(f'Total count: {len(matches)}')

# 150번째부터 153번째까지 """ 확인
for i, match in enumerate(matches[149:154], 150):  # 149는 150번째 (0-based)
    # 라인 번호 찾기
    line_num = content[:match.start()].count('\n') + 1
    # 라인 내용
    lines = content.split('\n')
    line_content = lines[line_num - 1] if line_num <= len(lines) else ''
    print(f'{i}. Line {line_num}: {repr(line_content[:60])}...')
    print(f'   Position: {match.start()}-{match.end()}')
