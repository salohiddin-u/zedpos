from django.urls import path, include
from .views import *
from pos import views as pos_views


urlpatterns = [
    path('', dashboard, name="dashboard"),
    path('pos/', point_of_sale, name="pos"),
    path('products/', products_list, name="products"),
    path('restock/<int:i>/', restock, name="restock"),
    path('products/add/', product_add, name="product_add"),
    path('products/<int:i>/detail/', product_detail, name="product_detail"),
    path('products/<int:i>/archive/', archive_product, name="archive_product"),
    path('products/<int:i>/unarchive/', unarchive_product, name="unarchive_product"),
    path('firm/', expenses, name="expenses"),
    path('firm/add/', add_firm_expense, name="add_firm_expense"),
    path('firm/category/<int:cat>/', category_detail, name="category_detail"),
    path('firm/category/add/', add_category, name="add_category"),
    path('manifest.json', pos_views.manifest, name='manifest'),
    path('sw.js', pos_views.service_worker, name='service_worker'),
    path('personal/', personal_expenses, name="personal_expenses"),
    path('personal/add/', add_expense, name="add_expense"),
    path('products/<int:i>/pin/', pin_product),
]
