from django.db import models

# Create your models here.

class user(models.Model):
    fname = models.CharField(max_length=30)
    lname = models.CharField(max_length=30)
    email = models.CharField(max_length=50)
    mobile = models.CharField(max_length=10)
    password = models.CharField(max_length=16)
    address = models.TextField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.fname

class expense(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"{self.user.fname} - {self.amount}"
class budget(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    month = models.DateField() 
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.fname} - {self.month}"
