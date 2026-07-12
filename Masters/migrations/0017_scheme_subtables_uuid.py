from django.db import migrations


SCHEME_TABLES = [
    "scheme_condition",
    "scheme_benefit",
    "scheme_applicability",
    "scheme_item",
    "scheme_history",
]


def convert_ids_to_uuid(apps, schema_editor):
    """
    Safe conversion for bigint PK -> uuid PK.
    Creates temp uuid column, fills it, swaps PK.
    """
    schema_editor.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    for table in SCHEME_TABLES:
        schema_editor.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = 'id_tmp_uuid'
                ) THEN
                    ALTER TABLE "{table}" ADD COLUMN id_tmp_uuid uuid;
                    UPDATE "{table}" SET id_tmp_uuid = gen_random_uuid();
                    ALTER TABLE "{table}" ALTER COLUMN id_tmp_uuid SET NOT NULL;
                END IF;
            END$$;
            """
        )

        # Drop existing PK, drop old id, promote uuid column to id, add PK.
        schema_editor.execute(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS "{table}_pkey";')
        schema_editor.execute(f'ALTER TABLE "{table}" DROP COLUMN IF EXISTS id;')
        schema_editor.execute(f'ALTER TABLE "{table}" RENAME COLUMN id_tmp_uuid TO id;')
        schema_editor.execute(f'ALTER TABLE "{table}" ADD PRIMARY KEY (id);')


def rollback_ids_to_bigint(apps, schema_editor):
    """
    Rollback to bigint PK is not safe without stored old values.
    We leave as a no-op to avoid data loss.
    """
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("Masters", "0016_remove_scheme_min_order_value"),
    ]

    operations = [
        migrations.RunPython(convert_ids_to_uuid, rollback_ids_to_bigint),
    ]
