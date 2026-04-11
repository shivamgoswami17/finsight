from django.shortcuts import render, redirect, get_object_or_404
from .models import user, expense, budget
from django.db.models import Sum


# ---------------- HOME ----------------
def home(request):
    uid = request.session.get('user_id')
    if not uid:
        return redirect('login')

    return render(request, 'home.html')


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
            amount=request.POST.get('txtamount'),
            category=request.POST.get('txtcategory'),
            description=request.POST.get('txtdescription')
        )
        return redirect('expense_list')

    return render(request, 'add_expense.html')


# ---------------- VIEW EXPENSES ----------------
def expense_list(request):
    uid = request.session.get('user_id')
    if not uid:
        return redirect('login')

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

    # -------- SAVE BUDGET --------
    if request.method == 'POST':
        month_value = request.POST.get('month')  # format: 2026-02

        budget.objects.create(
            user_id=uid,
            month=month_value + "-01",   # convert to full date (YYYY-MM-01)
            amount=request.POST.get('amount')
        )

        return redirect('budget')

    # -------- GET LATEST BUDGET --------
    latest_budget = budget.objects.filter(user_id=uid).last()

    total_expense = 0
    remaining = 0

    if latest_budget:
        month_date = latest_budget.month  # already DateField

        monthly_expenses = expense.objects.filter(
            user_id=uid,
            date__month=month_date.month,
            date__year=month_date.year
        )

        total_expense = monthly_expenses.aggregate(
            total=Sum('amount')
        )['total'] or 0

        remaining = latest_budget.amount - total_expense

    context = {
        'budget': latest_budget,
        'total_expense': total_expense,
        'remaining': remaining
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