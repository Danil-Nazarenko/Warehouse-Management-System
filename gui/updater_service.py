import os
import sys
import requests
import subprocess
import hashlib
from tkinter import messagebox, Toplevel, Label
from tkinter.ttk import Progressbar

VERSION_URL = "https://raw.githubusercontent.com/Danil-Nazarenko/Warehouse-Management-System/main/version.txt"
EXE_URL = "https://github.com/Danil-Nazarenko/Warehouse-Management-System/releases/latest/download/Ordo.exe"
CURRENT_VERSION = "2.0.0"

def get_file_hash(response):
    """Опционально: если на сервере есть хэш, можно проверять тут."""
    return True

def check_for_update(parent, silent=False):
    """
    Проверяет наличие новой версии.
    silent=True используется для автоматической проверки при старте (не беспокоит, если всё ок).
    """
    try:
        response = requests.get(VERSION_URL, timeout=5)
        response.raise_for_status()
        online_version = response.text.strip()

        if online_version == CURRENT_VERSION:
            if not silent:
                messagebox.showinfo("Обновление", "У вас установлена актуальная версия.")
            return

        if messagebox.askyesno("Обновление", f"Доступна новая версия {online_version}. Обновить сейчас?"):
            perform_update(parent)

    except Exception as e:
        if not silent:
            messagebox.showerror("Ошибка", f"Не удалось проверить обновления: {e}")

def perform_update(parent):
    progress_win = Toplevel(parent)
    progress_win.title("Обновление...")
    progress_win.geometry("300x100")
    progress_win.attributes("-topmost", True)
    Label(progress_win, text="Скачивание новой версии...").pack(pady=10)
    progress = Progressbar(progress_win, length=200, mode='determinate')
    progress.pack(pady=5)

    try:
        new_exe = "Ordo_new.exe"
        r = requests.get(EXE_URL, stream=True, timeout=30)
        total_length = r.headers.get('content-length')

        if total_length is None:
            with open(new_exe, 'wb') as f:
                f.write(r.content)
        else:
            dl = 0
            total_length = int(total_length)
            with open(new_exe, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    dl += len(chunk)
                    f.write(chunk)
                    done = int(100 * dl / total_length)
                    progress['value'] = done
                    progress_win.update()

        if os.path.getsize(new_exe) < 1000000:
             raise Exception("Скачанный файл слишком мал. Возможно, ссылка неверна.")

        current_exe = sys.executable
        exe_name = os.path.basename(current_exe)

        batch_script = f"""@echo off
chcp 65001 > nul
timeout /t 2 /nobreak > nul
taskkill /f /im "{exe_name}" > nul 2>&1
del /f /q "{current_exe}"
move /y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
""".encode('utf-8')

        with open("update.bat", "wb") as f:
            f.write(batch_script)

        subprocess.Popen(["update.bat"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        parent.destroy()
        sys.exit()

    except Exception as e:
        if os.path.exists("Ordo_new.exe"):
            os.remove("Ordo_new.exe")
        messagebox.showerror("Ошибка обновления", f"Не удалось обновить: {e}")
        progress_win.destroy()