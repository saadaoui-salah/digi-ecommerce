"""Page objects: the selectors the user stories talk to.

Keeping them here means a change in the markup only needs one edit, and the
tests read like the actions a person performs.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from conftest import FRONTEND, wait_text


class HomePage:
    def __init__(self, browser: WebDriver):
        self.browser = browser

    def open(self):
        self.browser.get(f"{FRONTEND}/")
        return self

    def category_tiles(self):
        return self.browser.find_elements(By.CSS_SELECTOR, "[data-category-tile]")

    def on_sale(self):
        self.browser.find_element(By.XPATH, "//button[normalize-space()='On sale']").click()

    def cards(self):
        return self.browser.find_elements(By.CSS_SELECTOR, "[data-product-card]")


class ProductPage:
    def __init__(self, browser: WebDriver, slug: str):
        self.browser = browser
        self.slug = slug

    def open(self):
        self.browser.get(f"{FRONTEND}/products/{self.slug}")
        wait_text(self.browser, "CHOOSE A REGION")
        return self

    def region_trigger(self):
        return self.browser.find_elements(By.CSS_SELECTOR, ".search-trigger")[0]

    def duration_trigger(self):
        return self.browser.find_elements(By.CSS_SELECTOR, ".search-trigger")[1]

    def choose_region(self, name: str):
        self.region_trigger().click()
        self._choose_option(name)

    def choose_duration(self, name: str):
        self.duration_trigger().click()
        self._choose_option(name)

    def _choose_option(self, name: str):
        option = WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//div[contains(@class,'search-menu')]//button[contains(., '{name}')]")
            )
        )
        option.click()

    def buy(self):
        self.browser.find_element(By.XPATH, "//button[contains(., 'Buy now')]").click()

    def coupon(self):
        """The text of the coupon block, if the customer has one."""
        blocks = self.browser.find_elements(By.CSS_SELECTOR, "[class*='emerald-500/25']")
        return blocks[0].text if blocks else ""


class ListPage:
    """The orders / transactions / credits / referrals pages."""

    def __init__(self, browser: WebDriver, path: str):
        self.browser = browser
        self.path = path

    def open(self):
        self.browser.get(f"{FRONTEND}{self.path}")
        return self

    def rows(self):
        return self.browser.find_elements(By.CSS_SELECTOR, "tbody tr")

    def first_row(self) -> str:
        return self.rows()[0].text


class AnalyticsPage:
    def __init__(self, browser: WebDriver):
        self.browser = browser

    def open(self):
        self.browser.get(f"{FRONTEND}/analytics")
        wait_text(self.browser, "Bought products by count")
        return self

    def period(self, name: str):
        self.browser.find_element(
            By.XPATH, f"//main//button[normalize-space()='{name}']"
        ).click()

    def scope(self, name: str):
        self.browser.find_element(
            By.XPATH, f"//main//button[normalize-space()='{name}']"
        ).click()

    def cards(self) -> str:
        return self.browser.find_element(By.CSS_SELECTOR, "main .grid").text

    def dropdown_value(self) -> str:
        trigger = self.browser.find_element(By.CSS_SELECTOR, "main .dropdown-trigger")
        return trigger.text.strip()

    def open_dropdown(self):
        self.browser.find_element(By.CSS_SELECTOR, "main .dropdown-trigger").click()

    def choose_dropdown_option(self, name: str):
        self.open_dropdown()
        option = WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//main//div[contains(@class,'dropdown-menu')]//button[contains(., '{name}')]")
            )
        )
        option.click()

    def bars(self):
        return self.browser.find_elements(By.CSS_SELECTOR, "main ul li")


class AdminAnalyticsPage:
    def __init__(self, browser: WebDriver, backend: str):
        self.browser = browser
        self.backend = backend

    def open(self, period: str = "month"):
        self.browser.get(f"{self.backend}/admin/analytics/?period={period}")
        wait_text(self.browser, "Bought products by count")
        return self

    def card(self, title: str) -> str:
        """The value shown in a card whose heading is ``title``."""
        heading = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//h2[normalize-space()='{title}']")
            )
        )
        return heading.find_element(By.XPATH, "..").text

    def chart_titles(self):
        return [
            element.text.strip()
            for element in self.browser.find_elements(By.CSS_SELECTOR, "h2")
        ]


class AdminListPage:
    def __init__(self, browser: WebDriver, backend: str, model: str):
        self.browser = browser
        self.url = f"{backend}/admin/accounts/{model}/"

    def open(self):
        self.browser.get(self.url)
        return self

    def rows(self):
        return self.browser.find_elements(By.CSS_SELECTOR, "#result_list tbody tr")

    def add(self):
        self.browser.get(f"{self.url}add/")

    def fill(self, name: str, value: str):
        field = self.browser.find_element(By.NAME, name)
        field.clear()
        field.send_keys(value)

    def select(self, name: str, value: str):
        Select(self.browser.find_element(By.NAME, name)).select_by_value(value)

    def check(self, name: str):
        self.browser.find_element(By.NAME, name).click()

    def save(self):
        self.browser.find_element(By.NAME, "_save").click()
