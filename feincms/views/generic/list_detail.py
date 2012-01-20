from django.views.generic import list_detail
from feincms.views.decorators import add_page_to_extra_context


object_list = add_page_to_extra_context(list_detail.object_list)
object_detail = add_page_to_extra_context(list_detail.object_detail)
