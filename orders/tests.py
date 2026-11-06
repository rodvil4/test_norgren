from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Customer, Product, SalesOrder, SalesOrderDetail


class OrdersTests(TestCase):
    def test_orders_list_shows_each_header_followed_by_its_details(self):
        first = SalesOrder.objects.create(
            order_number='SO-FIRST', customer_id=1, order_date='2026-11-05', total_amount='50'
        )
        second = SalesOrder.objects.create(
            order_number='SO-SECOND', customer_id=2, order_date='2026-11-06', total_amount='12'
        )
        empty = SalesOrder.objects.create(
            order_number='SO-EMPTY', customer_id=3, order_date='2026-11-07', total_amount='0'
        )
        SalesOrderDetail.objects.create(
            sales_order=first, line_number=2, product_id=1002, quantity=1, unit_price=12, line_total=12
        )
        SalesOrderDetail.objects.create(
            sales_order=first, line_number=1, product_id=1001, quantity=2, unit_price=19, line_total=38
        )
        SalesOrderDetail.objects.create(
            sales_order=second, line_number=1, product_id=1004, quantity=1, unit_price=12, line_total=12
        )
        with self.assertNumQueries(2):
            response = self.client.get(reverse('orders:ordenes-list'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        for value in ('ABC Corporation', 'XYZ Industries', '05/11/2026', '50.00', '19.00',
                      'Keyboard', 'Mouse', 'Printer', 'Esta orden no tiene detalles.'):
            self.assertIn(value, html)
        self.assertTrue(html.index('SO-FIRST') < html.index('Keyboard') < html.index('Mouse') <
                        html.index('SO-SECOND') < html.index('Printer') < html.index('SO-EMPTY') <
                        html.index('Esta orden no tiene detalles.'))
        for order in (first, second, empty):
            self.assertContains(response, reverse('orders:ordenes-update', args=[order.pk]))
            self.assertContains(response, reverse('orders:ordenes-delete', args=[order.pk]))
        self.assertContains(response, reverse('orders:ordenes-create'))

    def test_orders_list_empty(self):
        self.assertContains(self.client.get(reverse('orders:ordenes-list')), 'No hay registros.')

    def test_navigation_on_list_form_and_delete_pages(self):
        routes = ('ordenes', 'clientes', 'productos')
        pages = [
            (reverse(f'orders:{route}-list'), route) for route in routes
        ] + [
            (reverse('orders:ordenes-create'), 'ordenes'),
            (reverse('orders:clientes-update', args=[1]), 'clientes'),
            (reverse('orders:productos-delete', args=[1001]), 'productos'),
        ]
        for page, active_route in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'aria-label="Navegación principal"')
                self.assertNotContains(response, f'href="{reverse("orders:detalles-list")}"')
                for route in routes:
                    suffix = ' class="active"' if route == active_route else ''
                    self.assertContains(response, f'href="{reverse(f"orders:{route}-list")}"{suffix}')

    def test_seed_catalogs(self):
        self.assertEqual(Customer.objects.get(pk=1).name, 'ABC Corporation')
        self.assertEqual(Customer.objects.count(), 3)
        self.assertEqual(Product.objects.get(pk=1003).unit_price, Decimal('180.00'))
        self.assertEqual(Product.objects.count(), 4)

    def test_order_and_detail_crud(self):
        order_data = {
            'order_number': 'SO-001',
            'customer': 1,
            'order_date': '2026-11-05',
            'total_amount': '50.00',
            'details-TOTAL_FORMS': '1',
            'details-INITIAL_FORMS': '0',
            'details-0-line_number': '1',
            'details-0-product': '1001',
            'details-0-quantity': '2',
            'details-0-unit_price': '25.00',
            'details-0-line_total': '50.00',
        }
        response = self.client.post(reverse('orders:ordenes-create'), order_data)
        self.assertRedirects(response, reverse('orders:ordenes-list'))
        order = SalesOrder.objects.get(order_number='SO-001')
        self.assertContains(self.client.get(reverse('orders:ordenes-list')), 'SO-001')
        self.assertEqual(self.client.get(reverse('orders:ordenes-update', args=[order.pk])).status_code, 200)

        detail_data = {
            'sales_order': order.pk,
            'line_number': 1,
            'product': 1001,
            'quantity': '2',
            'unit_price': '25.00',
            'line_total': '50.00',
        }
        detail = SalesOrderDetail.objects.get(sales_order=order)
        self.assertContains(self.client.get(reverse('orders:detalles-list')), 'Keyboard')
        detail_data.update(quantity='3', line_total='75.00')
        self.assertRedirects(
            self.client.post(reverse('orders:detalles-update', args=[detail.pk]), detail_data),
            reverse('orders:detalles-list'),
        )
        detail.refresh_from_db()
        self.assertEqual(detail.quantity, Decimal('3'))
        self.assertEqual(detail.line_total, Decimal('75'))
        order_data['total_amount'] = '75.00'
        order_data.update({
            'details-INITIAL_FORMS': '1',
            'details-0-sales_order_detail_id': str(detail.pk),
            'details-0-quantity': '3',
            'details-0-line_total': '75.00',
        })
        response = self.client.post(reverse('orders:ordenes-update', args=[order.pk]), order_data)
        if response.status_code == 200:
            self.fail(f"Errores: {response.context['form'].errors}; {response.context['formset'].errors}")
        self.assertRedirects(response, reverse('orders:ordenes-list'))
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal('75'))
        self.assertEqual(self.client.get(reverse('orders:detalles-delete', args=[detail.pk])).status_code, 200)
        self.assertRedirects(
            self.client.post(reverse('orders:detalles-delete', args=[detail.pk])),
            reverse('orders:detalles-list'),
        )
        self.assertFalse(SalesOrderDetail.objects.filter(pk=detail.pk).exists())
        self.assertRedirects(
            self.client.post(reverse('orders:ordenes-delete', args=[order.pk])),
            reverse('orders:ordenes-list'),
        )
        self.assertFalse(SalesOrder.objects.filter(pk=order.pk).exists())

    def test_create_requires_valid_details_and_saves_multiple_together(self):
        data = {
            'order_number': 'SO-MULTI',
            'customer': '1',
            'order_date': '2026-11-05',
            'total_amount': '62.00',
            'details-TOTAL_FORMS': '1',
            'details-INITIAL_FORMS': '0',
        }
        response = self.client.post(reverse('orders:ordenes-create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agrega al menos 1 línea de detalle.')
        self.assertFalse(SalesOrder.objects.filter(order_number='SO-MULTI').exists())

        data.update({
            'details-TOTAL_FORMS': '2',
            'details-0-line_number': '1',
            'details-0-product': '1001',
            'details-0-quantity': '2',
            'details-0-unit_price': '25',
            'details-0-line_total': '50',
            'details-1-line_number': '2',
            'details-1-product': '999999',
            'details-1-quantity': '1',
            'details-1-unit_price': '12',
            'details-1-line_total': '12',
        })
        response = self.client.post(reverse('orders:ordenes-create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['formset'].errors)
        self.assertFalse(SalesOrder.objects.filter(order_number='SO-MULTI').exists())
        self.assertEqual(SalesOrderDetail.objects.count(), 0)

        data['details-1-product'] = '1002'
        response = self.client.post(reverse('orders:ordenes-create'), data)
        self.assertRedirects(response, reverse('orders:ordenes-list'))
        order = SalesOrder.objects.get(order_number='SO-MULTI')
        self.assertEqual(order.salesorderdetail_set.count(), 2)

    def test_automatic_line_numbers_on_create_delete_and_add(self):
        create = reverse('orders:ordenes-create')
        response = self.client.get(create)
        self.assertNotContains(response, 'name="details-0-line_number"')
        data = {
            'order_number': 'SO-NUMBER',
            'customer': '1',
            'order_date': '2026-11-05',
            'details-TOTAL_FORMS': '3',
            'details-INITIAL_FORMS': '0',
            'details-0-product': '1001',
            'details-0-quantity': '1',
            'details-0-line_number': '999',
            'details-1-product': '1002',
            'details-1-quantity': '1',
            'details-2-product': '1003',
            'details-2-quantity': '1',
        }
        self.assertRedirects(self.client.post(create, data), reverse('orders:ordenes-list'))
        order = SalesOrder.objects.get(order_number='SO-NUMBER')
        lines = list(order.salesorderdetail_set.all())
        self.assertEqual([line.line_number for line in lines], [1, 2, 3])
        edit = reverse('orders:ordenes-update', args=[order.pk])
        self.assertNotContains(self.client.get(edit), 'name="details-0-line_number"')
        data.update({
            'details-TOTAL_FORMS': '4',
            'details-INITIAL_FORMS': '3',
            'details-0-sales_order_detail_id': str(lines[0].pk),
            'details-1-sales_order_detail_id': str(lines[1].pk),
            'details-2-sales_order_detail_id': str(lines[2].pk),
            'details-1-DELETE': 'on',
            'details-3-product': '1004',
            'details-3-quantity': '1',
        })
        self.assertRedirects(self.client.post(edit, data), reverse('orders:ordenes-list'))
        lines = list(order.salesorderdetail_set.all())
        self.assertEqual([(line.product_id, line.line_number) for line in lines],
                         [(1001, 1), (1003, 2), (1004, 3)])

    def test_cannot_remove_all_details_during_order_edit(self):
        order = SalesOrder.objects.create(
            order_number='SO-EDIT', customer_id=1, order_date='2026-11-05', total_amount='25'
        )
        detail = SalesOrderDetail.objects.create(
            sales_order=order, line_number=1, product_id=1001, quantity=1, unit_price=25, line_total=25
        )
        response = self.client.post(reverse('orders:ordenes-update', args=[order.pk]), {
            'order_number': 'SO-CHANGED',
            'customer': '1',
            'order_date': '2026-11-05',
            'total_amount': '25',
            'details-TOTAL_FORMS': '1',
            'details-INITIAL_FORMS': '1',
            'details-0-sales_order_detail_id': str(detail.pk),
            'details-0-DELETE': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['formset'].non_form_errors())
        order.refresh_from_db()
        self.assertEqual(order.order_number, 'SO-EDIT')
        self.assertTrue(SalesOrderDetail.objects.filter(pk=detail.pk).exists())

    def test_calculated_totals_ignore_submitted_values_and_round_per_line(self):
        Product.objects.filter(pk=1001).update(unit_price=Decimal('0.01'))
        data = {
            'order_number': 'SO-CALC', 'customer': '1', 'order_date': '2026-11-05',
            'total_amount': '999', 'total_display': '999',
            'details-TOTAL_FORMS': '2', 'details-INITIAL_FORMS': '0',
            'details-0-line_number': '1', 'details-0-product': '1001',
            'details-0-quantity': '0.5000', 'details-0-unit_price': '0.01',
            'details-0-line_total': '999', 'details-0-line_total_display': '999',
            'details-1-line_number': '2', 'details-1-product': '1002',
            'details-1-quantity': '2.1250', 'details-1-unit_price': '12.00',
        }
        response = self.client.post(reverse('orders:ordenes-create'), data)
        self.assertRedirects(response, reverse('orders:ordenes-list'))
        order = SalesOrder.objects.get(order_number='SO-CALC')
        lines = list(order.salesorderdetail_set.all())
        self.assertEqual([line.line_total for line in lines], [Decimal('0.01'), Decimal('25.50')])
        self.assertEqual(order.total_amount, Decimal('25.51'))

        data.update({
            'details-INITIAL_FORMS': '2',
            'details-0-sales_order_detail_id': str(lines[0].pk),
            'details-1-sales_order_detail_id': str(lines[1].pk),
            'details-1-DELETE': 'on',
        })
        response = self.client.post(reverse('orders:ordenes-update', args=[order.pk]), data)
        self.assertRedirects(response, reverse('orders:ordenes-list'))
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal('0.01'))
        self.assertEqual(order.salesorderdetail_set.count(), 1)

    def test_overflow_is_rejected_without_saving(self):
        data = {
            'order_number': 'SO-OVERFLOW', 'customer': '1', 'order_date': '2026-11-05',
            'details-TOTAL_FORMS': '1', 'details-INITIAL_FORMS': '0',
            'details-0-line_number': '1', 'details-0-product': '1003',
            'details-0-quantity': '99999999999999.9999', 'details-0-unit_price': '9999999999999999.99',
        }
        response = self.client.post(reverse('orders:ordenes-create'), data)
        self.assertContains(response, 'El total de la línea supera el importe permitido.')
        self.assertFalse(SalesOrder.objects.filter(order_number='SO-OVERFLOW').exists())

    def test_order_edit_recalculates_unchanged_legacy_detail(self):
        order = SalesOrder.objects.create(
            order_number='SO-LEGACY', customer_id=1, order_date='2026-11-05', total_amount='1'
        )
        detail = SalesOrderDetail.objects.create(
            sales_order=order, line_number=1, product_id=1001, quantity=2, unit_price=25, line_total=1
        )
        response = self.client.post(reverse('orders:ordenes-update', args=[order.pk]), {
            'order_number': order.order_number, 'customer': '1', 'order_date': '2026-11-05',
            'details-TOTAL_FORMS': '1', 'details-INITIAL_FORMS': '1',
            'details-0-sales_order_detail_id': str(detail.pk), 'details-0-line_number': '1',
            'details-0-product': '1001', 'details-0-quantity': '2',
            'details-0-unit_price': '25',
        })
        self.assertRedirects(response, reverse('orders:ordenes-list'))
        detail.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(detail.line_total, Decimal('50'))
        self.assertEqual(order.total_amount, Decimal('50'))

    def test_catalog_price_and_historical_price(self):
        order = SalesOrder.objects.create(
            order_number='SO-PRICE', customer_id=1, order_date='2026-11-05', total_amount='40'
        )
        detail = SalesOrderDetail.objects.create(
            sales_order=order, line_number=1, product_id=1001, quantity=2, unit_price=20, line_total=40
        )
        data = {
            'order_number': order.order_number, 'customer': '1', 'order_date': '2026-11-05',
            'details-TOTAL_FORMS': '1', 'details-INITIAL_FORMS': '1',
            'details-0-sales_order_detail_id': str(detail.pk), 'details-0-line_number': '1',
            'details-0-product': '1001', 'details-0-quantity': '3',
            'details-0-unit_price': '999', 'details-0-unit_price_display': '999',
        }
        response = self.client.post(reverse('orders:ordenes-update', args=[order.pk]), data)
        self.assertRedirects(response, reverse('orders:ordenes-list'))
        detail.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(detail.unit_price, Decimal('20.00'))
        self.assertEqual(order.total_amount, Decimal('60.00'))
        data['details-0-product'] = '1002'
        response = self.client.post(reverse('orders:ordenes-update', args=[order.pk]), data)
        self.assertRedirects(response, reverse('orders:ordenes-list'))
        detail.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(detail.unit_price, Decimal('12.00'))
        self.assertEqual(order.total_amount, Decimal('36.00'))

    def test_catalog_crud(self):
        cases = [
            ('clientes', Customer, {'name': 'Nuevo cliente'}, {'name': 'Cliente editado'}),
            ('productos', Product, {'description': 'Nuevo producto', 'unit_price': '10.00'},
             {'description': 'Producto editado', 'unit_price': '12.00'}),
        ]
        for route, model, initial, updated in cases:
            with self.subTest(route=route):
                response = self.client.post(reverse(f'orders:{route}-create'), initial)
                self.assertRedirects(response, reverse(f'orders:{route}-list'))
                obj = model.objects.get(**initial)
                self.assertEqual(self.client.get(reverse(f'orders:{route}-update', args=[obj.pk])).status_code, 200)
                self.assertRedirects(
                    self.client.post(reverse(f'orders:{route}-update', args=[obj.pk]), updated),
                    reverse(f'orders:{route}-list'),
                )
                self.assertTrue(model.objects.filter(pk=obj.pk, **updated).exists())
                self.assertRedirects(
                    self.client.post(reverse(f'orders:{route}-delete', args=[obj.pk])),
                    reverse(f'orders:{route}-list'),
                )
                self.assertFalse(model.objects.filter(pk=obj.pk).exists())

    def test_references_and_order_deletion(self):
        order = SalesOrder.objects.create(
            order_number='SO-002', customer_id=1, order_date='2026-11-05', total_amount='25'
        )
        SalesOrderDetail.objects.create(
            sales_order=order, line_number=1, product_id=1001, quantity=1, unit_price=25, line_total=25
        )
        for route, pk, model in [('clientes', 1, Customer), ('productos', 1001, Product)]:
            response = self.client.post(reverse(f'orders:{route}-delete', args=[pk]), follow=True)
            self.assertContains(response, 'No se puede eliminar')
            self.assertTrue(model.objects.filter(pk=pk).exists())
        response = self.client.get(reverse('orders:ordenes-delete', args=[order.pk]))
        self.assertContains(response, 'También se eliminarán sus detalles')
        self.client.post(reverse('orders:ordenes-delete', args=[order.pk]))
        self.assertFalse(SalesOrderDetail.objects.filter(sales_order_id=order.pk).exists())

    def test_invalid_foreign_keys_are_rejected(self):
        response = self.client.post(reverse('orders:ordenes-create'), {
            'order_number': 'INVALID',
            'customer': 999999,
            'order_date': '2026-11-05',
            'total_amount': '1.00',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SalesOrder.objects.filter(order_number='INVALID').exists())
        self.assertTrue(response.context['form'].errors)
