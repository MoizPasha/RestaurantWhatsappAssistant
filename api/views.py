from rest_framework import viewsets, filters, status
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

    def get_queryset(self):
        qs = super().get_queryset()
        # Accept friendly param names from MCP tools or external callers
        def norm(v):
            if v is None:
                return None
            v = str(v).strip()
            # treat empty, null, -1 and 0 as 'no value' (some callers use 0 as sentinel)
            if v == '0':
                return None
            return v

        category = norm(self.request.query_params.get('category') or self.request.query_params.get('category_id'))
        subcategory = norm(self.request.query_params.get('subcategory') or self.request.query_params.get('subcategory_id'))
        # Support direct subcategory__category filter too
        subcat_cat = norm(self.request.query_params.get('subcategory__category'))

        if subcat_cat:
            qs = qs.filter(subcategory__category=subcat_cat)
        elif category:
            qs = qs.filter(subcategory__category=category)

        if subcategory:
            qs = qs.filter(subcategory=subcategory)

        return qs

class MenuItemSizeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MenuItemSize.objects.all()
    serializer_class = MenuItemSizeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['subcategory', 'subcategory__category']

    def get_queryset(self):
        qs = super().get_queryset()
        def norm(v):
            if v is None:
                return None
            v = str(v).strip()
            # treat empty, null, -1 and 0 as 'no value' (some callers use 0 as sentinel)
            if v == '0':
                return None
            return v

        category = norm(self.request.query_params.get('category') or self.request.query_params.get('category_id'))
        subcategory = norm(self.request.query_params.get('subcategory') or self.request.query_params.get('subcategory_id'))
        subcat_cat = norm(self.request.query_params.get('subcategory__category'))

        if subcat_cat:
            qs = qs.filter(subcategory__category=subcat_cat)
        elif category:
            qs = qs.filter(subcategory__category=category)

        if subcategory:
            qs = qs.filter(subcategory=subcategory)

        return qs

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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['phone']

    @action(detail=False, methods=["get"], url_path="by-phone")
    def by_phone(self, request):
        """Lookup a customer by phone number. Returns {exists: bool, customer: {...}} when found."""
        phone = request.query_params.get('phone') or request.data.get('phone')
        if not phone:
            return Response({'detail': 'phone query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        qs = self.get_queryset().filter(phone=phone)
        if not qs.exists():
            return Response({'exists': False}, status=status.HTTP_200_OK)

        customer = qs.first()
        return Response({'exists': True, 'customer': CustomerSerializer(customer).data}, status=status.HTTP_200_OK)

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
