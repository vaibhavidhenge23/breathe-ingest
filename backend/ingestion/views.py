from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

from .models import Client, IngestionBatch, RawRecord, EmissionRecord
from .parsers.sap import parse_sap_file
from .parsers.utility import parse_utility_file
from .parsers.travel import parse_travel_file
from .flagging import flag_outliers, apply_parser_flags


def get_or_create_default_client():
    client, _ = Client.objects.get_or_create(name="Demo Client")
    return client


def save_batch(source, filename, records, errors, file_content):
    client = get_or_create_default_client()
    batch = IngestionBatch.objects.create(
        client=client,
        source=source,
        filename=filename,
        total_rows=len(records) + len(errors),
        failed_rows=len(errors),
    )

    for i, rec in enumerate(records):
        raw = RawRecord.objects.create(
            batch=batch,
            row_number=i + 2,
            raw_data=rec['raw'],
        )
        emission = EmissionRecord.objects.create(
            raw_record=raw,
            client=client,
            scope=rec['scope'],
            category=rec['category'],
            quantity_original=rec['quantity_original'],
            unit_original=rec['unit_original'],
            quantity_normalized=rec['quantity_normalized'],
            unit_normalized=rec['unit_normalized'],
            emission_factor=rec.get('emission_factor'),
            emission_factor_source=rec.get('emission_factor_source', ''),
            kgco2e=rec.get('kgco2e'),
            activity_date=rec.get('activity_date'),
            period_start=rec.get('period_start'),
            period_end=rec.get('period_end'),
            location=rec.get('location', ''),
            description=rec.get('description', ''),
        )
        if rec.get('flag'):
            apply_parser_flags(emission, rec['flag'])

    # Failed rows bhi store karo as RawRecord (parse_error ke saath)
    for row_num, error_msg in errors:
        RawRecord.objects.create(
            batch=batch,
            row_number=row_num,
            raw_data={},
            parse_error=error_msg,
        )

    flag_outliers(batch)
    return batch


class SAPUploadView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=400)

        records, errors = parse_sap_file(file.read())
        batch = save_batch('sap', file.name, records, errors, None)

        return Response({
            'batch_id': batch.id,
            'total': batch.total_rows,
            'parsed': len(records),
            'failed': batch.failed_rows,
            'message': f"SAP file ingested. {len(records)} records parsed, {len(errors)} failed."
        }, status=201)


class UtilityUploadView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=400)

        records, errors = parse_utility_file(file.read())
        batch = save_batch('utility', file.name, records, errors, None)

        return Response({
            'batch_id': batch.id,
            'total': batch.total_rows,
            'parsed': len(records),
            'failed': batch.failed_rows,
        }, status=201)


class TravelUploadView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=400)

        records, errors = parse_travel_file(file.read())
        batch = save_batch('travel', file.name, records, errors, None)

        return Response({
            'batch_id': batch.id,
            'total': batch.total_rows,
            'parsed': len(records),
            'failed': batch.failed_rows,
        }, status=201)


class BatchListView(APIView):
    def get(self, request):
        batches = IngestionBatch.objects.all().order_by('-uploaded_at')[:20]
        return Response([{
            'id': b.id,
            'source': b.source,
            'filename': b.filename,
            'uploaded_at': b.uploaded_at,
            'total_rows': b.total_rows,
            'failed_rows': b.failed_rows,
        } for b in batches])
