from django.db import models
from django.utils import timezone


class VehicleStock(models.Model):
    STOCK_TYPE = [('new', 'New'), ('used', 'Used'), ('certified', 'Certified Pre-Owned'), ('demo', 'Demo')]
    CONDITION = [('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor'), ('salvage', 'Salvage')]
    STATUS = [
        ('available', 'Available'), ('reserved', 'Reserved'),
        ('sold', 'Sold'), ('trade_in', 'Trade-In'), ('service', 'In Service'), ('transit', 'In Transit'),
    ]
    TRANSMISSION = [('auto', 'Automatic'), ('manual', 'Manual'), ('semi_auto', 'Semi-Automatic'), ('ev', 'Electric')]
    FUEL = [('petrol', 'Petrol'), ('diesel', 'Diesel'), ('hybrid', 'Hybrid'), ('electric', 'Electric'), ('lpg', 'LPG'), ('other', 'Other')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='vehicle_stock')
    stock_number = models.CharField(max_length=30)

    # Vehicle details
    make = models.CharField(max_length=60)
    model = models.CharField(max_length=60)
    variant = models.CharField(max_length=80, blank=True)
    year = models.PositiveSmallIntegerField()
    colour = models.CharField(max_length=40, blank=True)
    interior_colour = models.CharField(max_length=40, blank=True)
    vin = models.CharField(max_length=50, blank=True)
    reg_number = models.CharField(max_length=30, blank=True)
    engine_size = models.CharField(max_length=20, blank=True)
    transmission = models.CharField(max_length=10, choices=TRANSMISSION, default='auto')
    fuel_type = models.CharField(max_length=10, choices=FUEL, default='petrol')
    body_type = models.CharField(max_length=30, blank=True)  # Sedan, SUV, Ute, etc.
    doors = models.PositiveSmallIntegerField(null=True, blank=True)
    seats = models.PositiveSmallIntegerField(null=True, blank=True)
    mileage = models.PositiveIntegerField(null=True, blank=True)

    # Classification
    stock_type = models.CharField(max_length=15, choices=STOCK_TYPE, default='used')
    condition = models.CharField(max_length=15, choices=CONDITION, default='good')
    status = models.CharField(max_length=15, choices=STATUS, default='available')
    location = models.CharField(max_length=100, blank=True)  # lot / yard location

    # Pricing
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    asking_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reserve_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Photos (main)
    main_photo = models.ImageField(upload_to='dms/vehicles/', null=True, blank=True)

    description = models.TextField(blank=True)
    features = models.TextField(blank=True)  # comma-separated features

    date_acquired = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('business', 'stock_number')]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.stock_number} — {self.year} {self.make} {self.model}"

    @property
    def display_name(self):
        return f"{self.year} {self.make} {self.model} {self.variant}".strip()


class VehiclePhoto(models.Model):
    vehicle = models.ForeignKey(VehicleStock, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='dms/vehicle_photos/')
    caption = models.CharField(max_length=100, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'uploaded_at']


class VehicleDeal(models.Model):
    STAGES = [
        ('enquiry', 'Enquiry'), ('test_drive', 'Test Drive Booked'),
        ('negotiation', 'Negotiation'), ('agreed', 'Price Agreed'),
        ('finance', 'Finance Processing'), ('documentation', 'Documentation'),
        ('delivered', 'Delivered'), ('lost', 'Lost'), ('cancelled', 'Cancelled'),
    ]
    FINANCE_TYPES = [
        ('cash', 'Cash'), ('finance', 'Dealer Finance'), ('bank', 'Bank Finance'),
        ('lease', 'Lease'), ('balloon', 'Balloon Finance'), ('other', 'Other'),
    ]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='vehicle_deals')
    deal_number = models.CharField(max_length=20)
    vehicle = models.ForeignKey(VehicleStock, on_delete=models.PROTECT, related_name='deals')
    stage = models.CharField(max_length=20, choices=STAGES, default='enquiry')

    # Customer
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=30, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_address = models.TextField(blank=True)

    # Deal financials
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    finance_type = models.CharField(max_length=10, choices=FINANCE_TYPES, default='cash')
    finance_provider = models.CharField(max_length=100, blank=True)
    finance_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monthly_repayment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    loan_term_months = models.PositiveSmallIntegerField(null=True, blank=True)

    salesperson = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    test_drive_date = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('business', 'deal_number')]
        ordering = ['-created_at']

    def __str__(self):
        return f"DEAL-{self.deal_number}: {self.vehicle} → {self.customer_name}"

    @property
    def gross_profit(self):
        if self.sale_price and self.vehicle.purchase_price:
            trade_in = self.trade_in.accepted_price if hasattr(self, 'trade_in') and self.trade_in.accepted_price else 0
            return self.sale_price - self.vehicle.purchase_price + trade_in
        return None


class TradeIn(models.Model):
    deal = models.OneToOneField(VehicleDeal, on_delete=models.CASCADE, related_name='trade_in')
    make = models.CharField(max_length=60)
    model = models.CharField(max_length=60, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    reg_number = models.CharField(max_length=30, blank=True)
    vin = models.CharField(max_length=50, blank=True)
    mileage = models.PositiveIntegerField(null=True, blank=True)
    condition = models.CharField(max_length=15, choices=VehicleStock.CONDITION, default='good')
    offered_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    accepted_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Trade-in: {self.year} {self.make} {self.model} for {self.deal}"


class DealNote(models.Model):
    deal = models.ForeignKey(VehicleDeal, on_delete=models.CASCADE, related_name='deal_notes')
    note = models.TextField()
    author = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
