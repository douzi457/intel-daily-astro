import re

with open('fetch_news.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count all uses of response.text
text_uses = content.count('response.text')
print(f'response.text uses: {text_uses}')

# Show context of each
for m in re.finditer(r'response\.text', content):
    start = max(0, m.start()-60)
    end = min(len(content), m.end()+40)
    print(f'\n  ...{content[start:end]}...')
