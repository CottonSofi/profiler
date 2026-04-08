import re

with open("profiler/app.py", "r", encoding="utf-8") as f:
    code = f.read()

# in _save_profile where profile is created:
SAVE_PROFILE_REPLACE = r'''schedule_mode=self._tr_reverse(self.schedule_mode_var.get()),'''
code = re.sub(r'schedule_mode=self\.schedule_mode_var\.get\(\),', SAVE_PROFILE_REPLACE, code)

with open("profiler/app.py", "w", encoding="utf-8") as f:
    f.write(code)
