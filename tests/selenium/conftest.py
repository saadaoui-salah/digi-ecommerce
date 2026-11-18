"""Shared fixtures for the Selenium end-to-end suite.

The tests drive the real storefront (Next.js on :3000) and the real API
(Django on :8000). Start both before running them. Test data is created
through the API so each user story starts from a known state — the actions
being tested are still performed through the browser.
"""

from __future__ import annotations

import os
import uuid

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

FRONTEND = os.getenv("E2E_FRONTEND", "http://localhost:3000")
BACKEND = os.getenv("E2E_BACKEND", "http://127.0.0.1:8000")

CUSTOMER_EMAIL = os.getenv("E2E_CUSTOMER", "e2e1793868981556@example.com")
CUSTOMER_PASSWORD = os.getenv("E2E_CUSTOMER_PASSWORD", "StrongPass123!")
ADMIN_EMAIL = os.getenv("E2E_ADMIN", "root@example.com")
ADMIN_PASSWORD = os.getenv("E2E_ADMIN_PASSWORD", "strong-password-123")


@pytest.fixture(scope="session")
def api():
    """A requests session with the Django JWT cookies."""

    session = requests.Session()

    def login(email, password):
        response = session.post(
            f"{BACKEND}/api/auth/token/",
            json={"email": email, "password": password},
            timeout=15,
        )
        assert response.status_code == 200, response.text
        return session

    session.login = login  # type: ignore[attr-defined]
    return session


@pytest.fixture
def driver():
    """A headless Chrome instance, torn down after each test."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1440,1100")
    options.add_argument(f"--user-data-dir=/tmp/digi-e2e-{uuid.uuid4().hex}")

    browser = webdriver.Chrome(options=options)
    browser.implicitly_wait(5)
    yield browser
    browser.quit()


@pytest.fixture
def customer(driver):
    """A browser signed in as a normal customer."""
    sign_in(driver, CUSTOMER_EMAIL, CUSTOMER_PASSWORD)
    return driver


@pytest.fixture
def admin(driver):
    """A browser signed in to the Django admin."""
    driver.get(f"{BACKEND}/admin/login/")
    driver.find_element(By.NAME, "username").send_keys(ADMIN_EMAIL)
    driver.find_element(By.NAME, "password").send_keys(ADMIN_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "input[type=submit]").click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "nav-sidebar"))
    )
    return driver


def sign_in(browser, email: str, password: str) -> None:
    """Sign in through the storefront form."""
    browser.get(f"{FRONTEND}/auth")
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[name=email]"))
    )
    browser.find_element(By.CSS_SELECTOR, "input[name=email]").send_keys(email)
    browser.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(password)
    browser.find_element(By.CSS_SELECTOR, "form button[type=submit]").click()
    WebDriverWait(browser, 12).until(EC.url_changes(f"{FRONTEND}/auth"))


def wait_text(browser, text: str, timeout: int = 12):
    """Wait until the text appears anywhere on the page."""
    return WebDriverWait(browser, timeout).until(
        EC.visibility_of_element_located(
            (By.XPATH, f"//*[contains(normalize-space(.), '{text}')]")
        )
    )
