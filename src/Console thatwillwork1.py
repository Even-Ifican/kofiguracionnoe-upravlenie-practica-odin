import tkinter as tk
import getpass
import socket
import re
import shlex
import argparse
import os

window = tk.Tk()
username = getpass.getuser()
hostname = socket.gethostname()
PROMPT = f"{username}@{hostname}:~$ "

def parse_args():
    p = argparse.ArgumentParser(description="Эмулятор оболочки")
    p.add_argument("--vfs", help="путь к физическому расположению VFS")
    p.add_argument("--script", help="путь к стартовому скрипту")
    return p.parse_args()

window.geometry("800x800")
window.title(f"{username}@{hostname}")
console = tk.Text(window, bg="black", fg="white",
@@ -70,6 +77,9 @@
        raise CommandError(f"{name}: команда не найдена")
    return handler(args)

def write(text):
    console.insert(tk.END, text)
    console.see(tk.END)

def print_prompt():
    console.insert(tk.END, PROMPT)
@@ -108,6 +118,40 @@
console.bind("<Key>", on_key)
console.bind("<BackSpace>", on_backspace)

def run_script(path):
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError as e:
        write(f"Не удалось открыть скрипт: {e}\n")
        return
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        write(PROMPT + line + "\n")
        if not run_line(line):
            write("Скрипт остановлен из-за ошибки\n")
            break

def run_line(line):
    try:
        out = execute(line)
        if out:
            write(out + "\n")
        return True
    except CommandError as e:
        write(f"{e}\n")
        return False

args = parse_args()

write("[отладка] параметры запуска:\n")
write(f"  vfs    = {args.vfs}\n")
write(f"  script = {args.script}\n\n")

if args.script:
    run_script(args.script)

print_prompt()
console.focus_set()
window.mainloop()
