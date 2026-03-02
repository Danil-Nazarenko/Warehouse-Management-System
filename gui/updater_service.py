import os
import sys
import requests
import subprocess
import time
from tkinter import messagebox

# КОНСТАНТЫ (Замени на свои ссылки из GitHub)
VERSION_URL = "https://raw.githubusercontent.com/Danil-Nazarenko/Warehouse-Management-System/main/version.txt"
EXE_URL = "https://github.com/Danil-Nazarenko/Warehouse-Management-System/releases/latest/download/Ordo.exe"
CURRENT_VERSION = "2.0.0"

def check_for_update(parent):
    try:
        # 1. Проверяем версию в сети
        response = requests.get(VERSION_URL, timeout=5)
        online_version = response.text.strip()

        if online_version == CURRENT_VERSION:
            messagebox.showinfo("Обновление", "У вас установлена актуальная версия.")
            return

        # 2. Если есть новая — спрашиваем
        if messagebox.askyesno("Обновление", f"Доступна новая версия {online_version}. Обновить сейчас?"):
            perform_update(parent)

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось проверить обновления: {e}")

def perform_update(parent):
    try:
        # Скачиваем новый EXE
        new_exe = "Ordo_new.exe"
        r = requests.get(EXE_URL, stream=True)
        
        with open(new_exe, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # Путь к текущему запущенному EXE
        current_exe = sys.executable

        # Создаем временный батник для подмены файлов
        # Он ждет закрытия программы, удаляет старую, переименовывает новую и запускает
        batch_script = f"""
        @echo off
        timeout /t 2 /nobreak > nul
        del "{current_exe}"
        ren "{new_exe}" "{os.path.basename(current_exe)}"
        start "" "{current_exe}"
        del "%~f0"
        """
        
        with open("update.bat", "w") as f:
            f.write(batch_script)

        # Запускаем батник и закрываем основное окно
        subprocess.Popen(["update.bat"], shell=True)
        parent.destroy()
        sys.exit()

    except Exception as e:
        messagebox.showerror("Ошибка обновления", f"Критическая ошибка: {e}")