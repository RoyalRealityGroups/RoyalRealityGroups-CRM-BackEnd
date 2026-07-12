from django.apps import AppConfig
from django.db.utils import ProgrammingError, OperationalError
from django.db import connection


class MastersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Masters'

    def ready(self):
        # Register signals (project status-history auto-write)
        try:
            import Masters.signals  # noqa: F401
        except ImportError:
            pass

        try:
            from Core.Reports.import_export_models import register_report_models
            from Masters.resources import (
                ItemResource, ItemTaxCompositionResource, CountryResource, StateResource,
                DistrictResource, MandalResource, CityResource, AreaResource, RouteResource,
                LocationResource, WareHouseResource, UOMResource, CategoryResource, BrandResource,
                TaxResource, SuperstockistResource, SuperstockistLocationResource,
                DistributorResource, DistributorLocationResource, RetailerResource,
                RetailerLocationResource, PriceBookResource, AgentResource,
                ProjectResource,
            )
            from Masters.models import (
                Item, ItemTaxComposition, Country, State, District, Mandal, City, Area,
                Route, Location, WareHouse, UOM, Category, Brand, Tax, Superstockist,
                SuperstockistLocation, Distributor, DistributorLocation, Retailer,
                RetailerLocation, PriceBook, Agent,
                Project,
            )

            register_report_models(only_imports=[
                {'Item': {'model_class': Item, 'resource_class': ItemResource}},
                {'ItemTaxComposition': {'model_class': ItemTaxComposition, 'resource_class': ItemTaxCompositionResource}},
                {'Country': {'model_class': Country, 'resource_class': CountryResource}},
                {'State': {'model_class': State, 'resource_class': StateResource}},
                {'District': {'model_class': District, 'resource_class': DistrictResource}},
                {'Mandal': {'model_class': Mandal, 'resource_class': MandalResource}},
                {'City': {'model_class': City, 'resource_class': CityResource}},
                {'Area': {'model_class': Area, 'resource_class': AreaResource}},
                {'Route': {'model_class': Route, 'resource_class': RouteResource}},
                {'Location': {'model_class': Location, 'resource_class': LocationResource}},
                {'WareHouse': {'model_class': WareHouse, 'resource_class': WareHouseResource}},
                {'UOM': {'model_class': UOM, 'resource_class': UOMResource}},
                {'Category': {'model_class': Category, 'resource_class': CategoryResource}},
                {'Brand': {'model_class': Brand, 'resource_class': BrandResource}},
                {'Tax': {'model_class': Tax, 'resource_class': TaxResource}},
                {'Superstockist': {'model_class': Superstockist, 'resource_class': SuperstockistResource}},
                {'SuperstockistLocation': {'model_class': SuperstockistLocation, 'resource_class': SuperstockistLocationResource}},
                {'Distributor': {'model_class': Distributor, 'resource_class': DistributorResource}},
                {'DistributorLocation': {'model_class': DistributorLocation, 'resource_class': DistributorLocationResource}},
                {'Retailer': {'model_class': Retailer, 'resource_class': RetailerResource}},
                {'RetailerLocation': {'model_class': RetailerLocation, 'resource_class': RetailerLocationResource}},
                {'PriceBook': {'model_class': PriceBook, 'resource_class': PriceBookResource}},
                {'Agent': {'model_class': Agent, 'resource_class': AgentResource}},
                {'Project': {'model_class': Project, 'resource_class': ProjectResource}},
            ], only_exports=[
                {'Agent': {'model_class': Agent, 'resource_class': AgentResource}},
                {'Project': {'model_class': Project, 'resource_class': ProjectResource}},
            ])
        except (ProgrammingError, OperationalError):
            # Database not ready yet (during migrations)
            pass
