from django.contrib import admin
from .models import PlotInventory, FlatInventory


@admin.register(PlotInventory)
class PlotInventoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'project', 'plot_number', 'area_sqyd', 'facing', 'total_price', 'status')
    list_filter = ('status', 'project', 'facing')
    search_fields = ('plot_number', 'code')
    ordering = ('project', 'plot_number')


@admin.register(FlatInventory)
class FlatInventoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'project', 'tower', 'floor', 'unit_number', 'flat_type', 'area_sqft', 'price', 'status')
    list_filter = ('status', 'project', 'tower', 'flat_type')
    search_fields = ('unit_number', 'code', 'tower')
    ordering = ('project', 'tower', 'floor', 'unit_number')
