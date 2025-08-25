from rest_framework import serializers
from .models import *

class MenuSubCategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuSubCategory
        fields = ['id', 'name']

class MenuCategorySerializer(serializers.ModelSerializer):
    subcategories = MenuSubCategorySimpleSerializer(many=True, read_only=True)

    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'subcategories']

class MenuCategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ['id', 'name']

class MenuItemSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    subcategory = MenuSubCategorySimpleSerializer(read_only=True)

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'is_available', 'category', 'subcategory']

    def get_category(self, obj):
        if obj.subcategory and hasattr(obj.subcategory, 'category'):
            return MenuCategorySimpleSerializer(obj.subcategory.category).data
        return None

class MenuItemSizeSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    subcategory = MenuSubCategorySimpleSerializer(read_only=True)

    class Meta:
        model = MenuItemSize
        fields = ['id', 'name', 'price', 'category', 'subcategory']

    def get_category(self, obj):
        if obj.subcategory and hasattr(obj.subcategory, 'parent'):
            return MenuCategorySimpleSerializer(obj.subcategory.parent).data
        return None
    
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'email', 'address']  
        # you can adjust fields based on your model


class BillItemSerializer(serializers.ModelSerializer):
    item = serializers.StringRelatedField()
    size = serializers.StringRelatedField()

    class Meta:
        model = BillItem
        fields = ['id', 'item', 'size', 'quantity', 'unit_price', 'get_total_price']


class BillSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)       # nested serializer
    items = BillItemSerializer(many=True, read_only=True)  # uses related_name from BillItem

    class Meta:
        model = Bill
        fields = [
            'id',
            'customer',
            'status',
            'order_type',
            'payment_method',
            'subtotal',
            'tax_rate',
            'tax_amount',
            'delivery_fee',
            'discount_amount',
            'tip_amount',
            'total_amount',
            'is_paid',
            'paid_at',
            'notes',
            'items',
            'created_at'
        ]
