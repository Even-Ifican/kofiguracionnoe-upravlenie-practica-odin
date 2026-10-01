import tkinter
from tkinter import *
import platform
import sys
import os
import shlex


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
            windows.destroy()
            sys.exit()
        else:
            return f"Команда '{cmd}' не найдена."


def on_enter(event):

    current_line = window_entry.get("insert linestart", "end-1c")


    cmd_line = current_line.replace(f"{full_path}>", "").strip()


    output = shell.execute(cmd_line)


    if output:
        window_entry.insert(END, "\n" + output)

    window_entry.insert(END, prompt)


    window_entry.mark_set(INSERT, END)
    window_entry.see(END)
    return "break"



windows = Tk()
windows.title(f"Эмулятор - {os.name} {platform.system()} {sys.platform}")
windows.geometry("500x500")


shell = Shell()


window_entry = Text(windows, bg="black", fg="white", insertbackground="white")
window_entry.pack(fill=BOTH, expand=True, pady=10)


window_entry.insert(1.0, f"{full_path}> ")
window_entry.mark_set(INSERT, END)

window_entry.bind("<Return>", on_enter)

windows.mainloop()
