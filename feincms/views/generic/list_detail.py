from django.views.generic import DetailView, ListView
from feincms.views.decorators import add_page_to_extra_context


object_list = add_page_to_extra_context(ListView.as_view())
object_detail = add_page_to_extra_context(DetailView.as_view())
