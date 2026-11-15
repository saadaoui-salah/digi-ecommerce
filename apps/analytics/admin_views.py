"""The analytics page of the admin.

The figures of the shop live on their own page: the dashboard of the admin
keeps the lists of the shop, this page shows what the shop sold.
"""

from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

from apps.analytics.models import AnalyticsPeriod
from apps.analytics.services import available_months, available_years, shop_figures

#: The periods the page can show.
PERIODS = {
    "day": AnalyticsPeriod.DAY,
    "month": AnalyticsPeriod.MONTH,
    "year": AnalyticsPeriod.YEAR,
}


class AnalyticsAdminView(TemplateView):
    """The figures of the shop: the cards and the charts.

    Only the staff of the shop can open it — the admin site itself already
    refuses anyone else.
    """

    #: The admin site the page belongs to. It is set by the URL conf.
    admin_site = None

    template_name = "admin/analytics/analytics.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        period_key = self.request.GET.get("period", "month")
        period = PERIODS.get(period_key, AnalyticsPeriod.MONTH)

        # The daily period can be narrowed down to one month, the monthly
        # period to one year.
        month = self.request.GET.get("month") or None
        year = self.request.GET.get("year") or None
        if period != AnalyticsPeriod.DAY:
            month = None
        if period != AnalyticsPeriod.MONTH:
            year = None

        context.update(
            {
                **self.admin_site.each_context(self.request),
                "title": "Analytics",
                "period": period,
                "period_key": period_key,
                "month": month,
                "year": year,
                "months": available_months(),
                "years": available_years(),
                "periods": [
                    {"key": key, "label": label, "active": key == period_key}
                    for key, label in (
                        ("day", "Daily"),
                        ("month", "Monthly"),
                        ("year", "Yearly"),
                    )
                ],
                **shop_figures(period, month, year),
            }
        )
        return context
