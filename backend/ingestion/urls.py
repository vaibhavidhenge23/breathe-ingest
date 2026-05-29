from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth.models import User

from ingestion.models import EmissionRecord, RawRecord
from .models import AuditLog


def get_or_create_user(role='analyst'):
    user, _ = User.objects.get_or_create(username=role)
    return user

def get_default_user():
    return get_or_create_user('analyst')

def log_action(user, action, record_id=None, batch_id=None, detail=''):
    AuditLog.objects.create(
        user=user, action=action,
        record_id=record_id, batch_id=batch_id, detail=detail
    )


class RecordListView(APIView):
    def get(self, request):
        qs = EmissionRecord.objects.select_related('raw_record__batch').all()
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        scope = request.query_params.get('scope')
        if scope:
            qs = qs.filter(scope=scope)
        batch_id = request.query_params.get('batch_id')
        if batch_id:
            qs = qs.filter(raw_record__batch_id=batch_id)
        return Response([serialize_record(r) for r in qs[:500]])


class ApproveRecordView(APIView):
    def post(self, request, record_id):
        try:
            record = EmissionRecord.objects.get(id=record_id)
        except EmissionRecord.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        if record.status == EmissionRecord.STATUS_APPROVED:
            return Response({'error': 'Already approved'}, status=400)
        user = get_default_user()
        record.status = EmissionRecord.STATUS_APPROVED
        record.approved_by = user
        record.approved_at = timezone.now()
        record.save(update_fields=['status', 'approved_by', 'approved_at'])
        log_action(user, AuditLog.ACTION_APPROVE, record_id=record.id,
                   detail=f"Approved {record.category} record — {record.kgco2e} kgCO2e")
        return Response({'message': 'Approved', 'id': record.id})


class BulkApproveView(APIView):
    def post(self, request):
        batch_id = request.data.get('batch_id')
        qs = EmissionRecord.objects.filter(status=EmissionRecord.STATUS_PENDING)
        if batch_id:
            qs = qs.filter(raw_record__batch_id=batch_id)
        user = get_default_user()
        now = timezone.now()
        ids = list(qs.values_list('id', flat=True))
        count = qs.update(status=EmissionRecord.STATUS_APPROVED, approved_by=user, approved_at=now)
        log_action(user, AuditLog.ACTION_APPROVE, detail=f"Bulk approved {count} records")
        return Response({'approved': count})


class RecordDetailView(APIView):
    def get(self, request, record_id):
        try:
            record = EmissionRecord.objects.select_related('raw_record').get(id=record_id)
        except EmissionRecord.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        data = serialize_record(record)
        data['raw_data'] = record.raw_record.raw_data
        data['parse_error'] = record.raw_record.parse_error
        return Response(data)


class DashboardSummaryView(APIView):
    def get(self, request):
        from django.db.models import Sum
        total = EmissionRecord.objects.count()
        pending = EmissionRecord.objects.filter(status='pending').count()
        flagged = EmissionRecord.objects.filter(status='flagged').count()
        approved = EmissionRecord.objects.filter(status='approved').count()
        total_co2 = EmissionRecord.objects.filter(status='approved').aggregate(total=Sum('kgco2e'))['total'] or 0
        return Response({
            'total': total, 'pending': pending,
            'flagged': flagged, 'approved': approved,
            'approved_kgco2e': round(float(total_co2), 2),
        })


class AuditLogView(APIView):
    """Full audit trail — every approve/flag/upload action."""
    def get(self, request):
        logs = AuditLog.objects.select_related('user').all()[:200]
        return Response([{
            'id': l.id,
            'user': l.user.username if l.user else 'system',
            'action': l.action,
            'record_id': l.record_id,
            'batch_id': l.batch_id,
            'detail': l.detail,
            'timestamp': l.timestamp,
        } for l in logs])


def serialize_record(r):
    return {
        'id': r.id,
        'scope': r.scope,
        'category': r.category,
        'status': r.status,
        'flag_reason': r.flag_reason,
        'quantity_original': str(r.quantity_original),
        'unit_original': r.unit_original,
        'kgco2e': str(r.kgco2e) if r.kgco2e else None,
        'activity_date': str(r.activity_date) if r.activity_date else None,
        'location': r.location,
        'description': r.description,
        'emission_factor_source': r.emission_factor_source,
        'batch_id': r.raw_record.batch_id,
        'source': r.raw_record.batch.source,
        'approved_at': str(r.approved_at) if r.approved_at else None,
    }
