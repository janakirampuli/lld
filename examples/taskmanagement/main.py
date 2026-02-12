'''
Docstring for examples.taskmanagement.main

user -> id, name, email
task -> id, title, description, due date, priority, status, assigned user, assigned by
task status -> enum (open, closed, resolved)
taskmanager to manage


'''

from enum import Enum, auto
from datetime import datetime, timedelta
from typing import Optional, Dict
import threading
import uuid
import time

class User:
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name
    
class TaskStatus(Enum):
    OPEN = auto()
    CLOSED = auto()
    RESOLVED = auto()

class TaskPriority(Enum):
    HIGH = 0
    MEDIUM = 1
    LOW = 2

class Task:
    def __init__(self, title: str, assigned_user: User, assigned_by: User, description: Optional[str]="", due_date: Optional[str]="", priority: Optional[TaskPriority]=TaskPriority.MEDIUM):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.assigned_user = assigned_user
        self.assigned_by = assigned_by
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def set_description(self, description: str):
        self.description = description

    def set_due_date(self, due_date: str):
        self.due_date = due_date

    def set_priority(self, priority: TaskPriority):
        self.priority = priority

class TaskManager:
    instance = None
    lock = threading.Lock()

    def __new__(cls):
        if cls.instance == None:
            with cls.lock:
                if cls.instance == None:
                    cls.instance = super(TaskManager, cls).__new__(cls)
                    cls.instance.initialize()
        return cls.instance
    
    def initialize(self):
        self.tasks: Dict[str, Task] = {}
        self.data_lock = threading.Lock()

    def create_task(self, title: str, assigned_user: User, assigned_by: User, description: Optional[str]="", due_date: Optional[str]="", priority: Optional[TaskPriority]=TaskPriority.MEDIUM):
        with self.data_lock:
            task = Task(title, assigned_user, assigned_by, description, due_date, priority)

            self.tasks[task.id] = task
            print(f'Created task {task.title}')
            return task
    
    def update_task(self, task_id: str, **kwargs):
        with self.data_lock:
            task = self.tasks.get(task_id)
            if not task:
                print(f"[ERROR] task doesn't exist")

            for k, v in kwargs.items():
                if hasattr(task, k):
                    setattr(task, k, v)
            
            task.updated_at = datetime.now()
            print(f"Updated task {task.title}")
            return task
        
    def delete_task(self, task_id: str):
        with self.data_lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                print(f"deleted task {task_id}")
                return True
            return False

    def search_tasks(self, query: str = None, status: TaskStatus = None, priority: TaskPriority = None, assigned_user: User = None):
        with self.data_lock:
            results = []
            for task in self.tasks.values():
                match = True
                if query and (query.lower() not in task.title.lower() and query.lower() not in task.description.lower()):
                    match = False
                if status and task.status != status:
                    match = False
                if priority and task.priority != priority:
                    match = False
                if assigned_user and task.assigned_user != assigned_user:
                    match = False
                
                if match:
                    results.append(task)
            return results

def demo():
    tm = TaskManager()
    u1 = User("janaki")
    u2 = User("foo")
    task = tm.create_task("task-1", assigned_user=u1, assigned_by=u2, priority=TaskPriority.HIGH)
    tm.update_task(task_id=task.id, due_date = datetime.now() + timedelta(days=2))

    tasks = tm.search_tasks(priority=TaskPriority.LOW)
    for t in tasks:
        print({t.title})

    def worker_task(user1: User, user2: User, title: str):
        tm.create_task(title=title, assigned_by=user1, assigned_user=user2, due_date=datetime.now() + timedelta(days=1), priority=TaskPriority.LOW)
        time.sleep(1)

    threads = []
    for i in range(5):
        t = threading.Thread(target=worker_task, args=(u1, u2, f'task thread {i}'))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

if __name__ == "__main__":
    demo()
        

