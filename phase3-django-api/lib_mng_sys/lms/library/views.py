from http.client import responses

from django.db.models import Case, When, IntegerField, Value, Q, CharField
from django.db.models.functions import Concat
from django.shortcuts import render
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.test import APIRequestFactory

from .models import (Review, Library, Author, Member, Category,
                     Book, Borrowing, BookAuthor, BookCategory, BorrowingStatus)

from .serializers import (AuthorReadSerializer, AuthorWriteSerializer,
                          BookAuthorSerializer, BookCategorySerializer,
                          BorrowingReadSerializer, BorrowingWriteSerializer, BorrowingReturnSerializer,
                          ReviewWriteSerializer, ReviewReadSerializer, BookReadSerializer, BookWriteSerializer,
                          LibraryReadSerializer, LibraryWriteSerializer, MemberWriteSerializer, MemberReadSerializer,
                          CategoryWriteSerializer, CategoryReadSerializer)

#-----------------------------BookAuthor ViewSet-------------------------------
class BookAuthorViewSet(viewsets.ModelViewSet):
    queryset = BookAuthor.objects.all()
    serializer_class = BookAuthorSerializer

#-----------------------------BookCategory ViewSet-----------------------------
class BookCategoryViewSet(viewsets.ModelViewSet):
    queryset = BookCategory.objects.all()
    serializer_class = BookCategorySerializer

# -------------------------------Library---------------------------------------
class LibraryViewSet(viewsets.ModelViewSet):
    queryset = Library.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["name", "campus_location", "contact_email", "phone_number", "phone_type"]
    search_fields = ["name", "campus_location", "phone_type"]
    ordering_fields = ["name", "created_at", "updated_at", "library_id", "updated_at"]
    ordering = ["library_id"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return LibraryWriteSerializer
        return LibraryReadSerializer

    def create(self, request, *args, **kwargs):
        """
        # While POST: libray_id is not returned
        response = super().create(request, *args, **kwargs)
        response.data = {
            "message": "Library added successfully.",
            "data": response.data
        }
        return response
        """
        # library_id is returned properly
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance  # <- saved Library instance
        read_serializer = LibraryReadSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Library added successfully.",
                "data": read_serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        instance = self.get_object()
        read_serializer = LibraryReadSerializer(instance)
        response.data = {
            "message": "Library updated successfully.",
            "data": read_serializer.data
        }
        return response

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(
            {"message": "Library deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

#-----------------------------------Author-------------------------------------------
class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["birth_date", "first_name", "last_name", "nationality"]
    search_fields = ["first_name", "last_name", "full_name_db"]
    ordering_fields = ["full_name_db", "birth_date", "created_at", "author_id", "updated_at"]
    ordering = ["author_id"]

    def get_queryset(self):
        # Annotate DB-level field for filtering/searching/ordering
        return super().get_queryset().annotate(
            full_name_db=Concat(
                'first_name', Value(' '), 'last_name',
                output_field=CharField()
            )
        )

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return AuthorWriteSerializer
        return AuthorReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance  # to save author instance
        read_serializer = AuthorReadSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Author added successfully.",
                "data": read_serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        instance = self.get_object()
        read_serializer = AuthorReadSerializer(instance)
        response.data = {
            "message": "Author updated successfully.",
            "data": read_serializer.data
        }
        return response

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(
            {"message": "Author deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

#----------------------------------Category-----------------------------------------
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering_fields = ["name", "category_id", "created_at"]
    ordering = ["category_id"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CategoryWriteSerializer
        return CategoryReadSerializer

    # Custom message
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        read_serializer = CategoryReadSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Author added successfully.",
                "data": read_serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        instance = self.get_object()
        read_serializer = CategoryReadSerializer(instance)
        response.data = {
            "message": "Author updated successfully.",
            "data": read_serializer.data
        }
        return response

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(
            {"message": "Category deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

#-------------------------------Book--------------------------------------------------
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["title", "isbn", "library"]
    search_fields = ["title", "isbn", "library"]
    ordering_fields = ["book_id", "publication_date", "created_at", "updated_at", "title", "total_copies", "available_copies",]
    ordering = ["book_id"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return BookWriteSerializer
        return BookReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        read_serializer = BookReadSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Book added successfully.",
                "data": read_serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        instance = self.get_object()
        read_serializer = BookReadSerializer(instance)
        response.data = {
            "message": "Author updated successfully.",
            "data": read_serializer.data
        }
        return response

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(
            {"message": "Book deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

#----------------------------Member-------------------------------------------
class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["member_type", "phone_type", "registration_date"]
    search_fields = ["first_name", "last_name", "email", "phone", "full_name_db"]
    ordering_fields = ["full_name_db", "created_at", "member_id"]
    ordering = ["member_id"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return MemberWriteSerializer
        return MemberReadSerializer

    def get_queryset(self):
        return super().get_queryset().annotate(
            full_name_db=Concat(
                'first_name', Value(' '), 'last_name',
                output_field=CharField()
            )
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        read_serializer = MemberReadSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Member added successfully.",
                "data": read_serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        instance = self.get_object()
        read_serializer = MemberReadSerializer(instance)
        response.data = {
            "message": "Member updated successfully.",
            "data": read_serializer.data
        }
        return response

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(
            {"message": "Member deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

#----------------------------Borrowing----------------------------------------
class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["member", "book", "status"]
    search_fields = ["member__first_name", "member__last_name", "book__title"]
    ordering_fields = ["due_date", "borrow_date", "return_date", "late_fee"]

    def get_queryset(self):
        return (
            Borrowing.objects.annotate(
                is_hold_first=Case(
                    When(status=BorrowingStatus.HOLD, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            .order_by("is_hold_first", "due_date", "borrowing_id")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingWriteSerializer
        elif self.action in ["update", "partial_update"]:
            return BorrowingReturnSerializer
        return BorrowingReadSerializer

    # Custom create (borrow a book)
    def perform_create(self, serializer):
        borrowing = serializer.save(status=BorrowingStatus.HOLD)

        # Decrease available copies
        book = borrowing.book
        book.available_copies -= 1
        book.save(update_fields=["available_copies"])

        return borrowing

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        borrowing = self.perform_create(serializer)
        return Response(
            {"message": "Book borrowed successfully.", "data": BorrowingReadSerializer(borrowing).data},
            status=status.HTTP_201_CREATED,
        )

    # Custom update (return a book)
    def perform_update(self, serializer):
        instance = serializer.instance

        # Only returning is allowed
        if instance.status != BorrowingStatus.HOLD:
            raise ValueError("This borrowing is already returned.")

        instance.status = BorrowingStatus.RETURNED
        instance.return_date = timezone.now()

        # Calculate late fee
        if instance.return_date.date() > instance.due_date:
            days_late = (instance.return_date.date() - instance.due_date).days
            instance.late_fee = days_late * 5  # Example: rate per day 5

        instance.save(update_fields=["status", "return_date", "late_fee"])

        # Increase available copies
        book = instance.book
        book.available_copies += 1
        book.save(update_fields=["available_copies"])

        return instance

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            borrowing = self.perform_update(serializer)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Book returned successfully.", "data": BorrowingReadSerializer(borrowing).data},
            status=status.HTTP_200_OK,
        )

#----------------------------------Review----------------------------------
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related("member", "book").all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["member", "book", "rating"]  # Filtering by exact fields
    search_fields = ["comment", "book__title", "member__first_name", "member__last_name"]  # Searching
    ordering_fields = ["review_date", "rating"]  # Sorting

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ReviewWriteSerializer
        return ReviewReadSerializer

    # My custom logic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"message": "Review added successfully.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {"message": "Review updated successfully.", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Review deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except:
            raise NotFound("Review not found.")
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


#--------------------------END--------------------------------------

# Advance API end point
# ----------------------------- Library with Books -----------------------------
class LibraryBookViewSet(viewsets.ViewSet):
    """
    Custom endpoint to fetch a library along with its books (book_id + title only).
    URL: /api/libraries/{library_id}/books/
    """

    def retrieve(self, request, pk=None):
        try:
            library = Library.objects.get(pk=pk)
        except Library.DoesNotExist:
            raise NotFound("Library not found.")

        books = library.book_set.all().values("book_id", "title")

        data = {
            "library_id": library.library_id,
            "name": library.name,
            "campus_location": library.campus_location,
            "contact_email": library.contact_email,
            "phone_number": str(library.phone_number),
            "phone_type": library.phone_type,
            "created_at": library.created_at,
            "updated_at": library.updated_at,
            "books": list(books),
        }

        return Response(data, status=status.HTTP_200_OK)

# /api/books/search/
class BookSearchViewSet(viewsets.ViewSet):
    """
    Search books by title, author, or category.
    URL: /api/books/search/?q=keyword
    """
    def list(self, request):
        query = request.query_params.get("q", None)
        if not query:
            return Response({"error": "Search query is required."}, status=status.HTTP_400_BAD_REQUEST)

        books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(authors__first_name__icontains=query) |
            Q(authors__last_name__icontains=query) |
            Q(categories__name__icontains=query)
        ).distinct()

        results = books.values("book_id", "title", "isbn", "publication_date")
        return Response({"results": list(results)}, status=status.HTTP_200_OK)


# /api/members/{member_id}/borrowings/
class MemberBorrowingHistoryViewSet(viewsets.ViewSet):
    """
    Get borrowing history of a member.
    URL: /api/members/{member_id}/borrowings/
    """
    def list(self, request, pk=None):
        try:
            member = Member.objects.get(pk=pk)
        except Member.DoesNotExist:
            raise NotFound("Member not found.")

        borrowings = Borrowing.objects.filter(member=member).select_related("book")
        data = [
            {
                "borrowing_id": b.borrowing_id,
                "book": b.book.title,
                "borrow_date": b.borrow_date,
                "return_date": b.return_date,
                "status": b.status,
            }
            for b in borrowings
        ]
        return Response({"member_id": member.member_id, "borrowings": data}, status=status.HTTP_200_OK)


# /api/books/{book_id}/availability/
class BookAvailabilityViewSet(viewsets.ViewSet):
    """
    Check availability of a book.
    URL: /api/books/{book_id}/availability/
    """
    def retrieve(self, request, pk=None):
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            raise NotFound("Book not found.")

        available = book.available_copies > 0
        data = {
            "book_id": book.book_id,
            "title": book.title,
            "available": available,
            "available_copies": book.available_copies,
            "total_copies": book.total_copies,
        }
        return Response(data, status=status.HTTP_200_OK)

# /api/libraries/{library_id}/statistics/
class LibraryStatisticsViewSet(viewsets.ViewSet):
    """
    Get statistics of a library.
    URL: /api/libraries/{library_id}/statistics/
    """
    def retrieve(self, request, pk=None):
        try:
            library = Library.objects.get(pk=pk)
        except Library.DoesNotExist:
            raise NotFound("Library not found.")

        total_books = library.book_set.count()

        # Count distinct members who have borrowed books from this library
        total_members = Member.objects.filter(
            borrowing__book__library=library
        ).distinct().count()

        total_borrowings = Borrowing.objects.filter(book__library=library).count()

        data = {
            "library_id": library.library_id,
            "name": library.name,
            "total_books": total_books,
            "total_members": total_members,
            "total_borrowings": total_borrowings,
        }
        return Response(data, status=status.HTTP_200_OK)