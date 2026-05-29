from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
   
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class IngestionBatch(models.Model):
    
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
   
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name='raw_records')
    row_number = models.IntegerField()
    raw_data = models.JSONField()  # exact row as dict
    parse_error = models.TextField(blank=True, null=True)  # agar parse hi nahi hua
    created_at = models.DateTimeField(auto_now_add=True)


class EmissionRecord(models.Model):
   
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