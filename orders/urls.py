from django.urls import path
from django.views.generic import RedirectView

from .views import (
    ENTITIES,
    EntityCreateView,
    EntityDeleteView,
    EntityListView,
    EntityUpdateView,
    OrderCreateView,
    OrderListView,
    OrderUpdateView,
)

app_name = 'orders'

urlpatterns = [path('', RedirectView.as_view(pattern_name='orders:ordenes-list', permanent=False), name='home')]

for route, model in ENTITIES:
    list_view = OrderListView if route == 'ordenes' else EntityListView
    create_view = OrderCreateView if route == 'ordenes' else EntityCreateView
    update_view = OrderUpdateView if route == 'ordenes' else EntityUpdateView
    urlpatterns += [
        path(f'{route}/', list_view.as_view(model=model, route_name=route), name=f'{route}-list'),
        path(f'{route}/nuevo/', create_view.as_view(model=model, route_name=route), name=f'{route}-create'),
        path(f'{route}/<int:pk>/editar/', update_view.as_view(model=model, route_name=route), name=f'{route}-update'),
        path(f'{route}/<int:pk>/eliminar/', EntityDeleteView.as_view(model=model, route_name=route), name=f'{route}-delete'),
    ]
