with open(r'D:\claude\DealBot\web_crawler.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 각 라인에 있는 """ 개수 확인 및 누적
total = 0
for i, line in enumerate(lines, 1):
    count = line.count('"""')
    if count > 0:
        total += count
        print(f'Line {i}: {count} (total: {total}) - {repr(line[:70])}')

print(f'Total count: {total}')
print(f'Is odd: {total % 2 == 1}')
