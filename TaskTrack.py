import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import Calendar
import datetime 
import json
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import time

class ToDoList:
    def __init__(self, root):
        self.root = root
        self.root.title("TaskTrack")
        self.root.geometry("1200x600")
        self.frames = {}
        self.root.rowconfigure(0, weight=1)
        self.setup_sidebar()  # Postavite sidebar sa dugmićima za navigaciju

        # Inicijalizacija frame-ova
        for F in (HomeFrame, NewTaskFrame,TasksFrame):
            frame = F(parent=self.root, controller=self)
            self.frames[F.__name__] = frame  # Čuva frame koristeći ime klase kao ključ
            frame.grid(row=0, column=1, sticky="nsew")  # Frame-ovi se prikazuju desno od sidebar-a

        self.show_frame("HomeFrame")  # Prikaz početnog frame-a

    def setup_sidebar(self):
        sidebar = tk.Frame(self.root, width=200, bg='#26580F', relief='sunken')
        # Grid pozicioniranje sa sticky opcijom 'ns' da se proteže od vrha do dna
        sidebar.grid(row=0, column=0, sticky='ns', rowspan=1)

        buttons = {
            "Home": "HomeFrame",
            "New Task": "NewTaskFrame",
            "Tasks":"TasksFrame"
        }
        for text, frame_name in buttons.items():
            button = tk.Button(sidebar, text=text, command=lambda f=frame_name: self.show_frame(f),
                               bg="#26580F", fg="white", width=18, height=2)
            button.pack(padx=10, pady=10, fill='y')

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()  # Dizanje izabranog frame-a na vrh steka

class HomeFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_home_widgets()
        self.load_alarms()
        self.start_alarm_thread()

    def setup_home_widgets(self):
        self.task_list_frame = tk.Frame(self)
        self.task_list_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)

        self.calendar_frame = tk.Frame(self)
        self.calendar_frame.grid(row=0, column=1, sticky='nsew', padx=20, pady=20)

        self.cal = Calendar(self.calendar_frame, selectmode='day', year=datetime.datetime.now().year, month=datetime.datetime.now().month, day=datetime.datetime.now().day)
        self.cal.pack(padx=10, pady=10)
        self.cal.bind("<<CalendarSelected>>", self.update_task_list)

        self.task_list_label = tk.Label(self.task_list_frame, text="Tasks for Today:", font=("Arial", 14))
        self.task_list_label.pack()

        self.task_list_box = tk.Listbox(self.task_list_frame, width=50, height=10)
        self.task_list_box.pack(pady=10)

        self.complete_task_button = tk.Button(self.task_list_frame, text="Complete Task", command=self.complete_task)
        self.complete_task_button.pack(pady=10)

        # Setup for alarm time entry with comboboxes
        self.hour_var = tk.StringVar()
        self.minute_var = tk.StringVar()
        self.hour_combobox = ttk.Combobox(self.task_list_frame, textvariable=self.hour_var, values=[f"{i:02d}" for i in range(24)], width=3, state='readonly')
        self.hour_combobox.pack(side=tk.LEFT, padx=5)
        self.minute_combobox = ttk.Combobox(self.task_list_frame, textvariable=self.minute_var, values=[f"{i:02d}" for i in range(60)], width=3, state='readonly')
        self.minute_combobox.pack(side=tk.LEFT, padx=5)

        self.set_alarm_button = tk.Button(self.task_list_frame, text="Set Alarm", command=self.add_alarm)
        self.set_alarm_button.pack(side=tk.LEFT, padx=10)

        self.alarm_list_box = tk.Listbox(self.task_list_frame, width=15, height=4)
        self.alarm_list_box.pack(pady=10)
        self.delete_alarm_button = tk.Button(self.task_list_frame, text="Delete Alarm", command=self.delete_alarm)
        self.delete_alarm_button.pack()

        self.update_task_list(None)

    def load_alarms(self):
        try:
            with open('alarms.json', 'r') as file:
                data = json.load(file)
                self.alarms = data["alarms"]
        except FileNotFoundError:
            self.alarms = []
        self.refresh_alarm_list()

    def save_alarms(self):
        with open('alarms.json', 'w') as file:
            json.dump({"alarms": self.alarms}, file)
        self.refresh_alarm_list()

    def add_alarm(self):
        time_str = f"{self.hour_var.get()}:{self.minute_var.get()}"
        if time_str and time_str not in self.alarms:
            self.alarms.append(time_str)
            self.save_alarms()

    def delete_alarm(self):
        selected_index = self.alarm_list_box.curselection()
        if selected_index:
            self.alarms.pop(selected_index[0])
            self.save_alarms()

    def refresh_alarm_list(self):
        self.alarm_list_box.delete(0, tk.END)
        for alarm in self.alarms:
            self.alarm_list_box.insert(tk.END, alarm)

    def start_alarm_thread(self):
        thread = threading.Thread(target=self.check_alarms)
        thread.daemon = True
        thread.start()

    def check_alarms(self):
        
        while True:
            now = datetime.datetime.now().strftime("%H:%M")
            if now in self.alarms:
                self.check_tasks()
            time.sleep(60)
    
    def check_tasks(self):
        today = datetime.datetime.now().strftime("%m/%d/%y")
        today = today.split('/')
        today = '/'.join([str(int(part)) for part in today])
        
        try:
            with open('tasks.json', 'r') as file:
                tasks = json.load(file)
            unfinished_tasks = [task for task in tasks if not task['Complete']and task['date'] == today]
            if unfinished_tasks:
                message = f"You have {len(unfinished_tasks)} unfinished tasks!"
                print(message)  # Ispisuje poruku o nedovršenim zadacima
                tk.messagebox.showinfo("Alarm Alert", message)
            else:
                tk.messagebox.showinfo("Bravo, nema nedovršenih taskova", message)  # Ispisuje poruku ako nema nedovršenih zadataka
        except FileNotFoundError:
            print("Tasks file not found, no tasks to check.")  # Ispisuje poruku ako datoteka nije pronađena

    def update_task_list(self, event):
        selected_date = self.cal.get_date()
        self.task_list_box.delete(0, tk.END)
        try:
            with open('tasks.json', 'r') as file:
                tasks = json.load(file)
            self.task_index_map = {}
            list_index = 0
            for i, task in enumerate(tasks):
                if task["date"] == selected_date and not task["Complete"]:
                    display_text = f"{task['time']} - {task['name']} - {task['description']}"
                    self.task_list_box.insert(tk.END, display_text)
                    self.task_index_map[list_index] = i
                    list_index += 1
        except FileNotFoundError:
            pass

    def complete_task(self):
        selection = self.task_list_box.curselection()
        if selection:
            list_index = selection[0]
            task_index = self.task_index_map[list_index]
            with open('tasks.json', 'r') as file:
                tasks = json.load(file)
            if not tasks[task_index]["Complete"]:
                tasks[task_index]["Complete"] = True
                with open('tasks.json', 'w') as file:
                    json.dump(tasks, file, indent=4)
                self.update_task_list(None)
                messagebox.showinfo("Task Complete", "Task marked as complete.")
        else:
            messagebox.showinfo("No Selection", "Please select a task to complete.")

# Assume the rest of the class definitions and main app initialization are the same as previously defined.

class NewTaskFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_new_task_widgets()

    def setup_new_task_widgets(self):
        self.name_entry = tk.Entry(self, width=50)
        self.description_entry = tk.Text(self, height=4, width=50)
        self.importance_var = tk.StringVar(value="Normal")
        self.hour_var = tk.StringVar(value="12")
        self.minute_var = tk.StringVar(value="00")
        self.frequency_var = tk.StringVar(value="One-time")
        self.cal = Calendar(self, selectmode='day', year=2024, month=5, day=15)
        # First column entry frame
        entry_frame_left = tk.Frame(self)
        entry_frame_left.grid(row=0, column=0, sticky='nw', padx=20, pady=10)

        # Second column entry frame
        entry_frame_right = tk.Frame(self)
        entry_frame_right.grid(row=0, column=1, sticky='nw', padx=20, pady=10)

        # Task Name
        tk.Label(entry_frame_left, text="Task Name:", font=("Arial", 14)).grid(row=0, column=0, sticky='w')
        self.name_entry = tk.Entry(entry_frame_left, width=25)
        self.name_entry.grid(row=1, column=0, sticky='w')

        # Description
        tk.Label(entry_frame_left, text="Description:", font=("Arial", 14)).grid(row=2, column=0, sticky='w')
        self.description_entry = tk.Text(entry_frame_left, height=4, width=30)
        self.description_entry.grid(row=3, column=0, sticky='w')

        # Importance
        tk.Label(entry_frame_left, text="Importance:", font=("Arial", 14)).grid(row=4, column=0, sticky='w')
        self.importance_options = ["Low", "Normal", "Important"]
        self.importance_var = tk.StringVar(value=self.importance_options[1])
        self.importance_menu = ttk.Combobox(entry_frame_left, textvariable=self.importance_var, values=self.importance_options, width=15, state='readonly')
        self.importance_menu.grid(row=5, column=0, sticky='w')

        # Select Date
        tk.Label(entry_frame_right, text="Select Date:", font=("Arial", 14)).grid(row=0, column=0, sticky='w')
        self.cal = Calendar(entry_frame_right, selectmode='day', year=2024, month=5, day=15)
        self.cal.grid(row=1, column=0, sticky='w')

        # Due Time
        tk.Label(entry_frame_right, text="Due Time:", font=("Arial", 14)).grid(row=2, column=0, sticky='w')
        self.time_frame = tk.Frame(entry_frame_right)
        self.time_frame.grid(row=3, column=0, sticky='w')
        self.hour_var = tk.StringVar(value="12")
        self.minute_var = tk.StringVar(value="00")
        self.hour_combobox = ttk.Combobox(self.time_frame, textvariable=self.hour_var, values=[f"{i:02d}" for i in range(24)], width=3)
        self.hour_combobox.pack(side='left')
        tk.Label(self.time_frame, text=":", font=("Arial", 14)).pack(side='left')
        self.minute_combobox = ttk.Combobox(self.time_frame, textvariable=self.minute_var, values=[f"{i:02d}" for i in range(60)], width=3)
        self.minute_combobox.pack(side='left')

        # Frequency
        tk.Label(entry_frame_right, text="Frequency:", font=("Arial", 14)).grid(row=4, column=0, sticky='w')
        self.frequency_var = tk.StringVar(value="One-time")
        self.frequency_options = ["One-time", "Daily", "Weekly", "Monthly"]
        self.frequency_menu = ttk.Combobox(entry_frame_right, textvariable=self.frequency_var, values=self.frequency_options, width=15, state='readonly')
        self.frequency_menu.grid(row=5, column=0, sticky='w')

        self.add_task_button = tk.Button(self, text="Add Task", command=self.save_task_to_json)
        self.add_task_button.grid(row=6, column=0, sticky='ew', padx=10, pady=10)
        
       
        self.configure_column_widths()
    
    def save_task_to_json(self):
        task_data = {
            "name": self.name_entry.get(),
            "description": self.description_entry.get("1.0", tk.END).strip(),
            "importance": self.importance_var.get(),
            "date": self.cal.get_date(),
            "time": f"{self.hour_var.get()}:{self.minute_var.get()}",
            "frequency": self.frequency_var.get(),
            "Complete":False
        }

        try:
            with open('tasks.json', 'r') as file:
                tasks = json.load(file)
        except FileNotFoundError:
            tasks = []

        tasks.append(task_data)

        with open('tasks.json', 'w') as file:
            json.dump(tasks, file, indent=4)

        messagebox.showinfo("Success", "Task added successfully!")  # Prikazuje pop-up obaveštenje o uspehu

        # Resetovanje polja za unos
        self.name_entry.delete(0, tk.END)
        self.description_entry.delete('1.0', tk.END)
        self.importance_var.set("Normal")
        self.hour_var.set("12")
        self.minute_var.set("00")
        self.frequency_var.set("One-time")
        #self.cal.set_date(datetime.datetime.now())
        
    def configure_column_widths(self):
        self.grid_columnconfigure(0, weight=1)  # Omogućava širenje prve kolone u skladu sa sadržajem
        self.grid_columnconfigure(1, weight=3)  # Ostavlja više prostora u drugoj koloni za druge widgete

class TasksFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_tasks_widgets()

    def setup_tasks_widgets(self):
        # Labela "Tasks" iznad liste
        self.tasks_label = tk.Label(self, text="Tasks", font=("Arial", 16))
        self.tasks_label.pack(pady=(10, 5))

        self.task_list_box = tk.Listbox(self, width=70, height=10)
        self.task_list_box.pack(padx=20, pady=10)

        # Frame za smještanje dugmadi
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=(5, 10))

        self.delete_button = tk.Button(self.button_frame, text="Delete Task", command=self.delete_task)
        self.delete_button.pack(side=tk.LEFT, padx=10)

        self.edit_button = tk.Button(self.button_frame, text="Edit Task", command=self.edit_task)
        self.edit_button.pack(side=tk.LEFT, padx=10)

        self.load_tasks()

    def load_tasks(self):
        try:
            with open('tasks.json', 'r') as file:
                self.tasks = json.load(file)
        except FileNotFoundError:
            self.tasks = []

        self.task_list_box.delete(0, tk.END)
        for task in self.tasks:
            task_info = f"{task['name']} - {task['description']} - {task['date']} {task['time']} - {'Complete' if task['Complete'] else 'Pending'} - {task['frequency']}"
            self.task_list_box.insert(tk.END, task_info)

    def delete_task(self):
        selection = self.task_list_box.curselection()
        if selection:
            task_index = selection[0]
            self.tasks.pop(task_index)
            with open('tasks.json', 'w') as file:
                json.dump(self.tasks, file, indent=4)
            self.load_tasks()
            messagebox.showinfo("Success", "Task deleted successfully.")
        else:
            messagebox.showinfo("Error", "Please select a task to delete.")

    def edit_task(self):
        selection = self.task_list_box.curselection()
        if selection:
            task_index = selection[0]
            task = self.tasks[task_index]
            self.open_edit_window(task, task_index)

    def open_edit_window(self, task, index):
        edit_window = tk.Toplevel(self)
        edit_window.title("Edit Task")

        tk.Label(edit_window, text="Name:").grid(row=0, column=0)
        name_entry = tk.Entry(edit_window)
        name_entry.grid(row=0, column=1)
        name_entry.insert(0, task["name"])

        tk.Label(edit_window, text="Description:").grid(row=1, column=0)
        description_entry = tk.Entry(edit_window)
        description_entry.grid(row=1, column=1)
        description_entry.insert(0, task["description"])

        tk.Label(edit_window, text="Date:").grid(row=2, column=0)
        date_entry = tk.Entry(edit_window)
        date_entry.grid(row=2, column=1)
        date_entry.insert(0, task["date"])

        tk.Label(edit_window, text="Time:").grid(row=3, column=0)
        time_entry = tk.Entry(edit_window)
        time_entry.grid(row=3, column=1)
        time_entry.insert(0, task["time"])

        tk.Label(edit_window, text="Frequency:").grid(row=4, column=0)
        frequency_var = tk.StringVar()
        frequency_combobox = ttk.Combobox(edit_window, textvariable=frequency_var, state='readonly')
        frequency_combobox['values'] = ('One-time', 'Daily', 'Weekly', 'Monthly')
        frequency_combobox.grid(row=4, column=1)
        frequency_combobox.set(task["frequency"])

        save_button = tk.Button(edit_window, text="Save Changes",
                                command=lambda: self.save_changes(
                                    name_entry.get(), description_entry.get(), 
                                    date_entry.get(), time_entry.get(), 
                                    frequency_combobox.get(), index, edit_window))
        save_button.grid(row=5, column=1, pady=10)

    def save_changes(self, name, description, date, time, frequency,index, edit_window):
        task = self.tasks[index]
        task["name"] = name
        task["description"] = description
        task["date"] = date  # Ažuriranje datuma direktno iz kalendara
        task["time"] = time
        task["frequency"] = frequency
        with open('tasks.json', 'w') as file:
            json.dump(self.tasks, file, indent=4)
        edit_window.destroy()
        self.load_tasks()
        messagebox.showinfo("Success", "Task updated successfully.")


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_tasks, 'cron', hour=0, minute=0)  # Executes daily at midnight
    scheduler.start()

def update_tasks():
    try:
        with open('last_update.json', 'r') as file:
            last_update_data = json.load(file)
        last_update = datetime.datetime.strptime(last_update_data['last_update'], "%Y-%m-%d")
    except (FileNotFoundError, KeyError):
        last_update = datetime.datetime.min  # Ako ne postoji datum, postavi na minimalni datum

    today = datetime.datetime.now()

    if last_update.date() != today.date():  # Provera da li je već ažurirano danas
        try:
            with open('tasks.json', 'r') as file:
                tasks = json.load(file)
        except FileNotFoundError:
            tasks = []

        modified = False
        for task in tasks:
            if task['frequency'] == 'Daily':
                task['Complete'] = False
                modified = True
            elif task['frequency'] == 'Weekly' and (today - last_update).days >= 7:
                task['Complete'] = False
                modified = True
            elif task['frequency'] == 'Monthly' and last_update.month < today.month:
                task['Complete'] = False
                modified = True

        if modified:
            with open('tasks.json', 'w') as file:
                json.dump(tasks, file, indent=4)
            with open('last_update.json', 'w') as file:
                # Ažuriranje datuma poslednjeg ažuriranja
                json.dump({'last_update': today.strftime("%Y-%m-%d")}, file, indent=4)


            
            
# Main application execution
start_scheduler()
update_tasks()
root = tk.Tk()
app = ToDoList(root)
root.mainloop()
