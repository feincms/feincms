from django.views.generic import dates
from feincms.views.decorators import add_page_to_extra_context


archive_index = add_page_to_extra_context(dates.ArchiveIndexView.as_view())
archive_year = add_page_to_extra_context(dates.YearArchiveView.as_view())
archive_month = add_page_to_extra_context(dates.MonthArchiveView.as_view())
archive_week = add_page_to_extra_context(dates.WeekArchiveView.as_view())
archive_day = add_page_to_extra_context(dates.DayArchiveView.as_view())
archive_today = add_page_to_extra_context(dates.TodayArchiveView.as_view())
object_detail = add_page_to_extra_context(dates.DateDetailView.as_view())
