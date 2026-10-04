from django.db import models
from django.utils import timezone

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=100)
    vendor_cost = models.IntegerField()
    sales_price = models.IntegerField()
    barcode = models.CharField(max_length=100)
    qty = models.FloatField()
    weight_based = models.BooleanField(default=False, null=True, blank=True)
    active = models.BooleanField(null=True, blank=True, default=True)
    pinned = models.BooleanField(null=True, blank=True, default=False)

    def __str__(self):
        return f"{self.name} - {self.vendor_cost} - {self.sales_price}"

class Sale(models.Model):
    PAID_BY_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('qr', 'QR')
    ]
    created_at = models.DateTimeField()
    total = models.IntegerField()
    paid_by = models.CharField(choices=PAID_BY_CHOICES, max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.id} - {timezone.localtime(self.created_at)} - {self.total}"


class SaleItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    price = models.IntegerField()
    qty = models.FloatField()
    profit = models.FloatField()

    def __str__(self):
        return f"{self.product.name} - {self.sale.id}"

class Supplier(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Suppliers"
        verbose_name = "Supplier"

class SupplierPayment(models.Model):
    amount = models.IntegerField()
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    created_at = models.DateTimeField()
    note = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.amount}"

class PersonalExpenseCategory(models.Model):
    label = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.label}"
    class Meta:
            verbose_name_plural = "Personal expense categories"
            verbose_name = "Personal expense category"

class PersonalExpense(models.Model):
    category = models.ForeignKey(PersonalExpenseCategory, on_delete=models.CASCADE, null=True)
    amount = models.IntegerField()
    created_at = models.DateTimeField()
    note = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.amount} - {self.category}"

class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.FloatField()
    created_at = models.DateTimeField()


    def __str__(self):
        return self.product.name