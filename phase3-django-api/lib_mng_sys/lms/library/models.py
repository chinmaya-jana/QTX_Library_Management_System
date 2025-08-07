from enum import unique

from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.
class Address(models.Model):
    street = models.CharField(max_length=100)
    district = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pin = models.CharField(max_length=10)
    country = models.CharField(max_length=50, default=['India'])

    def __str__(self):
        return f"{self.street}, {self.district}, {self.state} - {self.pin}"

class ContactNumber(models.Model):
    number = PhoneNumberField(region=['IN']) #example: 'US'
    type = models.CharField(max_length=20, choices=[('mobile', 'Mobile'), ('work', 'Work'), ('home', 'Home')])

    def __str__(self):
        return f"{self.number} ({self.type})"

class Library(models.Model):
    library_id = models.CharField(primary_key=True, max_length=10) #example: "LIB0210"
    name = models.CharField(max_length=100)
    campus_location = models.OneToOneField(Address,on_delete=models.CASCADE, null=True, blank=True)
    contact_email = models.EmailField(unique=True, max_length=100)
    phone_number = models.OneToOneField(ContactNumber, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.library_id} - {self.name}"

class Author(models.Model):
    author_id = models.CharField(primary_key=True, max_length=10) #example: 'ATR3019'
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField()
    nationality = models.CharField(max_length=20)
    biography = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.author_id} - {self.first_name + " " + self.last_name}"

class Member(models.Model):
    member_id = models.CharField(primary_key=True, max_length=10) #example: 'MBR0031'
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.OneToOneField(ContactNumber, on_delete=models.CASCADE, null=True, blank=True)
