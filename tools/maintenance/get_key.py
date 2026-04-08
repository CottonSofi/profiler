import re
with open("profiler/app.py", "r", encoding="utf-8") as f:
    text = f.read()
    match = re.search(r'def _download_mode_key.*?return .*?\n', text, re.DOTALL)
    if match: print(match.group(0))
