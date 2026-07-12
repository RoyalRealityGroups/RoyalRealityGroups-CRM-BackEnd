from django.core.management.commands.makemigrations import Command as MakeMigrationsCommand
from django.db.migrations.loader import MigrationLoader
from django.db import connections
from django.conf import settings
import os

class Command(MakeMigrationsCommand):
    def handle(self, *app_labels, **options):
        # First run the regular makemigrations command
        super().handle(*app_labels, **options)

        # After that, create or update the single empty migration in the General app
        self.create_single_empty_migration()

    def create_single_empty_migration(self):
        # Initialize the migration loader to access the migration graph
        connection = connections['default']
        loader = MigrationLoader(connection)

        # Get the list of installed apps
        apps_to_migrate = settings.INSTALLED_APPS

        # Template for creating the empty migration
        empty_migration_template = '''\
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = {dependencies}

    operations = [
        migrations.RunSQL(
            """
            CREATE VIEW stock_view AS
            SELECT DISTINCT ON (code, project_id, warehouse_id, item_id, batch_id, quantity) code,
                created_on as date,
                screen_name,
                project_id,
                warehouse_id,
                item_id,
                batch_id,
                quantity
            FROM ( SELECT b.code,
                        h.created_on,     
                        'stocktransferinitem'::text AS screen_name,
                        h.project_id,
                        h.warehouse_id,
                        b.item_id,
                        bt.id AS batch_id,
                        b.qty AS quantity
                    FROM "StockTransfer_stocktransferinitem" b
                        JOIN "StockTransfer_stocktransferin" h ON b.stocktransferin_id = h.id
				  		LEFT JOIN "Masters_batch" bt ON bt.id = b.batch_id
                    WHERE b.is_deleted = false AND h.is_deleted = false
                    UNION ALL
                    SELECT b.code,
                        h.created_on,
                        'stocktransferoutrejected'::text AS screen_name,
                        h.project_id,
                        h.warehouse_id,
                        b.item_id,
                        bt.id AS batch_id,
                        b.qty AS quantity
                    FROM "StockTransfer_stocktransferoutitem" b
                        JOIN "StockTransfer_stocktransferout" h ON b.stocktransferout_id = h.id
                        LEFT JOIN "Masters_batch" bt ON bt.id = b.batch_id
                    WHERE b.is_deleted = false AND h.is_deleted = false AND h.authorized_status = 3
                    UNION ALL
                    SELECT b.code,
                        h.created_on,
                        'productionreceiptitem'::text AS screen_name,
                        h.project_id,
                        h.warehouse_id,
                        b.item_id,
                        bt.id AS batch_id,
                        b.qty AS quantity
                    FROM "Production_productionreceiptitem" b
                        JOIN "Production_productionreceipt" h ON b.productionreceipt_id = h.id
                        LEFT JOIN "Masters_batch" bt ON bt.id = b.batch_id
                    WHERE b.is_deleted = false AND h.is_deleted = false
                    UNION ALL
                    SELECT b.code,
                        h.created_on,
                        'materialreceivednoteitem'::text AS screen_name,
                        h.project_id,
                        h.warehouse_id,
                        b.item_id,
                        bt.id AS batch_id,
                        b.qty AS quantity
                    FROM "MaterialReceivedNote_materialreceivednoteitem" b
                        JOIN "MaterialReceivedNote_materialreceivednote" h ON b.mrn_id = h.id
                        LEFT JOIN "Masters_batch" bt ON bt.id = b.batch_id
                    WHERE b.is_deleted = false AND h.is_deleted = false
                    UNION ALL
                    SELECT b.code,
                        h.created_on,
                        'materialreceiptitem'::text AS screen_name,
                        h.project_id,
                        h.warehouse_id,
                        b.item_id,
                        bt.id AS batch_id,
                        b.qty AS quantity
                    FROM "MaterialReceipt_materialreceiptitem" b
                        JOIN "MaterialReceipt_materialreceipt" h ON b.materialreceipt_id = h.id
                        LEFT JOIN "Masters_batch" bt ON bt.id = b.batch_id
                    WHERE b.is_deleted = false AND h.is_deleted = false
                    UNION ALL
                    SELECT b.code,
                        h.created_on,
                        'deliveryreturnnotesitem'::text AS screen_name,
                        h.project_id,
                        h.warehouse_id,
                        b.item_id,
                        NULL::uuid AS batch_id,
                        b.qty AS quantity
                    FROM "Delivery_deliveryreturnnotesitem" b
                        JOIN "Delivery_deliveryreturnnotes" h ON b.deliveryreturnnotes_id = h.id
                    WHERE b.is_deleted = false AND h.is_deleted = false
                    UNION ALL
                    SELECT b.code,
                        h.created_on,
                        'stocktransferoutitem'::text AS screen_name,
                        h.project_id,
                        h.warehouse_id,
                        b.item_id,
                        bt.id AS batch_id,
                        - b.qty AS quantity
                    FROM "StockTransfer_stocktransferoutitem" b
                        JOIN "StockTransfer_stocktransferout" h ON b.stocktransferout_id = h.id
                        LEFT JOIN "Masters_batch" bt ON bt.id = b.batch_id
                    WHERE b.is_deleted = false AND h.is_deleted = false
                    UNION ALL
                    SELECT b.code,
                        h.created_on,
                        'issuetoproductionitem'::text AS screen_name,
                        h.project_id,
                        h.warehouse_id,
                        b.item_id,
                        bt.id AS batch_id,
                        - b.qty AS quantity
                    FROM "Production_issuetoproductionitem" b
                        JOIN "Production_issuetoproduction" h ON b.issuetoproduction_id = h.id
                        LEFT JOIN "Masters_batch" bt ON bt.id = b.batch_id
                    WHERE b.is_deleted = false AND h.is_deleted = false
                    UNION ALL
                    SELECT b.code,
                        h.created_on,
                        'materialissueitem'::text AS screen_name,
                        h.project_id,
                        h.warehouse_id,
                        b.item_id,
                        bt.id AS batch_id,
                        -b.qty AS quantity
                    FROM "MaterialIssue_materialissueitem" b
                        JOIN "MaterialIssue_materialissue" h ON b.materialissue_id = h.id
                        LEFT JOIN "Masters_batch" bt ON bt.id = b.batch_id
                    WHERE b.is_deleted = false AND h.is_deleted = false
                UNION ALL
                    SELECT b.code,
                        h.created_on,
                        'materialissueitem'::text AS screen_name,
                        h.project_id,
                        h.to_warehouse_id AS warehouse_id,
                        b.item_id,
                        bt.id AS batch_id,
                        b.qty AS quantity
                    FROM "MaterialIssue_materialissueitem" b
                        JOIN "MaterialIssue_materialissue" h ON b.materialissue_id = h.id
                        LEFT JOIN "Masters_batch" bt ON bt.id = b.batch_id
                    WHERE b.is_deleted = false AND h.is_deleted = false
                    UNION ALL
                    SELECT b.code,
                        h.created_on,
                        'materialreceivednotereturnitem'::text AS screen_name,
                        h.project_id,
                        h.warehouse_id,
                        b.item_id,
                        bt.id AS batch_id,
                        - b.qty AS quantity
                    FROM "MaterialReceivedNoteReturn_materialreceivednotereturnitem" b
                        JOIN "MaterialReceivedNoteReturn_materialreceivednotereturn" h ON b.mrn_return_id = h.id
                        LEFT JOIN "Masters_batch" bt ON bt.id = b.batch_id
                    WHERE b.is_deleted = false AND h.is_deleted = false
                    UNION ALL
                    SELECT b.code,
                        h.created_on,
                        'deliverychallanitem'::text AS screen_name,
                        h.project_id,
                        h.warehouse_id,
                        b.item_id,
                        bt.id AS batch_id,
                        - b.qty AS quantity
                    FROM "Delivery_deliverychallanitem" b
                        JOIN "Delivery_deliverychallan" h ON b.deliverychallan_id = h.id
                        LEFT JOIN "Masters_batch" bt ON bt.id = b.batch_id
                    WHERE b.is_deleted = false AND h.is_deleted = false) subquery
            ORDER BY code, project_id, warehouse_id, item_id, batch_id, quantity;
            """,
            reverse_sql="DROP VIEW IF EXISTS stock_view;",
        ),
    ]
'''
        # This will store all dependencies from each app
        dependencies = []

        for app in apps_to_migrate:
            # Get the last migration for the app
            leaf_nodes = loader.graph.leaf_nodes(app.split('.')[-1])
            for migration in leaf_nodes:
                dependencies.append(migration)

        if dependencies:
            # Create a new migration file in the General app
            system_migrations_path = os.path.join(settings.BASE_DIR, 'General', 'migrations')
            os.makedirs(system_migrations_path, exist_ok=True)

            # Find the next available migration number (e.g., 000X)
            migration_files = [f for f in os.listdir(system_migrations_path) if f.endswith('.py')]
            next_migration_number = max(
                [int(f.split('_')[0]) for f in migration_files if f.split('_')[0].isdigit()],
                default=0
            ) + 1

            # Generate the file name with a unique identifier
            migration_file_name = os.path.join(system_migrations_path, f"{next_migration_number:04d}_auto_empty_migration.py")

            # Convert the dependencies into a readable format
            dependencies_str = repr(dependencies)

            # Write the empty migration with the gathered dependencies
            with open(migration_file_name, "w") as migration_file:
                migration_file.write(empty_migration_template.format(dependencies=dependencies_str))

            print(f"Single empty migration created/updated in General: {migration_file_name}")
        else:
            print("No dependencies found to create the migration.")



# python manage.py update_stock_view
