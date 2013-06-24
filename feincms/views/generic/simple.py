from django.views.generic import TemplateView
from feincms.views.decorators import add_page_to_extra_context


direct_to_template = add_page_to_extra_context(TemplateView.as_view())
