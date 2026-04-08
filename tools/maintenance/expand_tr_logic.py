import re

with open("profiler/app.py", "r", encoding="utf-8") as f:
    code = f.read()

# Add _tr_reverse method correctly
if "_tr_reverse" not in code:
    TR_REVERSE = r'''
    def _tr_reverse(self, text: str) -> str:
        lang = self.language_var.get()
        if lang == "Español" or lang not in TRANSLATIONS:
            return text
        
        reverse_dict = {v: k for k,v in TRANSLATIONS[lang].items()}
        return reverse_dict.get(text.strip(), text)
        
    def _apply_translations(self):'''
    code = code.replace("    def _apply_translations(self):", TR_REVERSE)

# Update _apply_translations to handle Combobox, Treeview
APPLY_REPLACEMENT = r'''    def _apply_translations(self):
        def walk(widget):
            # Normal text translation
            keys_to_translate = ["text", "title", "label"]
            for key in keys_to_translate:
                try:
                    current_val = widget.cget(key)
                    if current_val:
                        if not hasattr(widget, f"_orig_{key}"):
                            setattr(widget, f"_orig_{key}", current_val)
                        orig = getattr(widget, f"_orig_{key}")
                        widget.configure(**{key: self._tr(orig)})
                except tk.TclError:
                    pass
                except Exception:
                    pass
            
            # Combobox options translation
            if isinstance(widget, ttk.Combobox):
                try:
                    if not hasattr(widget, "_orig_values"):
                        widget._orig_values = widget.cget("values")
                    orig_vals = widget._orig_values
                    translated_vals = [self._tr(v) for v in orig_vals]
                    widget.configure(values=translated_vals)
                    
                    # Update currently selected value if it was matched in values
                    curr = widget.get()
                    if curr:
                        reverse_curr = self._tr_reverse(curr)
                        if reverse_curr in orig_vals:
                            widget.set(self._tr(reverse_curr))
                except Exception:
                    pass
                    
            # Treeview headers
            if isinstance(widget, ttk.Treeview):
                try:
                    columns = widget.cget("columns")
                    if not hasattr(widget, "_orig_headings"):
                        widget._orig_headings = {}
                        for col in columns:
                            widget._orig_headings[col] = widget.heading(col)["text"]
                    
                    for col in columns:
                        orig_text = widget._orig_headings[col]
                        widget.heading(col, text=self._tr(orig_text))
                except Exception:
                    pass

            for child in widget.winfo_children():
                walk(child)
        walk(self.root)
'''
code = re.sub(r'    def _apply_translations\(self\):\n        def walk\(widget\):.*?\n        walk\(self\.root\)\n', APPLY_REPLACEMENT, code, flags=re.DOTALL)

# Update _download_mode_key
DL_MODE_KEY = r'''    def _download_mode_key(self) -> str:
        val = self._tr_reverse(self.download_mode_var.get())
        reverse = {v: k for k, v in DOWNLOAD_MODE_LABELS.items()}
        return reverse.get(val, DOWNLOAD_MODE_NOTIFY_ONLY)
'''
code = re.sub(r'    def _download_mode_key\(self\) -> str:.*?DOWNLOAD_MODE_NOTIFY_ONLY\)\n', DL_MODE_KEY, code, flags=re.DOTALL)

with open("profiler/app.py", "w", encoding="utf-8") as f:
    f.write(code)
