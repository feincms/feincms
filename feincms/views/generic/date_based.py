from django.views.generic import date_based
from feincms.views.decorators import add_page_to_extra_context


archive_index = add_page_to_extra_context(date_based.archive_index)
archive_year = add_page_to_extra_context(date_based.archive_year)
archive_month = add_page_to_extra_context(date_based.archive_month)
archive_week = add_page_to_extra_context(date_based.archive_week)
archive_day = add_page_to_extra_context(date_based.archive_day)
archive_today = add_page_to_extra_context(date_based.archive_today)
object_detail = add_page_to_extra_context(date_based.object_detail)
