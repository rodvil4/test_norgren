from django.contrib import admin

from .models import Customer, Product, SalesOrder, SalesOrderDetail

admin.site.register([Customer, Product, SalesOrder, SalesOrderDetail])
