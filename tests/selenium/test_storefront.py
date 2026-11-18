"""User stories: browsing, buying and the account history."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from conftest import FRONTEND, wait_text
from pages import AnalyticsPage, ListPage, ProductPage


def test_us04_the_region_filters_the_durations(customer):
    """Picking a region shows only the durations of that region."""
    product = ProductPage(customer, "game-pass").open()
    product.choose_region("Turkey")

    product.duration_trigger().click()
    options = WebDriverWait(customer, 10).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.search-menu [role=option]")
        )
    )
    # The list of the second dropdown only, after the first one is hidden.
    visible = [option.text for option in options if option.is_displayed()]
    assert visible
    assert all("Turkey" in text for text in visible)


def test_us05_the_coupon_shows_the_real_and_the_discounted_price(customer):
    """A customer with a coupon sees the code, the old price and the new one."""
    product = ProductPage(customer, "game-pass").open()
    coupon = product.coupon()

    assert "YOUR COUPON" in coupon
    assert "DIGI" in coupon
    # There are two prices: the struck one and the discounted one.
    assert coupon.count("DA") >= 2


def test_us06_a_purchase_lands_in_the_order_history(customer):
    """Buying a product places an order that shows the product and package."""
    product = ProductPage(customer, "game-pass").open()
    product.choose_duration("1 Month")
    product.buy()
    wait_text(customer, "Order")

    orders = ListPage(customer, "/orders").open()
    wait_text(customer, "Game Pass")
    assert "Game Pass" in orders.first_row()


def test_us07_the_history_shows_product_and_package(customer):
    """Transactions name the product and the package, not 'Order N'."""
    transactions = ListPage(customer, "/transactions").open()
    wait_text(customer, "DA")

    text = transactions.browser.find_element(By.TAG_NAME, "tbody").text
    assert "Order " not in text or " · " in text


def test_us08_the_analytics_page_shows_the_three_charts(customer):
    """The customer analytics page has the cards and the three charts."""
    analytics = AnalyticsPage(customer).open()

    for title in (
        "Bought products by count",
        "Spend over time",
        "Benefits over time",
    ):
        assert title in analytics.browser.find_element(By.TAG_NAME, "main").text
    assert analytics.bars()


def test_us09_the_daily_period_offers_a_month_picker(customer):
    """In the daily period, a month picker narrows the charts down."""
    analytics = AnalyticsPage(customer).open()
    analytics.period("Daily")

    trigger = WebDriverWait(customer, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "main .dropdown-trigger"))
    )
    assert trigger.text.strip()

    analytics.open_dropdown()
    options = WebDriverWait(customer, 10).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "main .dropdown-menu [role=option]")
        )
    )
    assert options
