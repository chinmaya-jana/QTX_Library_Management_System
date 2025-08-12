from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AddressViewSet, ContactNumberViewSet, LibraryViewSet,
    AuthorViewSet, MemberViewSet, CategoryViewSet,
    BookViewSet, BorrowingViewSet, ReviewViewSet
)

router = DefaultRouter()
router.register(r'addresses', AddressViewSet)
router.register(r'contacts', ContactNumberViewSet)
router.register(r'libraries', LibraryViewSet)
router.register(r'authors', AuthorViewSet)
router.register(r'members', MemberViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'books', BookViewSet)
router.register(r'borrowings', BorrowingViewSet)
router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    path('', include(router.urls)),
]