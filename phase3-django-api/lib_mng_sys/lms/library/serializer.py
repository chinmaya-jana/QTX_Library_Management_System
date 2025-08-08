import re
from datetime import timezone

import phonenumbers
from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import (
    Address, ContactNumber, Library, Author, Member,
    Category, Book, Borrowing, Review,
    MemberType, ContactType
)

# Validators
def validate_name(value):
    if not re.fullmatch(r"[A-Za-z\s\-']+", value.strip()):
        raise serializers.ValidationError(
            "Must contain only letters, spaces, hyphens, or apostrophes."
        )
    return value.strip()

def validate_phone_number(value):
    if not value:
        return None
    try:
        number = phonenumbers.parse(str(value), None)
        if not phonenumbers.is_valid_number(number):
            raise serializers.ValidationError("Invalid phone number.")
        return  phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException as e:
        raise serializers.ValidationError("Invalid phone number format: {e}")

def validate_isbn(value):
    if value is None:
        return None
    clean = value.replace("-", "").replace(" ", "")
    if not clean.isdigit() or len(clean) not in (10, 13):
        raise serializers.ValidationError("ISBN must be 10 or 13 digits.")
    if not (clean.startswith("978") or clean.startswith("979")):
        raise serializers.ValidationError("ISBN must start with 978 or 979.")
    return clean

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

class ContactNumberSerializer(serializers.ModelSerializer):
    number = serializers.CharField(validators=[validate_phone_number])

    class Meta:
        model = ContactNumber
        fields = ['number', 'type']

    def validate_type(self, value):
        if value not in ContactType.values:
            raise serializers.ValidationError(f"Invalid contact type '{value}'.")
        return value

class LibrarySerializer(serializers.ModelSerializer):
    campus_location = AddressSerializer(required=False, allow_null=True)
    phone_number = ContactNumberSerializer(required=False, allow_null=True)

    class Meta:
        model = Library
        fields = ['name', 'campus_location', 'contact_email', 'phone_number']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Library name must not be empty.")
        return value.strip()

    def validate_contact_email(self, value):
        # EmailField already does email validation
        return value

    def validate(self, data):
        # Optional: You could check uniqueness or custom validations here
        return data

    def create(self, validated_data):
        # Handle nested create for campus_location and phone_number
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
        # Handle nested update for campus_location and phone_number
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
        fields = ['author_id', 'first_name', 'last_name', 'birth_date', 'nationality', 'biography']

    def validate_first_name(self, value):
        return validate_name(value)

    def validate_last_name(self, value):
        return validate_name(value)


# Member Serializer
class MemberSerializer(serializers.ModelSerializer):
    phone = ContactNumberSerializer()

    class Meta:
        model = Member
        fields = ['member_id', 'first_name', 'last_name', 'email', 'phone', 'member_type', 'registration_date']
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
        # EmailField already does email validation
        return value

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
        fields = ['category_id', 'name', 'description']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Category name must not be empty.")
        return value.strip()


# Book Serializer
class BookSerializer(serializers.ModelSerializer):
    library = serializers.PrimaryKeyRelatedField(queryset=Library.objects.all())
    authors = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), many=True)
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True)

    class Meta:
        model = Book
        fields = [
            'book_id', 'title', 'isbn', 'publication_date',
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
        # Validate copies consistency
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
        fields = ['borrowing_id', 'borrow_date', 'due_date', 'return_date', 'late_fee', 'member', 'book']
        read_only_fields = ['borrow_date']

    def validate_due_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value


# Review Serializer
class ReviewSerializer(serializers.ModelSerializer):
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Review