from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .models import user, expense, budget
from django.db.models import Sum
from datetime import datetime, date
from django.contrib import messages
from decimal import Decimal  
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User



# ---------------- Admin dashbord ----------------
def admin_dashboard(request):

    if not request.session.get('admin'):
        return redirect('admin_login')

    search_query = request.GET.get('search', '')
    user_id = request.GET.get('user_id')

    users = user.objects.all().order_by('-id')

    # 🔍 SEARCH FILTER (LIVE)
    if search_query:
        users = users.filter(
            Q(fname__icontains=search_query) |
            Q(lname__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(state__icontains=search_query) |
            Q(mobile__icontains=search_query)
        )

    total_users = user.objects.count()

    selected_user = None
    total_expenses = 0
    total_budget = 0
    monthly_expenses = 0

    current_month = datetime.now().month

    # 👤 SELECTED USER DATA
    if user_id:
        selected_user = get_object_or_404(user, id=user_id)

        total_expenses = expense.objects.filter(user=selected_user)\
            .aggregate(Sum('amount'))['amount__sum'] or 0

        total_budget = budget.objects.filter(user=selected_user)\
            .aggregate(Sum('amount'))['amount__sum'] or 0

        monthly_expenses = expense.objects.filter(
            user=selected_user,
            date__month=current_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'users': users,
        'total_users': total_users,
        'selected_user': selected_user,
        'total_expenses': total_expenses,
        'total_budget': total_budget,
        'monthly_expenses': monthly_expenses,
        'search_query': search_query
    }

    return render(request, "admin_dashboard.html", context)
 # ---------------- Admin ----------------
def admin_login(request):
    if request.method == "POST":
        user = request.POST.get("username")   # ✅ fixed
        password = request.POST.get("password")

        if user == "user" and password == "user":
            request.session['admin'] = True
            return redirect('/admin-dashboard/')
        else:
            return render(request, "admin_login.html", {
                "error": "Invalid admin credentials"
            })

    return render(request, "admin_login.html")

def get_monthly_budget_status(uid, target_date=None):
    if target_date is None:
        target_date = date.today()

    current_budget = budget.objects.filter(
        user_id=uid,
        month__year=target_date.year,
        month__month=target_date.month
    ).first()

    total_expense = expense.objects.filter(
        user_id=uid,
        date__year=target_date.year,
        date__month=target_date.month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    remaining = Decimal('0')
    warning = None
    if current_budget:
        remaining = current_budget.amount - total_expense
        if remaining <= Decimal('0'):
            warning = "Your budget for this month is finished!"
        elif remaining <= current_budget.amount * Decimal('0.2'):
            warning = "You have used 80% of your monthly budget!"

    return current_budget, total_expense, remaining, warning
# ---------------- User Details in dash bord ----------------
def user_detail(request, id):

    if not request.session.get('admin'):
        return redirect('admin_login')

    user_data = user.objects.get(id=id)

    # Optional: get user's expenses & budget
    user_expenses = expense.objects.filter(user=user_data)
    user_budget = budget.objects.filter(user=user_data)

    context = {
        'user': user_data,
        'expenses': user_expenses,
        'budgets': user_budget,
    }

    return render(request, "user_detail.html", context)

# ---------------- HOME ----------------
def home(request):
    uid = request.session.get('user_id')
    if not uid:
        return redirect('login')

    current_budget, total_expense, remaining, warning = get_monthly_budget_status(uid)

    if warning:
        messages.warning(request, warning)

    recent_expense = expense.objects.filter(user_id=uid).order_by('-date')[:5]

    context = {
        'total_expense': total_expense,
        'budget': current_budget,
        'remaining': remaining,
        'recent_expense': recent_expense,
        'show_popup': bool(warning),
        'popup_message': warning or "",
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

    error = None

    if request.method == 'POST':
        amount = Decimal(request.POST.get('txtamount'))
        date_value = request.POST.get('txtdate')
        expense_date = datetime.strptime(date_value, "%Y-%m-%d").date()

        current_budget, total_expense, remaining, warning = get_monthly_budget_status(uid, expense_date)

        if not current_budget:
            error = "No budget set for the selected month!"
        elif remaining - amount < Decimal('0'):
            error = "Adding this expense would exceed your budget!"
        else:
            expense.objects.create(
                user_id=uid,
                date=expense_date,
                amount=amount,
                category=request.POST.get('txtcategory'),
                description=request.POST.get('txtdescription')
            )
            return redirect('expense_list')

    today = date.today()
    _, _, _, warning = get_monthly_budget_status(uid, today)
    if warning:
        messages.warning(request, warning)

    return render(request, 'add_expense.html', {'error': error})



# ---------------- VIEW & UPDATE EXPENSES ----------------
def expense_list(request):
    uid = request.session.get('user_id')
    if not uid:
        return redirect('login')

    query = request.GET.get('q', '').strip()

    data = expense.objects.filter(user_id=uid)

    if query:
        data = data.filter(
            Q(category__icontains=query) |
            Q(description__icontains=query)
        )

    data = data.order_by('-date')

    # ✅ AJAX RESPONSE
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            list(data.values('id', 'date', 'amount', 'category', 'description')),
            safe=False
        )

    return render(request, 'expense_list.html', {'data': data})
#----
# def expense_list(request):
#     uid = request.session.get('user_id')
#     if not uid:
#         return redirect('login')

#     error = None

#     if request.method == 'POST':
#         exp_id = request.POST.get('id')
#         exp = expense.objects.get(id=exp_id, user_id=uid)

#         new_date = datetime.strptime(request.POST.get('txtdate'), "%Y-%m-%d").date()
#         new_amount = Decimal(request.POST.get('txtamount'))
#         category = request.POST.get('txtcategory')
#         description = request.POST.get('txtdescription')

#         current_budget = budget.objects.filter(
#             user_id=uid,
#             month__year=new_date.year,
#             month__month=new_date.month
#         ).first()

#         if not current_budget:
#             error = "No budget set for the selected month!"
#         else:
#             monthly_expenses = expense.objects.filter(
#                 user_id=uid,
#                 date__year=new_date.year,
#                 date__month=new_date.month
#             ).exclude(id=exp_id)

#             total_other = monthly_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
#             remaining = current_budget.amount - total_other

#             if remaining - new_amount < Decimal('0'):
#                 error = "Updating this expense would exceed the budget for that month!"
#             else:
#                 exp.date = new_date
#                 exp.amount = new_amount
#                 exp.category = category
#                 exp.description = description
#                 exp.save()
#                 return redirect('expense_list')

#     _, _, _, warning = get_monthly_budget_status(uid)
#     if warning:
#         messages.warning(request, warning)

#     data = expense.objects.filter(user_id=uid).order_by('-date')
#     return render(request, 'expense_list.html', {'data': data, 'error': error})


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
    current_budget, total_expense, remaining, warning = get_monthly_budget_status(uid, today)

    all_budgets = budget.objects.filter(user_id=uid).order_by('-month')

    if warning:
        messages.warning(request, warning)
       

    context = {
        'budget': current_budget,
        'total_expense': total_expense,
        'remaining': remaining,
        'error': error,
        'all_budgets': all_budgets,
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

# ---------------- PDF DON ----------------
def monthly_report(request):
    uid = request.session.get('user_id')
    if not uid:
        return redirect('login')

    month = request.GET.get('month')
    year = request.GET.get('year')

    if not month or not year:
        return HttpResponse("Month and Year required")

    month = int(month)
    year = int(year)

    usr = user.objects.get(id=uid)

    expenses = expense.objects.filter(
        user_id=uid,
        date__month=month,
        date__year=year
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="monthly_report.pdf"'

    p = canvas.Canvas(response)

    # ---------------- HEADER ----------------
    p.setFont("Helvetica-Bold", 16)
    p.drawString(170, 800, "Monthly Expense Report")

    p.setFont("Helvetica", 12)
    p.drawString(50, 770, f"Name: {usr.fname} {usr.lname}")
    p.drawString(50, 750, f"Month: {month}/{year}")

    p.line(50, 740, 550, 740)

    # ---------------- TABLE DATA ----------------
    data = [["Date", "Category", "Description", "Amount"]]

    total = 0

    for exp in expenses:
        data.append([
            str(exp.date),
            exp.category,
            exp.description,
            f"Rs. {exp.amount}"
        ])
        total += float(exp.amount)

    data.append(["", "", "Total Expense", f"Rs. {total}"])

    # ---------------- TABLE ----------------
    table = Table(data, colWidths=[100, 100, 200, 100])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # ✅ FIXED POSITION (no overlap)
    table.wrapOn(p, 50, 600)
    table.drawOn(p, 50, 500)

    # ---------------- FOOTER ----------------
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(380, 480, f"Generated on: {date.today()}")

    p.save()
    return response
