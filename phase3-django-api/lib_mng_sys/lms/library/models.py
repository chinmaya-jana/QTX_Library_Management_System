from datetime import timedelta

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

# Function to calculate default due date (14 days from now)
def default_due_date():
    return timezone.now().date() + timedelta(days=14)

# Enum for member types
class MemberType(models.TextChoices):
    # 1st 'Student' is the actual value stored in the DB
    # 2nd 'Student' is the human-readable name shown in forms
    STUDENT = "student", "Student"
    FACULTY = "faculty", "Faculty"

# Enum for contact number types
class ContactType(models.TextChoices):
    MOBILE = 'mobile', 'Mobile'
    WORK = 'work', 'Work'
    HOME = 'home', 'Home'

# Address model
class Address(models.Model):
    street = models.CharField(max_length=100)
    district = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pin = models.CharField(max_length=10)
    country = models.CharField(max_length=50, default='India')

    class Meta:
        db_table = 'Address'  #custom table name in db
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        constraints = [
            models.UniqueConstraint(
                fields=['street', 'district', 'state', 'pin', 'country'],
                name='unique_address'
            )
        ]  # prevent duplicate addresses

    def __str__(self):
        return f"{self.street}, {self.district}, {self.state}, {self.pin}, {self.country}"

# Contact number model
class ContactNumber(models.Model):
    number = PhoneNumberField(unique=True) #unique contact number
    type = models.CharField(max_length=20, choices=ContactType.choices)

    class Meta:
        db_table = "contact"
        verbose_name = "Contact Detail"
        verbose_name_plural = "Contact Details"
    def __str__(self):
        return f"{self.number} ({self.type})"

class BookLibrary(models.Model):
    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    library = models.ForeignKey("Library", on_delete=models.CASCADE)

    class Meta:
        db_table = "book_library"
        verbose_name = "Book Library"
        verbose_name_plural = "Book Libraries"
        constraints = [
            UniqueConstraint(fields=['book', 'library'], name='unique_book_library')
        ]

    def __str__(self):
        return f"{self.book} - {self.library}"

class BookAuthor(models.Model):
    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    author = models.ForeignKey("Author", on_delete=models.CASCADE)

    class Meta:
        db_table = "book_author"
        verbose_name = "Book Authors"
        constraints = [
            UniqueConstraint(fields=['book', 'author'], name='unique_book_author')
        ]

    def __str__(self):
        return f"{self.book} - {self.author}"

class BookCategory(models.Model):
    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    category = models.ForeignKey("Category", on_delete=models.CASCADE)

    class Meta:
        db_table = "book_category"
        verbose_name = "Book Categories"
        constraints = [
            UniqueConstraint(fields=['book', 'category'], name='unique_book_category')
        ]

    def __str__(self):
        return f"{self.book} - {self.category}"

# Library model
class Library(models.Model):
    library_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True) # Must be unique
    campus_location = models.ForeignKey(Address, on_delete=models.PROTECT)
    contact_email = models.EmailField(unique=True, max_length=100)
    phone_number = models.OneToOneField(ContactNumber, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)  # on create
    updated_at = models.DateTimeField(auto_now=True)  # on every save

    # relationship
    books = models.ManyToManyField(
        'Book',
        through='BookLibrary',
        related_name='library_set'  # <-- added to avoid clash
    )

    class Meta:
        db_table = "libraries"
        ordering = ['library_id'] #ASC order, for DESC order use '-library_id'
        verbose_name = "Library Details" #human-readable names shown in the Django admin or forms
        verbose_name_plural = "Libraries Details"

    def __str__(self):
        return f"{self.library_id} - {self.name}"

# Author model
class Author(models.Model):
    author_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField()
    nationality = models.CharField(max_length=20, default='Indian')
    biography = models.TextField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)  # on create
    updated_at = models.DateTimeField(auto_now=True)  # on every save

    class Meta:
        db_table = "author"
        ordering = ['first_name', 'last_name'] #ASC order
        verbose_name = "Book Author"
        verbose_name_plural = "Book Authors"
        constraints = [
            UniqueConstraint(fields=['first_name', 'last_name', 'birth_date'], name='unique_name')
        ]

    def __str__(self):
        return f"{self.author_id} - {self.first_name} {self.last_name}"
# Member model
class Member(models.Model):
    member_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True, max_length=100)
    phone = models.OneToOneField(ContactNumber, on_delete=models.CASCADE, unique=True)
    member_type = models.CharField(max_length=20, choices=MemberType.choices)
    registration_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)  # on create
    updated_at = models.DateTimeField(auto_now=True)  # on every save

    class Meta:
        db_table = "member"
        ordering = ['registration_date'] #ASC order
        verbose_name = "Member detail" #Book categories
        verbose_name_plural = "Member details"

    def __str__(self):
        return f"{self.member_id} - ({self.first_name} {self.last_name}) - {self.member_type}"

# Book Category model
class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)  # on create
    updated_at = models.DateTimeField(auto_now=True)  # on every save

    class Meta:
        db_table = "category"
        ordering = ['name'] #ASC order
        verbose_name = "Book Genre" #Book categories
        verbose_name_plural = "Book Genres"

    def __str__(self):
        return f"{self.category_id} - {self.name}"

# Book model
class Book(models.Model):
    book_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    isbn = models.CharField(unique=True, max_length=13)
    publication_date = models.DateField()
    total_copies = models.PositiveIntegerField()
    available_copies = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  # on create
    updated_at = models.DateTimeField(auto_now=True)  # on every save

    # Relationship
    authors = models.ManyToManyField(Author, related_name='books', through="BookAuthor")
    libraries = models.ManyToManyField(
        'Library',
        through='BookLibrary',
        related_name='book_set'  # <-- added to avoid clash
    )
    categories = models.ManyToManyField(Category, related_name='books', through="BookCategory")

    class Meta:
        db_table = "book"
        verbose_name = "Book Details"
        verbose_name_plural = "Books Details"
        ordering = ['created_at'] #ASC order

    def __str__(self):
        return f"{self.book_id} - {self.title}"

# Book Borrowing model
class Borrowing(models.Model):
    borrowing_id = models.AutoField(primary_key=True)
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(default=default_due_date) # After 14 days from borrow_date
    return_date = models.DateTimeField(null=True, blank=True) # Fill when he/she will return
    late_fee = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)  # on create
    updated_at = models.DateTimeField(auto_now=True)  # on every save

    #Relationship
    member = models.ForeignKey('Member', on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)

    class Meta:
        db_table = "borrowing"
        ordering = ['due_date']
        verbose_name = "Borrowed Book"
        verbose_name_plural = "Borrowed Books"
        constraints = [
            UniqueConstraint(fields=['member', 'book'], name='unique_book_member')
        ]

    def __str__(self):
        return  f"{self.borrowing_id} - {self.member.member_id}: {self.member.first_name} {self.member.last_name}"

# Book review model
class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    rating = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(5.0)])
    comment = models.CharField(max_length=500)
    review_date = models.DateTimeField(auto_now=True) # updated when edited
    created_at = models.DateTimeField(auto_now_add=True)  # on create
    updated_at = models.DateTimeField(auto_now=True)  # on every save

    # Relationship
    member = models.ForeignKey('Member', on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)

    class Meta:
        db_table = "review"
        constraints = [
            UniqueConstraint(fields=['member', 'book'], name='unique_review_per_member_book')
        ]
        verbose_name = "Book Review"
        verbose_name_plural = "Book Reviews"
        ordering = ['-review_date'] #DESC order

    def __str__(self):
        return f"{self.review_id} - {self.member.member_id}: {self.rating}"
