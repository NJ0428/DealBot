with open(r'D:\claude\DealBot\web_crawler.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 각 라인에 있는 """ 개수 확인
pair_count = 0
for i, line in enumerate(lines, 1):
    count = line.count('"""')
    if count > 0:
        pair_count += count
        is_even = pair_count % 2 == 0
        status = "EVEN" if is_even else "ODD"
        print(f'Line {i}: {count} (total: {pair_count}) [{status}] - {repr(line[:70])}')

print(f'Total count: {pair_count}')
print(f'Final status: {"EVEN" if pair_count % 2 == 0 else "ODD"}')
