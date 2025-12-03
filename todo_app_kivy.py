# todo_app_kivy.py
# Kivy To-Do / Productivity App (mobile GUI)
# Save as todo_app_kivy.py and run with `python todo_app_kivy.py` (or in PyDroid if Kivy is installed)

import os
import json
import csv
from datetime import datetime
from functools import partial

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button

TASKS_FILE = "tasks.json"

KV = """
<RootWidget>:
    orientation: "vertical"
    padding: 12
    spacing: 10

    BoxLayout:
        size_hint_y: None
        height: "40dp"
        spacing: 8

        TextInput:
            id: title_input
            hint_text: "Title"
            multiline: False

        TextInput:
            id: category_input
            hint_text: "Category"
            multiline: False
            size_hint_x: 0.6

    BoxLayout:
        size_hint_y: None
        height: "40dp"
        spacing: 8

        TextInput:
            id: due_input
            hint_text: "Due YYYY-MM-DD (optional)"
            multiline: False

        TextInput:
            id: priority_input
            hint_text: "Priority (High/Medium/Low)"
            multiline: False
            size_hint_x: 0.5

    BoxLayout:
        size_hint_y: None
        height: "40dp"
        spacing: 8

        Button:
            text: "Add Task"
            on_release: root.add_task()

        Button:
            text: "Refresh"
            on_release: root.refresh_tasks()

        Button:
            text: "Export CSV"
            on_release: root.export_csv_popup()

    Label:
        text: "Tasks"
        size_hint_y: None
        height: "26dp"
        bold: True

    ScrollView:
        do_scroll_x: False

        GridLayout:
            id: list_container
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            row_default_height: "56dp"
            spacing: 6
"""

class RootWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ensure file exists
        if not os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, "w") as f:
                json.dump([], f)
        self.refresh_tasks()

    # ---- storage ----
    def load_tasks(self):
        try:
            with open(TASKS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def save_tasks(self, tasks):
        with open(TASKS_FILE, "w") as f:
            json.dump(tasks, f, indent=4)

    # ---- utility ----
    def show_popup(self, title, message):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        content.add_widget(Label(text=message))
        btn = Button(text="OK", size_hint_y=None, height="38dp")
        content.add_widget(btn)
        p = Popup(title=title, content=content, size_hint=(0.85, 0.45))
        btn.bind(on_release=p.dismiss)
        p.open()

    # ---- app actions ----
    def add_task(self):
        title = self.ids.title_input.text.strip()
        category = self.ids.category_input.text.strip() or "General"
        due = self.ids.due_input.text.strip()
        priority = (self.ids.priority_input.text.strip().capitalize() or "Low")

        if not title:
            self.show_popup("Error", "Title cannot be empty.")
            return

        tasks = self.load_tasks()
        tasks.append({
            "title": title,
            "category": category,
            "due_date": due,
            "priority": priority,
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save_tasks(tasks)

        # clear inputs
        self.ids.title_input.text = ""
        self.ids.category_input.text = ""
        self.ids.due_input.text = ""
        self.ids.priority_input.text = ""

        self.refresh_tasks()

    def refresh_tasks(self):
        # clear the container
        container = self.ids.list_container
        container.clear_widgets()
        tasks = self.load_tasks()

        if not tasks:
            container.add_widget(Label(text="No tasks yet.", size_hint_y=None, height="40dp"))
            return

        for idx, t in enumerate(tasks, 1):
            row = BoxLayout(size_hint_y=None, height="56dp", spacing=8)

            status = "[✓]" if t.get("completed") else "[ ]"
            title_text = f"{idx}. {status} {t.get('title')} ({t.get('category')})\nDue: {t.get('due_date') or 'N/A'}  •  {t.get('priority')}"
            lbl = Label(text=title_text, halign="left", valign="middle")
            lbl.bind(size=lbl.setter('text_size'))
            row.add_widget(lbl)

            btn_complete = Button(text="Complete", size_hint_x=None, width="90")
            btn_complete.bind(on_release=partial(self.mark_complete, idx-1))
            row.add_widget(btn_complete)

            btn_delete = Button(text="Delete", size_hint_x=None, width="90")
            btn_delete.bind(on_release=partial(self.delete_task, idx-1))
            row.add_widget(btn_delete)

            container.add_widget(row)

    def mark_complete(self, index, *args):
        tasks = self.load_tasks()
        if 0 <= index < len(tasks):
            tasks[index]["completed"] = True
            self.save_tasks(tasks)
            self.refresh_tasks()
        else:
            self.show_popup("Error", "Invalid task index.")

    def delete_task(self, index, *args):
        tasks = self.load_tasks()
        if 0 <= index < len(tasks):
            title = tasks[index].get("title", "Task")
            tasks.pop(index)
            self.save_tasks(tasks)
            self.refresh_tasks()
            self.show_popup("Deleted", f"Removed: {title}")
        else:
            self.show_popup("Error", "Invalid task index.")

    def export_csv_popup(self):
        tasks = self.load_tasks()
        if not tasks:
            self.show_popup("Export", "No tasks to export.")
            return
        filename = f"tasks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(filename, "w", newline='') as csvfile:
                fieldnames = ["title","category","due_date","priority","completed","created_at"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for t in tasks:
                    writer.writerow({
                        "title": t.get("title"),
                        "category": t.get("category"),
                        "due_date": t.get("due_date"),
                        "priority": t.get("priority"),
                        "completed": t.get("completed"),
                        "created_at": t.get("created_at","")
                    })
            self.show_popup("Export", f"Exported to {filename}")
        except Exception as e:
            self.show_popup("Export Failed", str(e))


class TodoKivyApp(App):
    def build(self):
        Builder.load_string(KV)
        return RootWidget()


if __name__ == "__main__":
    TodoKivyApp().run()