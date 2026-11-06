from decimal import Decimal, ROUND_HALF_UP, localcontext

from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import SalesOrder, SalesOrderDetail


class SalesOrderForm(forms.ModelForm):
    total_display = forms.DecimalField(label='Importe total', required=False, disabled=True)

    class Meta:
        model = SalesOrder
        fields = ('order_number', 'customer', 'order_date')
        widgets = {'order_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['total_display'].initial = self.instance.total_amount


class SalesOrderDetailForm(forms.ModelForm):
    unit_price_display = forms.DecimalField(label='Precio unitario', required=False, disabled=True)
    line_total_display = forms.DecimalField(label='Total de línea', required=False, disabled=True)

    class Meta:
        model = SalesOrderDetail
        fields = ('product', 'quantity')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_product_id = self.instance.product_id
        self.original_price = self.instance.unit_price
        if self.instance.pk:
            self.fields['unit_price_display'].initial = self.original_price
            self.fields['line_total_display'].initial = self.instance.line_total
            self.fields['product'].widget.attrs.update({
                'data-original-product': self.original_product_id,
                'data-original-price': str(self.original_price),
            })

    def clean(self):
        cleaned = super().clean()
        quantity = cleaned.get('quantity')
        product = cleaned.get('product')
        price = None
        if product is not None:
            price = self.original_price if self.instance.pk and product.pk == self.original_product_id else product.unit_price
            self.instance.unit_price = price
        if quantity is not None and price is not None:
            with localcontext() as context:
                context.prec = 50
                total = (quantity * price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            try:
                SalesOrderDetail._meta.get_field('line_total').clean(total, self.instance)
            except ValidationError:
                raise ValidationError('El total de la línea supera el importe permitido.')
            self.instance.line_total = total
        return cleaned


class OrderDetailBaseFormSet(BaseInlineFormSet):
    default_error_messages = {
        'too_few_forms': 'Agrega al menos %(num)d línea de detalle.',
        'too_many_forms': 'Se permiten como máximo %(num)d líneas de detalle.',
    }

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if 'DELETE' in form.fields:
            form.fields['DELETE'].label = 'Eliminar línea'

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        self.order_total = sum(
            (form.instance.line_total for form in self.forms
             if form.cleaned_data and not form.cleaned_data.get('DELETE') and
             form.cleaned_data.get('quantity') is not None and form.cleaned_data.get('product') is not None),
            Decimal('0.00'),
        )
        try:
            SalesOrder._meta.get_field('total_amount').clean(self.order_total, self.instance)
        except ValidationError:
            raise ValidationError('El importe total supera el importe permitido.')


OrderDetailFormSet = inlineformset_factory(
    SalesOrder,
    SalesOrderDetail,
    form=SalesOrderDetailForm,
    formset=OrderDetailBaseFormSet,
    fields=('product', 'quantity'),
    extra=0,
    min_num=1,
    validate_min=True,
    max_num=1000,
    validate_max=True,
    can_delete=True,
)
