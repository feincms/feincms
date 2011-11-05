from django.views.generic import simple
from feincms.views.decorators import add_page_to_extra_context


direct_to_template = add_page_to_extra_context(simple.direct_to_template)
