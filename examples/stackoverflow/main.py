'''
Docstring for examples.stackoverflow.main

tag -> id, tag
user -> id, name, reputation
post(abstarct) -> id, content, author, creation time
question(post) -> title, answers, comments, tags
answer(post) -> question, votes, comments

'''

from typing import Dict, List
import uuid
from datetime import datetime
import threading
from abc import ABC

class Tag:
    def __init__(self, tag: str):
        self._id = str(uuid.uuid4())
        self._tag = tag

class User:
    def __init__(self, name: str):
        self._id = str(uuid.uuid4())
        self._name: str = name
        self._reputation: int = 1000

    def get_id(self):
        return self._id

class Post(ABC):
    def __init__(self, content: str, author: User):
        self._id = str(uuid.uuid4())
        self._content = content
        self._author = author
        self._creation_date = datetime.now()

    def get_content(self):
        return self._content
    
    def get_id(self):
        return self._id



class Comment(Post):
    def __init__(self, content: str, author: User):
        super().__init__(content, author)
    

class Question(Post):
    def __init__(self, title: str, content: str, author: User):
        super().__init__(content, author)
        self._title: str = title
        self._answers: List[Answer] = []
        self._comments: List[Comment] = []
        self._tags: List[Tag] = []
    
    def get_title(self):
        return self._title
    
    def post_answer(self, answer: 'Answer'):
        self._answers.append(answer)

    def get_answers(self):
        return self._answers
    
    def post_comment(self, comment: Comment):
        self._comments.append(comment)

    def get_comments(self):
        return self._comments
    

class Answer(Post):
    def __init__(self, content: str, author: User, question: Question):
        super().__init__(content, author)
        self._question = question
        self._votes = 0
        self._comments: List[Comment] = []

    def up_vote(self):
        self._votes += 1

    def down_vote(self):
        self._votes -= 1

    def get_content(self):
        return self._content
    
    def get_votes(self):
        return self._votes
    
    def post_comment(self, comment: Comment):
        self._comments.append(comment)

    def get_comments(self):
        return self._comments


class StackOverflow:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StackOverflow, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.users: Dict[str, User] = {}
        self.questions: Dict[str, Question] = {}
        self.answers: Dict[str, Answer] = {}
        self.comments: Dict[str, Comment] = {}

    def create_user(self, user: User) -> bool:
        with self._lock:
            if self.users.get(user.get_id()):
                print(f"ERROR - user already exists")
                return None
            else:
                self.users[user.get_id()] = user
            return user
        
    def create_question(self, question: Question):
        with self._lock:
            self.questions[question.get_id()] = question
            return True
    
    def post_answer(self, question_id: str, answer: Answer):
        with self._lock:
            self.questions[question_id].post_answer(answer)
            self.answers[answer.get_id()] = answer

    def up_vote(self, answer_id: str):
        with self._lock:
            self.answers[answer_id].up_vote()

    def down_vote(self, answer_id: str):
        with self._lock:
            self.answers[answer_id].down_vote()

    def search(self, query: str):
        matches = []
        for question in self.questions.values():
            if query.lower() in question.get_content() or query.lower() in question.get_title():
                matches.append(question)
        return matches

    def post_comment(self, post_id: str, comment: Comment):
        with self._lock:
            post = self.find_post_by_id(post_id)
            post.post_comment(comment)

    def find_post_by_id(self, id: str):
        if id in self.questions:
            return self.questions[id]
        elif id in self.answers:
            return self.answers[id]
        print(f'post not found')

def demo():
    so = StackOverflow()

    u1 = so.create_user(User("foo"))
    u2 = so.create_user(User("bar"))

    q1 = Question("how to design stack overflow?", "the title", u1)
    so.create_question(q1)
    a1 = Answer("design a low level system by creating classes....", u2, q1)
    c1 = Comment('can you please be more precise in your answer???', u1)
    c2 = Comment("need more info", u2)

    so.post_answer(q1.get_id(), a1)
    so.post_comment(a1.get_id(), c1)
    so.post_comment(q1.get_id(), c2)
    so.down_vote(a1.get_id())

    matches: List[Question] = so.search("design")
    for q in matches:
        print(f'QUE : {q.get_title()}')
        for c in q.get_comments():
            print(f'--- {c.get_content()}')
        answers = q.get_answers()
        for a in answers:
            print(f'ANS : {a.get_content()} -- votes {a.get_votes()}')
            for c in a.get_comments():
                print(f'----  COM {c.get_content()}')

if __name__ == "__main__":
    demo()
    