from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
    """
    Multi-tenancy ki neev. Har client ka data alag.
    Ek analyst sirf apna client dekh sakta hai.
    """
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class IngestionBatch(models.Model):
    """
    Ek baar upload = ek batch.
    Agar kuch galat nikla toh poori batch revert ho sakti hai.
    Source track karta hai — SAP tha ya utility ya travel.
    """
    SOURCE_SAP = 'sap'
    SOURCE_UTILITY = 'utility'
    SOURCE_TRAVEL = 'travel'
    SOURCE_CHOICES = [
        (SOURCE_SAP, 'SAP Fuel/Procurement'),
        (SOURCE_UTILITY, 'Utility Electricity'),
        (SOURCE_TRAVEL, 'Corporate Travel'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='batches')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    total_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.client.name} | {self.source} | {self.uploaded_at.date()}"


class RawRecord(models.Model):
    """
    Original data as-is — kuch bhi change nahi.

    Kyun alag rakha EmissionRecord se?
    Kyunki normalization galat ho sakti hai. Agar analyst baad mein bole
    "plant PL01 Mumbai tha Delhi nahi" — toh original se recalculate ho sake.
    Ye Breathe ESG ke audit trail ki zaroorat hai.
    """
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name='raw_records')
    row_number = models.IntegerField()
    raw_data = models.JSONField()  # exact row as dict
    parse_error = models.TextField(blank=True, null=True)  # agar parse hi nahi hua
    created_at = models.DateTimeField(auto_now_add=True)


class EmissionRecord(models.Model):
    """
    Normalized record — sab kuch common format mein.

    Scope 1: khud fuel jalaya (SAP diesel, petrol)
    Scope 2: bijli li bahar se (utility)
    Scope 3: travel, supply chain (Concur/Navan)

    GHG Protocol ka standard — auditors yahi expect karte hain.
    """
    SCOPE_1 = 1
    SCOPE_2 = 2
    SCOPE_3 = 3
    SCOPE_CHOICES = [(1, 'Scope 1'), (2, 'Scope 2'), (3, 'Scope 3')]

    CATEGORY_FUEL = 'fuel'
    CATEGORY_ELECTRICITY = 'electricity'
    CATEGORY_TRAVEL = 'travel'
    CATEGORY_CHOICES = [
        (CATEGORY_FUEL, 'Fuel & Combustion'),
        (CATEGORY_ELECTRICITY, 'Purchased Electricity'),
        (CATEGORY_TRAVEL, 'Business Travel'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_FLAGGED = 'flagged'
    STATUS_APPROVED = 'approved'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_FLAGGED, 'Flagged - Needs Attention'),
        (STATUS_APPROVED, 'Approved for Audit'),
    ]

    # Source tracking
    raw_record = models.OneToOneField(RawRecord, on_delete=models.CASCADE, related_name='emission')
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    # Classification
    scope = models.IntegerField(choices=SCOPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    # Normalized values
    # Original unit preserve kiya — agar audit mein poochha "liters mein kitna tha"
    quantity_original = models.DecimalField(max_digits=15, decimal_places=4)
    unit_original = models.CharField(max_length=20)  # L, GAL, kWh, km, etc.
    quantity_normalized = models.DecimalField(max_digits=15, decimal_places=4)
    unit_normalized = models.CharField(max_length=20)  # always kWh or kgCO2e

    # Emission calculation
    emission_factor = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    emission_factor_source = models.CharField(max_length=100, blank=True)  # "DEFRA 2023"
    kgco2e = models.DecimalField(max_digits=15, decimal_places=4, null=True)

    # Period
    activity_date = models.DateField(null=True)
    period_start = models.DateField(null=True)
    period_end = models.DateField(null=True)

    # Source-specific context
    location = models.CharField(max_length=255, blank=True)  # plant code, meter ID, route
    description = models.TextField(blank=True)

    # Review status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    flag_reason = models.TextField(blank=True)  # kyun flag kiya

    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_records'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    edit_history = models.JSONField(default=list)  # [{field, old, new, by, at}]

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client} | {self.category} | {self.activity_date} | {self.status}"
