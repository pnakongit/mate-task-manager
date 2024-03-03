from django import template
from django.http import HttpRequest

register = template.Library()


@register.simple_tag
def query_transform(request: HttpRequest, remove_page: bool = False, **kwargs: str) -> str:
    updated = request.GET.copy()
    if remove_page:
        updated.pop("page", 0)
    for key, value in kwargs.items():
        if value is not None:
            updated[key] = value
        else:
            updated.pop(key, 0)

    return updated.urlencode()
