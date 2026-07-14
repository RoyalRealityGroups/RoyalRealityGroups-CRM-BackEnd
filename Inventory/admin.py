from django.contrib import admin
from .models import Plot, Flat


@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = ('plot_number', 'project', 'area', 'price', 'status')
    list_filter = ('status', 'project')
    search_fields = ('plot_number', 'project__name')


@admin.register(Flat)
class FlatAdmin(admin.ModelAdmin):
    list_display = ('project', 'tower', 'floor', 'unit_number', 'area', 'price', 'status')
    list_filter = ('status', 'project', 'tower', 'floor')
    search_fields = ('tower', 'unit_number', 'project__name')