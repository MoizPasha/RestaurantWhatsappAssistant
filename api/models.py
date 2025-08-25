from decimal import Decimal, ROUND_HALF_UP
from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.utils import timezone

# -------------------------------
# Menu & Categories
# -------------------------------

class MenuCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Menu Categories"

    def __str__(self):
        return self.name


class MenuSubCategory(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        MenuCategory, related_name="subcategories", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = "Menu Sub Categories"
        unique_together = ("name", "category")

    def __str__(self):
        return f"{self.name}"


class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    subcategory = models.ForeignKey(
        MenuSubCategory, related_name="menu_items", on_delete=models.CASCADE
    )
    description = models.TextField(blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}"


class MenuItemSize(models.Model):
    name = models.CharField(max_length=15)  # Small, Medium, Large, etc.
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subcategory = models.ForeignKey(
        MenuSubCategory, related_name="item_sizes", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("name", "subcategory")

    def __str__(self):
        return f"{self.name} - ${self.price} ({self.subcategory.name})"


# -------------------------------
# Customers
# -------------------------------

class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# -------------------------------
# Billing
# -------------------------------

class Bill(models.Model):
    BILL_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("preparing", "Preparing"),
        ("ready", "Ready for Pickup"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("cash", "Cash"),
        ("card", "Card"),
        ("digital_wallet", "Digital Wallet"),
        ("bank_transfer", "Bank Transfer"),
        ("pending", "Pending Payment"),
    ]

    ORDER_TYPE_CHOICES = [
        ("dine_in", "Dine In"),
        ("takeaway", "Takeaway"),
        ("delivery", "Delivery"),
    ]

    customer = models.ForeignKey(
        Customer, related_name="bills", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20, choices=BILL_STATUS_CHOICES, default="pending"
    )
    order_type = models.CharField(
        max_length=15, choices=ORDER_TYPE_CHOICES, default="delivery"
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default="pending"
    )

    # Pricing breakdown
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------- Helpers ----------
    @staticmethod
    def _quantize(v: Decimal) -> Decimal:
        """Round to 2 decimal places using ROUND_HALF_UP."""
        if not isinstance(v, Decimal):
            v = Decimal(v)
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_tax_rate_by_payment_method(self) -> Decimal:
        """Return tax percentage based on payment method."""
        return Decimal("5.00") if self.payment_method == "cash" else Decimal("16.00")

    def calculate_subtotal(self) -> Decimal:
        """Sum all related BillItems."""
        return self._quantize(sum((item.get_total_price() for item in self.items.all()), Decimal("0.00")))

    def calculate_tax(self) -> Decimal:
        return self._quantize((self.subtotal * self.tax_rate) / Decimal("100"))

    def calculate_total(self) -> Decimal:
        total = self.subtotal + self.tax_amount + self.delivery_fee + self.tip_amount - self.discount_amount
        return self._quantize(total)

    def update_totals(self, save: bool = True):
        """Recalculate subtotal, tax, and total."""
        self.subtotal = self.calculate_subtotal()
        self.tax_rate = self.get_tax_rate_by_payment_method()
        self.tax_amount = self.calculate_tax()
        self.total_amount = self.calculate_total()

        if save:
            self.save(update_fields=[
                "subtotal", "tax_rate", "tax_amount",
                "delivery_fee", "tip_amount", "discount_amount",
                "total_amount", "updated_at"
            ])

    def add_tip_percentage(self, percentage: float):
        with transaction.atomic():
            self.update_totals(save=False)
            self.tip_amount = self._quantize((self.subtotal * Decimal(str(percentage))) / Decimal("100"))
            self.update_totals(save=True)

    def add_tip_amount(self, amount: float):
        with transaction.atomic():
            self.update_totals(save=False)
            self.tip_amount = self._quantize(Decimal(str(amount)))
            self.update_totals(save=True)

    def mark_paid(self, payment_method: str = None, notes: str = None):
        with transaction.atomic():
            if payment_method:
                self.payment_method = payment_method
            if notes:
                self.notes = (self.notes + f"\nPayment: {notes}") if self.notes else f"Payment: {notes}"
            self.is_paid = True
            self.paid_at = timezone.now()
            self.update_totals(save=False)
            self.save(update_fields=[
                "payment_method", "notes", "is_paid", "paid_at",
                "subtotal", "tax_rate", "tax_amount", "total_amount", "updated_at"
            ])

    def save(self, *args, **kwargs):
        """Ensure totals are always correct."""
        self.update_totals(save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bill #{self.pk} for {self.customer} - {self.total_amount}"


class BillItem(models.Model):
    bill = models.ForeignKey(
        Bill, related_name="items", on_delete=models.CASCADE
    )
    item = models.ForeignKey(
        MenuItem, related_name="bill_items", on_delete=models.CASCADE
    )
    size = models.ForeignKey(
        MenuItemSize, related_name="bill_items", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
        null=True, blank=True
    )

    class Meta:
        unique_together = ("bill", "item", "size")

    @property
    def total_price(self) -> Decimal:
        """Total price = unit_price * quantity."""
        price = self.unit_price if self.unit_price is not None else self.size.price
        return Bill._quantize(Decimal(price) * Decimal(self.quantity))

    def get_total_price(self) -> Decimal:
        return self.total_price

    def save(self, *args, **kwargs):
        if self.unit_price is None:
            self.unit_price = Decimal(self.size.price)
        super().save(*args, **kwargs)

        # Refresh bill totals
        try:
            with transaction.atomic():
                bill = Bill.objects.select_for_update().get(pk=self.bill.pk)
                bill.update_totals(save=True)
        except Exception:
            self.bill.update_totals(save=True)

    def delete(self, *args, **kwargs):
        bill = self.bill
        super().delete(*args, **kwargs)
        try:
            with transaction.atomic():
                bill = Bill.objects.select_for_update().get(pk=bill.pk)
                bill.update_totals(save=True)
        except Exception:
            bill.update_totals(save=True)

    def __str__(self):
        return f"{self.quantity} x {self.size.name} - {self.total_price}"
