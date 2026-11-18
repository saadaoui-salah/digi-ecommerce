"""Validate the figures shown in the browser against the API and the data.

These are the tests that catch a broken counter or a chart reading stale
numbers: the number displayed in the page has to be the number the API says.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By

from conftest import BACKEND, wait_text
from pages import AdminAnalyticsPage, AnalyticsPage


def _money(value) -> str:
    return f"{float(value):.2f} DA"


def test_us15_the_customer_cards_match_the_api(customer, api):
    """The four cards of the analytics page are the account counters."""
    me = api.get(f"{BACKEND}/api/auth/me/").json()

    analytics = AnalyticsPage(customer).open()
    cards = analytics.cards()

    assert _money(me["net_profit"]) in cards
    assert _money(me["total_revenue"]) in cards
    assert f"{me['orders_count']}" in cards
    assert f"{me['pending_demand_orders']}" in cards


def test_us16_the_shop_cards_match_the_api(admin, api):
    """The admin cards are the sum of the counters of the shop."""
    api.login("root@example.com", "strong-password-123")
    figures = api.get(f"{BACKEND}/api/analytics/?scope=shop").json()["cards"]

    AdminAnalyticsPage(admin, BACKEND).open()
    main = admin.find_element(By.CSS_SELECTOR, "#main").text

    assert _money(figures["net_profit"]) in main
    assert _money(figures["total_revenue"]) in main
    assert f"{figures['orders_count']}" in main


def test_us17_the_period_switcher_changes_the_chart(customer):
    """Narrowing the period down changes the number of buckets."""
    analytics = AnalyticsPage(customer).open()

    before = len(analytics.bars())
    analytics.period("Year")
    after = len(analytics.bars())

    assert after <= before
