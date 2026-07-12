from django import template

register = template.Library()

@register.filter
def mysubtract(value, arg=""):
    return value - arg

@register.filter
def add(value, arg=0):
    return int(value) + int(arg)

@register.filter()
def to_int(value):
    return int(value)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_from(key, dictionary):
    return dictionary.get(key)

@register.filter
def one_more(key, arg):
    return key, arg

@register.filter
def get_from_choices(arr, choices_list):
    key, row = arr
    val =row.get(key)
    choices =choices_list.get(key)
    return choices.get(val)