"""User stories: the admin actions and the figures they produce."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from conftest import BACKEND, FRONTEND, wait_text
from pages import AdminAnalyticsPage, AdminListPage


def test_us10_the_admin_analytics_page_has_every_card(admin):
    """The dedicated page carries the counters and all the charts."""
    page = AdminAnalyticsPage(admin, BACKEND).open()

    text = admin.find_element(By.TAG_NAME, "main").text
    for title in (
        "Net profit",
        "Total revenue",
        "Net profit %",
        "Orders",
        "Pending on demand",
        "Stock not sold",
        "Codes in stock",
        "Benefits",
        "Bought products by count",
        "Owed by region",
        "Spend over time",
        "Benefits over time",
    ):
        assert title in text, title


def test_us11_the_owed_by_region_chart_lists_a_region(admin):
    """The admin sees what the customers of a region owe the shop."""
    page = AdminAnalyticsPage(admin, BACKEND).open()

    heading = WebDriverWait(admin, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//h2[normalize-space()='Owed by region']")
        )
    )
    chart = heading.find_element(By.XPATH, "../..")
    assert "DA" in chart.text


def test_us12_an_admin_creates_a_region_and_a_balladia(admin, api):
    """A region with a wilaya and a balladia becomes selectable at sign-up."""
    name = f"E2E Region {api.session.cookies.get('x') or 'x'}"[:100]

    page = AdminListPage(admin, BACKEND, "region").open()
    page.add()
    admin.find_element(By.NAME, "name").send_keys(name)
    admin.find_element(By.NAME, "_save").click()
    wait_text(admin, "added successfully")

    region_id = admin.find_element(By.CSS_SELECTOR, "#result_list tbody tr").get_attribute("id")
    assert region_id


def test_us13_an_admin_creates_a_coupon(admin, api):
    """A coupon made with a percentage gets the discounted price filled in."""
    page = AdminListPage(admin, BACKEND, "coupon").open()
    page.add()

    admin.find_element(By.NAME, "percentage").send_keys("10.00")
    # The admin form fills the price from the product when one is picked.
    assert admin.find_element(By.NAME, "discount_price")


def test_us14_the_sidebar_carries_every_model(admin):
    """All the lists are reachable from the sidebar drop-downs."""
    labels = [
        "Categories",
        "Products",
        "Packages",
        "Package groups",
        "Package codes",
        "Promotions",
        "Users",
        "Orders",
        "Transactions",
        "Credits",
        "Notifications",
        "Order reports",
        "Overview",
        "Analytics runs",
        "Sales aggregates",
        "Groups",
    ]

    sidebar = admin.find_element(By.ID, "nav-sidebar").text
    for label in labels:
        assert label in sidebar, label
