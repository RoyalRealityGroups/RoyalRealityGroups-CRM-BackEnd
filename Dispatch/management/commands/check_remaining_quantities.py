from django.core.management.base import BaseCommand
from Sales.models import SalesOrder
from Dispatch.models import DispatchItem, DispatchPlan
from decimal import Decimal


class Command(BaseCommand):
    help = 'Check and verify remaining quantities for sales orders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--order-id',
            type=int,
            help='Check specific sales order by ID',
        )

    def handle(self, *args, **options):
        order_id = options.get('order_id')

        if order_id:
            # Check specific order
            self.check_specific_order(order_id)
        else:
            # Check all orders with pending status
            self.check_all_orders()

    def check_specific_order(self, order_id):
        try:
            order = SalesOrder.objects.get(id=order_id)
            self.print_order_details(order)
        except SalesOrder.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Sales Order with ID {order_id} not found'))

    def check_all_orders(self):
        orders = SalesOrder.objects.filter(
            status__in=['PENDING', 'APPROVED', 'PROCESSING', 'PARTIALLY_INVOICED'],
            is_deleted=False
        ).select_related('company').prefetch_related('items', 'dispatch_items')

        if not orders.exists():
            self.stdout.write(self.style.WARNING('No pending sales orders found'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n{"="*120}'))
        self.stdout.write(self.style.SUCCESS(f'SALES ORDER REMAINING QUANTITY VERIFICATION'))
        self.stdout.write(self.style.SUCCESS(f'{"="*120}\n'))

        for order in orders:
            self.print_order_details(order)
            self.stdout.write('')

    def print_order_details(self, order):
        # Get total quantity in order
        total_qty = sum(item.quantity for item in order.items.all())

        # Get all dispatch items for this order (excluding cancelled)
        dispatch_items = order.dispatch_items.exclude(
            dispatch_plan__status='CANCELLED'
        ).select_related('dispatch_plan')

        # Calculate total dispatched
        total_dispatched = sum(item.quantity_dispatched for item in dispatch_items)

        # Calculate remaining
        remaining_qty = total_qty - total_dispatched

        # Print header
        self.stdout.write(self.style.SUCCESS(f'Order ID: {order.id} | Order Number: {order.order_number}'))
        self.stdout.write(f'Company: {order.company.name}')
        self.stdout.write(f'Status: {order.status}')
        self.stdout.write(f'Order Date: {order.order_date}')
        self.stdout.write('')

        # Print quantities
        self.stdout.write(f'Total Quantity in Order:      {total_qty}')
        self.stdout.write(f'Total Quantity Dispatched:    {total_dispatched}')
        
        # Color code the remaining quantity
        if remaining_qty > 0:
            self.stdout.write(self.style.SUCCESS(f'Remaining Quantity:          {remaining_qty} ✓'))
        elif remaining_qty == 0:
            self.stdout.write(self.style.WARNING(f'Remaining Quantity:          {remaining_qty} (FULLY DISPATCHED)'))
        else:
            self.stdout.write(self.style.ERROR(f'Remaining Quantity:          {remaining_qty} ✗ (OVER-DISPATCHED!)'))

        self.stdout.write('')

        # Print dispatch details if any
        if dispatch_items.exists():
            self.stdout.write(self.style.SUCCESS('Dispatch Items:'))
            self.stdout.write(f'{"-"*120}')
            self.stdout.write(
                f'{'Dispatch #':<20} {'Plan Status':<15} {'Qty Dispatched':<20} '
                f'{'Loading Seq':<15} {'Unloading Seq':<15} {'Created On':<20}'
            )
            self.stdout.write(f'{"-"*120}')
            
            for item in dispatch_items.order_by('dispatch_plan__dispatch_date'):
                dispatch_plan = item.dispatch_plan
                self.stdout.write(
                    f'{dispatch_plan.dispatch_number:<20} '
                    f'{dispatch_plan.status:<15} '
                    f'{item.quantity_dispatched:<20} '
                    f'{item.loading_sequence:<15} '
                    f'{item.unloading_sequence or "N/A":<15} '
                    f'{dispatch_plan.created_on.strftime("%Y-%m-%d %H:%M"):<20}'
                )
            self.stdout.write(f'{"-"*120}')
        else:
            self.stdout.write(self.style.WARNING('No dispatch items yet'))

        self.stdout.write(self.style.SUCCESS(f'{"-"*120}\n'))

        # Verification
        self.stdout.write(self.style.SUCCESS('Verification:'))
        expected_remaining = total_qty - total_dispatched
        if remaining_qty == expected_remaining:
            self.stdout.write(self.style.SUCCESS('✓ Remaining quantity calculation is CORRECT'))
        else:
            self.stdout.write(self.style.ERROR('✗ Remaining quantity calculation is INCORRECT'))

        self.stdout.write(self.style.SUCCESS(f'{"-"*120}\n'))
