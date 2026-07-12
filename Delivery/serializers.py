from rest_framework import serializers
from .models import ProofOfDelivery, ProofOfDeliveryFile
from django.utils import timezone
import re
from Masters.validators import validate_contact_phone


class ProofOfDeliveryFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ProofOfDeliveryFile
        fields = ['id', 'file', 'file_url', 'original_filename', 'description', 'created_on']
        read_only_fields = ['id', 'created_on', 'file_url']

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class ProofOfDeliveryListSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    order_number = serializers.CharField(source='sales_order.order_number', read_only=True)
    customer_name = serializers.SerializerMethodField()
    authorized_status_name = serializers.SerializerMethodField()
    pending_approver_names = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProofOfDelivery
        fields = [
            'id', 'code', 'pod_number', 'invoice', 'invoice_number', 'sales_order', 'order_number',
            'customer_name', 'customer_type', 'status', 'delivered_date',
            'receiver_name', 'delivered_by', 'pod_date',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names'
        ]
        read_only_fields = fields

    def get_customer_name(self, obj):
        if obj.customer_type == 'RETAILER':
            return obj.sales_order.retailer.name if obj.sales_order.retailer else ''
        elif obj.customer_type == 'DISTRIBUTOR':
            return obj.sales_order.distributor.name if obj.sales_order.distributor else ''
        elif obj.customer_type == 'SUPERSTOCKIST':
            return obj.sales_order.superstockist.name if obj.sales_order.superstockist else ''
        return ''
    
    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()
    
    def get_pending_approver_names(self, obj):
        """Get pending approver names"""
        from Core.Users.serializers import get_pending_approver_names
        result = get_pending_approver_names(obj)
        if obj.authorized_status == 1:
            return result if result else 'TEST: No approvers found'
        return result


class ProofOfDeliveryDetailSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    invoice_date = serializers.DateField(source='invoice.invoice_date', read_only=True)
    company_name = serializers.CharField(source='invoice.company.name', read_only=True)
    company_address = serializers.CharField(source='invoice.company.address', read_only=True)
    company_phone = serializers.CharField(source='invoice.company.phone', read_only=True)
    company_email = serializers.CharField(source='invoice.company.email', read_only=True)
    company_gst = serializers.CharField(source='invoice.company.gst_number', read_only=True)
    company_logo = serializers.ImageField(source='invoice.company.logo', read_only=True)
    order_number = serializers.CharField(source='sales_order.order_number', read_only=True)
    order_date = serializers.DateField(source='sales_order.order_date', read_only=True)
    customer_name = serializers.SerializerMethodField()
    billing_address = serializers.SerializerMethodField()
    shipping_address = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()
    authorized_status_name = serializers.SerializerMethodField()
    pending_approver_names = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProofOfDelivery
        fields = [
            'id', 'code', 'pod_number', 'invoice', 'invoice_number', 'invoice_date',
            'sales_order', 'order_number', 'order_date',
            'customer_type', 'customer_id', 'customer_name',
            'billing_address', 'shipping_address',
            'company_name', 'company_address', 'company_phone', 'company_email', 'company_gst', 'company_logo',
            'pod_date', 'status',
            'receiver_name', 'receiver_phone',
            'delivered_by', 'delivered_date',
            'remarks', 'files',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names',
            'created_on', 'modified_on'
        ]
        read_only_fields = ['code', 'pod_number', 'authorized_status', 'authorized_status_name', 'authorized_level',
                            'authorized_by_type', 'authorized_by_identifier', 'authorized_on',
                            'current_authorized_level', 'current_authorized_status',
                            'current_authorized_by_type', 'current_authorized_by_identifier',
                            'current_authorized_on', 'pending_approver_names', 'created_on', 'modified_on']

    def get_customer_name(self, obj):
        if obj.customer_type == 'RETAILER':
            return obj.sales_order.retailer.name if obj.sales_order.retailer else ''
        elif obj.customer_type == 'DISTRIBUTOR':
            return obj.sales_order.distributor.name if obj.sales_order.distributor else ''
        elif obj.customer_type == 'SUPERSTOCKIST':
            return obj.sales_order.superstockist.name if obj.sales_order.superstockist else ''
        return ''

    def get_billing_address(self, obj):
        return obj.sales_order.billing_address or ''

    def get_shipping_address(self, obj):
        return obj.sales_order.shipping_address or ''

    def get_files(self, obj):
        files = obj.files.filter(is_deleted=False).order_by('-created_on')
        return ProofOfDeliveryFileSerializer(files, many=True, context=self.context).data
    
    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()
    
    def get_pending_approver_names(self, obj):
        """Get pending approver names"""
        from Core.Users.serializers import get_pending_approver_names
        return get_pending_approver_names(obj)

    def create(self, validated_data):
        if not validated_data.get('pod_number'):
            from django.db import transaction
            import re
            
            today = timezone.now().date()
            
            if today.month >= 4:
                fy_start = today.year
                fy_end = today.year + 1
            else:
                fy_start = today.year - 1
                fy_end = today.year
            
            fy_suffix = f"{str(fy_start)[-2:]}-{str(fy_end)[-2:]}"
            prefix = f"POD-{fy_suffix}"
            
            # Use atomic transaction with SELECT FOR UPDATE to prevent race conditions
            with transaction.atomic():
                pod_numbers = ProofOfDelivery.objects.filter(
                    pod_number__startswith=prefix
                ).select_for_update().values_list('pod_number', flat=True)
                
                max_suffix = 0
                for pn in pod_numbers:
                    match = re.search(r'-(\d+)$', pn or '')
                    if match:
                        try:
                            max_suffix = max(max_suffix, int(match.group(1)))
                        except ValueError:
                            continue
                
                pod_number = f"{prefix}-{max_suffix + 1}"
            
            validated_data['pod_number'] = pod_number
        
        return super().create(validated_data)

    def validate(self, attrs):
        invoice = attrs.get('invoice') or getattr(self.instance, 'invoice', None)
        sales_order = attrs.get('sales_order') or getattr(self.instance, 'sales_order', None)

        if invoice and sales_order and invoice.sales_order_id != sales_order.id:
            raise serializers.ValidationError("Invoice and Sales Order do not match.")

        # Check if POD already exists for this invoice
        if not self.instance and invoice:
            if ProofOfDelivery.objects.filter(invoice=invoice, is_deleted=False).exists():
                raise serializers.ValidationError("Proof of Delivery already exists for this invoice.")

        return attrs

    def validate_receiver_phone(self, value):
        try:
            return validate_contact_phone(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))


class ProofOfDeliveryStatusCountSerializer(serializers.Serializer):
    """Serializer for proof of delivery status counts"""
    PENDING = serializers.IntegerField(read_only=True, default=0)
    SUCCESS = serializers.IntegerField(read_only=True, default=0)
    FAILED = serializers.IntegerField(read_only=True, default=0)
    PARTIAL = serializers.IntegerField(read_only=True, default=0)
    total = serializers.IntegerField(read_only=True, default=0)