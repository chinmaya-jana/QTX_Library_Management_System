from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (ReviewViewSet, LibraryViewSet, AuthorViewSet,
                    MemberViewSet, CategoryViewSet, BookViewSet, BorrowingViewSet,
                    BookAuthorViewSet, BookCategoryViewSet, LibraryBookViewSet,
                    MemberBorrowingHistoryViewSet, BookAvailabilityViewSet,
                    LibraryStatisticsViewSet)

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

# Custom mapping for LibraryBookViewSet
library_books = LibraryBookViewSet.as_view({"get": "retrieve"})
member_borrowings = MemberBorrowingHistoryViewSet.as_view({"get": "list"})
book_availability = BookAvailabilityViewSet.as_view({"get": "retrieve"})
library_statistics = LibraryStatisticsViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path('', include(router.urls)),  #localhost:8000/api/

    # ----------------Advanced Endpoints----------------
    # Library with Books
    # Example: GET http://localhost:8000/api/libraries/3/books/
    path('libraries/<int:pk>/books/', library_books, name="library-books"),

    # Member borrowing history
    path('members/<int:pk>/borrowings/', member_borrowings, name="member-borrowings"),

    # Book availability
    path('books/<int:pk>/availability/', book_availability, name="book-availability"),

    # Library statistics
    path('libraries/<int:pk>/statistics/', library_statistics, name="library-statistics"),
]