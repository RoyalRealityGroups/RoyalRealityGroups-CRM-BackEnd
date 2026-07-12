"""Default Item Master field configuration definitions."""

from typing import Tuple

from Masters.models import ItemFieldConfiguration

DEFAULT_ITEM_FIELD_CONFIGS = [
    # Basic Information Section
    {"field_name": "code", "display_label": "Item Code", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 1, "section": "basic"},
    {"field_name": "name", "display_label": "Item Name", "is_visible": True, "is_required": True, "is_readonly": False, "display_order": 2, "section": "basic"},
    {"field_name": "short_name", "display_label": "Short Name", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 3, "section": "basic"},
    {"field_name": "description", "display_label": "Description", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 4, "section": "basic"},
    {"field_name": "image", "display_label": "Item Image", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 5, "section": "basic"},
    {"field_name": "item_type", "display_label": "Item Type", "is_visible": True, "is_required": True, "is_readonly": False, "display_order": 6, "section": "basic"},
    {"field_name": "product_type", "display_label": "Product Type", "is_visible": True, "is_required": True, "is_readonly": False, "display_order": 7, "section": "basic"},
    {"field_name": "sku", "display_label": "SKU", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 8, "section": "basic"},
    {"field_name": "barcode", "display_label": "Barcode", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 9, "section": "basic"},
    {"field_name": "company", "display_label": "Company", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 10, "section": "basic"},

    # Classification Section
    {"field_name": "category", "display_label": "Category", "is_visible": True, "is_required": True, "is_readonly": False, "display_order": 11, "section": "classification"},
    {"field_name": "brand", "display_label": "Brand", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 12, "section": "classification"},
    {"field_name": "base_uom", "display_label": "Base UOM", "is_visible": True, "is_required": True, "is_readonly": False, "display_order": 13, "section": "classification"},
    {"field_name": "bag_weight", "display_label": "Bag Weight", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 14, "section": "classification"},
    {"field_name": "hsn_code", "display_label": "HSN Code", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 15, "section": "classification"},
    {"field_name": "sac_code", "display_label": "SAC Code", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 16, "section": "classification"},
    {"field_name": "tax_category", "display_label": "Tax Category", "is_visible": True, "is_required": True, "is_readonly": False, "display_order": 17, "section": "classification"},
    {"field_name": "cess_applicable", "display_label": "CESS Applicable", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 18, "section": "classification"},
    {"field_name": "cess_rate", "display_label": "CESS Rate", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 19, "section": "classification"},

    # Pricing Section
    {"field_name": "cost_price", "display_label": "Cost Price", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 20, "section": "pricing"},
    {"field_name": "selling_price", "display_label": "Selling Price", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 21, "section": "pricing"},
    {"field_name": "mrp", "display_label": "MRP", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 22, "section": "pricing"},
    {"field_name": "min_price", "display_label": "Minimum Price", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 23, "section": "pricing"},
    {"field_name": "price_includes_tax", "display_label": "Price Includes Tax", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 24, "section": "pricing"},

    # Stock Management Section
    {"field_name": "is_stockable", "display_label": "Is Stockable", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 25, "section": "stock"},
    {"field_name": "track_inventory", "display_label": "Track Inventory", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 26, "section": "stock"},
    {"field_name": "min_stock_level", "display_label": "Min Stock Level", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 27, "section": "stock"},
    {"field_name": "max_stock_level", "display_label": "Max Stock Level", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 28, "section": "stock"},
    {"field_name": "reorder_level", "display_label": "Reorder Level", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 29, "section": "stock"},
    {"field_name": "reorder_quantity", "display_label": "Reorder Quantity", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 30, "section": "stock"},
    {"field_name": "weight", "display_label": "Weight", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 31, "section": "stock"},
    {"field_name": "weight_unit", "display_label": "Weight Unit", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 32, "section": "stock"},
    {"field_name": "length", "display_label": "Length", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 33, "section": "stock"},
    {"field_name": "width", "display_label": "Width", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 34, "section": "stock"},
    {"field_name": "height", "display_label": "Height", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 35, "section": "stock"},

    # Settings Section
    {"field_name": "is_active", "display_label": "Is Active", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 36, "section": "settings"},
    {"field_name": "is_saleable", "display_label": "Is Saleable", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 37, "section": "settings"},
    {"field_name": "is_purchasable", "display_label": "Is Purchasable", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 38, "section": "settings"},
    {"field_name": "is_featured", "display_label": "Is Featured", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 39, "section": "settings"},
    {"field_name": "allow_discount", "display_label": "Allow Discount", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 40, "section": "settings"},
    {"field_name": "allow_negative_stock", "display_label": "Allow Negative Stock", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 41, "section": "settings"},
    {"field_name": "manufacturer", "display_label": "Manufacturer", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 42, "section": "settings"},
    {"field_name": "warranty_period", "display_label": "Warranty Period (months)", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 43, "section": "settings"},
    {"field_name": "warranty_description", "display_label": "Warranty Description", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 44, "section": "settings"},
    {"field_name": "sync_with_erp", "display_label": "Sync with ERP", "is_visible": True, "is_required": False, "is_readonly": False, "display_order": 45, "section": "settings"},
]


def upsert_item_field_configurations() -> Tuple[int, int]:
    """Create or update all default Item field configurations."""
    created_count = 0
    updated_count = 0

    for config_data in DEFAULT_ITEM_FIELD_CONFIGS:
        _, created = ItemFieldConfiguration.objects.update_or_create(
            field_name=config_data["field_name"],
            defaults={
                "display_label": config_data["display_label"],
                "is_visible": config_data["is_visible"],
                "is_required": config_data["is_required"],
                "is_readonly": config_data["is_readonly"],
                "display_order": config_data["display_order"],
                "section": config_data["section"],
            },
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    return created_count, updated_count
