import pytest
from Masters.models import Item, Category, Brand, UOM, Company

@pytest.mark.django_db
class TestItemModel:
    def test_create_item(self):
        company = Company.objects.create(code='TEST001', name='Test Company')
        category = Category.objects.create(code='CAT001', name='Test Category')
        brand = Brand.objects.create(code='BRD001', name='Test Brand')
        uom = UOM.objects.create(code='UOM001', name='Piece')
        
        item = Item.objects.create(
            code='ITEM001',
            name='Test Item',
            company=company,
            category=category,
            brand=brand,
            base_uom=uom,
            selling_price=100.00
        )
        
        assert item.code == 'ITEM001'
        assert item.name == 'Test Item'
        assert item.is_active == True
    
    def test_item_str_representation(self):
        company = Company.objects.create(code='TEST001', name='Test Company')
        uom = UOM.objects.create(code='UOM001', name='Piece')
        item = Item.objects.create(
            code='ITEM001',
            name='Test Item',
            company=company,
            base_uom=uom
        )
        assert str(item) == 'Test Item'

@pytest.mark.django_db
class TestCategoryModel:
    def test_create_category(self):
        category = Category.objects.create(code='CAT001', name='Electronics')
        assert category.code == 'CAT001'
        assert category.is_active == True
