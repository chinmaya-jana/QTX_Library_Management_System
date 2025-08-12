import re

from django.db.models import Q
from django.utils import timezone
import phonenumbers
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    Address, ContactNumber, Library, Author, Member,
    Category, Book, Borrowing, Review,
    MemberType, ContactType
)

# Common Custom Validators
def validate_name(value):
    if not re.fullmatch(r"[A-Za-z\s\-']+", value.strip()):
        raise serializers.ValidationError(
            "Must contain only letters, spaces, hyphens, or apostrophes."
        )
    return value.replace(" ", "").replace("-","").strip()

def validate_phone_number(value):
    if not value:
        return None
    try:
        number = phonenumbers.parse(str(value), None)
        if not phonenumbers.is_valid_number(number):
            raise serializers.ValidationError("Invalid phone number.")
        return  phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException as e:
        raise serializers.ValidationError(f"Invalid phone number format: {e}")

# this is only for created_at and updated_at for each record
class TimestampMixin(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

# Address Serializer
class AddressSerializer(TimestampMixin):
    class Meta:
        model = Address
        fields = ['street', 'district', 'state', 'pin',
                  'country', 'created_at', 'updated_at']

    def validate_street(self, value):
        if not value.strip():
            raise serializers.ValidationError("Street must not be empty.")
        return value.strip()

    def validate_district(self, value):
        if not value.strip():
            raise serializers.ValidationError("District must not be empty.")
        return value.strip()

    def validate_state(self, value):
        if not value.strip():
            raise serializers.ValidationError("State must not be empty.")
        return value.strip()

    def validate_pin(self, value):
        if not value.strip():
            raise serializers.ValidationError("Pin must not be empty.")
        return value.strip()

    def validate_country(self, value):
        if not value.strip():
            raise serializers.ValidationError("Country must not be empty.")
        return value.strip()

# Contact number Serializer
class ContactNumberSerializer(TimestampMixin):
    number = serializers.CharField(validators=[validate_phone_number])

    class Meta:
        model = ContactNumber
        fields = ['number', 'type', 'created_at', 'updated_at']

    def validate_type(self, value):
        if value not in ContactType.values:
            raise serializers.ValidationError(f"Invalid contact type '{value}'.")
        return value

class BookMiniSerializer(serializers.ModelSerializer):
    authors = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['book_id', 'title', 'authors', 'categories']

    def get_authors(self, obj):
        return [f"{a.first_name} {a.last_name}" for a in obj.authors.all()]

    def get_categories(self, obj):
        return [c.name for c in obj.categories.all()]


class LibrarySerializer(TimestampMixin):
    library_id = serializers.IntegerField(read_only=True)
    campus_location = AddressSerializer(required=False, allow_null=True)
    phone_number = ContactNumberSerializer(required=False, allow_null=True)
    books = serializers.SerializerMethodField()

    class Meta:
        model = Library
        fields = [
            'library_id', 'name', 'campus_location',
            'contact_email', 'phone_number', 'books',
            'created_at', 'updated_at'
        ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Library name must not be empty.")
        if len(value) > 100:
            raise serializers.ValidationError("Library name must not exceed 100 characters.")
        return value

    def validate_contact_email(self, value):
        value = value.strip().lower()
        if Library.objects.filter(contact_email__iexact=value).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError("This contact email is already used by another library.")
        return serializers.EmailField().to_internal_value(value)

    def validate(self, data):
        phone_data = data.get('phone_number')
        if phone_data and phone_data.get('number'):
            number = phone_data['number']
            if ContactNumber.objects.filter(number=number).exclude(pk=getattr(self.instance.phone_number, 'pk', None)).exists():
                raise serializers.ValidationError({
                    "status": "error",
                    "message": f"Phone number {number} is already in use.",
                    "code": 400
                })

        name = data.get('name', '').strip()
        campus_location_data = data.get('campus_location')

        if name and campus_location_data:
            if self._is_duplicate(name, campus_location_data, exclude_id=self.instance.id if self.instance else None):
                raise serializers.ValidationError({
                    "status": "error",
                    "message": "A library with the same name and campus address already exists.",
                    "code": 400
                })
        return data

    def _is_duplicate(self, name, campus_data, exclude_id=None):
        queryset = Library.objects.filter(name__iexact=name)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        for lib in queryset:
            if lib.campus_location:
                match = all(
                    getattr(lib.campus_location, field) == campus_data.get(field)
                    for field in ['street', 'district', 'state', 'pin', 'country']
                )
                if match:
                    return True
        return False

    def create(self, validated_data):
        campus_location_data = validated_data.pop('campus_location', None)
        phone_number_data = validated_data.pop('phone_number', None)

        if campus_location_data:
            campus_location = Address.objects.create(**campus_location_data)
            validated_data['campus_location'] = campus_location
        else:
            validated_data['campus_location'] = None

        if phone_number_data:
            phone_number = ContactNumber.objects.create(**phone_number_data)
            validated_data['phone_number'] = phone_number
        else:
            validated_data['phone_number'] = None

        return super().create(validated_data)

    def update(self, instance, validated_data):
        campus_location_data = validated_data.pop('campus_location', None)
        phone_number_data = validated_data.pop('phone_number', None)

        if campus_location_data:
            if instance.campus_location:
                for attr, val in campus_location_data.items():
                    setattr(instance.campus_location, attr, val)
                instance.campus_location.save()
            else:
                instance.campus_location = Address.objects.create(**campus_location_data)

        if phone_number_data:
            if instance.phone_number:
                for attr, val in phone_number_data.items():
                    setattr(instance.phone_number, attr, val)
                instance.phone_number.save()
            else:
                instance.phone_number = ContactNumber.objects.create(**phone_number_data)

        return super().update(instance, validated_data)

    def get_books(self, obj):
        books = obj.book_set.all()
        if not books.exists():
            return {"message": "No books available in this library."}
        return BookMiniSerializer(books, many=True).data

class AuthorSerializer(TimestampMixin):
    author_id = serializers.IntegerField(read_only=True)
    books = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Author
        fields = [
            'author_id', 'first_name', 'last_name', 'birth_date',
            'nationality', 'biography', 'books',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['books']
    def validate_first_name(self, value):
        return validate_name(value)

    def validate_last_name(self, value):
        return validate_name(value)

    def validate_nationality(self, value):
        return value.strip() if value else None

    def validate_biography(self, value):
        return value.strip() if value else None

    def validate(self, data):
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        birth_date = data.get('birth_date')

        query = Q(first_name__iexact=first_name, last_name__iexact=last_name)
        if birth_date:
            query &= Q(birth_date=birth_date)

        existing = Author.objects.filter(query)
        # Prevent duplicate insertion
        if self.instance is None and existing.exists():
            raise ValidationError({
                "status": "error",
                "message": "Author with the same name and birth date already exists.",
                "code": 400
            })
        # Prevent duplicate on update (excluding current)
        if self.instance and existing.exclude(id=self.instance.id).exists():
            raise ValidationError({
                "status": "error",
                "message": "Another author with the same name and birth date already exists.",
                "code": 400
            })

        return data

    def get_books(self, obj):
        books = obj.book_set.prefetch_related('categories').all()
        return [
            {
                "book_id": book.id,
                "title": book.title,
                "categories": [category.name for category in book.categories.all()]
            }
            for book in books
        ]

# Member Serializer
class MemberSerializer(TimestampMixin):
    phone = ContactNumberSerializer()

    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'email', 'phone',
                  'member_type', 'registration_date', 'created_at', 'updated_at']
        read_only_fields = ['registration_date']

    def validate_first_name(self, value):
        return validate_name(value)

    def validate_last_name(self, value):
        return validate_name(value)

    def validate_email(self, value):
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError("Email is required.")

        # Check if already exists (for create only)
        if not self.instance and Member.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(f"Member with email '{value}' already exists.")
        return serializers.EmailField().to_internal_value(value)

    def validate_member_type(self, value):
        normalized = value.lower()
        allowed = ['student', 'faculty']
        if normalized not in allowed:
            raise serializers.ValidationError(f"member_type must be one of {allowed}")
        return normalized.capitalize()  # DB stores it as capitalized

    def validate(self, data):
        phone_data = data.get('phone')
        if phone_data:
            number = phone_data.get('number')
            if ContactNumber.objects.filter(number=number).exists():
                raise ValidationError({
                    "status": "error",
                    "message": f"Phone number '{number}' is already in use.",
                    "code": 400
                })

            phone_type = phone_data.get('type', '').lower()
            if phone_type not in [t.lower() for t in ContactType.values]:
                raise ValidationError({
                    "status": "error",
                    "message": f"Invalid contact type '{phone_type}'.",
                    "code": 400
                })

            # Normalize phone type
            phone_data['type'] = phone_type.capitalize()
        return data

    def create(self, validated_data):
        phone_data = validated_data.pop('phone')
        phone_serializer = ContactNumberSerializer(data=phone_data)
        phone_serializer.is_valid(raise_exception=True)

        phone = phone_serializer.save()
        validated_data['phone'] = phone

        return super().create(validated_data)

    def update(self, instance, validated_data):
        phone_data = validated_data.pop('phone', None)

        if phone_data:
            phone_type = phone_data.get('type', '').lower()
            if phone_type not in [t.lower() for t in ContactType.values]:
                raise ValidationError({
                    "status": "error",
                    "message": f"Invalid contact type '{phone_type}'.",
                    "code": 400
                })
            phone_data['type'] = phone_type.capitalize()

            phone_serializer = ContactNumberSerializer(instance.phone, data=phone_data)
            phone_serializer.is_valid(raise_exception=True)
            phone_serializer.save()

        return super().update(instance, validated_data)

# Category Serializer
class BookTitleAuthorSerializer(serializers.ModelSerializer):
    authors = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['title', 'authors']

    def get_authors(self, obj):
        return [f"{author.first_name} {author.last_name}" for author in obj.authors.all()]

# Category Serializer with nested books
class CategorySerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(read_only=True)
    books = BookTitleAuthorSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['category_id', 'name', 'description', 'books', 'created_at', 'updated_at']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Category name must not be empty.")
        return value.strip()

    def validate_description(self, value):
        if not value:
            return None
        return value.strip()

    def update(self, instance, validated_data):
        # Handle update safely
        name = validated_data.get('name', instance.name)
        description = validated_data.get('description', instance.description)

        instance.name = name.strip()
        instance.description = description.strip() if description else None
        instance.save()

        return instance

# Book Serializer
class BookSerializer(TimestampMixin):
    book_id = serializers.IntegerField(read_only=True)
    library = serializers.DictField(write_only=True)
    authors = serializers.ListField(child=serializers.DictField(), write_only=True)
    categories = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = Book
        fields = [
            'book_id', 'title', 'isbn', 'publication_date',
            'total_copies', 'available_copies',
            'library', 'authors', 'categories',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['publication_date']

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Book title must not be empty.")
        return value.strip()

    def validate_isbn(self, value):
        if value is None:
            return None
        clean = value.replace("-", "").replace(" ", "")
        if not clean.isdigit() or len(clean) not in (10, 13):
            raise serializers.ValidationError("ISBN must be 10 or 13 digits.")
        if not (clean.startswith("978") or clean.startswith("979")):
            raise serializers.ValidationError("ISBN must start with 978 or 979.")
        return clean

    def validate_total_copies(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total copies must be positive.")
        return value

    def validate(self, data):
        total = data.get('total_copies')
        available = data.get('available_copies')

        if available is not None and available < 0:
            raise serializers.ValidationError("Available copies cannot be negative.")
        if total is not None and available is not None and available > total:
            raise serializers.ValidationError("Available copies cannot exceed total copies.")

        return data

    def _get_or_create_library(self, lib_data):
        name = lib_data.get('name', '').strip()
        if not name:
            raise serializers.ValidationError("Library name is required.")

        library, _ = Library.objects.get_or_create(name=name)
        return library

    def _get_or_create_author(self, author_data):
        fname = author_data.get('first_name', '').strip()
        lname = author_data.get('last_name', '').strip()
        bdate = author_data.get('birth_date')

        if not fname or not lname:
            raise serializers.ValidationError("Author must include first_name and last_name.")

        author, _ = Author.objects.get_or_create(
            first_name__iexact=fname,
            last_name__iexact=lname,
            birth_date=bdate,
            defaults={
                'first_name': fname,
                'last_name': lname,
                'birth_date': bdate,
                'nationality': author_data.get('nationality'),
                'biography': author_data.get('biography')
            }
        )
        return author

    def _get_or_create_category(self, cat_data):
        name = cat_data.get('name', '').strip()
        if not name:
            raise serializers.ValidationError("Category name is required.")

        category, _ = Category.objects.get_or_create(
            name__iexact=name,
            defaults={
                'name': name,
                'description': cat_data.get('description')
            }
        )
        return category

    def create(self, validated_data):
        library_data = validated_data.pop('library')
        author_list = validated_data.pop('authors')
        category_list = validated_data.pop('categories')

        library = self._get_or_create_library(library_data)
        authors = [self._get_or_create_author(a) for a in author_list]
        categories = [self._get_or_create_category(c) for c in category_list]

        book = Book.objects.create(library=library, **validated_data)
        book.authors.set(authors)
        book.categories.set(categories)
        return book

    def update(self, instance, validated_data):
        library_data = validated_data.pop('library', None)
        author_list = validated_data.pop('authors', None)
        category_list = validated_data.pop('categories', None)

        if library_data:
            instance.library = self._get_or_create_library(library_data)

        if author_list:
            authors = [self._get_or_create_author(a) for a in author_list]
            instance.authors.set(authors)

        if category_list:
            categories = [self._get_or_create_category(c) for c in category_list]
            instance.categories.set(categories)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def delete(self, instance):
        # Clean related data
        instance.reviews.all().delete()
        instance.borrowings.all().delete()
        instance.authors.clear()
        instance.categories.clear()
        instance.delete()

# Borrowing Serializer
class BorrowingSerializer(TimestampMixin):
    borrowing_id = serializers.IntegerField(read_only=True)
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Borrowing
        fields = ['borrowing_id', 'borrow_date', 'due_date', 'return_date', 'late_fee', 'member', 'book', 'created_at', 'updated_at']
        read_only_fields = ['borrow_date', 'due_date']

    def validate_return_date(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Return date cannot be in the future.")
        return value

    def validate_late_fee(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Late fee must be a positive amount.")
        return float(round(value, 2)) if value is not None else None

    def validate(self, data):
        member, book = data['member'], data['book']
        return_date = data['return_date']

        # Check if member exists
        if not Member.objects.filter(pk=member.pk).exists():
            raise serializers.ValidationError({
                "status": "error",
                "message": f"Invalid member_id '{member.pk}': Member does not exist.",
                "code": 400
            })

        # Check if book exists
        if not Book.objects.filter(pk=book.pk).exists():
            raise serializers.ValidationError({
                "status": "error",
                "message": f"Invalid book_id '{book.pk}': Book does not exist.",
                "code": 400
            })

        #Maximum concurrent borrows: 10
        limit = 10
        active = Borrowing.objects.filter(member=member, return_date__isnull=True).count()
        if active >= limit:
            raise serializers.ValidationError({
                "status": "error",
                "message": f"Member has reached borrowing limit ({limit}).",
                "code": 400
            })
        # Prevent borrowing already borrowed book by same member
        if Borrowing.objects.filter(member=member, book=book, return_date__isnull=True).exists():
            raise serializers.ValidationError({
                "status": "error",
                "message": "This book is already borrowed by the member and not returned.",
                "code": 400
            })

        # Ensure book availability
        if self.instance is None and book.available_copies <= 0:
            raise serializers.ValidationError(f"The book '{book.title}' is currently not available.")

        # Return date logic (must be after borrow_date)
        if data.get('return_date') and data['return_date'] < data.get('borrow_date', timezone.now().date()):
            raise serializers.ValidationError("Return date cannot be before borrow date.")

        return data

    def create(self, validated_data):
        book = validated_data['book']
        book.available_copies -= 1
        book.save()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return_date = validated_data.get('return_date')
        if return_date and not instance.return_date:
            book = instance.book
            book.available_copies += 1
            book.save()
        return super().update(instance, validated_data)


# Review Serializer
class ReviewSerializer(TimestampMixin):
    review_id = serializers.IntegerField(read_only=True)
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Review
        fields = ['review_id', 'rating', 'comment', 'review_date', 'member', 'book', 'created_at', 'updated_at']
        read_only_fields = ['review_date']

    def to_internal_value(self, data):
        # check member_id exist in db or not
        member_id = data.get('member')
        if not Member.objects.filter(pk=member_id).exists():
            raise ValidationError({
                "status": "error",
                "message": f"Invalid member_id '{member_id}': Member does not exist.",
                "code": 400
            })

        book_id = data.get('book')
        if not Book.objects.filter(pk=book_id).exists():
            raise ValidationError({
                "status": "error",
                "message": f"Invalid book_id '{book_id}': Book not found.",
                "code": 400
            })
        return super().to_internal_value(data)

    def validate_rating(self, value):
        if value < 1.0 or value > 5.0:
            raise serializers.ValidationError("Rating must be between 1.0 and 5.0.")
        return round(value, 1)

    def validate_comment(self, value):
        # remove whitespace and limiting the comment length
        if value:
            value = value.strip()
            if len(value) > 500:
                raise serializers.ValidationError("Comment must not exceed 500 characters.")
        return value

    def validate(self, data):
        if self.instance is None:
            if Review.objects.filter(member=data['member'], book=data['book']).exists():
                raise ValidationError({
                    "status": "error",
                    "message": "This member has already submitted a review for this book.",
                    "code": 400
                })
        return data

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance.review_date = timezone.now().date()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance