from rest_framework import serializers
from .models import Booking, BookingStatusHistory, BOOKING_STATUS_CHOICES


class BookingStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()
    from_status_display = serializers.CharField(source='get_from_status_display', read_only=True)
    to_status_display = serializers.CharField(source='get_to_status_display', read_only=True)

    class Meta:
        model = BookingStatusHistory
        fields = '__all__'

    def get_changed_by_name(self, obj):
        if obj.changed_by:
            return f"{obj.changed_by.first_name} {obj.changed_by.last_name}".strip() or obj.changed_by.username
        return None


class BookingSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sales_executive_name = serializers.SerializerMethodField(read_only=True)
    plot_number_display = serializers.CharField(source='plot.plot_number', read_only=True)
    flat_unit_display = serializers.CharField(source='flat.unit_number', read_only=True)
    availability_project_name = serializers.CharField(source='availability_project.name', read_only=True)
    availability_unit_display = serializers.CharField(source='availability_unit.unit_number', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'code',
            'lead', 'customer_name', 'customer_mobile', 'customer_email',
            'project', 'project_name',
            'availability_project', 'availability_project_name',
            'availability_unit', 'availability_unit_display',
            'unit_type', 'plot', 'plot_number_display', 'flat', 'flat_unit_display', 'unit_number',
            'agreed_price', 'booking_amount', 'booking_date',
            'property_cost', 'revenue', 'incentive',
            'sales_executive', 'sales_executive_name',
            'status', 'status_display',
            'cancellation_reason', 'cancelled_date', 'remarks',
            'created_on', 'modified_on',
        ]
        read_only_fields = ('code', 'unit_number', 'created_on', 'modified_on')

    def get_project_name(self, obj):
        if obj.availability_project:
            return obj.availability_project.name
        if obj.project:
            return obj.project.name
        return None

    def get_sales_executive_name(self, obj):
        if obj.sales_executive:
            return f"{obj.sales_executive.first_name} {obj.sales_executive.last_name}".strip() or obj.sales_executive.username
        return None

    def validate(self, data):
        avail_project = data.get('availability_project', getattr(self.instance, 'availability_project', None))
        avail_unit = data.get('availability_unit', getattr(self.instance, 'availability_unit', None))

        # New flow: Availability List. Require a unit when an availability project is chosen.
        if avail_project:
            if not avail_unit:
                raise serializers.ValidationError(
                    {'availability_unit': 'Please select a unit from the Availability List.'}
                )
            # Ensure the unit belongs to the selected project
            if avail_unit and avail_unit.block.project_id != avail_project.id:
                raise serializers.ValidationError(
                    {'availability_unit': 'Selected unit does not belong to the selected project.'}
                )
            return data

        # Legacy flow: ProjectManagement + Inventory
        unit_type = data.get('unit_type', getattr(self.instance, 'unit_type', None))
        plot = data.get('plot', getattr(self.instance, 'plot', None))
        flat = data.get('flat', getattr(self.instance, 'flat', None))
        project = data.get('project', getattr(self.instance, 'project', None))
        if not project:
            raise serializers.ValidationError({'project': 'Project is required.'})
        if unit_type == 'PLOT' and not plot:
            raise serializers.ValidationError({'plot': 'Plot is required for PLOT bookings.'})
        if unit_type == 'FLAT' and not flat:
            raise serializers.ValidationError({'flat': 'Flat is required for FLAT bookings.'})
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by_type'] = 'User'
        validated_data['created_by_identifier'] = str(user.id)
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)
        # Auto-assign sales_executive to creating user if not set
        if not validated_data.get('sales_executive'):
            validated_data['sales_executive'] = user
        booking = super().create(validated_data)
        # Block the unit
        self._update_unit_status(booking, 'BOOKED')
        # Update linked lead status
        if booking.lead and booking.lead.status not in ('BOOKING', 'REGISTRATION'):
            booking.lead.status = 'BOOKING'
            booking.lead.save(update_fields=['status'])
        return booking

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['modified_by_type'] = 'User'
        validated_data['modified_by_identifier'] = str(user.id)
        return super().update(instance, validated_data)

    def _update_unit_status(self, booking, inv_status):
        """Sync unit status when booking is created/cancelled."""
        try:
            if booking.availability_unit:
                booking.availability_unit.status = inv_status
                booking.availability_unit.save(update_fields=['status'])
            elif booking.plot:
                booking.plot.status = inv_status
                booking.plot.save(update_fields=['status'])
            elif booking.flat:
                booking.flat.status = inv_status
                booking.flat.save(update_fields=['status'])
        except Exception:
            pass


BOOKING_STATUS_LIST = [{'value': k, 'label': v} for k, v in BOOKING_STATUS_CHOICES]
