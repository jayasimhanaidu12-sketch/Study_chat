with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
start = end = None
for i, line in enumerate(lines):
    if 'INDEX_HTML' in line and '"""' in line and start is None:
        start = i + 1
    if start and i > start and line.strip() == '"""':
        end = i + 1
        break
print('INDEX_HTML start line:', start)
print('INDEX_HTML end line:', end)
print('Total lines:', len(lines))
# Show first 3 lines after start
for j in range(start, min(start+3, len(lines))):
    print(f'  {j+1}: {lines[j].rstrip()}')
