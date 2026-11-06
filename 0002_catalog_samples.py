from decimal import Decimal

from django.db import migrations


def load_catalogs(apps, schema_editor):
    Customer = apps.get_model('orders', 'Customer')
    Product = apps.get_model('orders', 'Product')
    database = schema_editor.connection.alias

    for customer_id, name in [
        (1, 'ABC Corporation'),
        (2, 'XYZ Industries'),
        (3, 'Global Manufacturing'),
    ]:
        Customer.objects.using(database).get_or_create(customer_id=customer_id, defaults={'name': name})

    for product_id, description, price in [
        (1001, 'Keyboard', '25.00'),
        (1002, 'Mouse', '12.00'),
        (1003, 'Monitor', '180.00'),
        (1004, 'Printer', '250.00'),
    ]:
        Product.objects.using(database).get_or_create(
            product_id=product_id,
            defaults={'description': description, 'unit_price': Decimal(price)},
        )


class Migration(migrations.Migration):
    dependencies = [('orders', '0001_initial')]

    operations = [migrations.RunPython(load_catalogs, migrations.RunPython.noop)]
