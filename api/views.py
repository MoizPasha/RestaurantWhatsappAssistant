from rest_framework import viewsets,filters
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .models import *
from .serializers import *
from django_filters.rest_framework import DjangoFilterBackend

class MenuCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MenuCategory.objects.all()
    serializer_class = MenuCategorySerializer

class MenuItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['subcategory', 'subcategory__category']

class MenuItemSizeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MenuItemSize.objects.all()
    serializer_class = MenuItemSizeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['subcategory', 'subcategory__category']

@api_view(["GET"])
def full_menu_view(request):
    categories = MenuCategory.objects.prefetch_related(
        "subcategories__menu_items",
        "subcategories__item_sizes",
    )
    menu = []
    for cat in categories:
        cat_dict = {
            "id": cat.id,
            "name": cat.name,
            "subcategories": []
        }
        for sub in cat.subcategories.all():
            sub_dict = {
                "id": sub.id,
                "name": sub.name,
                "items": []
            }
            for item in sub.menu_items.all():
                item_dict = {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "is_available": item.is_available,
                    "sizes": [
                        {
                            "id": size.id,
                            "name": size.name,
                            "price": str(size.price)
                        }
                        for size in sub.item_sizes.all()
                    ]
                }
                sub_dict["items"].append(item_dict)
            cat_dict["subcategories"].append(sub_dict)
        menu.append(cat_dict)
    return Response(menu)

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        bill = self.get_object()
        bill.status = "cancelled"
        bill.save()
        return Response({"status": "Bill cancelled"}, status=status.HTTP_200_OK)
    
class BillItemViewSet(viewsets.ModelViewSet):
    queryset = BillItem.objects.all()
    serializer_class = BillItemSerializer
