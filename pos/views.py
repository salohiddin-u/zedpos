from django.db.models.functions import ExtractHour
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Sum, Avg, Count, F, FloatField, ExpressionWrapper
from django.utils.timezone import localtime
from .models import *

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from datetime import timedelta, time, datetime
from dateutil.relativedelta import relativedelta
import calendar

from django.db.models.functions import Coalesce

import json
from django.db import transaction
from django.http import HttpResponse
from django.conf import settings
import os

def manifest(request):
    path = os.path.join(settings.BASE_DIR, 'pos/pwa/manifest.json')
    with open(path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/manifest+json')

def service_worker(request):
    path = os.path.join(settings.BASE_DIR, 'pos/pwa/sw.js')
    with open(path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/javascript')


def get_percent_change(new_value, old_value):
    if old_value != 0:
        pct_change = ((new_value - old_value) / old_value) * 100
    elif new_value > 0:
        pct_change = 100
    else:
        pct_change = 0
    return pct_change


def get_period_totals(start, end):
    end += timedelta(days=1)
    return {
        "total_sales": Sale.objects.filter(created_at__date__range=(start, end)).aggregate(Sum("total"))["total__sum"] or 0,
        "total_profit": SaleItem.objects.filter(sale__created_at__date__range=(start, end)).aggregate(Sum("profit"))["profit__sum"] or 0,
        "total_supplier_payments": SupplierPayment.objects.filter(created_at__date__range=(start, end)).aggregate(Sum("amount"))["amount__sum"] or 0,
        "start_date": start,
        "end_date": end,
    }


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())

            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
    else:
        form = AuthenticationForm(request)

    return render(request, 'login.html', {'login': form, 'next': next_url})

@login_required
def dashboard(request):
    #custom_range
    custom_range_period = {
        "total_sales": 0,
        "total_profit": 0,
        "total_supplier_payments": 0,
    }

    start = request.GET.get("start_date")
    end = request.GET.get("end_date")
    custom_range_active = False
    if start and end:
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
            custom_range_period = get_period_totals(start_date, end_date)
            custom_range_active = True
        except ValueError:
            pass


    now = localtime()
    today = now.date()
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    

    #x-report
    today_sales = Sale.objects.filter(created_at__range=(today_midnight, now))

    today_sales_payment_methods = today_sales.values("paid_by").annotate(total=Sum("total"))

    payment_methods_totals = {"cash": 0, "card": 0, "qr": 0}
    for i in today_sales_payment_methods:
        method = i['paid_by'] or 'cash'
        if method in payment_methods_totals:
            payment_methods_totals[method] += int(i['total'])


    #sales by hour
    hour_totals_qs = (today_sales.annotate(hour=ExtractHour('created_at'))
                     .values('hour')
                     .annotate(total=Sum('total'))
                     .order_by('hour'))
    today_sales_by_hour = []
    hour_totals = {row['hour']: int(row['total']) for row in hour_totals_qs}
    for hour in range(0, 24):
        total = hour_totals.get(hour, 0)
        today_sales_by_hour.append({
            "hour": hour,
            "total": total,
        })

    #top sellers
    today_sale_items = (SaleItem.objects.filter(sale__created_at__range=(today_midnight, now))
                .values("product__name")
                .annotate(total_price=Sum("price"))
                ).order_by('-total_price')
    today_top_sellers = []
    for item in today_sale_items:
        today_top_sellers.append({
            "name": item["product__name"],
            "total": item["total_price"],
        })

    #REPORTS
    today_period = get_period_totals(today, today)
    yesterday_period = get_period_totals(yesterday, yesterday-timedelta(days=1))
    week_period = get_period_totals(today - timedelta(days=6), today)
    month_param = request.GET.get("month")
    try:
        selected_month = datetime.strptime(month_param, "%Y-%m").date()
    except:
        selected_month = now.date().replace(day=1)
    month_name = selected_month.strftime("%B")
    prev_month_param = (selected_month - relativedelta(months=1)).strftime("%Y-%m")
    next_month_param = (selected_month + relativedelta(months=1)).strftime("%Y-%m") if selected_month < today.replace(day=1) else None
    last_day_num = calendar.monthrange(selected_month.year, selected_month.month)[1]
    month_end = selected_month.replace(day=last_day_num)
    month_period = get_period_totals(selected_month, month_end)

    active_products_sales_value = Product.objects.filter(active=True).aggregate(
       total=Sum(ExpressionWrapper(F("sales_price") * F("qty"), output_field=FloatField()))
   )["total"] or 0
    active_products_vendor_cost = Product.objects.filter(active=True).aggregate(
       total=Sum(ExpressionWrapper(F("vendor_cost") * F("qty"), output_field=FloatField()))
   )["total"] or 0

    today_sales_change_pct = get_percent_change(new_value=today_period["total_sales"], old_value=yesterday_period["total_sales"])

    context = {
    # Today
    "today_total_sales": today_period["total_sales"],
    "today_total_profit": today_period["total_profit"],
    "today_total_supplier_payments": today_period["total_supplier_payments"],
    "today_sales_change_pct": today_sales_change_pct,
    "today_sales_by_hour": today_sales_by_hour,
    "today_top_sellers": today_top_sellers[:6],

    # Yesterday
    "yesterday_total_sales": yesterday_period["total_sales"],
    "yesterday_total_profit": yesterday_period["total_profit"],
    "yesterday_total_supplier_payments": yesterday_period["total_supplier_payments"],

    # Week
    "week_total_sales": week_period["total_sales"],
    "week_total_profit": week_period["total_profit"],
    "week_total_supplier_payments": week_period["total_supplier_payments"],

    # Month
    "month_name": month_name,
    "month_total_sales": month_period["total_sales"],
    "month_total_profit": month_period["total_profit"],
    "month_total_supplier_payments": month_period["total_supplier_payments"],

    # Custom range
    "custom_range_active": custom_range_active,
    "custom_range_period": custom_range_period,
    "custom_range_total_sales": custom_range_period["total_sales"],
    "custom_range_total_profit": custom_range_period["total_profit"],
    "custom_range_total_supplier_payments": custom_range_period["total_supplier_payments"],

    # Other
    "prev_month_param": prev_month_param,
    "next_month_param": next_month_param,
    "localtime": now,
    "active_products_vendor_cost": active_products_vendor_cost,
    "active_products_sales_value": active_products_sales_value,

    "payment_methods_totals": payment_methods_totals
}
    return render(request, "dashboard.html", context)


@login_required
def point_of_sale(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            cart_items = payload['items']
            paid_by = payload.get("paid_by")
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"message": "Noto'g'ri so'rov formati"}, status=400)

        if not cart_items:
            return JsonResponse({"message": "Savat bo'sh"}, status=400)

        try:
            with transaction.atomic():
                sale = Sale.objects.create(created_at=localtime(), total=0)
                sale_total = 0

                for product_id, cart_item in cart_items.items():
                    try:
                        product = Product.objects.select_for_update().get(id=product_id)
                    except Product.DoesNotExist:
                        raise ValueError(f"Mahsulot topilmadi (id={product_id})")

                    raw_qty = cart_item.get('qty')
                    raw_weight = cart_item.get('weight')
                    qty = raw_qty if raw_qty is not None else raw_weight

                    if qty is None or not isinstance(qty, (int, float)) or qty <= 0:
                        raise ValueError(f"Noto'g'ri miqdor - {product.name}")

                    price = cart_item.get('price')
                    if price is None or not isinstance(price, (int, float)) or price < 0:
                        raise ValueError(f"Noto'g'ri narx - {product.name}")

                    if abs(price - product.sales_price) > 0.01:
                        raise ValueError(f"Narx mos kelmadi - {product.name}")

                    if qty > product.qty:
                        raise ValueError(f"Yetarli mahsulot yo'q - {product.name}")

                    SaleItem.objects.create(
                        product=product,
                        sale=sale,
                        price=qty * price,
                        qty=float(qty),
                        profit=float((product.sales_price - product.vendor_cost) * qty),
                        
                    )

                    product.qty = round(product.qty - qty, 3)
                    product.save()

                    sale_total += qty * price
                sale.paid_by = payload.get("paid_by")
                sale.total = sale_total
                sale.save()

        except ValueError as e:
            return JsonResponse({"message": str(e)}, status=400)
        response = {
            "status": "ok",
            "sale_id": sale.id,
            "next_sale_id": sale.id + 1,
            "sale_total": sale.total,
            "updated_stock": {
                str(item.product.id): item.product.qty
                for item in SaleItem.objects.filter(sale=sale).select_related("product")
            }
        }
        if paid_by == "qr":
            response["qr_url"] = "https://i.postimg.cc/ZqKzKHj1/2026-06-15-23-57-54-527139-pdf-(1).png"
        return JsonResponse(response)

    context = {
        "active_products": Product.objects.filter(active=True).order_by('-pinned', 'name'),
    }
    return render(request, "pos.html", context)


@login_required
def products_list(request):
    context = {
        "products": Product.objects.all().order_by("-active")
    }
    return render(request, "products.html", context)

@login_required
def product_add(request):
    if request.method == "POST":
        name = request.POST.get("name")
        barcode = request.POST.get("barcode")
        sales_price = request.POST.get("price")
        vendor_cost = request.POST.get("vendor_cost")
        qty = request.POST.get("qty")
        pricing_unit = request.POST.get("pricing_unit")
        weight_based = pricing_unit == "kg"
        Product.objects.create(name=name, barcode=barcode, sales_price=sales_price, vendor_cost=vendor_cost, qty=qty, weight_based=weight_based, pinned=False)
        return redirect("/products/add/")
    return render(request, "product-add.html")

@login_required
def product_detail(request, product_id):
    today = localtime().now().date()
    product = Product.objects.get(id=product_id)
    week_start = today - timedelta(days=7)
    start_date = today - timedelta(days=15)
    week_qty_sold = SaleItem.objects.filter(sale__created_at__date__range=(week_start, today), product__id=product_id).aggregate(Sum("qty"))["qty__sum"] or 0

    week_sale_history = SaleItem.objects.filter(sale__created_at__date__range=(week_start, today), product__id=product_id).order_by("-sale__created_at")[:50]

    week_total_profit = SaleItem.objects.filter(sale__created_at__date__range=(week_start, today), product=product).aggregate(Sum("profit"))["profit__sum"] or 0
    restock_history = Stock.objects.filter(created_at__date__range=(start_date, today), product=product).order_by("-created_at")[:30]
    context = {
        "product": product,
        "week_qty_sold": week_qty_sold,
        "week_sale_history": week_sale_history,
        "week_total_profit": week_total_profit,
        "restock_history": restock_history,
    }
    return render(request, "product-detail.html", context)

@login_required
def archive_product(request, product_id):
    product = Product.objects.get(id=product_id)
    product.active = False
    product.save()
    return redirect("/products/")

@login_required
def unarchive_product(request, product_id):
    product = Product.objects.get(id=product_id)
    product.active = True
    product.save()
    return redirect(f"/products/{product_id}/detail/")

@login_required
def restock(request, product_id):
    product = Product.objects.get(id=product_id)
    now = localtime().now()
    if request.method == "POST":
        qty = request.POST.get("qty")
        product.qty += float(qty)
        product.save()
        Stock.objects.create(product=product, qty=qty, created_at=now)
    return redirect(f"/products/{product_id}/detail/")


@login_required
def supplier_payments(request):
    """
    Renamed from expenses(). Lists SupplierPayments, filterable/groupable by Supplier.
    """
    start = request.GET.get("start_date")
    end = request.GET.get("end_date")
    supplier_id = request.GET.get("supplier")

    now = localtime().now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=7)
    month_beginning = today.replace(day=1)

    payments = SupplierPayment.objects.all()
    today_total_supplier_payments = payments.filter(created_at__date=today).aggregate(Sum("amount"))["amount__sum"] or 0
    yesterday_total_supplier_payments = payments.filter(created_at__date=yesterday).aggregate(Sum("amount"))["amount__sum"] or 0
    week_total_supplier_payments = payments.filter(created_at__date__range=(week_start, today)).aggregate(Sum("amount"))["amount__sum"] or 0
    month_total_supplier_payments = payments.filter(created_at__date__range=(month_beginning, today)).aggregate(Sum("amount"))["amount__sum"] or 0

    if supplier_id:
        payments = payments.filter(supplier=supplier_id)

    if start and end:
        try:
            start = datetime.strptime(start, "%Y-%m-%d")
            end = datetime.strptime(end, "%Y-%m-%d")
            payments = payments.filter(created_at__date__range=(start, end))
        except:
            pass


    #payments by supplier
    supplier_payments_by_supplier = [{
        "name": item['supplier__name'],
        "total": item['total'] or 0,
        "id": item["supplier__id"],
    }
        for item in payments.values("supplier__name", "supplier__id").annotate(total=Sum('amount'))
    ]
    top_supplier_by_payments = payments.values("supplier__name").annotate(total=Sum("amount")).order_by("-total").first()

    context = {
        "supplier_payments": payments.order_by("-created_at"),
        "today_total_supplier_payments": today_total_supplier_payments,
        "yesterday_total_supplier_payments": yesterday_total_supplier_payments,
        "week_total_supplier_payments": week_total_supplier_payments,
        "month_total_supplier_payments": month_total_supplier_payments,
        "supplier_payments_by_supplier": supplier_payments_by_supplier,
        "all_products": Product.objects.all().order_by("-active"),
        "top_supplier_by_payments": top_supplier_by_payments,
        "today": today,
        "suppliers": Supplier.objects.annotate(total_paid=Coalesce(Sum('supplierpayment__amount'), 0)).order_by("total_paid"),
    }
    return render(request, 'supplier_payments.html', context)

@login_required
def add_supplier_payment(request):
    if request.method == "POST":
        amount = request.POST.get("amount")
        supplier = Supplier.objects.get(id=int(request.POST.get("supplier")))
        date = request.POST.get("date")
        note = request.POST.get("note")
        SupplierPayment.objects.create(amount=amount, supplier=supplier, created_at=date, note=note)
    return redirect("/suppliers/payments/")


@login_required
def supplier_detail(request, supplier_id):
    now = localtime().now()
    today = now.date()
    month_beginning = today.replace(day=1)

    supplier_total_paid = SupplierPayment.objects.filter(supplier__id=supplier_id).aggregate(Sum("amount"))["amount__sum"] or 0
    supplier_month_total_paid = SupplierPayment.objects.filter(supplier__id=supplier_id, created_at__date__range=(month_beginning, today)).aggregate(Sum("amount"))["amount__sum"] or 0
    supplier_payments = SupplierPayment.objects.filter(supplier__id=supplier_id)
    context = {
        "supplier": Supplier.objects.get(id=supplier_id),
        "supplier_total_paid": supplier_total_paid,
        "supplier_month_total_paid": supplier_month_total_paid,
        "supplier_payments": supplier_payments,
        "suppliers": Supplier.objects.all(),
    }
    return render(request, "suppliers.html", context)


@login_required
def add_supplier(request):
    if request.method == "POST":
        name = request.POST.get("name")
        Supplier.objects.create(name=name)
        return redirect("/suppliers/")


@login_required
def personal_expenses(request):
    now = localtime().now()
    today = now.date()

    month_beginning = now.date().replace(day=1)
    month_end = now.date().replace(day=calendar.monthrange(today.year, today.month)[1])

    week_start = now.date() - timedelta(days=6)


    context = {
        "personal_expense_categories": PersonalExpenseCategory.objects.all(),
        "personal_expenses": PersonalExpense.objects.all(),
        "week_total_personal_expenses": PersonalExpense.objects.filter(created_at__date__range=(week_start, today)).aggregate(Sum("amount"))["amount__sum"] or 0,
        "today_total_personal_expenses": PersonalExpense.objects.filter(created_at__date=today).aggregate(Sum("amount"))["amount__sum"] or 0,
        "month_total_personal_expenses": PersonalExpense.objects.filter(created_at__date__range=(month_beginning, month_end)).aggregate(Sum("amount"))["amount__sum"] or 0,
    }

    return render(request, "personal_expenses.html", context)

@login_required
def add_personal_expense(request):
    if request.method == "POST":
        amount = request.POST.get("expense")
        created_at = request.POST.get("created_at")
        note = request.POST.get("note")
        category_id = request.POST.get("category")
        category = PersonalExpenseCategory.objects.get(id=category_id)
        PersonalExpense.objects.create(amount=amount, category=category, created_at=created_at, note=note)
        return redirect("/personal/")


@login_required
def pin_product(request, product_id):
    product = Product.objects.get(id=product_id)
    product.pinned = not product.pinned
    product.save()
    return redirect('/pos/')


@login_required
def add_personal_expense_category(request):
    if request.method == "POST":
        label = request.POST.get("label")
        PersonalExpenseCategory.objects.create(label=label)
        return redirect("/personal/")
    
