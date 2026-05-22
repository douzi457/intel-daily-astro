import re

with open('fetch_news.py', 'r', encoding='utf-8') as f:
    content = f.read()

original = content

# Replace BeautifulSoup(response.text, ...) with BeautifulSoup(response.content, ...)
content = re.sub(
    r"BeautifulSoup\(response\.text,\s*'html\.parser'\)",
    "BeautifulSoup(response.content, 'html.parser')",
    content
)
content = re.sub(
    r"BeautifulSoup\(response\.text,\s*'xml'\)",
    "BeautifulSoup(response.content, 'xml')",
    content
)

# For producthunt, also fix the secondary html.parser call
content = content.replace(
    "if not soup.find('item'): soup = BeautifulSoup(response.text, 'html.parser')",
    "if not soup.find('item'): soup = BeautifulSoup(response.content, 'html.parser')"
)

old_bs = original.count('BeautifulSoup(response.content')
new_bs = content.count('BeautifulSoup(response.content')
print(f'BeautifulSoup(response.content): {old_bs} -> {new_bs}')

with open('fetch_news.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
