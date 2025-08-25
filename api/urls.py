from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

# Create router and register viewsets
router = DefaultRouter()

router = DefaultRouter()
router.register(r'categories', MenuCategoryViewSet, basename='category')
router.register(r'items', MenuItemViewSet, basename='item')
router.register(r'sizes', MenuItemSizeViewSet, basename='size')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'bills', BillViewSet, basename='bill')
router.register(r'bill-items', BillItemViewSet, basename='billitem')
# Include all router URLs
urlpatterns = [
    path('', include(router.urls)),
    path('menu/', full_menu_view, name='menu'),
]