from django.urls import path
from .views import (
    register,
    home,
    login,
    expadd,
    expense_list,
    delete_expense,
    budget_management,
    profile,
    logout_view,
    monthly_report,

)

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('home/', home, name='home'),
    path('add-expense/', expadd, name='expadd'),
    path('expenses/', expense_list, name='expense_list'),
    path('delete/<int:id>/', delete_expense, name='delete_expense'),
    path('budget/', budget_management, name='budget'),
    path('profile/', profile, name='profile'),
    path('logout/', logout_view, name='logout'),
    path('monthly-report/',monthly_report, name='monthly_report'),
]
