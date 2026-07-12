"""
Data service for dashboard widgets.
Handles dynamic data fetching based on data_source parameter.
"""
from django.db.models import Count, Sum, Q
from django.apps import apps


class WidgetDataService:
    """Service to fetch widget data based on data_source."""

    # Mapping of data_source to model and field
    DATA_SOURCE_MAP = {
        # Sales
        'sales.count': {'model': 'Sales.SalesOrder', 'field': None, 'type': 'count'},
        'sales.by_status': {'model': 'Sales.SalesOrder', 'field': 'status', 'type': 'group_by'},
        'sales.recent': {'model': 'Sales.SalesOrder', 'field': None, 'type': 'list'},
        'sales.list': {'model': 'Sales.SalesOrder', 'field': None, 'type': 'list'},
        'sales.over_time': {'model': 'Sales.SalesOrder', 'field': 'order_date', 'type': 'time_series'},
        
        # Dispatch
        'dispatch.count': {'model': 'Dispatch.DispatchPlan', 'field': None, 'type': 'count'},
        'dispatch.by_status': {'model': 'Dispatch.DispatchPlan', 'field': 'status', 'type': 'group_by'},
        'dispatch.recent': {'model': 'Dispatch.DispatchPlan', 'field': None, 'type': 'list'},
        'dispatch.list': {'model': 'Dispatch.DispatchPlan', 'field': None, 'type': 'list'},
        'dispatch.over_time': {'model': 'Dispatch.DispatchPlan', 'field': 'dispatch_date', 'type': 'time_series'},
        
        # Invoice
        'invoice.count': {'model': 'Invoice.Invoice', 'field': None, 'type': 'count'},
        'invoice.by_status': {'model': 'Invoice.Invoice', 'field': 'status', 'type': 'group_by'},
        'invoice.recent': {'model': 'Invoice.Invoice', 'field': None, 'type': 'list'},
        'invoice.list': {'model': 'Invoice.Invoice', 'field': None, 'type': 'list'},
        'invoice.over_time': {'model': 'Invoice.Invoice', 'field': 'invoice_date', 'type': 'time_series'},
        
        # Receipts
        'receipts.count': {'model': 'Receipts.Receipt', 'field': None, 'type': 'count'},
        'receipts.by_payment_mode': {'model': 'Receipts.Receipt', 'field': 'payment_mode', 'type': 'group_by'},
        'receipts.recent': {'model': 'Receipts.Receipt', 'field': None, 'type': 'list'},
        
        # Delivery
        'delivery.count': {'model': 'Delivery.ProofOfDelivery', 'field': None, 'type': 'count'},
        'delivery.by_status': {'model': 'Delivery.ProofOfDelivery', 'field': 'status', 'type': 'group_by'},
        'delivery.recent': {'model': 'Delivery.ProofOfDelivery', 'field': None, 'type': 'list'},
        
        # Masters
        'masters.distributors_count': {'model': 'Masters.Distributor', 'field': None, 'type': 'count'},
        'masters.retailers_count': {'model': 'Masters.Retailer', 'field': None, 'type': 'count'},
        'masters.superstockists_count': {'model': 'Masters.Superstockist', 'field': None, 'type': 'count'},
    }

    @staticmethod
    def get_model(model_path):
        """Get model class from string path like 'Sales.SalesOrder'"""
        app_label, model_name = model_path.split('.')
        return apps.get_model(app_label, model_name)

    @staticmethod
    def apply_filters(queryset, filters):
        """Apply filters to queryset dynamically."""
        if not filters:
            return queryset
        
        filter_kwargs = {}
        
        # Handle special filters
        for key, value in filters.items():
            if value is None or value == '':
                continue
            
            # Handle date_range filter (convert to created_on filter)
            if key == 'date_range':
                from datetime import datetime, timedelta
                from django.utils import timezone
                
                today = timezone.now().date()
                
                if value == 'today':
                    filter_kwargs['created_on__date'] = today
                elif value == 'yesterday':
                    filter_kwargs['created_on__date'] = today - timedelta(days=1)
                elif value == 'this_week':
                    start_of_week = today - timedelta(days=today.weekday())
                    filter_kwargs['created_on__date__gte'] = start_of_week
                elif value == 'this_month':
                    filter_kwargs['created_on__year'] = today.year
                    filter_kwargs['created_on__month'] = today.month
                elif value == 'last_month':
                    first_day_this_month = today.replace(day=1)
                    last_month = first_day_this_month - timedelta(days=1)
                    filter_kwargs['created_on__year'] = last_month.year
                    filter_kwargs['created_on__month'] = last_month.month
                elif value == 'this_year':
                    filter_kwargs['created_on__year'] = today.year
                elif value == 'last_7_days':
                    filter_kwargs['created_on__date__gte'] = today - timedelta(days=7)
                elif value == 'last_30_days':
                    filter_kwargs['created_on__date__gte'] = today - timedelta(days=30)
            else:
                # Regular field filter
                filter_kwargs[key] = value
        
        return queryset.filter(**filter_kwargs) if filter_kwargs else queryset

    @classmethod
    def get_data(cls, data_source, filters=None, user=None):
        """
        Get data for a specific data_source with optional filters.
        
        Args:
            data_source: String like 'sales.by_status'
            filters: Dict of filters like {'status': 'CONFIRMED', 'company': 'uuid'}
            user: Current user for permission filtering
        
        Returns:
            Dict with data
        """
        if data_source not in cls.DATA_SOURCE_MAP:
            return {'error': f'Unknown data_source: {data_source}'}
        
        config = cls.DATA_SOURCE_MAP[data_source]
        model = cls.get_model(config['model'])
        data_type = config['type']
        field = config['field']
        
        # Base queryset
        queryset = model.objects.filter(is_deleted=False)
        
        # Apply filters
        queryset = cls.apply_filters(queryset, filters)
        
        # Get data based on type
        if data_type == 'count':
            return cls._get_count_data(queryset, model)
        
        elif data_type == 'group_by':
            return cls._get_group_by_data(queryset, field)
        
        elif data_type == 'list':
            return cls._get_list_data(queryset, model)
        
        elif data_type == 'time_series':
            return cls._get_time_series_data(queryset, field)
        
        return {'error': 'Invalid data type'}

    @staticmethod
    def _get_count_data(queryset, model):
        """Get count data."""
        total = queryset.count()
        return {
            'value': total,
            'label': f'Total {model._meta.verbose_name_plural}'
        }

    @staticmethod
    def _get_group_by_data(queryset, field):
        """Get grouped data by field."""
        data = list(
            queryset.values(field)
            .annotate(value=Count('id'))
            .order_by('-value')
        )
        
        # Get all possible choices for the field
        model = queryset.model
        field_obj = model._meta.get_field(field)
        
        result = []
        
        # If field has choices, include all choices with 0 count if not present
        if hasattr(field_obj, 'choices') and field_obj.choices:
            # Create a dict of existing data
            data_dict = {item[field]: item['value'] for item in data}
            
            # Add all choices
            for choice_value, choice_label in field_obj.choices:
                result.append({
                    'name': choice_value,
                    'value': data_dict.get(choice_value, 0)
                })
        else:
            # No choices defined, just return the data as is
            result = [
                {'name': item[field], 'value': item['value']}
                for item in data
            ]
        
        return {'data': result}

    @staticmethod
    def _get_list_data(queryset, model, limit=10):
        """Get list of recent items."""
        items = queryset.order_by('-created_on')[:limit]
        
        result = []
        for item in items:
            item_data = {
                'id': str(item.id),
                'code': getattr(item, 'code', None),
            }
            
            # Add model-specific fields
            if hasattr(item, 'status'):
                item_data['status'] = item.status
            if hasattr(item, 'order_number'):
                item_data['order_number'] = item.order_number
            if hasattr(item, 'invoice_number'):
                item_data['invoice_number'] = item.invoice_number
            if hasattr(item, 'name'):
                item_data['name'] = item.name
            if hasattr(item, 'grand_total'):
                item_data['grand_total'] = float(item.grand_total)
            
            result.append(item_data)
        
        return {'items': result}

    @staticmethod
    def _get_time_series_data(queryset, date_field):
        """Get time series data grouped by date."""
        from django.db.models.functions import TruncDate
        
        data = list(
            queryset.annotate(date=TruncDate(date_field))
            .values('date')
            .annotate(value=Count('id'))
            .order_by('date')
        )
        
        return {
            'data': [
                {'date': item['date'].isoformat(), 'value': item['value']}
                for item in data
            ]
        }
