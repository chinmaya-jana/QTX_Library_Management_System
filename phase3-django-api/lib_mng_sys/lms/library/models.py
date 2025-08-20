from decimal import Decimal

from django.db import models
from datetime import timedelta

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import UniqueConstraint, CASCADE
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

# Function to calculate default due date (14 days from now)
def default_due_date():
    return timezone.now().date() + timedelta(days=14)

class MemberType(models.TextChoices):
    STUDENT = 'student', 'Student'
    FACULTY = 'faculty', 'Faculty'

class PhoneType(models.TextChoices):
    MOBILE = 'mobile', 'Mobile'
    WORK = 'work', 'Work'
    HOME = 'home', 'Home'

class BorrowingStatus(models.TextChoices):
    HOLD = 'hold', 'Hold'          # Active borrow (book in hand)
    RETURNED = 'returned', 'Returned'  # Returned book

class BookAuthor(models.Model):
    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    author = models.ForeignKey("Author", on_delete=models.CASCADE)

    class Meta:
        db_table = "book_author"
        verbose_name = "Book Author"
        verbose_name_plural = "Book Authors"
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
    campus_location = models.TextField(max_length=250)
    contact_email = models.EmailField(unique=True, max_length=100)
    phone_number = PhoneNumberField(unique=True)
    phone_type = models.CharField(max_length=10, choices=PhoneType.choices)
    created_at = models.DateTimeField(auto_now_add=True)  # on create
    updated_at = models.DateTimeField(auto_now=True)  # on every save

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
    birth_date = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=20, default='Indian')
    biography = models.TextField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)  # on create
    updated_at = models.DateTimeField(auto_now=True)  # on every save

    class Meta:
        db_table = "author"
        ordering = ['first_name', 'last_name'] #ASC order
        verbose_name = "Book Author"
        verbose_name_plural = "Book Authors"
        constraints = [
            UniqueConstraint(fields=['first_name', 'last_name'], name='unique_name')
        ]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.author_id} - {self.first_name} {self.last_name}"

# Member model
class Member(models.Model):
    member_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True, max_length=100)
    phone = PhoneNumberField(unique=True)
    phone_type = models.CharField(max_length=10, choices=PhoneType.choices)
    member_type = models.CharField(max_length=20, choices=MemberType.choices)
    registration_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # on every save

    class Meta:
        db_table = "member"
        ordering = ['registration_date'] #ASC order
        verbose_name = "Member detail" #Book categories
        verbose_name_plural = "Member details"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

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
    title = models.CharField(max_length=200, unique=True)
    isbn = models.CharField(unique=True, max_length=13)
    publication_date = models.DateField()
    total_copies = models.PositiveIntegerField(default=0)
    available_copies = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)  # on create
    updated_at = models.DateTimeField(auto_now=True)  # on every save

    # one-to-many relationship
    library = models.ForeignKey(Library, on_delete=CASCADE)
    # many-to-many relationship
    authors = models.ManyToManyField(Author, related_name='books', through="BookAuthor")
    categories = models.ManyToManyField(Category, related_name='books', through="BookCategory")

    class Meta:
        db_table = "book"
        verbose_name = "Book Details"
        verbose_name_plural = "Books Details"
        ordering = ['created_at'] #ASC order

    @property
    def borrowed_books(self):
        return self.total_copies - self.available_copies

    @property
    def library_name(self):
        return f"{self.library.name}"

    @property
    def author_name(self):
        return ", ".join([author.full_name for author in self.authors.all()])

    @property
    def category_name(self):
        return ", ".join([category.name for category in self.categories.all()])

    def __str__(self):
        return f"{self.book_id} - {self.title}"

# Book Borrowing model
class Borrowing(models.Model):
    borrowing_id = models.AutoField(primary_key=True)
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(default=default_due_date) # After 14 days from borrow_date
    return_date = models.DateTimeField(null=True, blank=True) # Fill when he/she will return
    late_fee = models.FloatField(default=0.0)
    status = models.CharField(
        max_length=10,
        choices=BorrowingStatus.choices,
        default=BorrowingStatus.HOLD
    )
    updated_at = models.DateTimeField(auto_now=True)  # on every save

    #one-to-many relationship
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    class Meta:
        db_table = "borrowing"
        ordering = ['due_date']
        verbose_name = "Borrowed Book"
        verbose_name_plural = "Borrowed Books"


    @property
    def member_name(self):
        return f"{self.member.full_name}"

    @property
    def book_title(self):
        return f"{self.book.title}"

    def __str__(self):
        return f"{self.borrowing_id} - {self.member.full_name} - {self.status}"

# Book review model
class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    rating = models.DecimalField(
        max_digits=2, decimal_places=1,
        validators=[MinValueValidator(Decimal('1.0')), MaxValueValidator(Decimal('5.0'))])
    comment = models.TextField(max_length=500)
    review_date = models.DateTimeField(auto_now=True) # updated when edited
    created_at = models.DateTimeField(auto_now_add=True)  # on create

    # one-to-many relationship
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    class Meta:
        db_table = "review"
        constraints = [
            UniqueConstraint(fields=['member', 'book'], name='unique_review_per_member_book')
        ]
        verbose_name = "Book Review"
        verbose_name_plural = "Book Reviews"
        ordering = ['-review_date'] #DESC order

    def __str__(self):
        return f"{self.review_id} - {self.member.full_name}: {self.rating}"