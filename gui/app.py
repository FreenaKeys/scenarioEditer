import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class EntryDialog(tk.Toplevel):
    def __init__(self, parent, entry_id=None, data=None):
        super().__init__(parent)
        self.title("Entry")
        self.resizable(False, False)
        self.result = None

        self.entry_id = tk.StringVar(value=entry_id if entry_id is not None else "")
        self.text = tk.StringVar(value=(data.get('text') if data else ""))
        self.rubi = tk.StringVar(value=(data.get('rubi') if data else ""))
        self.level = tk.StringVar(value=(data.get('level') if data else "basic"))

        frm = ttk.Frame(self, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frm, text="ID:").grid(row=0, column=0, sticky="e")
        # keep a reference to the Entry widget so we can call focus() on it
        self.entry_id_entry = ttk.Entry(frm, textvariable=self.entry_id)
        self.entry_id_entry.grid(row=0, column=1, sticky="we")

        ttk.Label(frm, text="Text:").grid(row=1, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.text, width=60).grid(row=1, column=1, sticky="we")

        ttk.Label(frm, text="Rubi:").grid(row=2, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.rubi).grid(row=2, column=1, sticky="we")

        ttk.Label(frm, text="Level:").grid(row=3, column=0, sticky="e")
        ttk.Combobox(frm, textvariable=self.level, values=["basic", "advanced"], state="readonly").grid(row=3, column=1, sticky="we")

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(8,0))
        ttk.Button(btn_frame, text="OK", command=self.on_ok).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).grid(row=0, column=1, padx=5)

        frm.columnconfigure(1, weight=1)
        self.grab_set()
        # focus the actual Entry widget (not the StringVar)
        try:
            self.entry_id_entry.focus()
        except Exception:
            # fallback: nothing to do
            pass

    def on_ok(self):
        eid = self.entry_id.get().strip()
        if not eid:
            messagebox.showerror("Error", "ID を入力してください")
            return
        self.result = {
            "id": eid,
            "text": self.text.get(),
            "rubi": self.rubi.get(),
            "level": self.level.get()
        }
        self.destroy()


class ScenarioEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Scenario Editor")
        self.geometry("800x480")

        self.data = {"meta": {"name": "", "uniqueid": "", "requiredver": ""}, "entries": {}}
        self.current_file = None

        self.create_widgets()

    def create_widgets(self):
        main = ttk.Frame(self, padding=8)
        main.pack(fill="both", expand=True)

        # Meta frame
        meta_frame = ttk.LabelFrame(main, text="Meta", padding=8)
        meta_frame.pack(fill="x")

        ttk.Label(meta_frame, text="Name:").grid(row=0, column=0, sticky="e")
        self.name_var = tk.StringVar()
        ttk.Entry(meta_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="w")

        ttk.Label(meta_frame, text="Unique ID:").grid(row=1, column=0, sticky="e")
        self.uid_var = tk.StringVar()
        ttk.Entry(meta_frame, textvariable=self.uid_var, width=40).grid(row=1, column=1, sticky="w")

        ttk.Label(meta_frame, text="Required Ver:").grid(row=2, column=0, sticky="e")
        self.ver_var = tk.StringVar()
        ttk.Entry(meta_frame, textvariable=self.ver_var, width=20).grid(row=2, column=1, sticky="w")

        # Entries frame
        entries_frame = ttk.LabelFrame(main, text="Entries", padding=8)
        entries_frame.pack(fill="both", expand=True, pady=(8,0))

        left = ttk.Frame(entries_frame)
        left.pack(side="left", fill="y")

        self.entries_list = tk.Listbox(left, width=20)
        self.entries_list.pack(side="left", fill="y")
        # update preview when selection changes
        self.entries_list.bind('<<ListboxSelect>>', lambda e: self.refresh_preview())
        self.entries_list.bind('<Double-1>', lambda e: self.edit_entry())

        btns = ttk.Frame(left)
        btns.pack(side="left", fill="y", padx=6)
        ttk.Button(btns, text="Add", command=self.add_entry).pack(fill="x", pady=2)
        ttk.Button(btns, text="Edit", command=self.edit_entry).pack(fill="x", pady=2)
        ttk.Button(btns, text="Delete", command=self.delete_entry).pack(fill="x", pady=2)

        # right: details
        right = ttk.Frame(entries_frame)
        right.pack(side="left", fill="both", expand=True, padx=(8,0))

        ttk.Label(right, text="Preview / Selected Entry").pack(anchor="w")
        self.preview = tk.Text(right, wrap="word", height=15)
        self.preview.pack(fill="both", expand=True)

        # bottom controls
        ctl = ttk.Frame(main, padding=(0,8))
        ctl.pack(fill="x")
        ttk.Button(ctl, text="Load", command=self.load_file).pack(side="left")
        ttk.Button(ctl, text="Save", command=self.save_file).pack(side="left", padx=6)
        ttk.Button(ctl, text="Save As", command=self.save_as).pack(side="left")

        ttk.Button(ctl, text="Export JSON", command=self.export_json).pack(side="right")

    def refresh_preview(self):
        sel = self.entries_list.curselection()
        self.preview.delete('1.0', tk.END)
        if sel:
            key = self.entries_list.get(sel[0])
            entry = self.data['entries'].get(key, {})
            try:
                self.preview.insert(tk.END, json.dumps(entry, ensure_ascii=False, indent=2))
            except Exception:
                # in case of unexpected data, show a simple repr
                self.preview.insert(tk.END, repr(entry))

    def update_entries_list(self, select_key=None):
        """Rebuild the entries list. If select_key is provided, select that item after rebuild.

        If select_key is None, attempt to preserve the previous selection if possible.
        """
        # remember previous selection
        prev = None
        cur = self.entries_list.curselection()
        if cur:
            try:
                prev = self.entries_list.get(cur[0])
            except Exception:
                prev = None

        self.entries_list.delete(0, tk.END)
        keys = sorted(self.data['entries'].keys(), key=lambda x: int(x) if x.isdigit() else x)
        for k in keys:
            self.entries_list.insert(tk.END, k)

        # decide which key to select
        target = select_key if select_key is not None else prev
        if target and target in keys:
            idx = keys.index(target)
            self.entries_list.selection_set(idx)
            self.entries_list.see(idx)

        # refresh preview according to selection
        self.refresh_preview()

    def add_entry(self):
        # compute next numeric id
        numeric_ids = [int(k) for k in self.data['entries'].keys() if k.isdigit()]
        next_id = str(max(numeric_ids) + 1 if numeric_ids else 1)
        dlg = EntryDialog(self, entry_id=next_id)
        self.wait_window(dlg)
        if dlg.result:
            eid = dlg.result['id']
            if eid in self.data['entries']:
                if not messagebox.askyesno('Overwrite?', f'ID {eid} exists. 上書きしますか？'):
                    return
            self.data['entries'][eid] = {"text": dlg.result['text'], "rubi": dlg.result['rubi'], "level": dlg.result['level']}
            self.update_entries_list(select_key=eid)

    def edit_entry(self):
        sel = self.entries_list.curselection()
        if not sel:
            messagebox.showinfo('Info', '編集するエントリを選んでください')
            return
        key = self.entries_list.get(sel[0])
        dlg = EntryDialog(self, entry_id=key, data=self.data['entries'].get(key))
        self.wait_window(dlg)
        if dlg.result:
            new_id = dlg.result['id']
            # handle id change
            if new_id != key and new_id in self.data['entries']:
                messagebox.showerror('Error', 'その ID は既に存在します')
                return
            self.data['entries'].pop(key, None)
            self.data['entries'][new_id] = {"text": dlg.result['text'], "rubi": dlg.result['rubi'], "level": dlg.result['level']}
            self.update_entries_list(select_key=new_id)

    def delete_entry(self):
        sel = self.entries_list.curselection()
        if not sel:
            return
        key = self.entries_list.get(sel[0])
        if messagebox.askyesno('Delete', f'ID {key} を削除しますか？'):
            self.data['entries'].pop(key, None)
            self.update_entries_list()

    def load_file(self):
        fp = filedialog.askopenfilename(filetypes=[('JSON Files', '*.json'), ('All', '*.*')])
        if not fp:
            return
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                d = json.load(f)
            # basic validation
            if 'meta' not in d or 'entries' not in d:
                messagebox.showerror('Error', 'このファイルは期待する形式ではありません')
                return
            self.data = d
            self.current_file = fp
            self.name_var.set(self.data.get('meta', {}).get('name', ''))
            self.uid_var.set(self.data.get('meta', {}).get('uniqueid', ''))
            self.ver_var.set(self.data.get('meta', {}).get('requiredver', ''))
            # if there are entries, select the first one after loading
            if self.data.get('entries'):
                keys = sorted(self.data['entries'].keys(), key=lambda x: int(x) if x.isdigit() else x)
                self.update_entries_list(select_key=keys[0])
            else:
                self.update_entries_list()
        except Exception as e:
            messagebox.showerror('Error', f'読み込みに失敗しました: {e}')

    def save_file(self):
        if not self.current_file:
            return self.save_as()
        self._write_file(self.current_file)

    def save_as(self):
        fp = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON Files', '*.json')])
        if not fp:
            return
        self.current_file = fp
        self._write_file(fp)

    def _write_file(self, fp):
        # update meta from fields
        self.data['meta'] = {"name": self.name_var.get(), "uniqueid": self.uid_var.get(), "requiredver": self.ver_var.get()}
        try:
            with open(fp, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo('Saved', f'{fp} に保存しました')
        except Exception as e:
            messagebox.showerror('Error', f'保存に失敗しました: {e}')

    def export_json(self):
        # quick export to clipboard or file
        fp = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON Files', '*.json')])
        if not fp:
            return
        try:
            with open(fp, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo('Exported', f'JSON exported to {fp}')
        except Exception as e:
            messagebox.showerror('Error', f'Export failed: {e}')


def main():
    app = ScenarioEditor()
    app.mainloop()


if __name__ == '__main__':
    main()
