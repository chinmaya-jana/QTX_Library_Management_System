from django.db.models import Case, When, IntegerField, Value
from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.decorators import action

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

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return LibraryWriteSerializer
        return LibraryReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        library = Library.objects.create(
            name=serializer.validated_data["name"].strip(),
            campus_location=serializer.validated_data["campus_location"].strip(),
            contact_email=serializer.validated_data["contact_email"].lower(),
            phone_number=serializer.validated_data["phone_number"],
            phone_type=serializer.validated_data["phone_type"]
        )
        return Response(
            {"message": "Library added successfully.", "data": LibraryReadSerializer(library).data},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(instance, field, value)

        instance.save()
        return Response(
            {"message": "Library updated successfully.", "data": LibraryReadSerializer(instance).data},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Delete related Books → Borrowings & Reviews will cascade
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

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except:
            raise NotFound("Library not found.")
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#-----------------------------------Author-------------------------------------------
class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return AuthorWriteSerializer
        return AuthorReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        author = serializer.save()
        return Response(
            {"message": "Author added successfully.", "data": AuthorReadSerializer(author).data},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        author = serializer.save()
        return Response(
            {"message": "Author updated successfully.", "data": AuthorReadSerializer(author).data},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {"message": "Author and related BookAuthor records deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#----------------------------------Category-----------------------------------------
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CategoryWriteSerializer
        return CategoryReadSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            category = serializer.save()
            return Response(
                {"message": "Category created successfully", "data": CategoryReadSerializer(category).data},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            category = serializer.save()
            return Response(
                {"message": "Category updated successfully", "data": CategoryReadSerializer(category).data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            category = self.get_object()
            serializer = self.get_serializer(category)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def list(self, request, *args, **kwargs):
        try:
            categories = self.get_queryset()
            serializer = self.get_serializer(categories, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            category = self.get_object()
            category.delete()  # CASCADE will remove from BookCategory too
            return Response({"message": "Category deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#-------------------------------Book--------------------------------------------------
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return BookWriteSerializer
        return BookReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        book = Book.objects.create(
            title=serializer.validated_data["title"].strip(),
            isbn=serializer.validated_data.get("isbn"),
            publication_date=serializer.validated_data["publication_date"],
            total_copies=serializer.validated_data["total_copies"],
            available_copies=serializer.validated_data["total_copies"],  # initially same
            library=serializer.validated_data["library"]
        )
        return Response(
            {"message": "Book added successfully.", "data": BookReadSerializer(book).data},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # If updating total copies, add to existing
        new_total = serializer.validated_data.get("total_copies")
        if new_total and new_total != instance.total_copies:
            diff = new_total - instance.total_copies
            if diff > 0:
                instance.total_copies += diff
                instance.available_copies += diff
            else:
                # Prevent reducing total below available
                if instance.available_copies > new_total:
                    return Response(
                        {"detail": "Cannot reduce total copies below available copies."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                instance.total_copies = new_total

        # Other fields
        for field, value in serializer.validated_data.items():
            if field not in ["total_copies"]:
                setattr(instance, field, value)

        instance.save()
        return Response(
            {"message": "Book updated successfully.", "data": BookReadSerializer(instance).data},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Delete related borrowings & reviews
        Borrowing.objects.filter(book=instance).delete()
        Review.objects.filter(book=instance).delete()
        instance.delete()
        return Response(
            {"message": "Book deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except:
            raise NotFound("Book not found.")
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#----------------------------Member-------------------------------------------
class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return MemberWriteSerializer
        return MemberReadSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            member = serializer.save()
            return Response(
                {"message": "Member created successfully", "data": MemberReadSerializer(member).data},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            member = serializer.save()
            return Response(
                {"message": "Member updated successfully", "data": MemberReadSerializer(member).data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            member = self.get_object()
            serializer = self.get_serializer(member)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def list(self, request, *args, **kwargs):
        try:
            members = self.get_queryset()
            serializer = self.get_serializer(members, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            member = self.get_object()
            member.delete()
            return Response({"message": "Member deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#----------------------------Borrowing----------------------------------------
class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()

    def get_queryset(self):
        return Borrowing.objects.annotate(
            is_hold_first=Case(
                When(status=BorrowingStatus.HOLD, then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('is_hold_first', 'due_date', 'borrowing_id')

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingWriteSerializer
        elif self.action in ["update", "partial_update"]:
            return BorrowingReturnSerializer
        return BorrowingReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        borrowing = Borrowing.objects.create(
            member=serializer.validated_data["member"],
            book=serializer.validated_data["book"],
            status=BorrowingStatus.HOLD
        )

        # Decrease available copies
        book = borrowing.book
        book.available_copies -= 1
        book.save(update_fields=["available_copies"])

        return Response(
            {"message": "Book borrowed successfully.", "data": BorrowingReadSerializer(borrowing).data},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # only returning is allowed
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if instance.status != BorrowingStatus.HOLD:
            return Response({"detail": "This borrowing is already returned."}, status=status.HTTP_400_BAD_REQUEST)

        # Mark as returned
        instance.status = BorrowingStatus.RETURNED
        instance.return_date = timezone.now()

        # Calculate late fee
        if instance.return_date.date() > instance.due_date:
            days_late = (instance.return_date.date() - instance.due_date).days
            instance.late_fee = days_late * 5  # Example rate: 5 currency/day

        instance.save(update_fields=["status", "return_date", "late_fee"])

        # Increase available copies
        book = instance.book
        book.available_copies += 1
        book.save(update_fields=["available_copies"])

        return Response(
            {"message": "Book returned successfully.", "data": BorrowingReadSerializer(instance).data},
            status=status.HTTP_200_OK
        )

#----------------------------------Review----------------------------------
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related("member", "book").all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ReviewWriteSerializer
        return ReviewReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"message": "Review added successfully.", "data": serializer.data},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {"message": "Review updated successfully.", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Review deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except:
            raise NotFound("Review not found.")
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
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