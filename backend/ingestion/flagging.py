from decimal import Decimal
from .models import EmissionRecord


def flag_outliers(batch):
    """
    Batch ke records check karo — suspicious values flag karo.

    Kyun alag file mein hai?
    Ye business logic hai, database logic nahi.
    Kal rule change ho toh sirf ye file badlegi — models.py nahi.
    Breathe ESG ka INARA AI yahi kaam ML se karta hai —
    hamare paas historical data nahi tha toh simple threshold use kiya.
    """
    records = EmissionRecord.objects.filter(
        raw_record__batch=batch,
        status=EmissionRecord.STATUS_PENDING
    )

    if not records.exists():
        return

    # Category wise average nikalo
    from django.db.models import Avg
    for category in ['fuel', 'electricity', 'travel']:
        cat_records = records.filter(category=category)
        if cat_records.count() < 2:
            continue

        avg = cat_records.aggregate(avg=Avg('kgco2e'))['avg']
        if not avg:
            continue

        threshold = Decimal(str(avg)) * Decimal('3')

        for record in cat_records:
            if record.kgco2e and record.kgco2e > threshold:
                existing = record.flag_reason or ''
                record.flag_reason = (existing + ' | ' if existing else '') + \
                    f"Outlier: {record.kgco2e:.1f} kgCO2e is 3x+ above batch average ({avg:.1f})"
                record.status = EmissionRecord.STATUS_FLAGGED
                record.save(update_fields=['flag_reason', 'status'])


def apply_parser_flags(record, flag_message):
    """Parser ne jo flag set kiya use apply karo."""
    if flag_message:
        record.flag_reason = flag_message
        record.status = EmissionRecord.STATUS_FLAGGED
        record.save(update_fields=['flag_reason', 'status'])
