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
    filterset_fields = ["name", "campus_location", "phone_type"]  # Example filters
    search_fields = ["name", "campus_location", "contact_email"]
    ordering_fields = ["name", "campus_location", "created_at"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return LibraryWriteSerializer
        return LibraryReadSerializer

    def perform_create(self, serializer):
        serializer.save(
            name=serializer.validated_data["name"].strip(),
            campus_location=serializer.validated_data["campus_location"].strip(),
            contact_email=serializer.validated_data["contact_email"].lower()
        )

    def perform_update(self, serializer):
        validated = {
            field: (value.strip() if isinstance(value, str) else value)
            for field, value in serializer.validated_data.items()
        }
        serializer.save(**validated)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        books = Book.objects.filter(library=instance)
        for book in books:
            Borrowing.objects.filter(book=book).delete()
            Review.objects.filter(book=book).delete()
            book.delete()
        instance.delete()
        return Response(
            {"message": "Library and all related records deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

#-----------------------------------Author-------------------------------------------
class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["birth_date", "first_name", "last_name", "nationality"]
    search_fields = ["first_name", "last_name", "full_name"]
    ordering_fields = ["first_name", "last_name", "birth_date", "created_at"]
    ordering = ["first_name"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Annotate a full_name field
        qs = qs.annotate(full_name=Concat(
            'first_name', Value(' '), 'last_name',
            output_field=CharField()
        ))
        return qs

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return AuthorWriteSerializer
        return AuthorReadSerializer

    def perform_create(self, serializer):
        # Strip extra spaces and save clean data
        first = serializer.validated_data.get("first_name", "").strip()
        last = serializer.validated_data.get("last_name", "").strip()
        self.instance = serializer.save(first_name=first, last_name=last)

    def perform_update(self, serializer):
        validated = {
            field: (value.strip() if isinstance(value, str) else value)
            for field, value in serializer.validated_data.items()
        }
        self.instance = serializer.save(**validated)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Explicitly delete BookAuthor links before deleting author
        BookAuthor.objects.filter(author=instance).delete()
        instance.delete()
        return Response(
            {"message": "Author and related BookAuthor records deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response(
            {
                "message": "Author added successfully.",
                "data": AuthorReadSerializer(self.instance, context={"request": request}).data
            },
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(
            {
                "message": "Author updated successfully.",
                "data": AuthorReadSerializer(self.instance, context={"request": request}).data
            },
            status=status.HTTP_200_OK
        )

#----------------------------------Category-----------------------------------------
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["name"]  # exact filtering
    search_fields = ["name"]     # partial search
    ordering_fields = ["name", "category_id"]  # sorting
    ordering = ["category_id"]            # default ordering

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CategoryWriteSerializer
        return CategoryReadSerializer


#-------------------------------Book--------------------------------------------------
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return BookWriteSerializer
        return BookReadSerializer

    # Filtering, Searching, Ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["title", "isbn", "library"]
    search_fields = ["title", "isbn"]
    ordering_fields = ["publication_date", "title", "total_copies", "available_copies"]
    ordering = ["title"]

    def perform_create(self, serializer):
        total_copies = serializer.validated_data["total_copies"]
        serializer.save(available_copies=total_copies)

    def perform_update(self, serializer):
        instance = self.get_object()
        new_total = serializer.validated_data.get("total_copies")

        if new_total and new_total != instance.total_copies:
            diff = new_total - instance.total_copies
            if diff > 0:
                instance.total_copies += diff
                instance.available_copies += diff
            else:
                # Prevent reducing total below available
                if instance.available_copies > new_total:
                    raise NotFound("Cannot reduce total copies below available copies.")
                instance.total_copies = new_total

        # Save other fields
        for field, value in serializer.validated_data.items():
            if field not in ["total_copies"]:
                setattr(instance, field, value)

        instance.save()

    def perform_destroy(self, instance):
        #Delete related borrowings & reviews before deleting a book.
        Borrowing.objects.filter(book=instance).delete()
        Review.objects.filter(book=instance).delete()
        instance.delete()

#----------------------------Member-------------------------------------------
class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Filtering
    filterset_fields = ["member_type", "phone_type"]

    # Searching (custom full_name + normal fields)
    search_fields = ["first_name", "last_name", "email", "phone"]

    # Ordering
    ordering_fields = ["first_name", "last_name", "email", "created_at"]
    ordering = ["first_name"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return MemberWriteSerializer
        return MemberReadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Allow searching by `full_name`
        full_name_query = self.request.query_params.get("search")
        if full_name_query:
            queryset = queryset.filter(
                Q(first_name__icontains=full_name_query) | Q(last_name__icontains=full_name_query)
            )
        return queryset

#----------------------------Borrowing----------------------------------------
class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Filtering (by member, book, status)
    filterset_fields = ["member", "book", "status"]
    # Searching (member/book string repr)
    search_fields = ["member__first_name", "member__last_name", "book__title"]
    # Sorting
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

# i. /api/books/search/
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


# ii. /api/members/{member_id}/borrowings/
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


# iii. /api/books/{book_id}/availability/
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


# iv. /api/books/borrow/
class BookBorrowViewSet(viewsets.ViewSet):
    """
    Borrow a book.
    Rules:
    - Member must exist
    - Book must exist and be available
    - Member must not exceed borrow limit
    - Member must not already hold the same book
    """
    def create(self, request):
        member_id = request.data.get("member_id")
        book_id = request.data.get("book_id")

        try:
            member = Member.objects.get(pk=member_id)
        except Member.DoesNotExist:
            raise NotFound("Member not found.")

        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            raise NotFound("Book not found.")

        # Already holding the same book?
        if Borrowing.objects.filter(member=member, book=book, status="BORROWED").exists():
            raise ValidationError("Member already borrowed this book.")

        # Borrow limit (example: 5 books)
        if Borrowing.objects.filter(member=member, status="BORROWED").count() >= 5:
            raise ValidationError("Member has reached the borrow limit (5 books).")

        if book.available_copies <= 0:
            raise ValidationError("Book is not available.")

        borrowing = Borrowing.objects.create(member=member, book=book, status="BORROWED")
        book.available_copies -= 1
        book.save()

        return Response(
            {"message": "Book borrowed successfully.", "borrowing_id": borrowing.borrowing_id},
            status=status.HTTP_201_CREATED,
        )


# v. /api/books/return/
class BookReturnView(APIView):
    """
    Return a borrowed book by member_id and book_id.
    URL: /api/books/return/
    """
    def put(self, request):
        member_id = request.data.get("member_id")
        book_id = request.data.get("book_id")

        if not member_id or not book_id:
            return Response(
                {"error": "member_id and book_id are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find borrowings on HOLD for this member and book
        borrowings = Borrowing.objects.filter(
            member_id=member_id,
            book_id=book_id,
            status='hold'
        )

        if not borrowings.exists():
            return Response(
                {"error": "No book on hold found for this member and book."},
                status=status.HTTP_404_NOT_FOUND
            )

        returned_books = []

        # Use existing BorrowingViewSet to perform the return
        factory = APIRequestFactory()
        view = BorrowingViewSet.as_view({'put': 'update'})

        for borrowing in borrowings:
            # Prepare request for BorrowingViewSet.update
            request_for_borrowing = factory.put(
                f"/borrowings/{borrowing.borrowing_id}/",
                {"status": "returned"},
                format='json'
            )

            response = view(request_for_borrowing, pk=borrowing.borrowing_id)

            if response.status_code != 200:
                return Response(response.data, status=response.status_code)

            returned_books.append(response.data)

        return Response(
            {
                "message": f"{len(returned_books)} book(s) returned successfully.",
                "returned_books": returned_books
            },
            status=status.HTTP_200_OK
        )

# vi. /api/libraries/{library_id}/statistics/
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