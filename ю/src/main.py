import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# --- База данных ---
conn = sqlite3.connect("repair.db")
conn.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT NOT NULL,
        client_phone TEXT,
        device TEXT NOT NULL,
        problem TEXT,
        status TEXT DEFAULT 'Принято',
        price REAL DEFAULT 0,
        created_date TEXT DEFAULT (date('now'))
    )
""")
conn.commit()

STATUSES = ["Все", "Принято", "В ремонте", "Готово", "Выдано"]

def load_orders(filter_status=None):
    for row in tree.get_children():
        tree.delete(row)
    
    if filter_status and filter_status != "Все":
        query = """
            SELECT id, client_name, client_phone, device, status, price, created_date
            FROM orders
            WHERE status = ?
            ORDER BY id DESC
        """
        cursor = conn.execute(query, (filter_status,))
    else:
        query = """
            SELECT id, client_name, client_phone, device, status, price, created_date
            FROM orders
            ORDER BY id DESC
        """
        cursor = conn.execute(query)

    for order in cursor:
        tree.insert("", "end", values=order)

def selected_order_id():
    selected = tree.selection()
    if not selected:
        messagebox.showinfo("Ничего не выбрано", "Кликните по строке с заявкой.")
        return None
    return tree.item(selected[0])["values"][0]

def change_status():
    order_id = selected_order_id()
    if order_id is None:
        return
    win = tk.Toplevel(root)
    win.title("Сменить статус")
    win.geometry("280x150")
    win.grab_set()
    tk.Label(win, text="Новый статус:").pack(pady=10)
    combo = ttk.Combobox(win, values=STATUSES[1:], state="readonly")
    combo.current(0)
    combo.pack(pady=5)

    def apply_status():
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (combo.get(), order_id))
        conn.commit()
        win.destroy()
        load_orders(current_filter.get())

    tk.Button(win, text="Применить", command=apply_status, width=12).pack(pady=10)

def delete_order():
    order_id = selected_order_id()
    if order_id is None:
        return
    if messagebox.askyesno("Удаление", f"Удалить заявку № {order_id}? Действие необратимо."):
        conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        load_orders(current_filter.get())

def edit_order():
    """Открывает форму редактирования с текущими данными заявки."""
    order_id = selected_order_id()
    if order_id is None:
        return

    # Получаем текущие данные
    cursor = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    data = cursor.fetchone()
    # data: (id, client_name, phone, device, problem, status, price, date)

    win = tk.Toplevel(root)
    win.title(f"Редактировать заявку № {order_id}")
    win.geometry("420x380")
    win.grab_set()

    labels = {
        "client_name": "Клиент (ФИО):",
        "client_phone": "Телефон:",
        "device": "Устройство (модель):",
        "price": "Цена (руб.):",
    }
    entries = {}
    row = 0
    for key, text in labels.items():
        tk.Label(win, text=text).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        entry = tk.Entry(win, width=30)
        # Заполняем текущими значениями
        if key == "client_name":
            entry.insert(0, data[1])
        elif key == "client_phone":
            entry.insert(0, data[2])
        elif key == "device":
            entry.insert(0, data[3])
        elif key == "price":
            entry.insert(0, str(data[6]).replace(".", ","))
        entry.grid(row=row, column=1, padx=10, pady=5)
        entries[key] = entry
        row += 1

    tk.Label(win, text="Неисправность:").grid(row=row, column=0, sticky="nw", padx=10, pady=5)
    problem = tk.Text(win, width=30, height=4)
    problem.insert("1.0", data[4] or "")
    problem.grid(row=row, column=1, padx=10, pady=5)
    entries["problem"] = problem

    def save_edited():
        name = entries["client_name"].get().strip()
        device = entries["device"].get().strip()

        if not name or not device:
            messagebox.showwarning("Не заполнено", "Обязательно укажите клиента и устройство.")
            return

        price_text = entries["price"].get().strip()
        try:
            price = float(price_text.replace(",", ".")) if price_text else 0
        except ValueError:
            messagebox.showwarning("Ошибка", "Цена должна быть числом, например 1500 или 1500.50")
            return

        conn.execute(
            "UPDATE orders SET client_name=?, client_phone=?, device=?, problem=?, price=? WHERE id=?",
            (name, entries["client_phone"].get().strip(),
             device, entries["problem"].get("1.0", "end").strip(), price, order_id)
        )
        conn.commit()
        win.destroy()
        load_orders(current_filter.get())

    tk.Button(win, text="Сохранить изменения", command=save_edited,
              width=18, bg="#4CAF50", fg="white").grid(row=row + 1, column=0, columnspan=2, pady=15)

    entries["client_name"].focus()

def save_order(win, entries):
    name = entries["client_name"].get().strip()
    device = entries["device"].get().strip()

    if not name or not device:
        messagebox.showwarning("Не заполнено", "Обязательно укажите клиента и устройство.")
        return

    price_text = entries["price"].get().strip()
    try:
        price = float(price_text.replace(",", ".")) if price_text else 0
    except ValueError:
        messagebox.showwarning("Ошибка", "Цена должна быть числом, например 1500 или 1500.50")
        return

    conn.execute(
        "INSERT INTO orders (client_name, client_phone, device, problem, price) VALUES (?, ?, ?, ?, ?)",
        (name, entries["client_phone"].get().strip(),
         device, entries["problem"].get("1.0", "end").strip(), price)
    )
    conn.commit()
    win.destroy()
    load_orders(current_filter.get())

def open_new_order():
    win = tk.Toplevel(root)
    win.title("Новая заявка")
    win.geometry("420x380")
    win.grab_set()

    labels = {
        "client_name": "Клиент (ФИО):",
        "client_phone": "Телефон:",
        "device": "Устройство (модель):",
        "price": "Цена (руб.):",
    }
    entries = {}
    row = 0
    for key, text in labels.items():
        tk.Label(win, text=text).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        entry = tk.Entry(win, width=30)
        entry.grid(row=row, column=1, padx=10, pady=5)
        entries[key] = entry
        row += 1

    tk.Label(win, text="Неисправность:").grid(row=row, column=0, sticky="nw", padx=10, pady=5)
    problem = tk.Text(win, width=30, height=4)
    problem.grid(row=row, column=1, padx=10, pady=5)
    entries["problem"] = problem

    tk.Button(win, text="Сохранить", command=lambda: save_order(win, entries),
              width=15, bg="#4CAF50", fg="white").grid(row=row + 1, column=0, columnspan=2, pady=15)

    entries["client_name"].focus()

# --- Главное окно ---
root = tk.Tk()
root.title("Учёт заявок — мастерская")
root.geometry("900x560")

tk.Label(root, text="Заявки на ремонт", font=("Arial", 16, "bold")).pack(pady=10)

# Фильтр по статусу
filter_frame = tk.Frame(root)
filter_frame.pack()
tk.Label(filter_frame, text="Фильтр по статусу:").pack(side="left", padx=(0, 10))
current_filter = ttk.Combobox(filter_frame, values=STATUSES, state="readonly", width=15)
current_filter.current(0)  # "Все"
current_filter.pack(side="left")
current_filter.bind("<<ComboboxSelected>>", lambda e: load_orders(current_filter.get()))

columns = ("id", "client", "phone", "device", "status", "price", "date")
headers = ("№", "Клиент", "Телефон", "Устройство", "Статус", "Цена", "Дата")

tree = ttk.Treeview(root, columns=columns, show="headings", height=14)
for col, header in zip(columns, headers):
    tree.heading(col, text=header)
    tree.column(col, width=120, anchor="w")

tree.column("id", width=40, anchor="center")
tree.column("status", width=100, anchor="center")
tree.column("price", width=80, anchor="e")

tree.pack(padx=10, pady=5, fill="both", expand=True)

scroll = ttk.Scrollbar(root, command=tree.yview)
tree.configure(yscrollcommand=scroll.set)
scroll.place(relx=0.99, rely=0.18, relheight=0.65, anchor="ne")

buttons = tk.Frame(root)
buttons.pack(pady=8)

tk.Button(buttons, text="＋ Новая заявка", command=open_new_order,
          width=13, bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
tk.Button(buttons, text="Редактировать", command=edit_order,
          width=13, bg="#FFC107", fg="black").pack(side="left", padx=5)
tk.Button(buttons, text="Сменить статус", command=change_status,
          width=13, bg="#FF9800", fg="white").pack(side="left", padx=5)
tk.Button(buttons, text="Удалить", command=delete_order,
          width=10, bg="#f44336", fg="white").pack(side="left", padx=5)

load_orders()
root.mainloop()
