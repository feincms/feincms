from django.views.generic import create_update
from feincms.views.decorators import add_page_to_extra_context


create_object = add_page_to_extra_context(create_update.create_object)
update_object = add_page_to_extra_context(create_update.update_object)
delete_object = add_page_to_extra_context(create_update.delete_object)
