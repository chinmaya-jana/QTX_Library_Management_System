from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (ReviewViewSet, LibraryViewSet, AuthorViewSet,
                    MemberViewSet, CategoryViewSet, BookViewSet, BorrowingViewSet,
                    BookAuthorViewSet, BookCategoryViewSet, LibraryBookViewSet)

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

urlpatterns = [
    path('', include(router.urls)),  #localhost:8000/api/

    # Custom endpoint to fetch books of a specific library
    # Example: GET http://localhost:8000/api/libraries/3/books/
    path('libraries/<int:pk>/books/', library_books, name="library-books"),
]