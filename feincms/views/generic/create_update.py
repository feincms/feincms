from django.views.generic import CreateView, UpdateView, DeleteView
from feincms.views.decorators import add_page_to_extra_context


create_object = add_page_to_extra_context(CreateView.as_view())
update_object = add_page_to_extra_context(UpdateView.as_view())
delete_object = add_page_to_extra_context(DeleteView.as_view())
