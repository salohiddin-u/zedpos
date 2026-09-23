from django.db.models.functions import ExtractHour
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Sum, Avg, Count, F, FloatField, ExpressionWrapper
from django.utils.timezone import localtime
from .models import *

from datetime import datetime, timedelta, time
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


def percent_change(new_value, old_value):
    if old_value!=0:
        percent_change = ((new_value-old_value)/old_value)*100
    elif new_value>0:
        percent_change = 100
    else:
        percent_change = 0

    return percent_change


def aggregate_period(start, end):
    context = {
        "sales": Sale.objects.filter(created_at__date__range=(start, end)).aggregate(Sum("total"))["total__sum"] or 0,
        "profit": SaleItem.objects.filter(sale__created_at__date__range=(start, end)).aggregate(Sum("profit"))["profit__sum"] or 0,
        "expenses": FirmExpense.objects.filter(created_at__date__range=(start, end)).aggregate(Sum("expense"))["expense__sum"] or 0,
        "start_date": start,
        "end_date": end,
    }
    return context

def dashboard(request):
    #custom_range
    custom_range_sales = {
        "sales": 0,
        "profit": 0,
        "expenses": 0,
    }

    start = request.GET.get("start_date")
    end = request.GET.get("end_date")
    custom_range_active = False
    if start and end:
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
            custom_range_sales = aggregate_period(start_date, end_date)
            custom_range_active = True
        except ValueError:
            pass


    now = localtime().now()
    today = now.date()
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    yesterday_midnight = today_midnight - timedelta(days=1)
    yesterday_current_time = now - timedelta(days=1)

    #x-report
    yesterday_sales = Sale.objects.filter(created_at__range=(yesterday_midnight, yesterday_current_time))
    today_sales = Sale.objects.filter(created_at__range=(today_midnight, now))
    yesterday_sales_total = yesterday_sales.aggregate(Sum("total"))["total__sum"] or 0
    today_sales_total = today_sales.aggregate(Sum("total"))["total__sum"] or 0

    percentage_change = percent_change(new_value=today_sales_total, old_value=yesterday_sales_total)

    difference = today_sales.count()-yesterday_sales.count()

    average_basket = today_sales.aggregate(Avg("total"))["total__avg"] or 0
    average_basket_yesterday = yesterday_sales.aggregate(Avg("total"))["total__avg"] or 0
    avg_percent_change = percent_change(new_value=average_basket, old_value=average_basket_yesterday)


    items_sold = SaleItem.objects.filter(sale__created_at__range=(today_midnight, now)
                                         ).aggregate(Sum("qty"))["qty__sum"] or 0
    items_sold_yesterday = SaleItem.objects.filter(sale__created_at__range=(yesterday_midnight, yesterday_current_time)
                                                   ).aggregate(Sum("qty"))["qty__sum"] or 0

    items_sold_change = percent_change(new_value=items_sold, old_value=items_sold_yesterday)


    #sales by hour
    hour_totals = (today_sales.annotate(hour=ExtractHour('created_at'))
                     .values('hour')
                     .annotate(total=Sum('total'))
                     .order_by('hour'))
    sales_by_hour = []
    hour_totals = {row['hour']: int(row['total']) for row in hour_totals}
    for hour in range(0, 24):
        total = hour_totals.get(hour, 0)
        sales_by_hour.append({
            "hour": hour,
            "total": total,
        })

    #top sellers
    saleitem = (SaleItem.objects.filter(sale__created_at__range=(today_midnight, now))
                .values("product__name")
                .annotate(total_price=Sum("price"))
                ).order_by('-total_price')
    top_sellers = []
    for item in saleitem:
        top_sellers.append({
            "name": item["product__name"],
            "total": item["total_price"],
        })

    #REPORTS
    today_profit = aggregate_period(today, today)

    yesterday_period = aggregate_period(yesterday, yesterday)
    week_period = aggregate_period(today - timedelta(days=6), today)
    month_param = request.GET.get("month")
    try:
        selected_month = datetime.strptime(month_param, "%Y-%m").date()
    except:
        selected_month = now.date().replace(day=1)
    month_name = selected_month.strftime("%B")
    prev_month_param = (selected_month - relativedelta(months=1)).strftime("%Y-%m")
    next_month_param = (selected_month + relativedelta(months=1)).strftime("%Y-%m")if selected_month < today.replace(day=1) else None
    last_day_num = calendar.monthrange(selected_month.year, selected_month.month)[1]
    month_end = selected_month.replace(day=last_day_num)
    month_period = aggregate_period(selected_month, month_end)

    products_sale_price = Product.objects.filter(active=True).aggregate(
       total=Sum(ExpressionWrapper(F("sales_price") * F("qty"), output_field=FloatField()))
   )["total"] or 0
    products_total_vendor = Product.objects.filter(active=True).aggregate(
       total=Sum(ExpressionWrapper(F("vendor_cost") * F("qty"), output_field=FloatField()))
   )["total"] or 0


    context = {
        "today_profit": today_profit["profit"],
        "today_total_expenses": FirmExpense.objects.filter(created_at__date=today).aggregate(Sum("expense"))["expense__sum"] or 0,
        "prev_month_param": prev_month_param,
        "next_month_param": next_month_param,
        "today_sales": today_sales,
        "custom_range_active": custom_range_active,
        "custom_sales": custom_range_sales["sales"],
        "custom_profit": custom_range_sales["profit"],
        "custom_expenses": custom_range_sales["expenses"],
        "yesterday_sales": yesterday_sales,
        "today_sales_total": today_sales_total,
        "yesterday_sales_total": yesterday_sales_total,
        "percentage_change": percentage_change,
        "difference": difference,
        "localtime": now,
        "average_basket": average_basket,
        "items_sold": items_sold,
        "avg_percent_change": avg_percent_change,
        "items_sold_change": items_sold_change,
        "sales_by_hour": sales_by_hour,
        "top_sellers": top_sellers[:6],
        "yesterday_all_sales": yesterday_period["sales"],
        "yesterday_profit": yesterday_period["profit"],
        "yesterday_expenses": yesterday_period["expenses"],
        "days_7_all_sales": week_period["sales"],
        "days_7_profit": week_period["profit"],
        "days_7_expenses": week_period["expenses"],
        "month_all_sales": month_period["sales"],
        "month_profit": month_period["profit"],
        "month_expenses": month_period["expenses"],
        "month_name": month_name,
        "custom_range_sales": custom_range_sales,
        "products_total_vendor": products_total_vendor,
        "products_sale_price": products_sale_price,
    }
    return render(request, "dashboard.html", context)


def point_of_sale(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            products = payload['items']
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"message": "Noto'g'ri so'rov formati"}, status=400)

        if not products:
            return JsonResponse({"message": "Savat bo'sh"}, status=400)
        """ =========================================== """
        # Everything below runs inside ONE atomic block, and every product row
        # is locked with select_for_update(). That means:
        #  - concurrent sales on the same product are serialized by the DB,
        #    not by anything in Python or JS (fixes #1, #2, #8)
        #  - if anything fails partway through, nothing is written at all
        #    (fixes #4, #5 no longer leave partial state)
        try:
            with transaction.atomic():
                sale = Sale.objects.create(created_at=localtime(), total=0)
                sale_total = 0

                for key, item in products.items():
                    # --- fix #5: don't let a bad/stale product id 500 the request
                    try:
                        # select_for_update() locks this row until the transaction
                        # commits or rolls back. A second, concurrent sale for the
                        # same product will block here until this one finishes,
                        # then re-read the now-current qty. This is what actually
                        # prevents the lost-update race, not the JS submit guard.
                        product = Product.objects.select_for_update().get(id=key)
                    except Product.DoesNotExist:
                        raise ValueError(f"Mahsulot topilmadi (id={key})")

                    # --- fix #3: explicit None-checks instead of `or`, so a
                    # legitimate 0 doesn't silently fall through to weight
                    raw_qty = item.get('qty')
                    raw_weight = item.get('weight')
                    qty = raw_qty if raw_qty is not None else raw_weight

                    # --- fix #4: validate qty and price before doing any math
                    if qty is None or not isinstance(qty, (int, float)) or qty <= 0:
                        raise ValueError(f"Noto'g'ri miqdor - {product.name}")

                    price = item.get('price')
                    if price is None or not isinstance(price, (int, float)) or price < 0:
                        raise ValueError(f"Noto'g'ri narx - {product.name}")

                    # --- fix #6: don't fully trust client-sent price. Require it
                    # to match the current catalog price (small epsilon for float
                    # rounding). If you need cashier-applied discounts, replace
                    # this with an explicit discount field instead of trusting
                    # an arbitrary client-sent price.
                    if abs(price - product.sales_price) > 0.01:
                        raise ValueError(f"Narx mos kelmadi - {product.name}")

                    # --- fix #1/#8: re-check stock against the LOCKED, current
                    # row, not the stale value from before the transaction
                    if qty > product.qty:
                        raise ValueError(f"Yetarli mahsulot yo'q - {product.name}")

                    SaleItem.objects.create(
                        product=product,
                        sale=sale,
                        price=qty * price,
                        qty=float(qty),
                        # --- fix #7: profit computed from the same price actually
                        # charged (product.sales_price, now verified == price),
                        # so SaleItem.price and profit can never disagree
                        profit=float((product.sales_price - product.vendor_cost) * qty),
                    )

                    # --- fix #9: round after each mutation to stop float drift
                    # from silently accumulating over many weight-based sales.
                    # (Better long-term fix: store qty as Decimal in the model.)
                    product.qty = round(product.qty - qty, 3)
                    product.save()

                    sale_total += qty * price

                # --- fix #10: total set once, from the same numbers written to
                # SaleItem rows, instead of accumulated field-by-field in a way
                # that could silently drift if the loop logic ever changes
                sale.total = sale_total
                sale.save()

        except ValueError as e:
            # Any validation failure anywhere in the loop rolls back the whole
            # transaction (no sale, no SaleItems, no stock changes) and returns
            # a clean message instead of a 500.
            return JsonResponse({"message": str(e)}, status=400)
        """ =========================================== """
        return JsonResponse({
            "status": "ok",
            "sale_id": sale.id,
            "next_sale_id": sale.id + 1,
            "sale_total": sale.total,
            "updated_stock": {
                str(item.product.id): item.product.qty
                for item in SaleItem.objects.filter(sale=sale).select_related("product")
            }
        })

    context = {
        "products": Product.objects.filter(active=True).order_by('-pinned', 'name'),
    }
    return render(request, "pos.html", context)


def products_list(request):
    context = {
        "products": Product.objects.all().order_by("-active")
    }
    return render(request, "products.html", context)

def product_add(request):
    if request.method == "POST":
        name = request.POST.get("name")
        barcode = request.POST.get("barcode")
        sales_price = request.POST.get("price")
        vendor_cost = request.POST.get("vendor_cost")
        qty = request.POST.get("qty")
        weight_based = request.POST.get("pricing_unit")
        if weight_based == "kg":
            unit = True
        else:
            unit = False
        product = Product.objects.create(name=name, barcode=barcode, sales_price=sales_price, vendor_cost=vendor_cost, qty=qty, weight_based=unit, pinned=False)
        return redirect("/products/add/")
    return render(request, "product-add.html")

def product_detail(request, i):
    today = localtime().now().date()
    product = Product.objects.get(id=i)
    week = today - timedelta(days=7)
    sold_this_week = SaleItem.objects.filter(sale__created_at__date__range=(week, today), product__id=i).aggregate(Sum("qty"))["qty__sum"] or 0

    sale_history = SaleItem.objects.filter(sale__created_at__date__range=(week, today), product__id=i).order_by("-sale__created_at")[:50]

    days_7_profit = SaleItem.objects.filter(sale__created_at__date__range=(week, today), product=product).aggregate(Sum("profit"))["profit__sum"] or 0
    restock_history = Stock.objects.filter(created_at__date__range=(week, today), product=product)[:30]
    context = {
        "product": product,
        "sold_this_week": sold_this_week,
        "sale_history": sale_history,
        "days_7_profit": days_7_profit,
        "restock_history": restock_history,
    }
    return render(request, "product-detail.html", context)

def archive_product(request, i):
    product = Product.objects.get(id=i)
    product.active = False
    product.save()
    return redirect("/products/")

def unarchive_product(request, i):
    product = Product.objects.get(id=i)
    product.active = True
    product.save()
    return redirect(f"/products/{i}/detail/")

def restock(request, i):
    product = Product.objects.get(id=i)
    now = localtime().now()
    if request.method == "POST":
        qty = request.POST.get("qty")
        product.qty += float(qty)
        product.save()
        Stock.objects.create(product=product, qty=qty, created_at=now)
    return redirect(f"/products/{i}/detail/")


def expenses(request):
    start = request.GET.get("start_date")
    end = request.GET.get("end_date")
    category = request.GET.get("category")

    now = localtime().now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)
    month_beginning = today.replace(day=1)

    expenses = FirmExpense.objects.all()
    todays_expenses = expenses.filter(created_at__date=today).aggregate(Sum("expense"))["expense__sum"] or 0
    yesterdays_expenses = expenses.filter(created_at__date=yesterday).aggregate(Sum("expense"))["expense__sum"] or 0
    weekly_expenses = expenses.filter(created_at__date__range=(last_week, today)).aggregate(Sum("expense"))["expense__sum"] or 0
    month_expenses = expenses.filter(created_at__date__range=(month_beginning, today)).aggregate(Sum("expense"))["expense__sum"] or 0

    if category:
        expenses = expenses.filter(category=category)

    if start and end:
        try:
            start = datetime.strptime(start, "%Y-%m-%d")
            end = datetime.strptime(end, "%Y-%m-%d")
            expenses = expenses.filter(created_at__date__range=(start, end))
        except:
            pass
    

    #expense by category
    expenses_by_category = [{
        "name": item['category__name'], 
        "total": item['total'] or 0, 
        "id": item["category__id"],
    }
        for item in expenses.values("category__name", "category__id").annotate(total=Sum('expense'))
    ]
    category_most_expenses = expenses.values("category__name").annotate(total=Sum("expense")).order_by("-total").first()
    
    context = {
        "expenses": expenses.order_by("-created_at"),
        "todays_expenses": todays_expenses,
        "yesterdays_expenses": yesterdays_expenses,
        "weekly_expenses": weekly_expenses,
        "month_expenses": month_expenses,
        "expenses_by_category": expenses_by_category,
        "products": Product.objects.all().order_by("-active"),
        "category_most_expenses": category_most_expenses,
        "today": today,
        "categories": ExpenseCategory.objects.annotate(total_expense=Coalesce(Sum('firmexpense__expense'), 0)).order_by("total_expense"),
    }
    return render(request, 'firm-expenses.html', context)

def add_firm_expense(request):
    if request.method == "POST":
        amount = request.POST.get("amount")
        category = ExpenseCategory.objects.get(id=int(request.POST.get("category")))
        date = request.POST.get("date")
        note = request.POST.get("note")
        FirmExpense.objects.create(expense=amount, category=category, created_at=date, note=note)
    return redirect("/firm/")


def category_detail(request, cat):
    now = localtime().now()
    today = now.date()
    month_beginning = today.replace(day=1)

    total_expenses = FirmExpense.objects.filter(category__id=cat).aggregate(Sum("expense"))["expense__sum"] or 0
    month_expenses = FirmExpense.objects.filter(category__id=cat, created_at__date__range=(month_beginning, today)).aggregate(Sum("expense"))["expense__sum"] or 0
    expenses = FirmExpense.objects.filter(category__id=cat)
    context = {
        "category": ExpenseCategory.objects.get(id=cat),
        "total_expenses": total_expenses,
        "this_month_expenses": month_expenses,
        "expenses": expenses,
    }
    return render(request, "category_detail.html", context)


def add_category(request):
    if request.method == "POST":
        name = request.POST.get("name")
        ExpenseCategory.objects.create(name=name)
        return redirect("/firm/")


def personal_expenses(request):
    now = localtime().now()
    today = now.date()

    month_beginning = now.date().replace(day=1)
    month_end = now.date().replace(day=calendar.monthrange(today.year, today.month)[1])

    week_beginning = now.date() - timedelta(days=6)

    
    context = {
        "expenses": PersonalExpense.objects.all(),
        "weekly_expenses": PersonalExpense.objects.filter(created_at__date__range=(week_beginning, today)).aggregate(Sum("expense"))["expense__sum"] or 0,
        "todays_expenses": PersonalExpense.objects.filter(created_at__date=today).aggregate(Sum("expense"))["expense__sum"] or 0,
        "months_expenses": PersonalExpense.objects.filter(created_at__date__range=(month_beginning, month_end)).aggregate(Sum("expense"))["expense__sum"] or 0,
    }

    return render(request, "personal_expenses.html", context)

def add_expense(request):
    if request.method == "POST":
        expense = request.POST.get("expense")
        created_at = request.POST.get("created_at")
        note = request.POST.get("note")
        PersonalExpense.objects.create(expense=expense, created_at=created_at, note=note)
        return redirect("/personal/")


def pin_product(request, i):
    product = Product.objects.get(id=i)
    if product.pinned == False:
        product.pinned = True
    else:
        product.pinned = False
    product.save()
    return redirect('/pos/')