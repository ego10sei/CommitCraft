import customtkinter as ctk
import subprocess
import json
import os
import datetime
import webbrowser
from tkinter import filedialog
import pyperclip
USAGE_FILE = ".commitcraft_usage.json"
MAX_FREE_COMMITS = 10
DONATE_URL = "https://boosty.to/commitcraft"

COLOR_BG = "#0B0F19"
COLOR_CARD = "#111827"
COLOR_BORDER = "#1F2937"
COLOR_TEXT_MAIN = "#F9FAFB"
COLOR_TEXT_MUTED = "#9CA3AF"
COLOR_ACCENT = "#3B82F6"
COLOR_ACCENT_HOVER = "#2563EB"
COLOR_SUCCESS = "#10B981"
COLOR_SUCCESS_HOVER = "#059669"
COLOR_DANGER = "#EF4444"

FONT_FAMILY = "Segoe UI" if os.name == "nt" else "Helvetica"
FONT_MONO = "Consolas" if os.name == "nt" else "Courier"
class CommitCraftCore:
    @staticmethod
    def is_git_repository(cwd: str) -> bool:
        try:
            subprocess.run(["git", "rev-parse"], cwd=cwd, check=True, capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            return True
        except:
            return False

    @staticmethod
    def get_git_diff(cwd: str) -> str:
        try:
            res = subprocess.run(["git", "diff", "--cached"], cwd=cwd, capture_output=True,
                                 text=True, encoding='utf-8',
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if not res.stdout.strip():
                res = subprocess.run(["git", "diff"], cwd=cwd, capture_output=True,
                                     text=True, encoding='utf-8',
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            return res.stdout.strip() or "Нет изменений"
        except Exception as e:
            return f"Ошибка: {e}"

    @staticmethod
    def execute_commit(cwd: str, message: str) -> tuple[bool, str]:
        try:
            res = subprocess.run(["git", "commit", "-m", message], cwd=cwd, capture_output=True,
                                 text=True, encoding='utf-8',
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            return (res.returncode == 0, res.stdout or res.stderr)
        except Exception as e:
            return False, str(e)

    @staticmethod
    def load_usage_data() -> dict:
        today = datetime.date.today().isoformat()
        default = {"date": today, "count": 0}
        if os.path.exists(USAGE_FILE):
            try:
                with open(USAGE_FILE, "r") as f:
                    data = json.load(f)
                if data.get("date") != today:
                    return default
                return data
            except:
                return default
        return default

    @staticmethod
    def save_usage_data(data: dict):
        with open(USAGE_FILE, "w") as f:
            json.dump(data, f)
class MinimalScrollableTextbox(ctk.CTkFrame):
    def __init__(self, master, is_mono=False, height=150):
        super().__init__(master, fg_color="#1E293B", border_width=0, corner_radius=12)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        font = ctk.CTkFont(family=FONT_MONO if is_mono else FONT_FAMILY, size=13)
        self.textbox = ctk.CTkTextbox(
            self, font=font, fg_color="transparent",
            text_color=COLOR_TEXT_MAIN, wrap="word", height=height,
            scrollbar_button_color="#374151", scrollbar_button_hover_color="#4B5563"
        )
        self.textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    def get(self, *args): return self.textbox.get(*args)
    def delete(self, *args): return self.textbox.delete(*args)
    def insert(self, *args): return self.textbox.insert(*args)

class CommitCraftApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CommitCraft — AI Commits")
        self.geometry("950x750")
        self.minsize(850, 600)
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLOR_BG)

        self.core = CommitCraftCore()
        self.usage_data = self.core.load_usage_data()
        self.current_repo_path = os.getcwd()
        self.current_diff = ""

        self.setup_styles()
        self.build_ui()
        self.after(300, self.validate_environment)

    def setup_styles(self):
        self.font_title = ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold")
        self.font_section = ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold")
        self.font_ui = ctk.CTkFont(family=FONT_FAMILY, size=13)
        self.font_small = ctk.CTkFont(family=FONT_FAMILY, size=11)

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0, border_width=0, height=70)
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_columnconfigure(1, weight=1)

        logo_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=25, pady=15, sticky="w")
        ctk.CTkLabel(logo_frame, text="✨", font=ctk.CTkFont(size=20)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(logo_frame, text="CommitCraft", font=self.font_title, text_color=COLOR_TEXT_MAIN).pack(side="left")

        right_header = ctk.CTkFrame(top_bar, fg_color="transparent")
        right_header.grid(row=0, column=2, padx=25, pady=15, sticky="e")
        self.limit_lbl = ctk.CTkLabel(right_header, text="Лимит: ...", font=self.font_ui, text_color=COLOR_TEXT_MUTED)
        self.limit_lbl.pack(side="left", padx=(0, 20))
        self.repo_btn = ctk.CTkButton(
            right_header, text="📁 Выбрать проект", font=self.font_ui,
            fg_color="#374151", hover_color="#4B5563", text_color=COLOR_TEXT_MAIN,
            height=36, corner_radius=8, command=self.action_select_repo
        )
        self.repo_btn.pack(side="left")

        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.grid(row=1, column=0, sticky="nsew", padx=40, pady=25)
        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_rowconfigure(1, weight=3)
        workspace.grid_rowconfigure(4, weight=2)

        diff_header = ctk.CTkFrame(workspace, fg_color="transparent")
        diff_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        diff_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(diff_header, text="Изменения (Git Diff)", font=self.font_section, text_color=COLOR_TEXT_MAIN).grid(row=0, column=0, sticky="w")
        self.refresh_btn = ctk.CTkButton(
            diff_header, text="🔄 Обновить", font=self.font_small, width=90, height=28,
            fg_color="transparent", border_width=1, border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_MUTED, hover_color=COLOR_CARD, command=self.action_load_diff
        )
        self.refresh_btn.grid(row=0, column=1, sticky="e")

        self.diff_view = MinimalScrollableTextbox(workspace, is_mono=True)
        self.diff_view.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        ai_frame = ctk.CTkFrame(workspace, fg_color="transparent")
        ai_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        ai_frame.grid_columnconfigure(0, weight=1)
        ai_frame.grid_columnconfigure(1, weight=1)
        ai_frame.grid_columnconfigure(2, weight=1)

        self.btn_deepseek = ctk.CTkButton(
            ai_frame, text="🤖 DeepSeek", font=self.font_section,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="white",
            height=40, corner_radius=8, command=lambda: self.open_ai("deepseek")
        )
        self.btn_deepseek.grid(row=0, column=0, padx=5, sticky="ew")

        self.btn_gemini = ctk.CTkButton(
            ai_frame, text="🔷 Gemini", font=self.font_section,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="white",
            height=40, corner_radius=8, command=lambda: self.open_ai("gemini")
        )
        self.btn_gemini.grid(row=0, column=1, padx=5, sticky="ew")

        self.btn_chatgpt = ctk.CTkButton(
            ai_frame, text="💬 ChatGPT", font=self.font_section,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="white",
            height=40, corner_radius=8, command=lambda: self.open_ai("chatgpt")
        )
        self.btn_chatgpt.grid(row=0, column=2, padx=5, sticky="ew")

        paste_header = ctk.CTkFrame(workspace, fg_color="transparent")
        paste_header.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(paste_header, text="Вставить ответ AI (Ctrl+V)", font=self.font_section, text_color=COLOR_TEXT_MAIN).pack(side="left")
        self.paste_btn = ctk.CTkButton(
            paste_header, text="📋 Вставить из буфера", font=self.font_small, width=120, height=28,
            fg_color="transparent", border_width=1, border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_MUTED, command=self.action_paste_from_clipboard
        )
        self.paste_btn.pack(side="right")

        self.commit_msg_view = MinimalScrollableTextbox(workspace, is_mono=False, height=100)
        self.commit_msg_view.grid(row=4, column=0, sticky="nsew", pady=(0, 20))

        footer = ctk.CTkFrame(workspace, fg_color="transparent")
        footer.grid(row=5, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        self.donate_btn = ctk.CTkButton(
            footer, text="☕ Поддержать автора", font=self.font_small,
            fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color=COLOR_CARD,
            height=36, corner_radius=8, command=self.open_donate
        )
        self.donate_btn.grid(row=0, column=0, sticky="w")

        self.status_lbl = ctk.CTkLabel(footer, text="Готово к работе", font=self.font_ui, text_color=COLOR_TEXT_MUTED)
        self.status_lbl.grid(row=0, column=1, sticky="e", padx=(0, 20))

        self.commit_btn = ctk.CTkButton(
            footer, text="Сделать Commit", font=self.font_section,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER, text_color="white",
            width=160, height=42, corner_radius=8, command=self.action_run_commit
        )
        self.commit_btn.grid(row=0, column=2, sticky="e")

        self.update_limit_label()

    def show_status(self, text, mode="info"):
        colors = {"info": COLOR_TEXT_MUTED, "success": COLOR_SUCCESS, "error": COLOR_DANGER}
        self.status_lbl.configure(text=text, text_color=colors.get(mode, COLOR_TEXT_MUTED))

    def update_limit_label(self):
        used = self.usage_data["count"]
        remains = max(0, MAX_FREE_COMMITS - used)
        self.limit_lbl.configure(text=f"Осталось сегодня: {remains}/{MAX_FREE_COMMITS}")

    def open_donate(self):
        webbrowser.open(DONATE_URL)

    def action_select_repo(self):
        folder = filedialog.askdirectory(title="Выберите папку с Git-репозиторием")
        if folder:
            self.current_repo_path = folder
            self.validate_environment()

    def validate_environment(self):
        if not self.core.is_git_repository(self.current_repo_path):
            self.show_status("Не найден Git-репозиторий", "error")
            self.diff_view.delete("0.0", "end")
            self.diff_view.insert("0.0", f"В папке {self.current_repo_path} не найден Git.\n\nНажмите «📁 Выбрать проект» сверху и укажите корневую папку вашего проекта.")
            self.btn_deepseek.configure(state="disabled")
            self.btn_gemini.configure(state="disabled")
            self.btn_chatgpt.configure(state="disabled")
            self.commit_btn.configure(state="disabled")
            return
        self.btn_deepseek.configure(state="normal")
        self.btn_gemini.configure(state="normal")
        self.btn_chatgpt.configure(state="normal")
        self.commit_btn.configure(state="normal")
        self.action_load_diff()

    def action_load_diff(self):
        self.diff_view.delete("0.0", "end")
        self.commit_msg_view.delete("0.0", "end")
        diff = self.core.get_git_diff(self.current_repo_path)
        if not diff or diff == "Нет изменений":
            self.diff_view.insert("0.0", "Изменений не найдено.\n\nУбедитесь, что вы сохранили файлы или сделали `git add .`")
            self.show_status("Нет активных изменений", "info")
            self.btn_deepseek.configure(state="disabled")
            self.btn_gemini.configure(state="disabled")
            self.btn_chatgpt.configure(state="disabled")
        else:
            self.current_diff = diff
            self.diff_view.insert("0.0", diff)
            self.show_status(f"Проект загружен ({os.path.basename(self.current_repo_path)})", "success")
            self.btn_deepseek.configure(state="normal")
            self.btn_gemini.configure(state="normal")
            self.btn_chatgpt.configure(state="normal")

    def open_ai(self, ai_name):
        if not self.current_diff:
            self.show_status("Сначала загрузите изменения (Diff)", "error")
            return
        prompt = f"""You are an expert developer. Write a short, clear git commit message in English (Conventional Commits format). ONLY the message, no explanations, no quotes.

Changes:
{self.current_diff}"""

        pyperclip.copy(prompt)
        self.show_status(f"Промпт скопирован в буфер обмена. Открываю {ai_name}...", "success")

        if ai_name == "deepseek":
            webbrowser.open("https://chat.deepseek.com/")
        elif ai_name == "gemini":
            webbrowser.open("https://gemini.google.com/")
        elif ai_name == "chatgpt":
            webbrowser.open("https://chat.openai.com/")

        self.show_status(f"Открыт {ai_name}. Вставьте промпт (Ctrl+V), отправьте, затем скопируйте ответ и вернитесь в программу", "success")

    def action_paste_from_clipboard(self):
        try:
            msg = pyperclip.paste().strip()
            if msg:
                self.commit_msg_view.delete("0.0", "end")
                self.commit_msg_view.insert("0.0", msg)
                self.show_status("Сообщение вставлено из буфера", "success")
            else:
                self.show_status("Буфер пуст", "error")
        except Exception as e:
            self.show_status(f"Ошибка вставки: {str(e)}", "error")

    def action_run_commit(self):
        msg = self.commit_msg_view.get("0.0", "end").strip()
        if not msg:
            self.show_status("Поле сообщения пустое! Сначала сгенерируйте или вставьте сообщение.", "error")
            return
        ok, out = self.core.execute_commit(self.current_repo_path, msg)
        if ok:
            self.show_status("Коммит успешно создан!", "success")
            self.commit_msg_view.delete("0.0", "end")
            self.action_load_diff()
            self.usage_data["count"] += 1
            self.core.save_usage_data(self.usage_data)
            self.update_limit_label()
        else:
            self.show_status(f"Ошибка Git: {out[:60]}...", "error")

if __name__ == "__main__":
    try:
        import pyperclip
    except ImportError:
        os.system("pip install pyperclip")
        import pyperclip
    app = CommitCraftApp()
    app.mainloop()