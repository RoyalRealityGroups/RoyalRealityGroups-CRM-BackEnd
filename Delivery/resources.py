from import_export import resources
from import_export.fields import Field

from .models import ProofOfDelivery


class ProofOfDeliveryResource(resources.ModelResource):
    """Resource for Proof of Delivery report export."""

    pod_number = Field(column_name='POD Number', attribute='pod_number')
    pod_date = Field(column_name='POD Date', attribute='pod_date')
    invoice_number = Field(column_name='Invoice Number', attribute='invoice__invoice_number')
    invoice_date = Field(column_name='Invoice Date', attribute='invoice__invoice_date')
    order_number = Field(column_name='Order Number', attribute='sales_order__order_number')
    order_date = Field(column_name='Order Date', attribute='sales_order__order_date')
    customer_type = Field(column_name='Customer Type', attribute='customer_type')
    customer_name = Field(column_name='Customer Name')
    status = Field(column_name='Status', attribute='status')
    receiver_name = Field(column_name='Receiver Name', attribute='receiver_name')
    receiver_phone = Field(column_name='Receiver Phone', attribute='receiver_phone')
    delivered_by = Field(column_name='Delivered By', attribute='delivered_by')
    delivered_date = Field(column_name='Delivered Date', attribute='delivered_date')
    grand_total = Field(column_name='Invoice Amount', attribute='invoice__grand_total')
    authorization_status = Field(column_name='Authorization Status')
    agent_name = Field(column_name='Agent Name')
    remarks = Field(column_name='Remarks', attribute='remarks')

    class Meta:
        model = ProofOfDelivery 
        fields = (
            'pod_number', 'pod_date', 'invoice_number', 'invoice_date',
            'order_number', 'order_date', 'customer_type', 'customer_name',
            'status', 'receiver_name', 'receiver_phone',
            'delivered_by', 'delivered_date', 'grand_total', 'authorization_status', 'agent_name', 'remarks',
        )
        export_order = fields

    def dehydrate_status(self, obj):
        """Return display value for status instead of raw DB value."""
        return obj.get_status_display()

    def dehydrate_authorization_status(self, obj):
        """Return display value for authorization status."""
        status_map = {
            0: 'Draft',
            1: 'Pending', 
            2: 'Approved',
            3: 'Rejected'
        }
        # Handle None/null values by defaulting to 'Pending'
        auth_status = getattr(obj, 'authorized_status', None)
        if auth_status is None:
            return 'Pending'
        return status_map.get(auth_status, f'Unknown ({auth_status})')

    def dehydrate_agent_name(self, obj):
        """Resolve agent name from distributor."""
        if obj.sales_order and obj.sales_order.distributor and obj.sales_order.distributor.agent:
            return obj.sales_order.distributor.agent.name
        return ''

    def dehydrate_customer_name(self, obj):
        """Resolve customer name based on customer_type."""
        if obj.customer_type == 'RETAILER':
            return obj.sales_order.retailer.name if obj.sales_order and obj.sales_order.retailer else ''
        elif obj.customer_type == 'DISTRIBUTOR':
            return obj.sales_order.distributor.name if obj.sales_order and obj.sales_order.distributor else ''
        elif obj.customer_type == 'SUPERSTOCKIST':
            return obj.sales_order.superstockist.name if obj.sales_order and obj.sales_order.superstockist else ''
        return ''
