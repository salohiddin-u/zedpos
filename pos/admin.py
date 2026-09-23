from django.contrib import admin

from .models import *

admin.site.register(Product)
admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(ExpenseCategory)
admin.site.register(FirmExpense)
admin.site.register(Stock)