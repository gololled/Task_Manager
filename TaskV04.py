import tkinter as tk
from tkinter import messagebox, Toplevel, Text
from tkcalendar import Calendar
from datetime import datetime
import psycopg2

show_only_completed_mode = False  # Режим отображения только завершенных задач

# Подключение к базе данных PostgreSQL
def connect_db():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="Your_database",
            user="Your_username",
            password="Your_password"
        )
        return conn
    except Exception as e:
        messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к базе данных: {e}")
        return None

# Загрузка задач из базы данных
# На 33 строчке надо поменять Your_table на название вашей таблицы из БД
def load_tasks():
    global tasks, favorite_tasks
    tasks = []
    favorite_tasks = set()

    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Your_table ORDER BY id")
        rows = cursor.fetchall()
        for row in rows:
            task_id, task_text, due_date, is_favorite, is_completed, description = row
            tasks.append((task_text, due_date, is_completed, description))
            if is_favorite:
                favorite_tasks.add(task_text)
        conn.close()

# Сохранение задач в базе данных
# На 48 и 51 строчках надо поменять Your_table на название вашей таблицы из БД
def save_tasks():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Your_table")
        for task, due_date, is_completed, description in tasks:
            cursor.execute(
                "INSERT INTO Your_table (task, due_date, is_favorite, is_completed, description) VALUES (%s, %s, %s, %s, %s)",
                (task, due_date, task in favorite_tasks, is_completed, description)
            )
        conn.commit()
        conn.close()

def clean_task_text(task_text):
    """Удаляет дополнительные пометки из текста задачи."""
    task_text = task_text.split(" (осталось")[0].strip()  # Убираем дату с остатком дней
    task_text = task_text.split(" (была на")[0].strip()  # Убираем дату завершенной задачи
    task_text = task_text.replace("✔", "").strip()  # Убираем галочку завершенной задачи
    task_text = task_text.replace("⭐", "").strip()  # Убираем пометку избранного
    return task_text

def update_task_listbox():
    task_listbox.delete(0, tk.END)

    if show_only_completed_mode:  # Если активирован режим отображения завершенных задач
        tasks_to_show = [task for task in tasks if task[2]]  # Только завершенные задачи
    else:
        tasks_to_show = [task for task in tasks if not task[2]]  # Все задачи, кроме завершенных

    if not show_only_completed_mode and show_favorites_mode:
        tasks_to_show = [task for task in tasks_to_show if task[0] in favorite_tasks]

    for task, due_date, is_completed, _ in tasks_to_show:
        task_text = task
        if due_date:  # Показываем дату, если она указана
            days_left = (due_date - datetime.now().date()).days
            if not is_completed:
                task_text = f"{task} (осталось {days_left} дней)"
            else:
                task_text = f"{task} (была на {due_date.strftime('%d/%m/%Y')})"
        if task in favorite_tasks:
            task_text += " ⭐"
        if is_completed:
            task_text = f"✔ {task_text}"  # Добавляем галочку к завершенной задаче
        task_listbox.insert(tk.END, task_text)

# Смена темы интерфейса
def switch_theme():
    global dark_theme
    dark_theme = not dark_theme

    bg_color = "#2e2e2e" if dark_theme else "#ffffff"
    fg_color = "#ffffff" if dark_theme else "#000000"

    root.configure(bg=bg_color)
    for widget in root.winfo_children():
        if isinstance(widget, tk.Button) or isinstance(widget, tk.Listbox):
            widget.configure(bg=bg_color, fg=fg_color)

# Сортировка по дате
def sort_by_date():
    global tasks
    tasks.sort(key=lambda x: (x[1] is None, x[1]))
    update_task_listbox()

# Сортировка по алфавиту
def sort_by_alphabet():
    global tasks
    tasks.sort(key=lambda x: x[0].lower())
    update_task_listbox()

def mark_as_completed():
    selected_index = task_listbox.curselection()
    if selected_index:
        task_text = task_listbox.get(selected_index[0])  # Получаем выбранную строку
        task_text_clean = clean_task_text(task_text)  # Очищаем текст задачи

        # Ищем задачу в списке и помечаем как выполненную
        for i, (task, due_date, is_completed, description) in enumerate(tasks):
            if task == task_text_clean:
                tasks[i] = (task, due_date, True, description)  # Обновляем статус на "выполнено"
                if task in favorite_tasks:  # Если задача избранная
                    favorite_tasks.remove(task)  # Удаляем из избранного
                break

        save_tasks()
        update_task_listbox()

# Добавление/удаление задачи из избранного
def toggle_favorite():
    selected_index = task_listbox.curselection()
    if not selected_index:
        return  # Если ничего не выбрано, ничего не делаем

    task_text = task_listbox.get(selected_index[0])  # Получаем выбранную строку
    task_text_clean = clean_task_text(task_text)  # Очищаем текст задачи

    for task, due_date, is_completed, description in tasks:
        if task == task_text_clean:  # Ищем задачу без добавочного текста
            if task in favorite_tasks:
                favorite_tasks.remove(task)
            else:
                favorite_tasks.add(task)
            break

    save_tasks()
    update_task_listbox()

# Удаление задачи
def delete_task():
    selected_task_index = task_listbox.curselection()
    if selected_task_index:
        task_text = task_listbox.get(selected_task_index[0])  # Получаем выбранную строку
        task_text_clean = clean_task_text(task_text)  # Очищаем текст задачи

        # Ищем индекс задачи в списке tasks
        for i, (task, due_date, is_completed, description) in enumerate(tasks):
            if task == task_text_clean:
                del tasks[i]  # Удаляем задачу из списка
                if task in favorite_tasks:
                    favorite_tasks.remove(task)  # Убираем из избранных
                break

        save_tasks()
        update_task_listbox()

# Функция для переключения между всеми задачами и избранными задачами
def toggle_favorites_view():
    global show_favorites_mode
    show_favorites_mode = not show_favorites_mode
    update_task_listbox()

def show_completed_tasks():
    global show_only_completed_mode
    show_only_completed_mode = not show_only_completed_mode
    show_completed_button.config(
        text="Показать все задачи" if show_only_completed_mode else "Показать завершенные"
    )
    update_task_listbox()

# Функция для открытия карточки задачи
def show_task_card(task_text_clean):
    for task, due_date, is_completed, description in tasks:
        if task == task_text_clean:
            task_card = Toplevel(root)
            task_card.title("Карточка задачи")

            tk.Label(task_card, text=f"Задача: {task}").pack(pady=5)
            if due_date:
                tk.Label(task_card, text=f"Срок истечения: {due_date.strftime('%d/%m/%Y')}").pack(pady=5)
            status_text = "Завершена" if is_completed else "Активна"
            tk.Label(task_card, text=f"Статус: {status_text}").pack(pady=5)

            tk.Label(task_card, text="Описание:").pack(pady=5)
            description_text = Text(task_card, width=40, height=10, wrap=tk.WORD)
            description_text.insert(tk.END, description)
            description_text.config(state=tk.DISABLED)  # Запрещаем редактирование
            description_text.pack(pady=5)

            tk.Button(task_card, text="Закрыть", command=task_card.destroy).pack(pady=5)
            break

# Функция для добавления или редактирования задачи
def show_task_window(is_edit=False, task_to_edit=None):
    global selected_date
    selected_date = None

    task_window = Toplevel(root)
    task_window.title("Добавить/Редактировать задачу")

    task_label = tk.Label(task_window, text="Введите задачу:")
    task_label.pack()
    task_entry = tk.Entry(task_window, width=40)
    task_entry.pack()

    if is_edit:
        task_entry.insert(0, task_to_edit[0])

    date_label = tk.Label(task_window, text="Выбранная дата:")
    date_label.pack()
    selected_date_var = tk.StringVar(value="Дата не выбрана")
    date_display = tk.Label(task_window, textvariable=selected_date_var)
    date_display.pack()

    def choose_date():
        cal_window = Toplevel(task_window)
        cal_window.title("Выбор даты")
        cal = Calendar(cal_window, selectmode="day", date_pattern="dd/mm/yyyy")
        cal.pack()

        def confirm_date():
            global selected_date
            selected_date = cal.get_date()
            selected_date_var.set(selected_date)
            cal_window.destroy()

        confirm_button = tk.Button(cal_window, text="Выбрать", command=confirm_date)
        confirm_button.pack()

    calendar_button = tk.Button(task_window, text="Выбрать дату", command=choose_date)
    calendar_button.pack()

    description_label = tk.Label(task_window, text="Введите описание:")
    description_label.pack()
    description_text = Text(task_window, width=40, height=5, wrap=tk.WORD)
    description_text.pack()

    if is_edit:
        description_text.insert(tk.END, task_to_edit[3])

    def save_task():
        task = task_entry.get().strip()
        description = description_text.get("1.0", tk.END).strip()
        if task:
            due_date_obj = None
            if selected_date:
                due_date_obj = datetime.strptime(selected_date, "%d/%m/%Y").date()

            if is_edit:
                tasks[tasks.index(task_to_edit)] = (task, due_date_obj, task_to_edit[2], description)
            else:
                tasks.append((task, due_date_obj, False, description))
            save_tasks()
            update_task_listbox()
            task_window.destroy()
        else:
            messagebox.showwarning("Ошибка", "Задача не может быть пустой!")

    save_button = tk.Button(task_window, text="Сохранить", command=save_task)
    save_button.pack()
    cancel_button = tk.Button(task_window, text="Отмена", command=task_window.destroy)
    cancel_button.pack()

# Основное окно приложения
root = tk.Tk()
root.title("Task Manager")
root.geometry("350x360")

show_favorites_mode = False
show_completed_mode = False
dark_theme = False

load_tasks()

task_listbox = tk.Listbox(root, width=50, height=10)
task_listbox.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

def on_task_double_click(event):
    selected_index = task_listbox.curselection()
    if selected_index:
        task_text = task_listbox.get(selected_index[0])
        task_text_clean = clean_task_text(task_text)
        show_task_card(task_text_clean)

task_listbox.bind("<Double-1>", on_task_double_click)

# Кнопки для функционала
add_button = tk.Button(root, text="Добавить задачу", command=lambda: show_task_window(is_edit=False))
favorite_toggle_button = tk.Button(root, text="⭐/❌", command=toggle_favorite)
edit_button = tk.Button(root, text="Редактировать", command=lambda: show_task_window(is_edit=True, task_to_edit=tasks[task_listbox.curselection()[0]]))
delete_button = tk.Button(root, text="Удалить", command=delete_task)
favorites_view_button = tk.Button(root, text="Избранные", command=toggle_favorites_view)
theme_button = tk.Button(root, text="Сменить тему", command=switch_theme)
sort_date_button = tk.Button(root, text="Сортировать по дате", command=sort_by_date)
sort_alpha_button = tk.Button(root, text="Сортировать по алфавиту", command=sort_by_alphabet)
complete_button = tk.Button(root, text="Пометить выполненной", command=mark_as_completed)
show_completed_button = tk.Button(root, text="Показать завершенные", command=show_completed_tasks)

add_button.grid(row=0, column=0, padx=5, pady=3)
favorite_toggle_button.grid(row=0, column=1, padx=5, pady=3)
edit_button.grid(row=1, column=0, padx=5, pady=3)
delete_button.grid(row=1, column=1, padx=5, pady=3)
favorites_view_button.grid(row=3, column=0, padx=5, pady=3)
theme_button.grid(row=3, column=1, padx=5, pady=3)
sort_date_button.grid(row=4, column=0, padx=5, pady=3)
sort_alpha_button.grid(row=4, column=1, padx=5, pady=3)
complete_button.grid(row=5, column=0, padx=5, pady=3)
show_completed_button.grid(row=5, column=1, padx=5, pady=3)

update_task_listbox()

root.mainloop()
