from django.urls import path
from pos import views as pos_views

urlpatterns = [
    path('', pos_views.dashboard, name="dashboard"),
    path('pos/', pos_views.point_of_sale, name="pos"),

    path('products/', pos_views.products_list, name="products"),
    path('products/add/', pos_views.product_add, name="product_add"),
    path('products/<int:product_id>/detail/', pos_views.product_detail, name="product_detail"),
    path('products/<int:product_id>/archive/', pos_views.archive_product, name="archive_product"),
    path('products/<int:product_id>/unarchive/', pos_views.unarchive_product, name="unarchive_product"),
    path('products/<int:product_id>/pin/', pos_views.pin_product, name="pin_product"),
    path('products/<int:product_id>/restock/', pos_views.restock, name="restock"),

    path('suppliers/', pos_views.add_supplier, name="add_supplier"),
    path('suppliers/payments/', pos_views.supplier_payments, name="supplier_payments"),
    path('suppliers/payments/add/', pos_views.add_supplier_payment, name="add_supplier_payment"),
    path('suppliers/<int:supplier_id>/', pos_views.supplier_detail, name="supplier_detail"),

    path('personal/', pos_views.personal_expenses, name="personal_expenses"),
    path('personal/add/', pos_views.add_personal_expense, name="add_personal_expense"),

    path('manifest.json', pos_views.manifest, name='manifest'),
    path('sw.js', pos_views.service_worker, name='service_worker'),
]