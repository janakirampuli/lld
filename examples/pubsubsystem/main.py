import threading
from typing import Set, Dict
import concurrent.futures
import time

class Message:
    def __init__(self, msg: str):
        self.msg = msg

class Subscriber:
    def __init__(self, name: str):
        self.name = name

    def print(self, name: str, msg: Message):
        thread_name = threading.current_thread().name
        print(f"{thread_name} received from {name} : {msg.msg}")
        time.sleep(0.5)

class Topic:
    def __init__(self, name: str):
        self.name = name
        self.subscribers: Set[Subscriber] = set()
        self.lock = threading.Lock()

    def add_subscriber(self, subscriber: Subscriber):
        with self.lock:
            self.subscribers.add(subscriber)
            print(f"{subscriber.name} subscribed to {self.name}")

    def remove_subscriber(self, subscriber: Subscriber):
        with self.lock:
            if subscriber in self.subscribers:
                self.subscribers.remove(subscriber)

    def get_subscribers(self):
        return self.subscribers


class PubSubSystem:
    instance = None
    lock = threading.Lock()

    def __new__(cls):
        if cls.instance is None:
            with cls.lock:
                if cls.instance is None:
                    cls.instance = super(PubSubSystem, cls).__new__(cls)
                    cls.instance.initialize()
        return cls.instance
    
    def initialize(self):
        self.topics: Dict[str, Topic] = {}
        self.topic_lock = threading.Lock()

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix="worker")

    def create_topic(self, name: str):
        with self.topic_lock:
            if name not in self.topics:
                self.topics[name] = Topic(name)
                print(f"cretaed topic {name}")
            return self.topics[name]
        
    def subscribe(self, name: str, subscriber: Subscriber):
        topic = self.topics[name]
        if topic:
            topic.add_subscriber(subscriber)
        else:
            print(f"topic {name} doesn't exist")
        
    def publish(self, name: str, msg: Message):
        topic = self.topics[name]
        if topic:
            subs = topic.get_subscribers()

            for sub in subs:
                self.executor.submit(self.notify_subscriber, sub, name, msg)
        else:
            print(f"topic {name} doesn't exist")

    def notify_subscriber(self, subscriber: Subscriber, name: str, msg: Message):
        try:
            subscriber.print(name, msg)
        except Exception as e:
            print(f"failed to deliver to {subscriber.name} : {e}")

def demo():
    pss = PubSubSystem()

    pss.create_topic("a")
    pss.create_topic("b")

    s1 = Subscriber("foo")
    s2 = Subscriber("bar")

    pss.subscribe("a", s1)
    pss.subscribe("a", s2)
    pss.subscribe("b", s2)

    m1 = Message("msg in a")
    m2 = Message("msg in b")
    pss.publish("a", m1)
    pss.publish("b", m2)


if __name__ == "__main__":
    demo()