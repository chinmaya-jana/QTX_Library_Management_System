import re

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

def validate_isbn(value):
    if value is None:
        return None
    clean = value.replace("-", "").replace(" ", "")
    if not clean.isdigit() or len(clean) not in (10, 13):
        raise serializers.ValidationError("ISBN must be 10 or 13 digits.")
    if not (clean.startswith("978") or clean.startswith("979")):
        raise serializers.ValidationError("ISBN must start with 978 or 979.")
    return clean

# Address Serializer
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['street', 'district', 'state', 'pin', 'country']

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
class ContactNumberSerializer(serializers.ModelSerializer):
    number = serializers.CharField(validators=[validate_phone_number])

    class Meta:
        model = ContactNumber
        fields = ['number', 'type']

    def validate_type(self, value):
        if value not in ContactType.values:
            raise serializers.ValidationError(f"Invalid contact type '{value}'.")
        return value

# Library Serializer
class LibrarySerializer(serializers.ModelSerializer):
    campus_location = AddressSerializer(required=False, allow_null=True)
    phone_number = ContactNumberSerializer(required=False, allow_null=True)

    class Meta:
        model = Library
        fields = ['name', 'campus_location', 'contact_email', 'phone_number']

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Library name must not be empty.")
        if len(value) > 100:
            raise serializers.ValidationError("Library name must not exceed 100 characters.")
        return value

    def validate_contact_email(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Email is required")
        return serializers.EmailField().to_internal_value(value)

    def _is_duplicate(self, name, campus_data, exclude_id=None):
        queryset = Library.objects.filter(name_iexact= name)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        for lib in queryset:
            if lib.campus_location:
                match = all (
                    getattr(lib.campus_location, field) == campus_data.get(field)
                    for field in ['street', 'district', 'state', 'pin', 'country']
                )
                if match:
                    return True
        return False

    def validate(self, data):
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

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['first_name', 'last_name', 'birth_date', 'nationality', 'biography']

    def validate_first_name(self, value):
        return validate_name(value)

    def validate_last_name(self, value):
        return validate_name(value)

    def validate_nationality(self, value):
        if not value:
            return None
        return value.strip()

    def validate_biography(self, value):
        if not value:
            return None
        return value.strip()

    def validate(self, data):
        if Author.objects.filter(
                first_name__iexact=data['first_name'].strip(),
                last_name__iexact=data['last_name'].strip(),
                birth_date=data.get('birth_date')
            ).exists():
            raise serializers.ValidationError("Author with this name and birth date already exists.")
        return data


# Member Serializer
class MemberSerializer(serializers.ModelSerializer):
    phone = ContactNumberSerializer()

    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'email', 'phone', 'member_type', 'registration_date']
        read_only_fields = ['registration_date']

    def validate_first_name(self, value):
        return validate_name(value)

    def validate_last_name(self, value):
        return validate_name(value)

    def validate_member_type(self, value):
        if value not in MemberType.values:
            raise serializers.ValidationError(f"Invalid member_type '{value}'.")
        return value

    def validate_email(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Email is required")
        return serializers.EmailField().to_internal_value(value)

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
            phone_serializer = ContactNumberSerializer(instance.phone, data=phone_data)
            phone_serializer.is_valid(raise_exception=True)
            phone_serializer.save()
        return super().update(instance, validated_data)


# Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'description']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Category name must not be empty.")
        return value.strip()

    def validate_description(self, value):
        if not value:
            return None
        return value.strip()


# Book Serializer
class BookSerializer(serializers.ModelSerializer):
    library = serializers.PrimaryKeyRelatedField(queryset=Library.objects.all())
    authors = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), many=True)
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True)

    class Meta:
        model = Book
        fields = [
            'title', 'isbn', 'publication_date',
            'total_copies', 'available_copies', 'library', 'authors', 'categories'
        ]
        read_only_fields = ['publication_date']

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title must not be empty.")
        return value.strip()

    def validate_isbn(self, value):
        return validate_isbn(value)

    def validate_total_copies(self, value):
        if value <= 0:
            raise serializers.ValidationError("total_copies must be positive.")
        return value

    def validate(self, data):
        available = data.get('available_copies', getattr(self.instance, 'available_copies', None))
        total = data.get('total_copies', getattr(self.instance, 'total_copies', None))

        if available is not None and available < 0:
            raise serializers.ValidationError("available_copies cannot be negative.")
        if total is not None and available is not None and available > total:
            raise serializers.ValidationError("available_copies cannot exceed total_copies.")
        return data


# Borrowing Serializer
class BorrowingSerializer(serializers.ModelSerializer):
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Borrowing
        fields = ['borrow_date', 'due_date', 'return_date', 'late_fee', 'member', 'book']
        read_only_fields = ['borrow_date']

    def validate_due_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value

    def validate_return_date(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Return date cannot be in the future.")
        return value

    def validate(self, data):
        member = data.get('member')
        book = data.get('book')
        due_date = data.get('due_date')
        return_date = data.get('return_date')

        # Ensure book availability
        if self.instance is None and book.available_copies <= 0:
            raise serializers.ValidationError({
                "status": "error",
                "message": f"The book '{book.title}' is currently not available.",
                "code": 400
            })

        # Prevent duplicate borrow without return
        overlapping = Borrowing.objects.filter(member=member, book=book, return_date__isnull=True)
        if self.instance:
            overlapping = overlapping.exclude(pk=self.instance.pk)
        if overlapping.exists():
            raise serializers.ValidationError({
                "status": "error",
                "message": f"Member '{member}' has already borrowed this book and has not returned it.",
                "code": 400
            })

        borrow_date = self.instance.borrow_date if self.instance else timezone.now().date()
        if return_date and return_date < borrow_date:
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
class ReviewSerializer(serializers.ModelSerializer):
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Review
        fields = ['rating', 'comment', 'review_date', 'member', 'book']
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
        if Review.objects.filter(member=data['member'], book=data['book']).exists():
            raise ValidationError({
                "status": "error",
                "message": "This member has already submitted a review for this book.",
                "code": 400
            })
        return data