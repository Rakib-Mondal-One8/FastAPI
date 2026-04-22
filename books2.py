from typing import Optional

from fastapi import Body, FastAPI, Path, Query, HTTPException
from pydantic import BaseModel, Field
from starlette import status

app = FastAPI()


class Book:
    id: int
    title: str
    author: str
    description: str
    rating: int
    publish_date: int

    def __init__(self, id, title, author, description, rating,publish_date):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.rating = rating
        self.publish_date = publish_date


class BookRequest(BaseModel):
    id: Optional[int] = Field(
        description="ID is not needed for creation !", default=None
    )
    title: str = Field(min_length=3)
    author: str = Field(min_length=1)
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(gt=0, lt=6)
    publish_date: int = Field(gt=1999, lt=2031)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "A new Book",
                "author": "CodingWithRockey",
                "description": "A new Description",
                "rating": 5,
                "publish_date" : 2029
            }
        }
    }


BOOKS = [
    Book(1, "Computer Science Pro", "CodingWithRockey", "It is a very nice Book !", 5,2030),
    Book(2, "Move Fast with FastAPI", "CodingWithRockey", "It is a awesome Book !", 5,2030),
    Book(3, "Mastering API endpoints", "CodingWithRockey", "It is a fantastic Book !", 5,2029),
    Book(4, "HP1", "Author1", "Book description 1", 1,2028),
    Book(5, "HP2", "Author2", "Book description 2", 2,2027),
    Book(6, "HP3", "Author3", "Book description 3", 1,2026)
]


@app.get("/books",status_code=status.HTTP_200_OK)
async def read_all_books():
    return BOOKS


@app.get("/books/{book_id}",status_code=status.HTTP_200_OK)
async def read_book(book_id: int = Path(gt=0)):
    for book in BOOKS:
        if book.id == book_id:
            return book
    
    raise HTTPException(status_code=404,detail="Item Not Found!")


@app.get("/books/", status_code=status.HTTP_200_OK)
async def read_book_by_rating(
    book_rating: int = Query(gt=0, lt=6)):
    books_to_return = []

    for book in BOOKS:
        if book.rating == book_rating:
            books_to_return.append(book)

    return books_to_return


@app.get("/books/publish/", status_code=status.HTTP_200_OK)
async def read_book_by_pushlish_date(publish_date: int = Query(gt=1999,lt=2031)):
    books_to_return = []
    for book in BOOKS:
        if book.publish_date == publish_date:
            books_to_return.append(book)
    return books_to_return


@app.post("/create-book",status_code=status.HTTP_201_CREATED)
async def create_book(book_request: BookRequest):
    new_book = Book(**book_request.model_dump())
    BOOKS.append(find_book_id(new_book))


def find_book_id(book: Book):
    book.id = 1 if len(BOOKS) == 0 else BOOKS[-1].id + 1
    # if(len(BOOKS) > 0):
    #     book.id = BOOKS[-1].id+1
    # else:
    #     book.id = 1;

    return book


@app.put("/books/update-book",status_code=status.HTTP_204_NO_CONTENT)
async def update_book(book: BookRequest):
    book_change = False
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book.id:
            BOOKS[i] = book
            book_change = True
            break;
    
    if not book_change : raise HTTPException(status_code=404,detail="Item Not Found!")

@app.delete("/books/delete-book/",status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int = Query(gt=0)):
    book_delete = False
    for i in range(len(BOOKS)):
        if(BOOKS[i].id == book_id):
            BOOKS.pop(i)
            book_delete = True
            break
    
    if not book_delete: raise HTTPException(status_code=404,detail="Item Not Found!")
