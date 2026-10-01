
from tkinter import *
import platform
import sys
import os
import shlex
import argparse



def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--vfs", help="путь к физическому расположению VFS")
    p.add_argument("--script", help="путь к стартовому скрипту")
    return p.parse_args()


args = parse_args()

print("=== Параметры запуска ===")
print(f"VFS path: {args.vfs}")
print(f"Script path: {args.script}")
print("==========================")


os.environ["HOME_MOCK"] = "aha"
raw_path = "$HOME_MOCK/Desktop/Even's Hub"
full_path = os.path.expandvars(raw_path)
prompt = f"\n{full_path}> "


class Shell:
    def expand_vars(self, line):
        return os.path.expandvars(line)

    def execute(self, line):
        line = self.expand_vars(line.strip())
        if not line:
            return ""

        try:
            parts = shlex.split(line)
        except ValueError as e:
            return f"Ошибка разбора: {e}"

        cmd, *args = parts

        if cmd == "help":
            return "Доступные команды: help, echo, exit"
        elif cmd == "echo":
            return " ".join(args)
        elif cmd == "exit":
            raise SystemExit(0)
        else:
            return f"Команда '{cmd}' не найдена."


def on_enter(event):
    current_line = window_entry.get("insert linestart", "end-1c")
    cmd_line = current_line.replace(f"{full_path}>", "").strip()
    run_line(cmd_line)
    return "break"


def run_line(cmd_line):

    try:
        output = shell.execute(cmd_line)
    except SystemExit:
        close_after_exit()
        return

    if output:
        window_entry.insert(END, "\n" + output)

    window_entry.insert(END, prompt)
    window_entry.mark_set(INSERT, END)
    window_entry.see(END)


def close_after_exit():
    window_entry.insert(END, "\nВыход из эмулятора")
    window_entry.see(END)
    windows.after(800, windows.destroy)



def run_script(path):

    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        window_entry.insert(END, f"\nНе удалось открыть скрипт: {e}")
        window_entry.insert(END, prompt)
        return

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if not line.strip():
            continue


        window_entry.insert(END, line)

        try:
            output = shell.execute(line)
            if output:
                window_entry.insert(END, "\n" + output)
        except SystemExit:
            close_after_exit()
            return
        except Exception as e:
            window_entry.insert(END, f"\n[скрипт] ошибка, строка пропущена: {e}")

        window_entry.insert(END, prompt)

    window_entry.mark_set(INSERT, END)
    window_entry.see(END)


windows = Tk()
windows.title(f"Эмулятор - {os.name} {platform.system()} {sys.platform}")
windows.geometry("500x500")


shell = Shell()


window_entry = Text(windows, bg="black", fg="white", insertbackground="white")
window_entry.pack(fill=BOTH, expand=True, pady=10)


window_entry.insert(1.0, f"{full_path}> ")
window_entry.mark_set(INSERT, END)

window_entry.bind("<Return>", on_enter)

if args.script:
    run_script(args.script)

windows.mainloop()