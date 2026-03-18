import tkinter as tk
from tkinter import ttk, messagebox
from openpyxl import Workbook
import sqlite3
import os

DB_NAME = "attendance.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)


        c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("admin","admin"))

        c.execute("SELECT COUNT(*) FROM students")
        if c.fetchone()[0] == 0:
            students = load_students_from_files()
            if students:
                c.executemany("INSERT INTO students (name, gender, status) VALUES (?,?,?)", students)

        conn.commit()

def load_students_from_files():
    files = ["Student_3A.txt","Student_3B.txt","Student_3C.txt","Student_3D.txt"]
    students = []
    for f in files:
        if os.path.exists(f):
            with open(f,"r") as file:
                for line in file:
                    name = line.strip()
                    if name:
                        gender = "Male" if "A" in f or "C" in f else "Female"
                        students.append((name, gender, "Absent"))
    return students

def verify_user(username,password):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",(username,password))
        return c.fetchone()

def fetch_students():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM students")
        return c.fetchall()

def add_student(name,gender,status):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO students (name, gender, status) VALUES (?,?,?)",(name,gender,status))
        conn.commit()

def update_student(student_id,name,gender,status):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("UPDATE students SET name=?, gender=?, status=? WHERE id=?",(name,gender,status,student_id))
        conn.commit()

def delete_student(student_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM students WHERE id=?",(student_id,))
        conn.commit()

def export_to_excel():
    data = fetch_students()
    if not data:
        messagebox.showwarning("No Data", "No records to export!")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"

    headers = ["ID", "Name", "Gender", "Status"]
    ws.append(headers)

    for row in data:
        ws.append(row)

    filename = "attendance.xlsx"
    try:
        wb.save(filename)
        messagebox.showinfo("Success", f"Exported as {filename}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def setup_ui(root):
    global name_var, gender_var, status_var, selected_id, tree

    name_var = tk.StringVar()
    gender_var = tk.StringVar()
    status_var = tk.StringVar()
    selected_id = None

    root.title("Dashboard")
    root.geometry("1100x500")
    root.configure(bg="white")
    
    icon = tk.PhotoImage(file="./icons/student_icon.png")
    root.iconphoto(False, icon)

    tk.Label(root,text="STUDENT ATTENDANCE SYSTEM",font=("Arial",20,"bold"),fg="black",bg="skyblue",pady=10).pack(fill=tk.X)

    frame = tk.LabelFrame(root,text="Manage Attendance",font=("Arial",14,"bold"),padx=20,pady=20)
    frame.place(x=20,y=80,width=350,height=300)

    tk.Label(frame, text="Name:", font=("Arial", 12)).grid(row=0, column=0, pady=5)
    tk.Entry(frame, textvariable=name_var, width=25, font=("Arial", 12)).grid(row=0, column=1, padx=10, pady=5)

    tk.Label(frame, text="Gender:", font=("Arial", 12)).grid(row=1, column=0, pady=5)
    ttk.Combobox(frame, textvariable=gender_var, values=("Male","Female"),state="readonly", font=("Arial", 12)).grid(row=1, column=1, padx=10, pady=5)

    tk.Label(frame, text="Status:", font=("Arial", 12)).grid(row=2, column=0, pady=5)
    ttk.Combobox(frame, textvariable=status_var, values=("Present","Absent"),state="readonly", font=("Arial", 12)).grid(row=2, column=1, padx=10, pady=5)

    btn_frame = tk.Frame(frame)
    btn_frame.grid(row=3,column=0,columnspan=2,pady=20)

    style = {"width":10, "font":("Arial",11,"bold"), "cursor":"hand2", "bd":0, "relief":"ridge"}

    tk.Button(btn_frame, text="Add", command=add_record, bg="#4CAF50", fg="white", **style).grid(row=0, column=0, padx=5, pady=5)
    tk.Button(btn_frame, text="Update", command=update_record, bg="#2196F3", fg="white", **style).grid(row=0, column=1, padx=5, pady=5)
    tk.Button(btn_frame, text="Delete", command=delete_record, bg="#f44336", fg="white", **style).grid(row=0, column=2, padx=5, pady=5)
    tk.Button(btn_frame, text="Export", command=export_to_excel, bg="#FF9800", fg="black", **style).grid(row=1, column=1, pady=10)

    table_frame = tk.Frame(root)
    table_frame.place(x=400, y=80, width=650, height=350)

    scrollbar = tk.Scrollbar(table_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(
        table_frame,
        columns=("ID","NAME","GENDER","STATUS"),
        show="headings",
        yscrollcommand=scrollbar.set
    )

    scrollbar.config(command=tree.yview)

    tree.heading("ID", text="ID")
    tree.column("ID", width=60, anchor="center")

    tree.heading("NAME", text="NAME")
    tree.column("NAME", width=250, anchor="w")

    tree.heading("GENDER", text="GENDER")
    tree.column("GENDER", width=120, anchor="center")

    tree.heading("STATUS", text="STATUS")
    tree.column("STATUS", width=120, anchor="center")

    tree.tag_configure("present", foreground="green")
    tree.tag_configure("absent", foreground="red")

    def insert_student(id, name, gender, status):
        tag = "present" if status == "Present" else "absent"
        tree.insert("", "end", values=(id, name, gender, status), tags=(tag,))

    tree.pack(fill=tk.BOTH, expand=True)
    tree.bind("<ButtonRelease-1>", select_record)

    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
    style.configure("Treeview", font=("Arial", 11))
    load_data()

def load_data():
    tree.delete(*tree.get_children())
    for row in fetch_students():
        tag = "present" if row[3] == "Present" else "absent"
        tree.insert("", tk.END, values=row, tags=(tag,))

def add_record():
    if name_var.get():
        add_student(name_var.get(),gender_var.get(),status_var.get())
        load_data()
        clear_form()

def update_record():
    global selected_id
    if selected_id:
        update_student(selected_id,name_var.get(),gender_var.get(),status_var.get())
        load_data()
        clear_form()

def delete_record():
    global selected_id
    if selected_id:
        delete_student(selected_id)
        load_data()
        clear_form()

def select_record(event):
    global selected_id
    selected = tree.selection()
    if selected:
        data = tree.item(selected,"values")
        selected_id = int(data[0])
        name_var.set(data[1])
        gender_var.set(data[2])
        status_var.set(data[3])

def clear_form():
    global selected_id
    name_var.set("")
    gender_var.set("Male")
    status_var.set("Absent")
    selected_id = None

def login(root):
    if verify_user(username_var.get(), password_var.get()):
        messagebox.showinfo("Login","Access Granted")
        root.destroy()
        open_main_app()
    else:
        messagebox.showerror("Error","Invalid credentials!!")

def login_ui(root):
    global username_var, password_var
    username_var = tk.StringVar()
    password_var = tk.StringVar()

    root.title("Login Account")
    root.geometry("450x250")
    root.configure(bg="white")

    icon = tk.PhotoImage(file="./icons/login_icon.png")
    root.iconphoto(False, icon)

    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    tk.Label(root, text="Login Account", font=("Arial", 18, "bold"),fg="black", bg="skyblue", pady=10).grid(row=0, column=0, columnspan=2, sticky="ew")

    tk.Label(root, text="Username:", font=("Helvetica", 12), bg="white").grid(row=1, column=0, padx=10, pady=15, sticky="ew")
    user_entry = tk.Entry(root, textvariable=username_var, font=("Helvetica", 12))
    user_entry.grid(row=1, column=1, padx=10, pady=15, ipady=5, sticky="ew")
    user_entry.config(highlightthickness=1, highlightbackground="gray", highlightcolor="gray")
    add_placeholder(user_entry, "Username")

    tk.Label(root, text="Password:", font=("Helvetica", 12), bg="white").grid(row=2, column=0, padx=10, pady=5, sticky="ew")
    pwd_entry = tk.Entry(root, textvariable=password_var, font=("Helvetica", 12), show="*")
    pwd_entry.grid(row=2, column=1, padx=10, pady=5, ipady=5, sticky="ew")
    pwd_entry.config(highlightthickness=1, highlightbackground="gray", highlightcolor="gray")
    add_placeholder(pwd_entry, "Password")
    
    tk.Button(root, text="Login", command=lambda: login(root),bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"),width=20, cursor="hand2", relief="flat", bd=0, activeforeground="white", activebackground="#4CAF50").grid(row=3, column=0, columnspan=2, pady=20)

def add_placeholder(entry, placeholder):
    entry.insert(0, placeholder)
    entry.config(fg="grey")

    def on_focus_in(event):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.config(fg="black")

    def on_focus_out(event):
        if entry.get() == "":
            entry.insert(0, placeholder)
            entry.config(fg="grey")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

def open_main_app():
    main = tk.Tk()
    setup_ui(main)
    main.mainloop()

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    login_ui(root)
    root.mainloop()