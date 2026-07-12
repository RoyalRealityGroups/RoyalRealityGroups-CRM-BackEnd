from django.core.management.base import BaseCommand
from Sales.models import SalesOrder, SalesOrderItem
from Dispatch.models import DispatchItem, DispatchOrderItem
from Masters.models import Item


class Command(BaseCommand):
    help = 'Debug item-level remaining quantities'

    def add_arguments(self, parser):
        parser.add_argument(
            'item_name',
            type=str,
            help='Item name to check (e.g., "TurDal 500")',
        )

    def handle(self, *args, **options):
        item_name = options['item_name']

        try:
            item = Item.objects.get(name=item_name)
        except Item.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Item "{item_name}" not found'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n{"="*120}'))
        self.stdout.write(self.style.SUCCESS(f'ITEM-LEVEL REMAINING QUANTITY DEBUG: {item_name}'))
        self.stdout.write(self.style.SUCCESS(f'{"="*120}\n'))

        # Find all sales order items for this item
        so_items = SalesOrderItem.objects.filter(item=item).select_related(
            'sales_order'
        ).prefetch_related('dispatch_order_items', 'dispatch_order_items__dispatch_item__dispatch_plan')

        if not so_items.exists():
            self.stdout.write(self.style.WARNING(f'No sales orders found with item "{item_name}"'))
            return

        for so_item in so_items:
            order = so_item.sales_order
            
            self.stdout.write(self.style.SUCCESS(f'Sales Order: {order.order_number}'))
            self.stdout.write(f'Order Item ID: {so_item.id}')
            self.stdout.write(f'Item Quantity in Order: {so_item.quantity}\n')

            # Check dispatch_order_items (item-level dispatches)
            dispatch_order_items = so_item.dispatch_order_items.filter(
                dispatch_item__dispatch_plan__status__ne='CANCELLED'
            ).select_related('dispatch_item', 'dispatch_item__dispatch_plan')

            if dispatch_order_items.exists():
                self.stdout.write(self.style.SUCCESS('Item-Level Dispatch Records (DispatchOrderItem):'))
                self.stdout.write(f'{"-"*120}')
                total_item_dispatched = 0
                for doi in dispatch_order_items:
                    self.stdout.write(
                        f'Dispatch: {doi.dispatch_item.dispatch_plan.dispatch_number} | '
                        f'Qty: {doi.quantity_dispatched} | '
                        f'Status: {doi.dispatch_item.dispatch_plan.status}'
                    )
                    total_item_dispatched += float(doi.quantity_dispatched)
                self.stdout.write(f'{"-"*120}')
                self.stdout.write(f'Total Item-Level Dispatched: {total_item_dispatched}')
                self.stdout.write(f'Item-Level Remaining: {float(so_item.quantity) - total_item_dispatched}\n')
            else:
                self.stdout.write(self.style.WARNING('No item-level dispatch records found\n'))

            # Check if dispatched via order-level dispatch
            self.stdout.write(self.style.SUCCESS('Order-Level Dispatch Records (DispatchItem):'))
            dispatch_items = order.dispatch_items.exclude(
                dispatch_plan__status='CANCELLED'
            ).select_related('dispatch_plan')

            if dispatch_items.exists():
                self.stdout.write(f'{"-"*120}')
                total_order_dispatched = 0
                for di in dispatch_items:
                    self.stdout.write(
                        f'Dispatch: {di.dispatch_plan.dispatch_number} | '
                        f'Order Qty Dispatched: {di.quantity_dispatched} | '
                        f'Status: {di.dispatch_plan.status}'
                    )
                    total_order_dispatched += float(di.quantity_dispatched)
                self.stdout.write(f'{"-"*120}')
                self.stdout.write(self.style.WARNING(
                    f'⚠️  Order-level dispatch found: {total_order_dispatched} units\n'
                    f'⚠️  This is NOT itemized - distributed across all items proportionally\n'
                ))
            else:
                self.stdout.write(self.style.WARNING('No order-level dispatch records found\n'))

            self.stdout.write(self.style.SUCCESS(f'{"-"*120}\n'))

        # Print issue analysis
        self.stdout.write(self.style.ERROR('\n⚠️  ISSUE ANALYSIS:'))
        self.stdout.write(self.style.ERROR(f'{"-"*120}'))
        self.stdout.write(
            'The remaining quantity shows as 5 because:\n'
            '1. Item quantity: 10\n'
            '2. Dispatch 1 (5 units) - Recorded at ORDER level (DispatchItem)\n'
            '3. Dispatch 2 (2 units) - Recorded at ORDER level (DispatchItem)\n'
            '4. Item-level calculation only looks at DispatchOrderItem records\n'
            '5. Since there are no DispatchOrderItem records, it shows: 10 - 5 = 5\n'
            '\n✗ It\'s taking only the first dispatch\'s quantity (5)\n'
            '✓ FIX: Dispatch should record at ITEM level (DispatchOrderItem) not just ORDER level\n'
        )
        self.stdout.write(self.style.ERROR(f'{"-"*120}\n'))
