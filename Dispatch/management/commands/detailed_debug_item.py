from django.core.management.base import BaseCommand
from Sales.models import SalesOrder, SalesOrderItem
from Dispatch.models import DispatchItem, DispatchOrderItem
from Masters.models import Item


class Command(BaseCommand):
    help = 'Detailed debug of dispatch records for an item'

    def add_arguments(self, parser):
        parser.add_argument(
            'item_name',
            type=str,
            help='Item name to check (e.g., "TurDal 500")',
        )
        parser.add_argument(
            '--order-id',
            type=str,
            help='Specific order ID to check',
        )

    def handle(self, *args, **options):
        item_name = options['item_name']
        order_id = options.get('order_id')

        try:
            item = Item.objects.get(name=item_name)
        except Item.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Item "{item_name}" not found'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n{"="*140}'))
        self.stdout.write(self.style.SUCCESS(f'DETAILED DEBUG: {item_name}'))
        self.stdout.write(self.style.SUCCESS(f'{"="*140}\n'))

        # Find all sales orders with this item
        so_items = SalesOrderItem.objects.filter(item=item).select_related('order')
        
        if order_id:
            so_items = so_items.filter(order_id=order_id)

        for so_item in so_items:
            order = so_item.order
            
            self.stdout.write(self.style.SUCCESS(f'\n>>> Sales Order: {order.order_number} (ID: {order.id})'))
            self.stdout.write(f'Item in Order: {so_item.item.name} | Qty: {so_item.quantity}\n')

            # 1. Check ORDER-LEVEL dispatches
            self.stdout.write(self.style.SUCCESS('1️⃣  ORDER-LEVEL DISPATCH RECORDS (DispatchItem):'))
            order_dispatches = order.dispatch_items.exclude(
                dispatch_plan__status='CANCELLED'
            ).select_related('dispatch_plan')
            
            order_total_dispatched = 0
            if order_dispatches.exists():
                self.stdout.write(f'{"-"*140}')
                for di in order_dispatches:
                    self.stdout.write(
                        f'  Dispatch: {di.dispatch_plan.dispatch_number:<20} | '
                        f'Status: {di.dispatch_plan.status:<12} | '
                        f'Order Qty Dispatched: {di.quantity_dispatched:<10} | '
                        f'Created: {di.dispatch_plan.created_on.strftime("%Y-%m-%d %H:%M")}'
                    )
                    order_total_dispatched += float(di.quantity_dispatched)
                self.stdout.write(f'{"-"*140}')
                self.stdout.write(f'TOTAL ORDER-LEVEL DISPATCHED: {order_total_dispatched}\n')
            else:
                self.stdout.write('No order-level dispatches\n')

            # 2. Check ITEM-LEVEL dispatches
            self.stdout.write(self.style.SUCCESS('2️⃣  ITEM-LEVEL DISPATCH RECORDS (DispatchOrderItem):'))
            item_dispatches = so_item.dispatch_order_items.exclude(
                dispatch_item__dispatch_plan__status='CANCELLED'
            ).select_related('dispatch_item', 'dispatch_item__dispatch_plan')
            
            item_total_dispatched = 0
            if item_dispatches.exists():
                self.stdout.write(f'{"-"*140}')
                for doi in item_dispatches:
                    self.stdout.write(
                        f'  Dispatch: {doi.dispatch_item.dispatch_plan.dispatch_number:<20} | '
                        f'Status: {doi.dispatch_item.dispatch_plan.status:<12} | '
                        f'Item Qty Dispatched: {doi.quantity_dispatched:<10} | '
                        f'Created: {doi.dispatch_item.dispatch_plan.created_on.strftime("%Y-%m-%d %H:%M")}'
                    )
                    item_total_dispatched += float(doi.quantity_dispatched)
                self.stdout.write(f'{"-"*140}')
                self.stdout.write(f'TOTAL ITEM-LEVEL DISPATCHED: {item_total_dispatched}\n')
            else:
                self.stdout.write('No item-level dispatches\n')

            # 3. Calculate remaining
            total_qty = float(so_item.quantity)
            total_dispatched = order_total_dispatched + item_total_dispatched
            remaining = total_qty - total_dispatched

            self.stdout.write(self.style.SUCCESS('3️⃣  CALCULATION SUMMARY:'))
            self.stdout.write(f'{"-"*140}')
            self.stdout.write(f'Total Quantity in Order:           {total_qty}')
            self.stdout.write(f'Order-Level Dispatched:            {order_total_dispatched}')
            self.stdout.write(f'Item-Level Dispatched:             {item_total_dispatched}')
            self.stdout.write(f'Total Dispatched:                  {total_dispatched}')
            
            if remaining > 0:
                self.stdout.write(self.style.SUCCESS(f'REMAINING QUANTITY:                {remaining} ✓'))
            elif remaining == 0:
                self.stdout.write(self.style.WARNING(f'REMAINING QUANTITY:                {remaining} (FULLY DISPATCHED)'))
            else:
                self.stdout.write(self.style.ERROR(f'REMAINING QUANTITY:                {remaining} ✗ (ERROR - OVER DISPATCHED!)'))
            
            self.stdout.write(f'{"-"*140}\n')

            # 4. Show what the API returns
            self.stdout.write(self.style.SUCCESS('4️⃣  API RESPONSE CHECK:'))
            self.stdout.write('Run check_remaining_quantities command to see what API returns')
            self.stdout.write(f'{"-"*140}\n')
