from django.contrib import admin
from .models import *

admin.site.register(Customer)
admin.site.register(MenuCategory)
admin.site.register(MenuSubCategory)
admin.site.register(MenuItem)
admin.site.register(MenuItemSize)
admin.site.register(Bill)
admin.site.register(BillItem)