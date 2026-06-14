import re

with open(r'D:\claude\DealBot\web_crawler.py', 'r', encoding='utf-8') as f:
    content = f.read()

# """ 찾기
pattern = r'\"\"\"'
matches = list(re.finditer(pattern, content))

print(f'Total count: {len(matches)}')
for i, match in enumerate(matches[-10:], len(matches) - 10 + 1):
    # 라인 번호 찾기
    line_num = content[:match.start()].count('\n') + 1
    # 주변 텍스트
    start = max(0, match.start() - 20)
    end = min(len(content), match.end() + 20)
    context = content[start:end].replace('\n', '\\n')
    print(f'{i}. Line {line_num}: ...{context}...')
