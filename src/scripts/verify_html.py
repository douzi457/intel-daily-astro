import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

path = r"C:\Users\douzi457\.qclaw\workspace\情报系统\output\day\2026-05-19.html"
sz = os.path.getsize(path)
print(f"文件大小: {sz//1024}KB")

html = open(path, encoding='utf-8').read()
tabs = re.findall(r'data-platform="([^"]+)"', html)
unique_plats = set(tabs)
print(f"总行数: {len(tabs)}")
print(f"平台数: {len(unique_plats)}")
print(f"平台列表: {sorted(unique_plats)}")
has_tab = 'class="tab' in html
has_search = 'id="q"' in html
has_tabs_placeholder = '__TABS_HTML__' in html
print(f"包含Tab: {has_tab}, 搜索框: {has_search}, placeholder: {has_tabs_placeholder}")
