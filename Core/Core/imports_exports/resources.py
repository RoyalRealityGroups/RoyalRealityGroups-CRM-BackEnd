from import_export import resources
from import_export import fields



class ModelImportExportResource(resources.ModelResource):

    def get_import_fields(self):
        if hasattr(self._meta, 'import_fields'):
            return [self.fields[f] for f in self._meta.import_fields]
        else:
            return super().get_import_fields()


class UserResourceRelatedField(fields.Field):
    def export(self, obj, **kwargs):
        value = self.get_value(obj)
        # Pass `obj` explicitly to the widget's render method
        return self.widget.render(value, obj=obj)