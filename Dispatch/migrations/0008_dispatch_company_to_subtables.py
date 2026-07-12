from django.db import migrations, models


def backfill_dispatch_companies(apps, schema_editor):
    DispatchItem = apps.get_model('Dispatch', 'DispatchItem')
    DispatchOrderItem = apps.get_model('Dispatch', 'DispatchOrderItem')

    for item in DispatchItem.objects.select_related('sales_order').all():
        if item.sales_order_id and item.company_id is None:
            item.company_id = item.sales_order.company_id
            item.save(update_fields=['company'])

    sales_order_item_field = DispatchOrderItem._meta.get_field('sales_order_item')
    SalesOrderItem = sales_order_item_field.remote_field.model
    order_relation_name = 'sales_order' if any(
        f.name == 'sales_order' for f in SalesOrderItem._meta.get_fields()
    ) else 'order'

    for order_item in DispatchOrderItem.objects.select_related(
        f'sales_order_item__{order_relation_name}'
    ).all():
        if order_item.sales_order_item_id and order_item.company_id is None:
            sales_order = getattr(order_item.sales_order_item, order_relation_name, None)
            if sales_order and getattr(sales_order, 'company_id', None):
                order_item.company_id = sales_order.company_id
                order_item.save(update_fields=['company'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('Dispatch', '0007_alter_dispatchplan_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='dispatchitem',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT, related_name='dispatch_items', to='Masters.company'),
        ),
        migrations.AddField(
            model_name='dispatchorderitem',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT, related_name='dispatch_order_items', to='Masters.company'),
        ),
        migrations.RunPython(backfill_dispatch_companies, noop_reverse),
        migrations.RemoveField(
            model_name='dispatchplan',
            name='company',
        ),
        migrations.AddIndex(
            model_name='dispatchitem',
            index=models.Index(fields=['company'], name='dispatch_ite_company_2a8a3b_idx'),
        ),
        migrations.AddIndex(
            model_name='dispatchorderitem',
            index=models.Index(fields=['company'], name='dispatch_ord_company_5d280b_idx'),
        ),
    ]
