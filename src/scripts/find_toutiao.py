import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

skill_dir = r"C:\Users\douzi457\.qclaw\workspace\skills\news-aggregator-skill\scripts"
for fname in os.listdir(skill_dir):
    if not fname.endswith('.py'):
        continue
    fpath = os.path.join(skill_dir, fname)
    content = open(fpath, encoding='utf-8', errors='replace').read()
    if 'toutiao' in content.lower():
        print(f"\n=== {fname} (含toutiao) ===")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'toutiao' in line.lower():
                print(f"  {i+1}: {line.rstrip()}")
