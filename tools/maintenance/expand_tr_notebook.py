import re

with open("profiler/app.py", "r", encoding="utf-8") as f:
    code = f.read()

# Make sure we translate Notebook Tabs !
NOTEBOOK_TAB_REPLACEMENT = r'''
            # Notebook tabs
            if isinstance(widget, ttk.Notebook):
                try:
                    tabs = widget.tabs()
                    if not hasattr(widget, "_orig_tabs"):
                        widget._orig_tabs = {}
                        for t in tabs:
                            widget._orig_tabs[t] = widget.tab(t, "text")
                    
                    for t in tabs:
                        orig_text = widget._orig_tabs.get(t, "")
                        if orig_text:
                            widget.tab(t, text=self._tr(orig_text))
                except Exception:
                    pass
'''
if "Notebook tabs" not in code:
    code = code.replace("for child in widget.winfo_children():", NOTEBOOK_TAB_REPLACEMENT + "            for child in widget.winfo_children():")

with open("profiler/app.py", "w", encoding="utf-8") as f:
    f.write(code)
