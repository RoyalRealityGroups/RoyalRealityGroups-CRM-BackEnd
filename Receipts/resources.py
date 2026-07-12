from import_export import resources
from import_export.fields import Field

from .models import Receipt


class ReceiptResource(resources.ModelResource):
    """Resource for Receipt report export via generic export endpoint."""

    receipt_number = Field(column_name='Receipt Number', attribute='receipt_number')
    receipt_date = Field(column_name='Receipt Date', attribute='receipt_date')
    payment_date = Field(column_name='Payment Date', attribute='payment_date')
    customer_type = Field(column_name='Customer Type', attribute='customer_type')
    customer_name = Field(column_name='Customer Name')
    payment_mode = Field(column_name='Payment Mode', attribute='payment_mode')
    total_amount = Field(column_name='Total Amount', attribute='total_amount')
    reference_number = Field(column_name='Reference Number', attribute='reference_number')
    bank_name = Field(column_name='Bank Name', attribute='bank_name')
    company_name = Field(column_name='Company', attribute='company__name')
    location_name = Field(column_name='Location', attribute='location__name')
    authorization_status = Field(column_name='Authorization Status')
    agent_name = Field(column_name='Agent Name')
    remarks = Field(column_name='Remarks', attribute='remarks')

    class Meta:
        model = Receipt
        fields = (
            'receipt_number', 'receipt_date', 'payment_date',
            'customer_type', 'customer_name',
            'payment_mode', 'total_amount', 'reference_number', 'bank_name',
            'company_name', 'location_name',
            'authorization_status', 'agent_name', 'remarks',
        )
        export_order = fields

    def dehydrate_customer_name(self, obj):
        return obj.get_customer_name() or ''

    def dehydrate_payment_mode(self, obj):
        return obj.get_payment_mode_display()

    def dehydrate_authorization_status(self, obj):
        status_map = {0: 'Draft', 1: 'Pending', 2: 'Approved', 3: 'Rejected'}
        return status_map.get(obj.authorized_status, '')

    def dehydrate_agent_name(self, obj):
        if obj.distributor and obj.distributor.agent:
            return obj.distributor.agent.name
        return ''
