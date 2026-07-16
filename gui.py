import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from converters import log
from convert_all import convert_files_to_md
from generate_notes import build_prompt, call_llm_api


PROVIDERS = {
    "硅基流动 (SiliconFlow)": "siliconflow",
    "深度求索 (DeepSeek)": "deepseek",
    "智谱AI (Zhipu)": "zhipu"
}


class NotesOutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("学习笔记生成工具 - NotesOut")
        self.root.geometry("720x680")
        self.root.minsize(640, 560)

        self.ipynb_files = []
        self._is_running = False

        self._setup_style()
        self._build_ui()

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Microsoft YaHei", 16, "bold"))
        style.configure("Subtitle.TLabel", font=("Microsoft YaHei", 10), foreground="#666")

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(main_frame, text="📚 学习笔记生成工具", style="Title.TLabel")
        title.pack(anchor="w")
        subtitle = ttk.Label(main_frame, text="拖拽上传 ipynb、py、md、docx、xlsx、txt 或 html 文件，一键生成高质量学习笔记", style="Subtitle.TLabel")
        subtitle.pack(anchor="w", pady=(2, 12))

        self._build_drop_zone(main_frame)
        self._build_file_list(main_frame)
        self._build_config_section(main_frame)
        self._build_action_section(main_frame)
        self._build_log_section(main_frame)

    def _build_drop_zone(self, parent):
        drop_frame = tk.Frame(parent, bg="#f0f4f8", bd=2, relief="groove", height=110)
        drop_frame.pack(fill=tk.X, pady=(0, 10))
        drop_frame.pack_propagate(False)

        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind("<<Drop>>", self._on_drop)

        icon_label = tk.Label(drop_frame, text="📁", font=("Segoe UI Emoji", 28), bg="#f0f4f8")
        icon_label.pack(pady=(14, 2))

        hint_label = tk.Label(
            drop_frame,
            text="将 .ipynb、.py、.md、.docx、.xlsx、.txt 或 .html 文件拖拽到此处  或  点击选择文件",
            font=("Microsoft YaHei", 10),
            fg="#555",
            bg="#f0f4f8",
            cursor="hand2"
        )
        hint_label.pack()
        hint_label.bind("<Button-1>", self._choose_files)

        self.drop_frame = drop_frame

    def _build_file_list(self, parent):
        list_frame = ttk.LabelFrame(parent, text="已选文件", padding=8)
        list_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_listbox = tk.Listbox(list_frame, height=5, font=("Consolas", 9), activestyle="dotbox")
        self.file_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btn_frame, text="添加", width=8, command=self._choose_files).pack(pady=2)
        ttk.Button(btn_frame, text="移除", width=8, command=self._remove_selected).pack(pady=2)
        ttk.Button(btn_frame, text="清空", width=8, command=self._clear_files).pack(pady=2)

    def _build_config_section(self, parent):
        config_frame = ttk.LabelFrame(parent, text="API 配置", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))

        grid = ttk.Frame(config_frame)
        grid.pack(fill=tk.X)
        grid.columnconfigure(1, weight=1)

        ttk.Label(grid, text="模型供应商：").grid(row=0, column=0, sticky="w", pady=4)
        self.provider_var = tk.StringVar(value=list(PROVIDERS.keys())[0])
        provider_combo = ttk.Combobox(
            grid,
            textvariable=self.provider_var,
            values=list(PROVIDERS.keys()),
            state="readonly",
            font=("Microsoft YaHei", 10)
        )
        provider_combo.grid(row=0, column=1, sticky="ew", pady=4, padx=(8, 0))

        ttk.Label(grid, text="API Key：").grid(row=1, column=0, sticky="w", pady=4)
        self.api_key_var = tk.StringVar()
        self.api_entry = ttk.Entry(grid, textvariable=self.api_key_var, show="•", font=("Consolas", 10))
        self.api_entry.grid(row=1, column=1, sticky="ew", pady=4, padx=(8, 0))

        show_btn = ttk.Button(grid, text="显示", width=6, command=self._toggle_api_key)
        show_btn.grid(row=1, column=2, padx=(8, 0))
        self._show_api_key = False

    def _build_action_section(self, parent):
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress = ttk.Progressbar(action_frame, mode="indeterminate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.generate_btn = ttk.Button(
            action_frame, text="🚀 生成学习笔记", command=self._start_generate
        )
        self.generate_btn.pack(side=tk.RIGHT)

    def _build_log_section(self, parent):
        log_frame = ttk.LabelFrame(parent, text="运行日志", padding=6)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            font=("Consolas", 9),
            state=tk.DISABLED,
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#d4d4d4"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _toggle_api_key(self):
        self._show_api_key = not self._show_api_key
        self.api_entry.config(show="" if self._show_api_key else "•")

    def _on_drop(self, event):
        paths = self._parse_drop_paths(event.data)
        valid = [p for p in paths if (p.endswith('.ipynb') or p.endswith('.py') or p.endswith('.md') or p.endswith('.docx') or p.endswith('.xlsx') or p.endswith('.txt') or p.endswith('.html') or p.endswith('.htm')) and os.path.isfile(p)]
        duplicates = 0
        for p in valid:
            if p not in self.ipynb_files:
                self.ipynb_files.append(p)
                self.file_listbox.insert(tk.END, os.path.basename(p))
            else:
                duplicates += 1
        if valid:
            self._log(f"已添加 {len(valid) - duplicates} 个文件" + (f"（跳过 {duplicates} 个重复）" if duplicates else ""))
        else:
            self._log("⚠ 未找到有效的 .ipynb、.py、.md、.docx、.xlsx、.txt 或 .html 文件")

    def _parse_drop_paths(self, data):
        paths = []
        current = ""
        in_brace = False
        for ch in data:
            if ch == '{':
                in_brace = True
                current = ""
            elif ch == '}':
                in_brace = False
                if current:
                    paths.append(current)
                current = ""
            elif ch == ' ' and not in_brace:
                if current:
                    paths.append(current)
                    current = ""
            else:
                current += ch
        if current:
            paths.append(current)
        return paths

    def _choose_files(self, event=None):
        files = filedialog.askopenfilenames(
            title="选择 ipynb、py、md、docx、xlsx、txt 或 html 文件",
            filetypes=[("Jupyter Notebook", "*.ipynb"), ("Python 文件", "*.py"), ("Markdown 文件", "*.md"), ("Word 文档", "*.docx"), ("Excel 表格", "*.xlsx"), ("文本文件", "*.txt"), ("HTML 文件", "*.html"), ("HTML 文件", "*.htm"), ("所有文件", "*.*")]
        )
        added = 0
        for f in files:
            if f not in self.ipynb_files:
                self.ipynb_files.append(f)
                self.file_listbox.insert(tk.END, os.path.basename(f))
                added += 1
        if added:
            self._log(f"已添加 {added} 个文件")

    def _remove_selected(self):
        selection = list(self.file_listbox.curselection())
        for idx in reversed(selection):
            self.file_listbox.delete(idx)
            del self.ipynb_files[idx]
        if selection:
            self._log(f"已移除 {len(selection)} 个文件")

    def _clear_files(self):
        self.ipynb_files.clear()
        self.file_listbox.delete(0, tk.END)
        self._log("已清空文件列表")

    def _log(self, message):
        def _append():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _append)

    def _start_generate(self):
        if self._is_running:
            return
        if not self.ipynb_files:
            messagebox.showwarning("提示", "请先添加至少一个文件")
            return
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("提示", "请输入 API Key")
            return

        provider_name = self.provider_var.get()
        provider_key = PROVIDERS[provider_name]

        self._is_running = True
        self.generate_btn.config(state=tk.DISABLED, text="生成中...")
        self.progress.start(12)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

        thread = threading.Thread(
            target=self._run_generate,
            args=(self.ipynb_files.copy(), provider_key, api_key),
            daemon=True
        )
        thread.start()

    def _run_generate(self, ipynb_files, provider_key, api_key):
        try:
            self._log("=" * 50)
            self._log("开始处理...")
            self._log(f"文件数量: {len(ipynb_files)}")
            self._log("")

            md_contents = convert_files_to_md(ipynb_files, log_fn=self._log)

            self._log("")
            self._log("正在构建提示词...")
            prompt = build_prompt(md_contents)

            self._log("")
            result = call_llm_api(prompt, provider_key, api_key, log_fn=self._log)

            if result is None:
                raise RuntimeError("API 调用失败，请检查 API Key 和网络连接")

            output_path = os.path.join(os.path.dirname(ipynb_files[0]), "学习笔记.md")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)

            self._log("")
            self._log("=" * 50)
            self._log(f"✨ 生成完成！笔记已保存到:")
            self._log(f"   {output_path}")
            self._log("=" * 50)

            self.root.after(0, lambda path=output_path: messagebox.showinfo("成功", f"学习笔记已生成！\n\n保存路径：{path}"))

        except Exception as e:
            self._log("")
            self._log(f"❌ 错误: {str(e)}")
            self.root.after(0, lambda err=e: messagebox.showerror("错误", str(err)))
        finally:
            self._finish_generate()

    def _finish_generate(self):
        self._is_running = False
        self.progress.stop()
        self.generate_btn.config(state=tk.NORMAL, text="🚀 生成学习笔记")


def main():
    root = TkinterDnD.Tk()
    app = NotesOutApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
