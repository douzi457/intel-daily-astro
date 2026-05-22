import sys, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\douzi457\.qclaw\workspace\情报系统")

from collect.collector import collect_weibo, collect_sspai, collect_gzh

print("=== 微博 ===")
r1 = collect_weibo()
print(f"微博: {len(r1)}条")
if r1:
    print(f"  第一条: {r1[0]['title'][:50]}")

print("\n=== 少数派 ===")
r2 = collect_sspai()
print(f"少数派: {len(r2)}条")
if r2:
    print(f"  第一条: {r2[0]['title'][:50]}")

print("\n=== 公众号 ===")
r3 = collect_gzh()
print(f"公众号: {len(r3)}条")
if r3:
    print(f"  第一条: {r3[0].get('title','')[:50]}")
