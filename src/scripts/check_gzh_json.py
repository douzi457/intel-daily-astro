import json, sys
sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open(r"C:\Users\douzi457\.qclaw\workspace\情报系统\副业_爆款数据.json", encoding='utf-8'))
print("Type:", type(d))
if isinstance(d, dict):
    print("Keys:", list(d.keys()))
    for k, v in d.items():
        if isinstance(v, list):
            print(f"  {k}: list of {len(v)}")
            if v:
                print(f"  first item keys: {list(v[0].keys()) if isinstance(v[0], dict) else v[0]}")
                print(f"  first item: {str(v[0])[:200]}")
                break
elif isinstance(d, list):
    print("List of", len(d))
