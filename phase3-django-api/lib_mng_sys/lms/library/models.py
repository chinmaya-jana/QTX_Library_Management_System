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

# Abstract Base Class
class TimeStampedModel(models.Model):
    #Abstract model that adds created_at and updated_at timestamps
    created_at = models.DateTimeField(auto_now_add=True)  # on create
    updated_at = models.DateTimeField(auto_now=True)      # on every save

    class Meta:
        abstract = True   # ensures no separate table is created

# Address model
class Address(TimeStampedModel):
    street = models.CharField(max_length=100)
    district = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pin = models.CharField(max_length=10)
    country = models.CharField(max_length=50, default='India')

    class Meta:
        db_table = 'Address'  #custom table name in db
        verbose_name = "Address"
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.street}, {self.district}, {self.state}, {self.pin}, {self.country}"

# Contact number model
class ContactNumber(TimeStampedModel):
    number = PhoneNumberField(blank=True, null=True) #example: 'US'
    type = models.CharField(max_length=20, choices=ContactType.choices)

    class Meta:
        db_table = "contact"
        verbose_name = "Contact Detail"
        verbose_name_plural = "Contact Details"
    def __str__(self):
        return f"{self.number} ({self.type})"

class BookLibrary(TimeStampedModel):
    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    library = models.ForeignKey("Library", on_delete=models.CASCADE)

    class Meta:
        db_table = "book_library"
        verbose_name = "Book Library"
        verbose_name_plural = "Book Libraries"
        unique_together = ('book', 'library')

    def __str__(self):
        return f"{self.book} - {self.library}"

class BookAuthor(TimeStampedModel):
    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    author = models.ForeignKey("Author", on_delete=models.CASCADE)

    class Meta:
        db_table = "book_author"
        verbose_name = "Book Authors"
        unique_together = ('book', 'author')

    def __str__(self):
        return f"{self.book} - {self.author}"

class BookCategory(TimeStampedModel):
    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    category = models.ForeignKey("Category", on_delete=models.CASCADE)

    class Meta:
        db_table = "book_category"
        verbose_name = "Book Categories"
        unique_together = ('book', 'category')

    def __str__(self):
        return f"{self.book} - {self.category}"

# Library model
class Library(TimeStampedModel):
    library_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    campus_location = models.OneToOneField('Address', on_delete=models.CASCADE)
    contact_email = models.EmailField(unique=True, max_length=100)
    phone_number = models.OneToOneField('ContactNumber', unique=True, on_delete=models.CASCADE)

    # relationship
    books = models.ManyToManyField('Book', related_name='libraries', blank=True)

    class Meta:
        db_table = "libraries"
        ordering = ['library_id'] #ASC order, for DESC order use '-library_id'
        verbose_name = "Library Details" #human-readable names shown in the Django admin or forms
        verbose_name_plural = "Libraries Details"

    def __str__(self):
        return f"{self.library_id} - {self.name}"

# Author model
class Author(TimeStampedModel):
    author_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField()
    nationality = models.CharField(max_length=20, default='Indian')
    biography = models.CharField(max_length=200)

    class Meta:
        db_table = "author"
        ordering = ['first_name', 'last_name'] #ASC order
        verbose_name = "Book Author"
        verbose_name_plural = "Book Authors"

    def __str__(self):
        return f"{self.author_id} - {self.first_name} {self.last_name}"
# Member model
class Member(TimeStampedModel):
    member_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True, max_length=100)
    phone = models.OneToOneField(ContactNumber, on_delete=models.CASCADE, unique=True)
    member_type = models.CharField(max_length=20, choices=MemberType.choices)
    registration_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "member"
        ordering = ['registration_date'] #ASC order
        verbose_name = "Member detail" #Book categories
        verbose_name_plural = "Member details"

    def __str__(self):
        return f"{self.member_id} - ({self.first_name} {self.last_name}) - {self.member_type}"

# Book Category model
class Category(TimeStampedModel):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)

    class Meta:
        db_table = "category"
        ordering = ['name'] #ASC order
        verbose_name = "Book Genre" #Book categories
        verbose_name_plural = "Book Genres"

    def __str__(self):
        return f"{self.category_id} - {self.name}"

# Book model
class Book(TimeStampedModel):
    book_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    isbn = models.CharField(unique=True, max_length=13)
    publication_date = models.DateField()
    total_copies = models.PositiveIntegerField()
    available_copies = models.PositiveIntegerField()

    # Relationship
    authors = models.ManyToManyField('Author', related_name='books', through="BookAuthor")
    categories = models.ManyToManyField('Category', related_name='books', through="BookCategory")

    class Meta:
        db_table = "book"
        verbose_name = "Book Details"
        verbose_name_plural = "Books Details"
        ordering = ['created_at'] #ASC order

    def __str__(self):
        return f"{self.book_id} - {self.title}"

# Book Borrowing model
class Borrowing(TimeStampedModel):
    borrowing_id = models.AutoField(primary_key=True)
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(default=default_due_date) # After 14 days from borrow_date
    return_date = models.DateTimeField(null=True, blank=True) # Fill when he/she will return
    late_fee = models.FloatField(default=0.0)

    #Relationship
    member = models.ForeignKey('Member', on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)

    class Meta:
        db_table = "borrowing"
        ordering = ['due_date']
        verbose_name = "Borrowed Book"
        verbose_name_plural = "Borrowed Books"

    def __str__(self):
        return  f"{self.borrowing_id} - {self.member.member_id}: {self.member.first_name} {self.member.last_name}"

# Book review model
class Review(TimeStampedModel):
    review_id = models.AutoField(primary_key=True)
    rating = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(5.0)])
    comment = models.CharField(max_length=500)
    review_date = models.DateTimeField(auto_now=True) # updated when edited

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
