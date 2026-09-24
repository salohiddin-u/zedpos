from django.contrib import admin

from .models import *

admin.site.register(Product)
admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(Supplier)
admin.site.register(SupplierPayment)
admin.site.register(Stock)
admin.site.register(PersonalExpenseCategory)
admin.site.register(PersonalExpense)