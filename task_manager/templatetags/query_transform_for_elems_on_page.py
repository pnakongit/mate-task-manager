from django import template

register = template.Library()


@register.simple_tag
def query_transform_for_elems_on_page(request, **kwargs):
    updated = request.GET.copy()
    updated.pop("page", 0)
    for key, value in kwargs.items():
        if value is not None:
            updated[key] = value
        else:
            updated.pop(key, 0)

    return updated.urlencode()

