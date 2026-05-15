import csv
import json
from io import StringIO

from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response


TEMPLATES = {
    'credit': {
        'filename': 'fintrust-credit-dataset-template',
        'rows': [
            {
                'user_id': '',
                'monthly_income': 180000,
                'mobile_money_frequency': 52,
                'late_payments': 1,
                'account_age_months': 18,
            },
            {
                'user_id': '',
                'monthly_income': 95000,
                'mobile_money_frequency': 28,
                'late_payments': 4,
                'account_age_months': 9,
            },
        ],
    },
    'fraud': {
        'filename': 'fintrust-fraud-dataset-template',
        'rows': [
            {
                'transaction_id': '',
                'amount': 750000,
                'location': 'Yaounde',
                'device_change': True,
                'avg_amount': 90000,
            },
            {
                'transaction_id': '',
                'amount': 45000,
                'location': 'Douala',
                'device_change': False,
                'avg_amount': 60000,
            },
        ],
    },
    'transactions': {
        'filename': 'fintrust-transactions-template',
        'rows': [
            {
                'user_id': '',
                'amount': 750000,
                'type': 'transfer',
                'payment_method': 'mobile_money',
                'location': 'Yaounde',
                'timestamp': '2026-05-15T09:30:00Z',
                'device_change': True,
            },
            {
                'user_id': '',
                'amount': 45000,
                'type': 'debit',
                'payment_method': 'bank',
                'location': 'Douala',
                'timestamp': '2026-05-14T15:00:00Z',
                'device_change': False,
            },
        ],
    },
}


class DatasetTemplateDownloadView(APIView):
    def get(self, request, template_type, file_format):
        template = TEMPLATES.get(template_type)
        if not template or file_format not in ('csv', 'json'):
            return Response(
                {'error': 'Template not found. Use credit, fraud, or transactions with csv or json.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        filename = f"{template['filename']}.{file_format}"
        if file_format == 'json':
            response = HttpResponse(
                json.dumps({'entries': template['rows']}, indent=2),
                content_type='application/json',
            )
        else:
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=template['rows'][0].keys())
            writer.writeheader()
            writer.writerows(template['rows'])
            response = HttpResponse(output.getvalue(), content_type='text/csv')

        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
