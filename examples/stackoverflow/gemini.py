'''
after feedback from gemini

'''

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from enum import Enum
import uuid
import threading
from datetime import datetime

class VoteType(Enum):
    UPVOTE = 1
    DOWNVOTE = -1

class User:
    def __init__(self, name: str, email: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.email = email
        self.reputation = 0

    def update_reputation(self, score: int):
        self.reputation += score

class Tag:
    def __init__(self, name: str):
        self.name = name

class Commentable(ABC):
    def __init__(self):
        self.comments: List['Comment'] = []

    def add_comment(self, comment: 'Comment'):
        self.comments.append(comment)
    
    def get_comments(self):
        return self.comments
    
class Votable(ABC):
    def __init__(self, author: User):
        self.author = author
        self.votes: Dict[str, VoteType] = {}

    def vote(self, user: User, type: VoteType):
        if user.id in self.votes:
            old_vote = self.votes[user.id]
            if old_vote == type:
                return
            self._revert_reputation(old_vote)
        self.votes[user.id] = type
        self._apply_reputation(type)

    def _apply_reputation(self, type: VoteType):
        if type == VoteType.UPVOTE:
            self.author.update_reputation(10)
        else:
            self.author.update_reputation(-5)

    def _revert_reputation(self, type: VoteType):
        if type == VoteType.UPVOTE:
            self.author.update_reputation(-10)
        else:
            self.author.update_reputation(5)

    def get_vote_count(self):
        return sum(v.value for v in self.votes.values())
    
class Comment(Commentable):
    def __init__(self, content: str, author: User):
        super().__init__()
        self.id = str(uuid.uuid4())
        self.content = content
        self.author = author
        self.creation_date = datetime.now()

class Question(Votable, Commentable):
    def __init__(self, title: str, content: str, author: User, tags: List[str]):
        Votable.__init__(self, author)
        Commentable.__init__(self)
        self.id = str(uuid.uuid4())
        self.title = title
        self.content = content
        self.tags = [Tag(t) for t in tags]
        self.answers: List['Answer'] = []
        self.creation_date = datetime.now()

    def add_answer(self, answer: 'Answer'):
        self.answers.append(answer)

class Answer(Votable, Commentable):
    def __init__(self, content: str, author: User, question_id: str):
        Votable.__init__(self, author)
        Commentable.__init__(self)
        self.id = str(uuid.uuid4())
        self.content = content
        self.question_id = question_id
        self.creation_date = datetime.now()

class StackOverflowSystem:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StackOverflowSystem, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.users: Dict[str, User] = {}
        self.questions: Dict[str, Question] = {}
        self.answers: Dict[str, Answer] = {}

    def register_user(self, name: str, email: str):
        user = User(name, email)
        self.users[user.id] = user
        return user
    
    def post_question(self, user: User, title: str, content: str, tags: List[str]):
        q = Question(title, content, user, tags)
        self.questions[q.id] = q
        return q
    
    def post_answer(self, user: User, question_id: str, content: str):
        if question_id not in self.questions:
            raise ValueError("Question not found")
        
        a = Answer(content, user, question_id)
        self.questions[question_id].add_answer(a)
        self.answers[a.id] = a
        return a
    
    def add_comment(self, user: User, target_id: str, content: str):
        comment = Comment(content, user)
        target = self.questions.get(target_id) or self.answers.get(target_id)
        if target:
            target.add_comment(comment)
        else:
            raise ValueError("target post not found")
        
    def vote(self, user: User, target_id: str, vote_type: VoteType):
        target = self.questions.get(target_id) or self.answers.get(target_id)
        if target:
            target.vote(user, vote_type)
        else:
            raise ValueError("target post not found")
        
    def search(self, query: str):
        questions = []
        for q in self.questions.values():
            if query.lower() in q.title or query.lower() in q.content():
                questions.append(q)
        return questions
    
def demo():
    so = StackOverflowSystem()

    u1 = so.register_user("foo", "foo@gmail.com")
    u2 = so.register_user("bar", "bar@gmail.com")

    q1 = so.post_question(u1, "how to design stackoverflow?", "I want to learn lld. how to learn? explain using stackoverflow", ["lld", "oop", "python"])

    a1 = so.post_answer(u2, q1.id, "blah blahh")

    so.vote(u2, q1.id, VoteType.UPVOTE)

    so.add_comment(u1, a1.id, "thankss")

    for q in so.questions.values():
        print(f'QUESTION - {q.title} - {q.content} - {q.get_vote_count()}')
        for c in q.comments:
            print(f'COMMENT - {c.content}')
        for a in q.answers:
            print(f'ANSWER - {a.content} - {a.get_vote_count()}')
            for c in a.comments:
                print(f'COMMENT - {c.content}')


if __name__ == "__main__":
    demo()