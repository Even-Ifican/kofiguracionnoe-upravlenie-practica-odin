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

 Эмулятор командной строки — Этап 2 (Конфигурация)

GUI-эмулятор командной строки на Python/Tkinter. На этом этапе эмулятор становится настраиваемым: принимает параметры командной строки и умеет выполнять стартовый скрипт автоматически при запуске.


| Параметр   | Назначение                                        | Обязателен? |
|------------|-----------------------------------------------------|:---:|
| `--vfs`    | путь к физическому расположению VFS (на этом этапе только принимается и печатается, сама загрузка появится на Этапе 3) | нет |
| `--script` | путь к стартовому скрипту, который выполняется автоматически при запуске | нет |



## Как это работает

### Общая структура


argparse (разбор --vfs / --script)
        ↓
Shell (парсер команд, логика help/echo/exit)
        ↓
Tkinter GUI (окно, текстовое поле, обработка Enter)
        ↓
run_script (прогон стартового скрипта через ту же логику, что и ручной ввод)


Ключевая идея этапа: выполнение скрипта не дублирует логику — функция `run_line`, которая раньше вызывалась только из `on_enter` (при нажатии Enter), вынесена отдельно и используется и для ручного ввода, и для строк скрипта. Это гарантирует, что скрипт ведёт себя ровно так же, как если бы пользователь вводил те же команды руками.

 Разбор параметров (`parse_args`)

python
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--vfs", help="путь к физическому расположению VFS")
    p.add_argument("--script", help="путь к стартовому скрипту")
    return p.parse_args()

argparse.ArgumentParser — стандартный способ в Python читать параметры, с которыми был запущен скрипт. `p.add_argument("--vfs", ...)` регистрирует необязательный именованный параметр: если его не передать, `args.vfs` будет `None`.

Разбор происходит в самом начале файла, до создания окна, — поэтому отладочный вывод параметров виден в консоли ещё до того, как откроется GUI.

Класс `Shell` — без изменений в логике команд

`Shell.execute` работает так же, как на Этапе 1: раскрывает переменные окружения (`expand_vars`), разбивает строку на токены (`shlex.split`), ищет команду среди `help`, `echo`, `exit`.

Единственное изменение — `exit`:

python
elif cmd == "exit":
    raise SystemExit(0)


Раньше здесь было `windows.destroy(); sys.exit()` — прямое управление окном прямо из логики команд. Проблема в том, что при выполнении `exit` **внутри скрипта** окно уничтожалось бы мгновенно, раньше, чем код в `run_script` успевал бы вывести сообщение о завершении. Теперь `Shell` просто выбрасывает `SystemExit` — стандартное исключение Python для завершения программы, которое **не перехватывается** `except Exception` (оно наследуется от `BaseException`, а не от `Exception`). Это позволяет вызывающему коду (`run_line` и `run_script`) самому решить, когда и как закрыть окно.

`run_line` — выполнение одной команды

python
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


Вынесена из `on_enter` в отдельную функцию, чтобы её можно было переиспользовать для строк скрипта. Ловит `SystemExit` отдельно от обычных ошибок — если команда была `exit`, вызывается `close_after_exit()` вместо попытки напечатать результат.

`on_enter` теперь короче — просто определяет, что ввёл пользователь, и передаёт это в `run_line`:

python
def on_enter(event):
    current_line = window_entry.get("insert linestart", "end-1c")
    cmd_line = current_line.replace(f"{full_path}>", "").strip()
    run_line(cmd_line)
    return "break"


run_script — выполнение стартового скрипта

python
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


Построчно читает файл скрипта и для каждой непустой строки:

1. Печатает её в окно как «ввод» — имитирует диалог с пользователем (требование задания).
2. Выполняет через `shell.execute(line)` и печатает результат — это «вывод» того же диалога.
3. Если строка вызвала ошибку (например, неизвестная команда) — ошибка перехватывается `except Exception`, выводится сообщение, и цикл идёт дальше, **не прерывая** выполнение оставшихся строк. Это ключевое требование Этапа 2.
4. Если строка была `exit` — скрипт останавливается и окно закрывается через `close_after_exit`.

close_after_exit — корректное закрытие окна

python
def close_after_exit():
    window_entry.insert(END, "\nВыход из эмулятора")
    window_entry.see(END)
    windows.after(800, windows.destroy)


windows.after(800, windows.destroy) откладывает закрытие окна на 800 миллисекунд, чтобы пользователь успел увидеть сообщение «Выход из эмулятора», прежде чем окно реально закроется. Без этой задержки окно исчезло бы мгновенно вместе с сообщением.

Запуск скрипта при старте
python
if args.script:
    run_script(args.script)

windows.mainloop()


Если параметр --script был передан, скрипт выполняется один раз сразу после создания окна. После этого (или если скрипта не было вовсе) запускается `windows.mainloop()` — основной цикл Tkinter, и пользователь может продолжать вводить команды вручную в том же окне.

Структура файлов


main_stage2.py              # весь код эмулятора
scripts_stage2/
  basic.txt                  # успешные команды: help, echo, выход
  errors.txt                 # неизвестная команда и незакрытая кавычка — проверка, что скрипт не падает
run_tests.sh                 # скрипт реальной ОС (Linux/macOS): прогоняет все варианты параметров
run_tests.bat                # тот же набор тестов для Windows


 run_tests.sh / run_tests.bat

Это не скрипты самого эмулятора, а скрипты **реальной ОС**, которые запускают эмулятор несколько раз подряд с разными комбинациями параметров — без параметров, только с `--script`, только с `--vfs`, с обоими сразу. Это демонстрирует, что все заявленные параметры командной строки действительно поддерживаются (требование пункта 3).

Запуск на Linux/macOS:
bash
chmod +x run_tests.sh
./run_tests.sh
