from fastapi import Body, FastAPI

app = FastAPI()

# @app.get("/api-endpoint")
# async def first_api():
#     return {"message":"Hello Rakib!"}

BOOKS = [
    {"title": "title one", "author": "author one", "category": "science"},
    {"title": "title two", "author": "author two", "category": "science"},
    {"title": "title three", "author": "author three", "category": "history"},
    {"title": "title four", "author": "author four", "category": "math"},
    {"title": "title five", "author": "author five", "category": "math"},
    {"title": "title six", "author": "author one", "category": "physics"},
]


@app.get("/books")
async def read_all_books():
    return BOOKS


# @app.get("/books/mybook")
# async def read_all_books():
#     return {"My book": "My favorite book!!"}


@app.get("/books/{book_title}")
async def read_all_books(book_title: str):
    for book in BOOKS:
        if book.get("title").casefold() == book_title.casefold():
            return {"Book": book}


# @app.get("/books/")
# async def read_category_by_query(category: str):
#     books_to_return = []
#     for book in BOOKS:
#         if book.get("category").casefold() == category.casefold():
#             books_to_return.append(book)

#     return books_to_return


@app.get("/books/{book_author}/")
async def read_author_category_by_query(book_author: str, category: str):
    books_to_return = []
    for book in BOOKS:
        if (
            book.get("author").casefold() == book_author.casefold()
            and book.get("category").casefold() == category.casefold()
        ):
            books_to_return.append(book)
    return books_to_return


@app.post("/books/create_book")
async def create_book(new_book=Body()):
    BOOKS.append(new_book)
    # return BOOKS


@app.put("/books/update_book")
async def update_book(updated_book=Body()):
    for i in range(len(BOOKS)):
        if BOOKS[i].get("title").casefold() == updated_book.get("title").casefold():
            BOOKS[i] = updated_book


@app.delete("/books/delete_book/")
async def delete_book(book_title: str):
    for i in range(len(BOOKS)):
        if BOOKS[i].get("title").casefold() == book_title.casefold():
            BOOKS.pop(i)
            break


# Assignment
@app.get("/books/")
async def books_from_author(author_name :str):
    books_to_return = []
    for book in BOOKS:
        if (book.get("author").casefold() == author_name.casefold()):
            books_to_return.append(book)
    return books_to_return
