import re
with open("profiler/app.py", "r", encoding="utf-8") as f:
    text = f.read()
    match = re.search(r'self\.download_mode_combo = ttk\.Combobox\((.*?)\)', text, re.DOTALL)
    if match: print(match.group(0))
