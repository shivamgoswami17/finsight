from django.shortcuts import render, redirect, get_object_or_404
from .models import user, expense, budget
from django.db.models import Sum
from datetime import datetime, date
from django.contrib import messages
from decimal import Decimal  


# ---------------- HOME ----------------
def home(request):
    uid = request.session.get('user_id')
    if not uid:
        return redirect('login')

    today = date.today()

    current_budget = budget.objects.filter(
        user_id=uid,
        month__year=today.year,
        month__month=today.month
    ).first()

    
    total_expense = expense.objects.filter(
        user_id=uid,
        date__year=today.year,
        date__month=today.month
    ).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')

    remaining = Decimal('0')

    if current_budget:
        remaining = current_budget.amount - total_expense

        # ⚠ Budget notifications
        if remaining <= Decimal('0'):
            messages.warning(request, "Your budget for this month is finished!")
        elif remaining <= current_budget.amount * Decimal('0.2'):
            messages.warning(request, "You have used 80% of your monthly budget!")

    recent_expense = expense.objects.filter(user_id=uid).order_by('-date')[:5]

    context = {
        'total_expense': total_expense,
        'budget': current_budget,
        'remaining': remaining,
        'recent_expense': recent_expense,
    }

    return render(request, 'home.html', context)

# ---------------- LOGIN ----------------
def login(request):
    if request.method == 'POST':
        email = request.POST.get('txtemail')
        password = request.POST.get('txtpassword')

        usr = user.objects.filter(email=email, password=password).first()

        if usr:
            request.session['user_id'] = usr.id
            request.session['user_name'] = usr.fname
            return redirect('home')

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


# ---------------- REGISTER ----------------
def register(request):
    if request.method == 'POST':
        obj = user()
        obj.fname = request.POST.get('txtfname')
        obj.lname = request.POST.get('txtlname')
        obj.email = request.POST.get('txtemail')
        obj.mobile = request.POST.get('txtmobile')
        obj.password = request.POST.get('txtpassword')
        obj.address = request.POST.get('txtaddress')
        obj.city = request.POST.get('txtcity')
        obj.state = request.POST.get('txtstate')
        obj.save()
        return redirect('login')

    return render(request, 'register.html')


# ---------------- ADD EXPENSE ----------------
def expadd(request):
    uid = request.session.get('user_id')
    if not uid:
        return redirect('login')

    if request.method == 'POST':
        expense.objects.create(
            user_id=uid,
            date=request.POST.get('txtdate'),
            amount=Decimal(request.POST.get('txtamount')),   
            category=request.POST.get('txtcategory'),
            description=request.POST.get('txtdescription')
        )
        return redirect('expense_list')

    return render(request, 'add_expense.html')


# ---------------- VIEW & UPDATE EXPENSES ----------------
def expense_list(request):
    uid = request.session.get('user_id')
    if not uid:
        return redirect('login')

    if request.method == 'POST':
        exp_id = request.POST.get('id')
        exp = expense.objects.get(id=exp_id, user_id=uid)

        exp.date = request.POST.get('txtdate')
        exp.amount = Decimal(request.POST.get('txtamount'))  
        exp.category = request.POST.get('txtcategory')
        exp.description = request.POST.get('txtdescription')
        exp.save()

        return redirect('expense_list')

    data = expense.objects.filter(user_id=uid).order_by('-date')
    return render(request, 'expense_list.html', {'data': data})


# ---------------- DELETE EXPENSE ----------------
def delete_expense(request, id):
    uid = request.session.get('user_id')
    if not uid:
        return redirect('login')

    exp = get_object_or_404(expense, id=id, user_id=uid)
    exp.delete()
    return redirect('expense_list')


# ---------------- BUDGET MANAGEMENT ----------------
def budget_management(request):
    uid = request.session.get('user_id')
    if not uid:
        return redirect('login')

    error = None

    if request.method == 'POST':
        month_value = request.POST.get('month')
        amount = Decimal(request.POST.get('amount'))  

        month_date = datetime.strptime(month_value, "%Y-%m").date()
        today = date.today()

        if month_date.year < today.year or (month_date.year == today.year and month_date.month < today.month):
            error = "Cannot create budget for past months!"

        elif budget.objects.filter(
            user_id=uid,
            month__year=month_date.year,
            month__month=month_date.month
        ).exists():
            error = "Budget already exists for this month!"

        else:
            budget.objects.create(
                user_id=uid,
                month=month_date,
                amount=amount
            )
            return redirect('budget')

    today = date.today()
    current_budget = budget.objects.filter(
        user_id=uid,
        month__year=today.year,
        month__month=today.month
    ).first()

    remaining = Decimal('0')  
    total_expense = Decimal('0')   

    if current_budget:
        monthly_expenses = expense.objects.filter(
            user_id=uid,
            date__year=current_budget.month.year,
            date__month=current_budget.month.month
        )

        total_expense = monthly_expenses.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')  

        remaining = current_budget.amount - total_expense

        if remaining <= Decimal('0'):  
            messages.warning(request, "Your budget for this month is finished!")
        elif remaining <= current_budget.amount * Decimal('0.2'):   
            messages.warning(request, "You have used 80% of your monthly budget!")

    context = {
        'budget': current_budget,
        'total_expense': total_expense,
        'remaining': remaining,
        'error': error
    }

    return render(request, 'budget.html', context)


# ---------------- PROFILE ----------------
def profile(request):
    uid = request.session.get('user_id')
    if not uid:
        return redirect('login')

    usr = user.objects.get(id=uid)

    if request.method == 'POST':
        usr.fname = request.POST.get('txtfname')
        usr.lname = request.POST.get('txtlname')
        usr.email = request.POST.get('txtemail')
        usr.mobile = request.POST.get('txtmobile')
        usr.address = request.POST.get('txtaddress')
        usr.city = request.POST.get('txtcity')
        usr.state = request.POST.get('txtstate')
        usr.save()
        return redirect('profile')

    return render(request, 'profile.html', {'user': usr})


# ---------------- LOGOUT ----------------
def logout_view(request):
    request.session.flush()
    return redirect('login')