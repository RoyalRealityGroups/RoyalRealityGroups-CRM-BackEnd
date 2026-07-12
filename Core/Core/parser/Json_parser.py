

def small_int_choices_parser(field, instance):
    """
    Returns 'value - label' if the field has choices,
    otherwise returns the raw value.
    """
    value = getattr(instance, field.name)
    if value is None:
        return None

    # If the field defines choices, map them into a dict and look up the label.
    if field.choices:
        choices_dict = dict(field.choices)
        label = choices_dict.get(value, str(value))
        return f"{value} - {label}"
    else:
        # Fallback: just return the raw value
        return value

# FIELD_PARSERS = {
#     #
#     # Example: convert SmallIntegerField to a "1 - Pending" style string if it has choices
#     #
#     models.SmallIntegerField: small_int_choices_parser,

FIELD_PARSERS = {
    #
    # Primary key / numeric fields
    #
    'AutoField': lambda field, instance: int(getattr(instance, field.name)),
    'BigAutoField': lambda field, instance: int(getattr(instance, field.name)),
    # models.IntegerField: lambda field, instance: int(getattr(instance, field.name)),
    # models.BigIntegerField: lambda field, instance: int(getattr(instance, field.name)),
    # models.PositiveIntegerField: lambda field, instance: int(getattr(instance, field.name)),
    # models.PositiveSmallIntegerField: lambda field, instance: int(getattr(instance, field.name)),
    'IntegerField': lambda field, instance: int(getattr(instance, field.name)) if getattr(instance, field.name) is not None else None,
    'BigIntegerField': lambda field, instance: int(getattr(instance, field.name)) if getattr(instance, field.name) is not None else None,
    'PositiveIntegerField': lambda field, instance: int(getattr(instance, field.name)) if getattr(instance, field.name) is not None else None,
    'PositiveSmallIntegerField': lambda field, instance: int(getattr(instance, field.name)) if getattr(instance, field.name) is not None else None,
    # models.SmallIntegerField: lambda field, instance: int(getattr(instance, field.name)),
    'SmallIntegerField': small_int_choices_parser,
    'FloatField': lambda field, instance: float(getattr(instance, field.name))
        if getattr(instance, field.name) is not None else None,
    'DecimalField': lambda field, instance: float(getattr(instance, field.name))
        if getattr(instance, field.name) is not None else None,

    #
    # Boolean field
    #
    'BooleanField': lambda field, instance: "Yes" if bool(getattr(instance, field.name)) else "No",

    #
    # String-like fields
    #
    'CharField': lambda field, instance: str(getattr(instance, field.name))
        if getattr(instance, field.name) is not None else None,
    'TextField': lambda field, instance: str(getattr(instance, field.name))
        if getattr(instance, field.name) is not None else None,
    'SlugField': lambda field, instance: str(getattr(instance, field.name))
        if getattr(instance, field.name) is not None else None,
    'EmailField': lambda field, instance: str(getattr(instance, field.name))
        if getattr(instance, field.name) is not None else None,
    'URLField': lambda field, instance: str(getattr(instance, field.name))
        if getattr(instance, field.name) is not None else None,
    'UUIDField': lambda field, instance: str(getattr(instance, field.name))
        if getattr(instance, field.name) is not None else None,
    'GenericIPAddressField': lambda field, instance: str(getattr(instance, field.name))
        if getattr(instance, field.name) is not None else None,
    'FilePathField': lambda field, instance: str(getattr(instance, field.name))
        if getattr(instance, field.name) is not None else None,

    #
    # File / image fields (just return the string path or name)
    #
    'FileField': lambda field, instance: str(getattr(instance, field.name))
        if getattr(instance, field.name) else None,
    'ImageField': lambda field, instance: str(getattr(instance, field.name))
        if getattr(instance, field.name) else None,

    #
    # Date/Time fields
    #
    'DateField': lambda field, instance: getattr(instance, field.name).strftime('%Y-%m-%d')
        if getattr(instance, field.name) else None,
    'DateTimeField': lambda field, instance: getattr(instance, field.name).strftime('%Y-%m-%d %I:%M:%S %p %z')
        if getattr(instance, field.name) else None,
    'TimeField': lambda field, instance: getattr(instance, field.name).strftime('%I:%M:%S %p')
        if getattr(instance, field.name) else None,

    #
    # Relations (use string representation of related objects)
    #
    'ForeignKey': lambda field, instance: {'d': str(getattr(instance, field.name)),'id': str(getattr(getattr(instance, field.name), 'id')) if getattr(instance, field.name) else None} 
        if getattr(instance, field.name) else None,

    'OneToOneField': lambda field, instance: {'d': str(getattr(instance, field.name)),'id': str(getattr(getattr(instance, field.name), 'id')) if getattr(instance, field.name) else None} 
        if getattr(instance, field.name) else None,

    'ManyToManyField': lambda field, instance: [{'d': str(obj),'id': str(getattr(obj, 'id'))}
        for obj in getattr(instance, field.name).all()],
    }

