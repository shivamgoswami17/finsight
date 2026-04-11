from django.contrib import admin
from .models import user , expense , budget

# Register your models here.



class user_(admin.ModelAdmin):
    list_display = ['id','fname','lname','email','mobile','password','address','city','state']

class expense_(admin.ModelAdmin):
    list_display = ['id','date','amount','category','description']

class budget_(admin.ModelAdmin):
    list_display = ['id','month','amount']

admin.site.register(user,user_)
admin.site.register(expense,expense_)
admin.site.register(budget,budget_)