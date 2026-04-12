'''

requirements:
1. users can post questions(with tags), post answers, post comments on both questions/answers
2. upvote/downvote questions and answers
3. search by keywords, tags, user
4. reputation system based on votes received and activity
5. concurrent voting - no double voting by same user
6. data consistency on vote + reputation update
7. scalable content model

core entities:

User
Question
Answer
Comment
Vote
Tag
SearchCriteria

enums:

VoteType: UPVOTE, DOWNVOTE
PostStatus: ACTIVE, CLOSED, DELETED
QuestionStatus: OPEN, CLOSED, DUPLICATE
AccountStatus: ACTIVE, SUSPENDED, DELETED

classes and interfaces:

Votable(ABC):
- vote_id_map: {user_id: vote_type}
- upvote_count
- get_score()
- add_vote(user_id, vote_type)
- remove_vote(user_id)

Commentable(ABC):
- comments: list[Comment]
- add_comment(comment)

SearchService(ABC):
- search(criteria: SearchCriteria) -> list[Question]

ReputationService(ABC):
- on_vote(post_author, voter, vote_type, is_question)
- on_accept_answer(answer_author)
- undo_vote(post_author, voter, vote_type, is_question)

User:
- user_id
- reputation
- account_status
- questions
- answers
- created_at

Tag:
- tag_id
- name
- description
- usage_count

Question(Votable, Commentable):
- question_id
- title
- body
- author
- tags
- answers
- accepted_answer
- status
- created_at
- accept_answer(answer)

Answer(Votable, Commentable):
- answer_id
- body
- author
- question_id
- is_accpeted
- status
- created_at

Comment:
- comment_id
- author
- parent_id
- created_at

Vote:
- vote_id
- user_id
- post_id
- vote_type
- created_at

SearchCriteria:
- keywords
- tags
- author_username

StackOverflowSystem
- user_service
- question_service
- vote_service
- search_service
- reputation_service
- tag_service

UserService:
- users: dict[str, User]
- register(user_name, email)
- get_user(user_id)
- get_user_questions(user_id)
- get_user_answers(user_id)

QuestionService:
- questions: dict[str, Question]
- answers: dict[str, Answer]
- post_question(author, title, body, tag_names)
- get_question(question_id)
- post_answer(author, question_id, body)
- add_comment(author, parent_id, body)
- accept_answer(user_id, question_id, answer_id)
- close_question(question_id)

VoteService:
- vote(user_id, post_id, vote_type)
- undo_vote(user_id, post_id)

TagService:
- tags: dict[str, Tag]
- tag_questions: dict[str, list[str]]
- get_or_create(tag_name)
- get_questions_by_tag(tag_name)

ReputationServiceImpl(ReputationService):
- adjust user.reputation based on voteType

SearchServiceImpl(SearchService):
- search(criteria)




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
    