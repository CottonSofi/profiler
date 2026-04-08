import re
with open("profiler/app.py", "r", encoding="utf-8") as f:
    r = re.findall(r'text\s*=\s*(["\'])(.*?)\1', f.read())
    print("\n".join(sorted(set(m[1] for m in r))))
