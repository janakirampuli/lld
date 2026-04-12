'''

requirements:
1. book management system
2. add a new book to library
3. retreive a book by book_id
4. list books with filters
5. borrow a book if it's available
6. list books borrowed by a user
7. concurrency: no double lending of same copy
8. data consistency on borrow/return

core entities:
Book
BookCopy
User
BorrowRecord
BookFilter

enums:
CopyStatus: AVAILABLE, BORROWED
BorrowStatus: ACTIVE, RETURNED

classes and interfaces:

BookRepository(ABC):
- add_book(book)
- get_book_by_id(book_id)
- list_books(filters: BookFilter)

UserRepository(ABC):
- register_user(user)
- get_user_by_id(user_id)

BorrowService(ABC):
- borrow_books(user_id, copy_ids)
- return_book(user_id, copy_id)
- get_borrowed_books(user_id)

Book:
- book_id
- title
- copies: list[BookCopy]
- get_available_copies()

BookCopy:
- copy_id
- book_id
- status: CopyStatus

User:
- user_id
- name
- email
- phone

BorrowRecord:
- record_id
- user_id
- borrow_time
- return_time
- status: BorrowStatus

BookFilter:
- author
- genre
- available_only
- title

LibrarySystem:
- book_repo
- user_repo
- borrow_service

BookRepositoryImpl(BookRepository):
- books
- copies
- list_books(filters)

UserRepositoryImpl(UserRepository):
- users

BorrowServiceImpl(BorrowService):
- records
- user_active_records
- copy_locks
- user_locks
- borrow_books(user_id, copy_ids)
- return_book(user_id, copy_id)
- get_borrowed_books(user_id)



'''