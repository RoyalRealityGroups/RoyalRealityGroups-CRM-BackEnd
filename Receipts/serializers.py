from rest_framework import serializers
from decimal import Decimal
from .models import Receipt, ReceiptAllocation, ReceiptAttachment, CustomerLedgerEntry
from Invoice.models import Invoice


class ReceiptAllocationSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    invoice_date = serializers.DateField(source='invoice.invoice_date', read_only=True)
    invoice_amount = serializers.DecimalField(source='invoice.grand_total', max_digits=15, decimal_places=2, read_only=True)
    invoice_balance = serializers.DecimalField(source='invoice.balance_amount', max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = ReceiptAllocation
        fields = ['id', 'invoice', 'invoice_number', 'invoice_date', 'invoice_amount', 'invoice_balance', 'allocated_amount']
        
    def validate(self, data):
        invoice = data.get('invoice')
        allocated_amount = data.get('allocated_amount')
        
        if allocated_amount <= 0:
            raise serializers.ValidationError({'allocated_amount': 'Amount must be greater than zero'})
        
        # Skip balance check in edit mode (balance will be restored before validation in view)
        # The view handles reversal before creating new allocations
        
        return data


class ReceiptAttachmentSerializer(serializers.ModelSerializer):
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = ReceiptAttachment
        fields = ['id', 'attachment_type', 'file', 'file_name', 'file_size', 'remarks']
    
    def get_file_name(self, obj):
        return obj.file.name.split('/')[-1] if obj.file else None
    
    def get_file_size(self, obj):
        return obj.file.size if obj.file else None


class ReceiptListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    customer_name = serializers.SerializerMethodField()
    payment_mode_display = serializers.CharField(source='get_payment_mode_display', read_only=True)
    authorized_status_name = serializers.SerializerMethodField()
    pending_approver_names = serializers.SerializerMethodField()
    allocations_count = serializers.IntegerField(source='allocations.count', read_only=True)
    allocated_amount = serializers.SerializerMethodField()
    adjustment_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Receipt
        fields = [
            'id', 'code', 'receipt_number', 'receipt_date', 'payment_date', 'payment_mode', 'payment_mode_display',
            'company_name', 'location_name', 'customer_type', 'customer_name',
            'total_amount', 'allocated_amount', 'adjustment_amount', 'allocations_count',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names'
        ]
        read_only_fields = fields
    
    def get_customer_name(self, obj):
        return obj.get_customer_name()
    
    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()
    
    def get_pending_approver_names(self, obj):
        from Core.Users.serializers import get_pending_approver_names
        result = get_pending_approver_names(obj)
        if obj.authorized_status == 1:
            return result if result else 'TEST: No approvers found'
        return result
    
    def get_allocated_amount(self, obj):
        from django.db.models import Sum
        total = obj.allocations.aggregate(total=Sum('allocated_amount'))['total']
        return float(total) if total else 0.0
    
    def get_adjustment_amount(self, obj):
        allocated = self.get_allocated_amount(obj)
        return float(obj.total_amount) - allocated


class ReceiptDetailSerializer(serializers.ModelSerializer):
    allocations = ReceiptAllocationSerializer(many=True, required=False)
    attachments = ReceiptAttachmentSerializer(many=True, required=False)
    credit_utilizations = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='company.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    location_code = serializers.CharField(source='location.code', read_only=True)
    customer_name = serializers.SerializerMethodField()
    payment_mode_display = serializers.CharField(source='get_payment_mode_display', read_only=True)
    authorized_status_name = serializers.SerializerMethodField()
    pending_approver_names = serializers.SerializerMethodField()
    allocated_amount = serializers.SerializerMethodField()
    adjustment_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Receipt
        fields = [
            'id', 'code', 'receipt_number', 'receipt_date', 'payment_date', 'payment_mode', 'payment_mode_display',
            'reference_number', 'bank_name',
            'company', 'company_name', 'location', 'location_name', 'location_code',
            'customer_type', 'retailer', 'distributor', 'superstockist', 'customer_name',
            'total_amount', 'allocated_amount', 'adjustment_amount', 'remarks',
            'authorized_status', 'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names',
            'allocations', 'attachments', 'credit_utilizations', 'created_on', 'modified_on'
        ]
        read_only_fields = (
            'id', 'code', 'receipt_number', 'company_name', 'location_name', 'location_code',
            'customer_name', 'payment_mode_display', 'allocated_amount', 'adjustment_amount',
            'authorized_status_name', 'authorized_level', 'authorized_by_type',
            'authorized_by_identifier', 'authorized_on', 'current_authorized_level',
            'current_authorized_status', 'current_authorized_by_type', 'current_authorized_by_identifier',
            'current_authorized_on', 'pending_approver_names', 'created_on', 'modified_on'
        )
    
    def get_customer_name(self, obj):
        return obj.get_customer_name()
    
    def get_authorized_status_name(self, obj):
        return obj.get_authorized_status_display()
    
    def get_pending_approver_names(self, obj):
        from Core.Users.serializers import get_pending_approver_names
        return get_pending_approver_names(obj)
    
    def get_allocated_amount(self, obj):
        from django.db.models import Sum
        total = obj.allocations.aggregate(total=Sum('allocated_amount'))['total']
        return float(total) if total else 0.0
    
    def get_adjustment_amount(self, obj):
        allocated = self.get_allocated_amount(obj)
        return float(obj.total_amount) - allocated
    
    def get_credit_utilizations(self, obj):
        return [{
            'id': str(util.id),
            'utilized_amount': float(util.utilized_amount),
            'utilized_on': util.utilized_on,
        } for util in obj.credit_utilizations.all()]
    
    def validate(self, data):
        allocations = data.get('allocations', [])
        total_amount = data.get('total_amount', 0)
        
        if not allocations:
            raise serializers.ValidationError({'allocations': 'At least one invoice allocation is required'})
        
        total_allocated = sum(alloc.get('allocated_amount', 0) for alloc in allocations)
        
        # Get credit_amount from context (passed from view)
        credit_amount = Decimal(str(self.context.get('credit_amount', 0)))
        total_payment_capacity = total_amount + credit_amount
        
        if total_allocated > total_payment_capacity:
            raise serializers.ValidationError({'allocations': 'Total allocated amount cannot exceed receipt amount'})
        
        # Validate customer consistency
        customer_type = data.get('customer_type')
        retailer = data.get('retailer')
        distributor = data.get('distributor')
        superstockist = data.get('superstockist')
        
        if customer_type == 'RETAILER' and not retailer:
            raise serializers.ValidationError({'retailer': 'Retailer is required for RETAILER customer type'})
        if customer_type == 'DISTRIBUTOR' and not distributor:
            raise serializers.ValidationError({'distributor': 'Distributor is required for DISTRIBUTOR customer type'})
        if customer_type == 'SUPERSTOCKIST' and not superstockist:
            raise serializers.ValidationError({'superstockist': 'Superstockist is required for SUPERSTOCKIST customer type'})
        
        # Validate all invoices belong to same customer
        for alloc in allocations:
            invoice = alloc.get('invoice')
            if invoice:
                if invoice.sales_order.customer_type != customer_type:
                    raise serializers.ValidationError({'allocations': 'All invoices must belong to the same customer'})
                
                if customer_type == 'RETAILER' and invoice.sales_order.retailer_id != retailer.id:
                    raise serializers.ValidationError({'allocations': 'All invoices must belong to the selected retailer'})
                elif customer_type == 'DISTRIBUTOR' and invoice.sales_order.distributor_id != distributor.id:
                    raise serializers.ValidationError({'allocations': 'All invoices must belong to the selected distributor'})
                elif customer_type == 'SUPERSTOCKIST' and invoice.sales_order.superstockist_id != superstockist.id:
                    raise serializers.ValidationError({'allocations': 'All invoices must belong to the selected superstockist'})
        
        return data
    
    def create(self, validated_data):
        allocations_data = validated_data.pop('allocations')
        attachments_data = validated_data.pop('attachments', [])
        
        receipt = Receipt.objects.create(**validated_data)
        
        for alloc_data in allocations_data:
            ReceiptAllocation.objects.create(receipt=receipt, **alloc_data)
        
        for attach_data in attachments_data:
            ReceiptAttachment.objects.create(receipt=receipt, **attach_data)
        
        return receipt
    
    def update(self, instance, validated_data):
        allocations_data = validated_data.pop('allocations', None)
        attachments_data = validated_data.pop('attachments', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Allocations and attachments are handled in the view's perform_update
        # to ensure proper reversal logic
        if allocations_data is not None:
            for alloc_data in allocations_data:
                ReceiptAllocation.objects.create(receipt=instance, **alloc_data)
        
        if attachments_data is not None:
            instance.attachments.all().delete()
            for attach_data in attachments_data:
                ReceiptAttachment.objects.create(receipt=instance, **attach_data)
        
        return instance


class CustomerLedgerEntrySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomerLedgerEntry
        fields = [
            'id', 'code', 'posting_date', 'document_date',
            'document_type', 'document_number', 'event_type',
            'customer_type', 'customer_name',
            'debit_amount', 'credit_amount',
            'company_name', 'location_name',
            'entry_status', 'remarks', 'meta_data',
            'created_on'
        ]
        read_only_fields = fields

    def get_customer_name(self, obj):
        if obj.customer_type == 'RETAILER' and obj.retailer:
            return obj.retailer.name
        if obj.customer_type == 'DISTRIBUTOR' and obj.distributor:
            return obj.distributor.name
        if obj.customer_type == 'SUPERSTOCKIST' and obj.superstockist:
            return obj.superstockist.name
        return None
