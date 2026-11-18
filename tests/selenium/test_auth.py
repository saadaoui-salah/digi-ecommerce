"""User stories: authentication and the account."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from conftest import BACKEND, FRONTEND, sign_in, wait_text
from pages import HomePage


def test_us01_a_visitor_can_sign_in(driver):
    """A customer with an account reaches the storefront signed in."""
    sign_in(driver, "e2e1793868981556@example.com", "StrongPass123!")

    wait_text(driver, "E2E Tester")
    assert driver.find_elements(By.CSS_SELECTOR, "[data-sidebar-panel]")


def test_us02_the_signup_form_offers_wilaya_and_balladia(driver):
    """The two Algerian location fields are select boxes, and the balladias
    follow the chosen wilaya."""
    driver.get(f"{FRONTEND}/auth")

    trigger = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Create account']")
        )
    )
    trigger.click()

    wilaya = driver.find_element(By.ID, "wilaya")
    balladia = driver.find_element(By.ID, "balladia")

    assert len(wilaya.find_elements(By.TAG_NAME, "option")) > 1
    assert balladia.is_enabled() is False

    Select(wilaya).select_by_index(1)
    assert balladia.is_enabled() is True
    assert len(balladia.find_elements(By.TAG_NAME, "option")) > 1


def test_us03_sign_out_locks_the_member_pages(driver):
    """After signing out, the member pages ask for a sign in again."""
    sign_in(driver, "e2e1793868981556@example.com", "StrongPass123!")
    HomePage(driver).open()

    driver.get(f"{BACKEND}/api/auth/logout/")
    driver.get(f"{FRONTEND}/orders")
    wait_text(driver, "sign")
