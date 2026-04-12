'''

requirements:
1. allow users to create, read, update and delete tasks
2. task should have title, descripton, due date, priority, status
3. users should be able to assign task to other users and set reminders
4. concurrent access to tasks and ensure data consistency


core entities:

User
Task
TaskHistory
Reminder
SearchCriteria


enums:

TaskStatus: PENDING, IN_PROGRESS, COMPLETED, DELETED
TaskPriority: LOW, MEDIUM, HIGH, CRITICAL
ReminderStatus: ACTIVE, TRIGGERED, CANCELLED
ChangeType: CREATED, UPDATED, STATUS_CHANGED, ASSIGNED, DELETED, COMPLETED

classes and interfaces:

TaskRepository(ABC):
- save(task)
- get_by_id(task_id)
- delete(task_id)
- search(citeria)
- get_tasks_by_user(user_id)

NotificationService(ABC):
- send(user_id, message)

ReminderService(ABC):
- schedule(reminder)
- cancel(reminder_id)

User:
- user_id
- created_tasks
- assigned_tasks

Task:
- task_id
- title
- due_date
- priority
- status
- created_by
- assigned_to
- reminders
- history
- created_at
- updated_at

TaskHistory:
- history_id
- task_id
- change_type
- field_change
- old_value
- new_value
- changed_by
- changed_at

Reminder:
- reminder_id
- task_id
- user_id
- remind_at
- status

SearchCriteria:
- priority
- status
- assigned_to
- due_before
- due_after
- created_by
- keyword
- sort_by
- sort_order

TaskManagerSystem:
- task_service
- user_service
- notification_service
- reminder_service

UserService:
- users: dict[str, User]
- register(name, email)
- get_user(user_id)

TaskService:
- task_repo
- task_locks: dict[str, threading.Lock]
- create_task(user_id, title, description, due_date, priority)
- update_task(user_id, task_id, **fields)
- change_status(user_id, task_id, new_status)
- assign_task(assigner_id, task_id, assignee_id)
- delete_task(user_id, task_id)
- add_reminder(user_id, task_id, remind_at)
- mark_completed(user_id, task_id)
- get_task_history(task_id)
- search_tasks(criteria)


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
        

