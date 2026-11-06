from django.db import models


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True, db_column='CustomerID')
    name = models.CharField('Nombre', max_length=255, db_column='Name')

    class Meta:
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'
        ordering = ['customer_id']

    def __str__(self):
        return f'{self.customer_id} - {self.name}'


class Product(models.Model):
    product_id = models.AutoField(primary_key=True, db_column='ProductID')
    description = models.CharField('Descripción', max_length=255, db_column='Description')
    unit_price = models.DecimalField('Precio unitario', max_digits=18, decimal_places=2, db_column='UnitPrice')

    class Meta:
        verbose_name = 'producto'
        verbose_name_plural = 'productos'
        ordering = ['product_id']

    def __str__(self):
        return f'{self.product_id} - {self.description}'


class SalesOrder(models.Model):
    sales_order_id = models.AutoField(primary_key=True, db_column='SalesOrderID')
    order_number = models.CharField('Número de orden', max_length=100, db_column='OrderNumber')
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, verbose_name='Cliente', db_column='CustomerID'
    )
    order_date = models.DateField('Fecha de orden', db_column='OrderDate')
    total_amount = models.DecimalField('Importe total', max_digits=18, decimal_places=2, db_column='TotalAmount')

    class Meta:
        verbose_name = 'orden de venta'
        verbose_name_plural = 'órdenes de venta'
        ordering = ['sales_order_id']

    def __str__(self):
        return f'{self.sales_order_id} - {self.order_number}'


class SalesOrderDetail(models.Model):
    sales_order_detail_id = models.AutoField(primary_key=True, db_column='SalesOrderDetailID')
    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, verbose_name='Orden de venta', db_column='SalesOrderID'
    )
    line_number = models.IntegerField('Número de línea', db_column='SOLineNumber')
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, verbose_name='Producto', db_column='ProductID'
    )
    quantity = models.DecimalField('Cantidad', max_digits=18, decimal_places=4, db_column='Quantity')
    unit_price = models.DecimalField('Precio unitario', max_digits=18, decimal_places=2, db_column='UnitPrice')
    line_total = models.DecimalField('Total de línea', max_digits=18, decimal_places=2, db_column='LineTotal')

    class Meta:
        verbose_name = 'detalle de orden'
        verbose_name_plural = 'detalles de orden'
        ordering = ['sales_order_id', 'line_number', 'sales_order_detail_id']

    def __str__(self):
        return f'Orden {self.sales_order_id}, línea {self.line_number}: {self.product}'
