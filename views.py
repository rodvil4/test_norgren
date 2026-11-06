from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import OrderDetailFormSet, SalesOrderForm
from .models import Customer, Product, SalesOrder, SalesOrderDetail


class CatalogContextMixin:
    route_name = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entity_name'] = self.model._meta.verbose_name
        context['entity_name_plural'] = self.model._meta.verbose_name_plural
        context['route_name'] = self.route_name
        return context


class EntityListView(CatalogContextMixin, ListView):
    template_name = 'orders/list.html'


class OrderListView(EntityListView):
    template_name = 'orders/order_list.html'

    def get_queryset(self):
        return super().get_queryset().select_related('customer').prefetch_related(
            Prefetch('salesorderdetail_set', queryset=SalesOrderDetail.objects.select_related('product'))
        )


class EntityCreateView(CatalogContextMixin, CreateView):
    fields = '__all__'
    template_name = 'orders/form.html'

    def get_success_url(self):
        return reverse_lazy(f'orders:{self.route_name}-list')


class EntityUpdateView(CatalogContextMixin, UpdateView):
    fields = '__all__'
    template_name = 'orders/form.html'

    def get_success_url(self):
        return reverse_lazy(f'orders:{self.route_name}-list')


class OrderWithDetailsMixin:
    template_name = 'orders/order_form.html'
    form_class = SalesOrderForm
    fields = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_prices'] = {
            str(product.pk): str(product.unit_price) for product in Product.objects.all()
        }
        if 'formset' not in context:
            context['formset'] = OrderDetailFormSet(
                self.request.POST if self.request.method == 'POST' else None,
                instance=self.object,
                prefix='details',
            )
        return context

    def form_valid(self, form):
        formset = OrderDetailFormSet(self.request.POST, instance=form.instance, prefix='details')
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, formset=formset))
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.total_amount = formset.order_total
            self.object.save()
            formset.instance = self.object
            line_number = 0
            for detail_form in formset.forms:
                if detail_form.cleaned_data.get('DELETE'):
                    if detail_form.instance.pk:
                        detail_form.instance.delete()
                elif detail_form.cleaned_data.get('quantity') is not None:
                    line_number += 1
                    detail = detail_form.save(commit=False)
                    detail.sales_order = self.object
                    detail.line_number = line_number
                    detail.save()
        return HttpResponseRedirect(self.get_success_url())


class OrderCreateView(OrderWithDetailsMixin, EntityCreateView):
    pass


class OrderUpdateView(OrderWithDetailsMixin, EntityUpdateView):
    pass


class EntityDeleteView(CatalogContextMixin, DeleteView):
    template_name = 'orders/confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy(f'orders:{self.route_name}-list')

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, 'No se puede eliminar porque existen registros relacionados.')
            return redirect(self.get_success_url())


ENTITIES = (
    ('clientes', Customer),
    ('productos', Product),
    ('ordenes', SalesOrder),
    ('detalles', SalesOrderDetail),
)
