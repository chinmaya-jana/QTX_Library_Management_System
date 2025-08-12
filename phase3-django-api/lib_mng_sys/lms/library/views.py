from django.core.serializers import serialize
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

# Create your views here.
from .models import (
    Address, ContactNumber, Library, Author, Member,
    Category, Book, Borrowing, Review
)
from .serializers import (
    AddressSerializer, ContactNumberSerializer, LibrarySerializer,
    AuthorSerializer, MemberSerializer, CategorySerializer,
    BookSerializer, BorrowingSerializer, ReviewSerializer
)

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

class ContactNumberViewSet(viewsets.ModelViewSet):
    queryset = ContactNumber.objects.all()
    serializer_class = ContactNumberSerializer

class LibraryViewSet(viewsets.ModelViewSet):
    queryset = Library.objects.all()
    serializer_class = LibrarySerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"status": "error", "message": "No libraries available.", "code": 404},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        try:
            library = self.get_object()
        except:
            return Response(
                {"status": "error", "message": "Library not found.", "code": 404},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(library)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors, "code": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
        except:
            return Response(
                {"status": "error", "message": "Library not found.", "code": 404},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors, "code": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except:
            return Response(
                {"status": "error", "message": "Library not found.", "code": 404},
                status=status.HTTP_404_NOT_FOUND,
            )
        self.perform_destroy(instance)
        return Response(
            {"status": "success", "message": "Library deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all().prefetch_related('book_set__categories')
    serializer_class = AuthorSerializer

    def get_object(self):
        return get_object_or_404(Author, pk=self.kwargs.get('pk'))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        author = serializer.save()
        return Response({
            "status": "success",
            "message": "Author created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        authors = self.get_queryset()
        serializer = self.get_serializer(authors, many=True)
        return Response({
            "status": "success",
            "message": "Authors retrieved successfully.",
            "data": serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        try:
            author = self.get_object()
        except NotFound:
            return Response({
                "status": "error",
                "message": "Author not found.",
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(author)
        return Response({
            "status": "success",
            "message": "Author retrieved successfully.",
            "data": serializer.data
        })

    def update(self, request, *args, **kwargs):
        try:
            author = self.get_object()
        except NotFound:
            return Response({
                "status": "error",
                "message": "Author not found.",
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(author, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "status": "success",
            "message": "Author updated successfully.",
            "data": serializer.data
        })

    def partial_update(self, request, *args, **kwargs):
        try:
            author = self.get_object()
        except NotFound:
            return Response({
                "status": "error",
                "message": "Author not found.",
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(author, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "status": "success",
            "message": "Author partially updated successfully.",
            "data": serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        try:
            author = self.get_object()
        except NotFound:
            return Response({
                "status": "error",
                "message": "Author not found.",
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)
        author.delete()
        return Response({
            "status": "success",
            "message": "Author deleted successfully."
        }, status=status.HTTP_204_NO_CONTENT)

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    def get_object(self):
        return get_object_or_404(Member, pk=self.kwargs.get('pk'))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # Validate but do not allow creation if duplicate
        serializer.is_valid(raise_exception=True)
        member = serializer.save()
        return Response({
            "status": "success",
            "message": "Member created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": "success",
            "message": "Member list fetched successfully.",
            "data": serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        try:
            member = self.get_object()
        except NotFound:
            return Response({
                "status": "error",
                "message": "Member not found.",
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(member)
        return Response({
            "status": "success",
            "message": "Member retrieved successfully.",
            "data": serializer.data
        })

    def update(self, request, *args, **kwargs):
        try:
            member = self.get_object()
        except NotFound:
            return Response({
                "status": "error",
                "message": "Member not found.",
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(member, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "status": "success",
            "message": "Member updated successfully.",
            "data": serializer.data
        })

    def partial_update(self, request, *args, **kwargs):
        try:
            member = self.get_object()
        except NotFound:
            return Response({
                "status": "error",
                "message": "Member not found.",
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(member, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "status": "success",
            "message": "Member partially updated successfully.",
            "data": serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        try:
            member = self.get_object()
        except NotFound:
            return Response({
                "status": "error",
                "message": "Member not found.",
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)
        member.delete()
        return Response({
            "status": "success",
            "message": "Member deleted successfully."
        }, status=status.HTTP_204_NO_CONTENT)

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.prefetch_related(
        Prefetch('books', queryset=Book.objects.prefetch_related('authors'))
    ).all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if Category.objects.filter(name__iexact=request.data.get('name', '').strip()).exists():
            return Response({
                "status": "error",
                "message": f"Category '{request.data.get('name')}' already exists.",
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        try:
            category = self.get_object()
        except NotFound:
            return Response({
                "status": "error",
                "message": "Category not found.",
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(category, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        try:
            category = self.get_object()
        except NotFound:
            return Response({
                "status": "error",
                "message": "Category not found.",
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)

        # Remove M2M links before delete
        category.books.clear()
        category.delete()
        return Response({
            "status": "success",
            "message": "Category deleted successfully.",
            "code": 200
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except NotFound:
            return Response({
                "status": "error",
                "message": "Category not found.",
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if not queryset.exists():
            return Response({
                "status": "error",
                "message": "No categories available.",
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().select_related('library').prefetch_related('authors', 'categories')
    serializer_class = BookSerializer

    def get_object(self):
        return get_object_or_404(Book, pk=self.kwargs.get('pk'))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            book = serializer.save()
            return Response({
                "status": "success",
                "message": "Book created successfully.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "message": "Failed to create book.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        book = self.get_object()
        serializer = self.get_serializer(book, data=request.data, partial=False)
        if serializer.is_valid():
            book = serializer.save()
            return Response({
                "status": "success",
                "message": "Book updated successfully.",
                "data": serializer.data
            })
        return Response({
            "status": "error",
            "message": "Failed to update book.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        book = self.get_object()
        serializer = self.get_serializer(book, data=request.data, partial=True)
        if serializer.is_valid():
            book = serializer.save()
            return Response({
                "status": "success",
                "message": "Book partially updated.",
                "data": serializer.data
            })
        return Response({
            "status": "error",
            "message": "Failed to partially update book.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        book = self.get_object()
        book.authors.clear()
        book.categories.clear()
        book.reviews.all().delete()
        book.borrowing_set.all().delete()
        book.delete()
        return Response({
            "status": "success",
            "message": "Book and related data deleted successfully."
        }, status=status.HTTP_204_NO_CONTENT)

class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all().select_related('member', 'book')
    serializer_class = BorrowingSerializer

    def get_object(self):
        obj = get_object_or_404(Borrowing, pk=self.kwargs.get('pk'))
        return obj

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "message": "Borrowing creation failed.",
            "errors": serializer.errors,
            "code": 400
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        borrowing = self.get_object()
        serializer = self.get_serializer(borrowing, data=request.data, partial=False)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        return Response({
            "status": "error",
            "message": "Borrowing update failed.",
            "errors": serializer.errors,
            "code": 400
        }, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        borrowing = self.get_object()
        serializer = self.get_serializer(borrowing, data=request.data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        return Response({
            "status": "error",
            "message": "Borrowing partial update failed.",
            "errors": serializer.errors,
            "code": 400
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        borrowing = self.get_object()
        borrowing.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all().select_related('member', 'book')
    serializer_class = ReviewSerializer

    def get_object(self):
        return get_object_or_404(Review, pk=self.kwargs.get('pk'))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "status": "success",
                "message": "Review created successfully.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "message": "Failed to create review.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        review = self.get_object()
        serializer = self.get_serializer(review, data=request.data, partial=False)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                "status": "success",
                "message": "Review updated successfully.",
                "data": serializer.data
            })
        return Response({
            "status": "error",
            "message": "Failed to update review.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        review = self.get_object()
        serializer = self.get_serializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                "status": "success",
                "message": "Review partially updated.",
                "data": serializer.data
            })
        return Response({
            "status": "error",
            "message": "Failed to partially update review.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        review = self.get_object()
        review.delete()
        return Response({
            "status": "success",
            "message": "Review deleted successfully."
        }, status=status.HTTP_204_NO_CONTENT)