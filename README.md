Эмулятор командной строки — Этап 1 (REPL)
Как это работает
Код состоит из двух частей:

- Shell — логика: разбирает введённую строку и решает, что на неё ответить. Ничего не знает про окно, кнопки или Tkinter.
- Tkinter-окно — отображает всё в одном текстовом поле (window_entry), которое работает одновременно и как вывод, и как поле ввода, имитируя настоящий терминал.

Связь между ними простая: когда пользователь нажимает Enter, GUI берёт текст строки, отдаёт его в shell.execute(...) и печатает то, что вернул Shell.

Заголовок окна
Заголовок строится из реальных данных операционной системы, на которой запущен эмулятор: os.name (posix nt), platform.system() (Linux/Windows/Darwin), sys.platform.

Промпт и раскрытие переменных окружения

python
os.environ["HOME_MOCK"] = "aha"
raw_path = "$HOME_MOCK/Desktop/Even's Hub"
full_path = os.path.expandvars(raw_path)
prompt = f"\n{full_path}> "

os.environ["HOME_MOCK"] = "aha" — здесь переменная окружения задаётся прямо в коде, для демонстрации. В реальной работе переменные вроде $HOME уже существуют в ОС и ничего задавать не нужно.

os.path.expandvars(raw_path) — ищет в строке конструкции $VAR или ${VAR} и заменяет их значениями из окружения. Это и есть механизм раскрытия переменных окружения, требуемый заданием (пример в задании — $HOME).

Результат (full_path) используется как часть промпта — то, что видно перед вводом пользователя, как `/home/user>` в настоящем терминале.

Класс `Shell` — разбор и выполнение команд

python
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
        ...


Каждая введённая строка проходит три шага:

1. Раскрытие переменных — expand_vars раскрывает $VAR в самой введённой команде, не только в промпте. Например, echo $HOME_MOCK раскроется в echo aha ещё до разбора на аргументы.
2. Разбиение на слова — shlex.split режет строку на токены с учётом кавычек (в отличие от обычного .split(), который кавычки не понимает). Если кавычка не закрыта, shlex.split кидает ValueError, который перехватывается и превращается в понятное сообщение об ошибке, а не в падение программы.
3. Разделение на команду и аргументы — cmd, *args = parts кладёт первое слово в cmd, остальные — списком в args.

Поддерживаемые команды

| Команда | Что делает |
| help | печатает список доступных команд |
| echo текст | возвращает переданные аргументы, склеенные пробелом |
| exit | закрывает окно и завершает процесс |
| что угодно ещё | возвращается сообщение Команда '...' не найдена |

Это всё, что требует Этап 1: пара рабочих команд плюс явная обработка ошибки «неизвестная команда».

Обработка Enter в текстовом поле

python
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


Так как ввод и вывод происходят в одном и том же виджете Text, нужно вручную вычислить, что именно напечатал пользователь:

- window_entry.get("insert linestart", "end-1c") — забирает текст от начала текущей строки (где стоит курсор) до конца содержимого поля.
- .replace(f"{full_path}>", "") — убирает из этой строки сам промпт, чтобы остался только текст команды.
- shell.execute(cmd_line) — выполняет команду и получает текстовый результат.
- Результат дописывается в поле, затем добавляется новый промпт, курсор переводится в конец (mark_set(INSERT, END)), поле прокручивается вниз (see(END)).
- return "break" — отменяет стандартное поведение Text на Enter (вставку обычного переноса строки), чтобы не было лишнего пустого перехода.

Создание окна

python
windows = Tk()
windows.title(...)
windows.geometry("500x500")

shell = Shell()

window_entry = Text(windows, bg="black", fg="white", insertbackground="white")
window_entry.pack(fill=BOTH, expand=True, pady=10)

window_entry.insert(1.0, f"{full_path}> ")
window_entry.mark_set(INSERT, END)

window_entry.bind("<Return>", on_enter)

windows.mainloop()
 
- bg="black", fg="white" — чёрный фон и белый текст, визуально похоже на настоящий терминал.
- insertbackground="white" — делает белым сам курсор ввода .
- window_entry.insert(1.0, ...) — печатает самый первый промпт при запуске .
- window_entry.bind("<Return>", on_enter) — связывает нажатие Enter с обработчиком.
- windows.mainloop() — запускает основной цикл Tkinter: окно становится видимым и реагирует на события, пока не будет закрыто.
