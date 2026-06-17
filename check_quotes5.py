import re

with open(r'D:\claude\DealBot\web_crawler.py', 'r', encoding='utf-8') as f:
    content = f.read()

# """ 찾기
pattern = r'\"\"\"'
matches = list(re.finditer(pattern, content))

print(f'Total count: {len(matches)}')
print(f'Expected even number, got {"even" if len(matches) % 2 == 0 else "odd"}')

# 각 """의 라인 번호와 컨텍스트 확인
lines = content.split('\n')
for i, match in enumerate(matches, 1):
    line_num = content[:match.start()].count('\n') + 1
    line_content = lines[line_num - 1] if line_num <= len(lines) else ''
    print(f'{i}. Line {line_num}: {repr(line_content[:70])}...')
