from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend


# Global registries
only_import_models = {}
only_export_models = {}

DEFAULT_FILTER_BACKENDS = [DjangoFilterBackend, SearchFilter, OrderingFilter]

def register_report_models(only_imports=[], only_exports=[]):

    def unpack_entries(entries):
        return {list(entry.keys())[0]: list(entry.values())[0] for entry in entries}

    def prepare_config(config):
        model_class = config['model_class']
        return {
            'model_class': model_class,
            'resource_class': config['resource_class'],
            'queryset': config.get('queryset', model_class.objects.filter()),
            'filter_backends': config.get('filter_backends', DEFAULT_FILTER_BACKENDS),
            'filterset_class': config.get('filterset_class'),
            'search_fields': config.get('search_fields', []),
            'ordering_fields': config.get('ordering_fields', []),
            'permissions': config.get('permissions', []),  # Default to empty list to avoid None + list error
        }

    for key, config in unpack_entries(only_exports).items():
        only_export_models[key] = prepare_config(config)

    for key, config in unpack_entries(only_imports).items():
        only_import_models[key] = prepare_config(config)

