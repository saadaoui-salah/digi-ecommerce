# Selenium end-to-end test plan

Real-browser tests that drive the storefront and the Django admin the way a
person does, then check that the **figures on the page match the API and the
data**. They catch the class of bug that unit tests miss: a broken selector, a
form that does nothing, a chart reading stale numbers, a counter that moved
twice.

## Run them

```bash
pip install -r requirements-dev.txt

# both servers have to be up
python manage.py runserver 127.0.0.1:8000
cd frontend && npm run dev          # :3000

# from the repo root
pytest tests/selenium -v
pytest tests/selenium -k "analytics" -v   # one user story
```

Headless Chrome is used; Selenium Manager downloads the matching driver on
first run. Override the defaults with `E2E_FRONTEND`, `E2E_BACKEND`,
`E2E_CUSTOMER`, `E2E_CUSTOMER_PASSWORD`, `E2E_ADMIN` and `E2E_ADMIN_PASSWORD`.

`conftest.py` signs in through the real forms and creates test data through
the API, so each story starts from a known state. The actions being tested
are still performed in the browser.

## The user stories

| Story | What the person does | What the test checks | File |
| --- | --- | --- | --- |
| US-01 | Signs in | Their name appears in the header and the drawer exists | `test_auth.py` |
| US-02 | Opens the sign-up form | Wilaya and daira are two select boxes; the dairas follow the wilaya | `test_auth.py` |
| US-03 | Signs out | The member pages ask for a sign-in again | `test_auth.py` |
| US-04 | Picks a region on a product | Only the durations of that region are offered | `test_storefront.py` |
| US-05 | Has a coupon | The code, the real price and the discounted price are shown | `test_storefront.py` |
| US-06 | Buys a package | The order lands in the history with the product and the package | `test_storefront.py` |
| US-07 | Opens the transaction history | Rows name the product · package, not "Order N" | `test_storefront.py` |
| US-08 | Opens their analytics | The cards and the three charts are there | `test_storefront.py` |
| US-09 | Switches the daily period | A month picker appears | `test_storefront.py` |
| US-10 | Signs in to the admin and opens Analytics | Every card and every chart is present, including *Owed by region* | `test_admin.py` |
| US-11 | Looks at *Owed by region* | The chart contains the amounts owed, in DA | `test_admin.py` |
| US-12 | Creates a region and a daira | The admin form saves them; the public pickers can use them | `test_admin.py` |
| US-13 | Creates a coupon with a percentage | The form accepts it and shows the price field | `test_admin.py` |
| US-14 | Uses the admin sidebar | Every model of the shop has an entry | `test_admin.py` |
| US-15 | Opens their analytics | The four cards equal the `/auth/me/` counters | `test_stats.py` |
| US-16 | Opens the admin analytics | The shop cards equal `/api/analytics/?scope=shop` | `test_stats.py` |
| US-17 | Switches the period | The chart has fewer buckets in the yearly period | `test_stats.py` |

## What is deliberately **not** in here

- The destructive path of the SSH tripwire (`ops/ssh-tripwire/`) — it belongs
  on the server and is verified with its own `--check` and `--test-line`
  flags, never in an automated browser test.
- Sending real email or pushing to GitHub — those are covered by the CI
  workflow and the git push itself.
- Resetting the database — the tests read and write through the running app;
  point them at a scratch database.

## Page objects

`pages.py` holds the selectors for the storefront and the admin. When a class
name or a label changes in the UI, edit it there once instead of in every
test.
