from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (ReviewViewSet, LibraryViewSet, AuthorViewSet,
                    MemberViewSet, CategoryViewSet, BookViewSet, BorrowingViewSet,
                    BookAuthorViewSet, BookCategoryViewSet,
                    BookAvailabilityViewSet, books_in_library, member_borrowings, library_statistics, return_book,
                    borrow_book)

router = DefaultRouter()
router.register(r'book_authors', BookAuthorViewSet)
router.register(r'book_categories', BookCategoryViewSet)
router.register(r'libraries', LibraryViewSet)
router.register(r'authors', AuthorViewSet)
router.register(r'members', MemberViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'books', BookViewSet)
router.register(r'borrowings', BorrowingViewSet)
router.register(r'reviews', ReviewViewSet)

book_availability = BookAvailabilityViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path('', include(router.urls)),  #localhost:8000/api/

    # ----------------Advanced Endpoints----------------

    # Example: GET http://localhost:8000/api/libraries/3/books/
    path("libraries/<int:pk>/books/", books_in_library, name="books-in-library"),

    # Member borrowing history
    path('members/<int:pk>/borrowings/', member_borrowings, name="member-borrowings"),

    # Book availability
    path('books/<int:pk>/availability/', book_availability, name="book-availability"),

    # Library statistics
    path('libraries/<int:pk>/statistics/', library_statistics, name="library-statistics"),

    # Return a Book
    path('book/return/', return_book, name="return-book"),

    # Borrow a book
    path('book/borrow/', borrow_book, name="borrow-book"),
]