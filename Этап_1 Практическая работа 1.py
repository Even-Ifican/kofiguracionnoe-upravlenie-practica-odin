from tkinter import *
import getpass
import socket
import sys
import os
import shlex
import argparse
import xml.etree.ElementTree as ET
import base64




def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--vfs", help="путь к физическому расположению VFS (XML)")
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




class VFSError(Exception):
    pass


class VFSNode:
    def __init__(self, name, is_dir, content=None):
        self.name = name
        self.is_dir = is_dir
        self.content = content      
        self.children = {}          


class VFS:
    def __init__(self, path):
        self.root = VFSNode("/", is_dir=True)
        self._load(path)

    def _load(self, path):
        try:
            tree = ET.parse(path)
        except FileNotFoundError:
            raise VFSError(f"файл VFS не найден: {path}")
        except ET.ParseError as e:
            raise VFSError(f"неверный формат VFS: {e}")
        except OSError as e:
            raise VFSError(f"не удалось прочитать файл VFS: {e}")

        self._build(tree.getroot(), self.root)

    def _build(self, elem, node):
        for child in elem:
            name = child.get("name")
            if child.tag in ("dir", "file") and not name:
                raise VFSError(f"у элемента <{child.tag}> нет атрибута name")
            if child.tag == "dir":
                d = VFSNode(name, is_dir=True)
                node.children[name] = d
                self._build(child, d)
            elif child.tag == "file":
                raw = (child.text or "").strip()
                try:
                    data = base64.b64decode(raw, validate=True) if raw else b""
                except Exception:
                    raise VFSError(f"неверные base64-данные в файле {name}")
                node.children[name] = VFSNode(name, is_dir=False, content=data)

    def tree_text(self):
        
        lines = ["/"]

        def walk(node, prefix):
            names = sorted(node.children)
            for i, name in enumerate(names):
                child = node.children[name]
                last = i == len(names) - 1
                lines.append(prefix + ("└── " if last else "├── ") + name + ("/" if child.is_dir else ""))
                if child.is_dir:
                    walk(child, prefix + ("    " if last else "│   "))

        walk(self.root, "")
        return "\n".join(lines)




class Shell:
    def __init__(self, vfs=None):
        self.vfs = vfs

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

        cmd, *cmd_args = parts

        if cmd == "help":
            return "Доступные команды: help, echo, ls, cd, vfs, exit"
        elif cmd == "echo":
            return " ".join(cmd_args)
        elif cmd == "ls":
            return f"ls вызван с аргументами: {cmd_args}"      
        elif cmd == "cd":
            return f"cd вызван с аргументами: {cmd_args}"      
        elif cmd == "vfs":
            return self.cmd_vfs(cmd_args)
        elif cmd == "exit":
            raise SystemExit(0)
        else:
            return f"Команда '{cmd}' не найдена."

    def cmd_vfs(self, cmd_args):
        """Служебная команда: показывает, что VFS загружена, и печатает её дерево."""
        if self.vfs is None:
            return "vfs: VFS не загружена (запустите с --vfs путь.xml)"
        return self.vfs.tree_text()




def close_after_exit():
    window_entry.insert(END, "\nВыход из эмулятора")
    window_entry.see(END)
    windows.after(800, windows.destroy)


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


def on_enter(event):
    current_line = window_entry.get("insert linestart", "end-1c")
    cmd_line = current_line.replace(f"{full_path}>", "").strip()
    run_line(cmd_line)
    return "break"


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
windows.title(f"Эмулятор - [{getpass.getuser()}@{socket.gethostname()}]")
windows.geometry("500x500")

window_entry = Text(windows, bg="black", fg="white", insertbackground="white")
window_entry.pack(fill=BOTH, expand=True, pady=10)


vfs = None
if args.vfs:
    try:
        vfs = VFS(args.vfs)
        print(f"VFS успешно загружена из {args.vfs}")
    except VFSError as e:
        print(f"Ошибка загрузки VFS: {e}")
        window_entry.insert(END, f"[VFS] ошибка загрузки: {e}\n")

shell = Shell(vfs=vfs)

window_entry.insert(END, f"{full_path}> ")
window_entry.mark_set(INSERT, END)
window_entry.bind("<Return>", on_enter)

if args.script:
    run_script(args.script)

windows.mainloop()from tkinter import *
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
