import datetime
import re
from datetime import timezone
from phonenumber_field.formfields import PhoneNumberField
from rest_framework import serializers
from .models import (
    Library, Author, Member, Category, Book, Borrowing, Review, BookAuthor, BookCategory, BorrowingStatus
)
from .models import PhoneType, MemberType

# ----------------- BookAuthor -----------------
class BookAuthorSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all())
    class Meta:
        model = BookAuthor
        fields = "__all__"

# ----------------- BookCategory -----------------
class BookCategorySerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    class Meta:
        model = BookCategory
        fields = "__all__"

# ----------------- Library -----------------
class LibraryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Library
        fields = ["name", "campus_location", "contact_email", "phone_number", "phone_type"]

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned.isalpha() and not all(ch.isalpha() or ch.isspace() for ch in cleaned):
            raise serializers.ValidationError("Library name must contain only letters and spaces.")
        if Library.objects.filter(name__iexact=cleaned).exists():
            raise serializers.ValidationError("A library with this name already exists.")
        return cleaned

    def validate_campus_location(self, value):
        cleaned = value.strip()
        if "," not in cleaned:
            raise serializers.ValidationError("Campus location must be comma separated (e.g., City, State).")
        return cleaned

    def validate_contact_email(self, value):
        cleaned = value.strip().lower()
        if Library.objects.filter(contact_email__iexact=cleaned).exists():
            raise serializers.ValidationError("This email is already registered with another library.")
        return cleaned

    def validate_phone_number(self, value):
        if Library.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already registered with another library.")
        return value

class LibraryReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Library
        fields = "__all__"

# ----------------- Author -----------------
class AuthorWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['first_name', 'last_name', 'birth_date', 'nationality', 'biography']

    def validate_first_name(self, value):
        if not re.fullmatch(r"[A-Za-z\s\-']+", value.strip()):
            raise serializers.ValidationError(
                "Must contain only letters, spaces, hyphens, or apostrophes."
            )
        return value.strip().capitalize()

    def validate_last_name(self, value):
        if not re.fullmatch(r"[A-Za-z']+", value.strip()):
            raise serializers.ValidationError(
                "Must contain only letters, spaces, hyphens, or apostrophes."
            )
        return value.strip().capitalize()

    def validate_birth_date(self, value):
        if value and value > datetime.date.today():
            raise serializers.ValidationError("Birth date must be in the past.")
        return value

    def validate_nationality(self, value):
        if value and not re.fullmatch(r"[A-Za-z]+", value.strip()):
            raise serializers.ValidationError("Nationality must contain only letters, spaces, or hyphens.")
        return value.replace("-","").replace(" ", "").strip().capitalize()

class AuthorReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = "__all__"

# -----------------------------Member-----------------------------------
class MemberWriteSerializer(serializers.ModelSerializer):
    phone = PhoneNumberField()
    class Meta:
        model = Member
        fields = ["first_name", "last_name", "email", "phone", "phone_type", "member_type"]

    def validate_first_name(self, value):
        if not value.strip().replace(" ","").replace("-",""):
            raise serializers.ValidationError("Name must be non empty")

        if not re.fullmatch(r"[A-Za-z]+", value):
            raise serializers.ValidationError("First name must contain only alphabets.")
        return value.strip().replace(" ", "").replace("-","").capitalize()

    def validate_last_name(self, value):
        if not re.fullmatch(r"[A-Za-z]+", value):
            raise serializers.ValidationError("Last name must contain only alphabets.")
        return value.strip().replace(" ", "").replace("-","").capitalize()

    def validate_member_type(self, value):
        allowed = [choice[0] for choice in MemberType.choices]
        if value not in allowed:
            raise serializers.ValidationError("Member type must be either 'Student' or 'Faculty'.")
        return value

    def validate_email(self, value):
        cleaned = value.strip().lower()
        if Member.objects.filter(email__iexact=cleaned).exists():
            raise serializers.ValidationError("This email is already registered with another member.")
        return cleaned

    def validate_phone(self, value):
        if Member.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already exists. Please use a different one.")
        return value

class MemberReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = "__all__"

# ----------------- Category -----------------
class CategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name", "description"]

    def validate_name(self, value):
        if not re.fullmatch(r"[A-Za-z ]+", value):
            raise serializers.ValidationError("Category name must contain only alphabets and spaces.")
        if Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Category with this name already exists.")
        return value.strip().replace("  ", " ")

class CategoryReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

# ----------------- Book -----------------
class BookWriteSerializer(serializers.ModelSerializer):
    library = serializers.PrimaryKeyRelatedField(queryset=Library.objects.all())
    class Meta:
        model = Book
        fields = ["title", "isbn", "publication_date", "total_copies", "library"]

    def validate_title(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Title cannot be empty or only spaces.")
        if Book.objects.filter(title__iexact=cleaned).exists():
            raise serializers.ValidationError("A book with this title already exists.")
        return cleaned

    def validate_isbn(self, value):
        if not value:
            return value  # Allow empty/null ISBN
        isbn = value.replace("-", "").replace(" ", "")
        isbn10_pattern = r"^\d{9}[\dX]$"
        isbn13_pattern = r"^\d{13}$"
        if not re.match(isbn10_pattern, isbn) and not re.match(isbn13_pattern, isbn):
            raise serializers.ValidationError("Invalid ISBN format. Must be ISBN-10 or ISBN-13.")
        if Book.objects.filter(isbn=isbn).exists():
            raise serializers.ValidationError("A book with this ISBN already exists.")
        return isbn

    def validate_total_copies(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total copies must be greater than zero.")
        return value

    def validate(self, attrs):
        library = attrs.get("library")
        if not Library.objects.filter(pk=getattr(library, "pk", library)).exists():
            raise serializers.ValidationError({"library": "Library ID does not exist."})
        return attrs

class BookReadSerializer(serializers.ModelSerializer):
    library = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    class Meta:
        model = Book
        fields = "__all__"

    def get_library(self, obj):
        return f"{obj.library.library_id} - ({obj.library.name})"

    def get_authors(self, obj):
        return [f"{a.first_name} {a.last_name}" for a in obj.authors.all()]

    def get_categories(self, obj):
        return [c.name for c in obj.categories.all()]

# ----------------- Borrowing -----------------
class BorrowingWriteSerializer(serializers.ModelSerializer):
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    class Meta:
        model = Borrowing
        fields = ["member", "book"]  # No 'status' in POST
        read_only_fields = ["borrow_date", "due_date", "late_fee", "return_date"]

    def validate(self, attrs):
        member = attrs.get("member")
        book = attrs.get("book")

        if not Member.objects.filter(pk=member.pk).exists():
            raise serializers.ValidationError({"member": "Member ID does not exist."})

        if not Book.objects.filter(pk=book.pk).exists():
            raise serializers.ValidationError({"book": "Book ID does not exist."})

        # Prevent duplicate active borrow
        if Borrowing.objects.filter(member=member, book=book, status=BorrowingStatus.HOLD).exists():
            raise serializers.ValidationError(
                {"detail": "This book is already borrowed by you and not yet returned."}
            )

        # Check available copies
        if book.available_copies <= 0:
            raise serializers.ValidationError({"book": "No copies of this book are currently available."})

        # Limit to 10 active borrows
        active_count = Borrowing.objects.filter(member=member, status=BorrowingStatus.HOLD).count()
        if active_count >= 10:
            raise serializers.ValidationError(
                {"detail": "You cannot borrow more than 10 books at the same time."}
            )

        return attrs

class BorrowingReturnSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=[BorrowingStatus.RETURNED])
    class Meta:
        model = Borrowing
        fields = ["status"]

    def validate(self, attrs):
        borrowing = self.instance
        if borrowing.status != BorrowingStatus.HOLD:
            raise serializers.ValidationError({"detail": "This borrowing is already returned."})
        return attrs

class BorrowingReadSerializer(serializers.ModelSerializer):
    member = serializers.StringRelatedField()
    book = serializers.StringRelatedField()
    class Meta:
        model = Borrowing
        fields = "__all__"

# ----------------- Review -----------------
class ReviewWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"

    def validate_rating(self, value):
        try:
            value = round(float(value), 1)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Rating must be a decimal number.")
        if not (1.0 <= value <= 5.0):
            raise serializers.ValidationError("Rating must be between 1.0 and 5.0.")
        return value

    def validate_comment(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Comment cannot be empty or only spaces.")
        if len(cleaned) > 500:
            raise serializers.ValidationError("Comment cannot exceed 500 characters.")
        return cleaned

    def validate(self, attrs):
        member = attrs.get("member")
        book = attrs.get("book")
        request = self.context.get("request")

        if not Member.objects.filter(pk=getattr(member, "pk", member)).exists():
            raise serializers.ValidationError({"member": "Member ID does not exist."})

        if not Book.objects.filter(pk=getattr(book, "pk", book)).exists():
            raise serializers.ValidationError({"book": "Book ID does not exist."})

        # Creation: block if review already exists
        if request and request.method == "POST":
            if Review.objects.filter(member=member, book=book).exists():
                raise serializers.ValidationError(
                    {"detail": "You have already reviewed this book. Please edit your existing review."}
                )

        # Update: ensure review exists for given member/book
        if request and request.method in ["PUT", "PATCH"]:
            if not Review.objects.filter(member=member, book=book).exists():
                raise serializers.ValidationError(
                    {"detail": "No review found for this member and book combination to update."}
                )

        return attrs

class ReviewReadSerializer(serializers.ModelSerializer):
    member = serializers.SerializerMethodField()
    book = serializers.SerializerMethodField()
    class Meta:
        model = Review
        fields = "__all__"

    def get_member(self, obj):
        return f"{obj.member.member_id} - ({obj.member.first_name} {obj.member.last_name}) - {obj.member.member_type}"

    def get_book(self, obj):
        return f"{obj.book.book_id} - {obj.book.title}"