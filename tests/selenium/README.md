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

The plan follows the roles of the shop: **visitor/customer**, **subadmin/staff**
and **admin**. `Scripted` means a test already drives the browser;
`Planned` means the story is specified here and still needs its test written.
The story IDs are stable — keep them when you add the missing test.

### Visitor and customer

| Story | What the person does | What the test checks | File | Status |
| --- | --- | --- | --- | --- |
| US-01 | Signs in | Their name appears in the header and the drawer exists | `test_auth.py` | Scripted |
| US-02 | Opens the sign-up form | Wilaya and daira are two select boxes; the dairas are fetched for the chosen wilaya | `test_auth.py` | Scripted (update to `daira` ids) |
| US-03 | Signs out | A spinner shows while the logout request runs, then the home page opens and member pages ask for a sign-in again | `test_auth.py` | Scripted (extend for loading/redirect) |
| US-04 | Picks a region on a product | Only the durations of that region are offered | `test_storefront.py` | Scripted |
| US-05 | Has a coupon | The code, the real price and the discounted price are shown | `test_storefront.py` | Scripted |
| US-06 | Buys a package | The order lands in the history with the product and the package | `test_storefront.py` | Scripted |
| US-07 | Opens the transaction history | Rows name the product · package, not "Order N" | `test_storefront.py` | Scripted |
| US-08 | Opens their analytics | The cards and the three charts are there | `test_storefront.py` | Scripted |
| US-09 | Switches the daily period | A month picker appears | `test_storefront.py` | Scripted |
| US-18 | Opens the catalog while unapproved | The review notice replaces the member pages; *Check again* and sign out work; approval notification unlocks the catalog | `test_account.py` | Planned |
| US-19 | Opens settings | Profile `PATCH /auth/me/` and password change work; invalid email/phone/current password show translated errors | `test_account.py` | Planned |
| US-20 | Opens the notification bell | Order updates are listed, new ones toast, and marking them as read empties the badge | `test_account.py` | Planned |
| US-21 | Opens credits | Balance, owed and granted totals match `/api/auth/credits/`; a free-spend account reads *Unlimited* | `test_storefront.py` | Planned |
| US-22 | Searches and filters orders | Debounced search, Sold/Not sold chips, recorded resale price and refreshed summary; masked code with copy button | `test_storefront.py` | Planned |
| US-23 | Buys an on-demand product that requires info | Buy now opens the popup, empty submit keeps it open with an error, filled submit places the order with the buyer info | `test_storefront.py` | Planned |
| US-24 | Follows an on-demand order | Placed → taken → in progress → has problems → delivered notifications appear in the bell; reports stay on the order | `test_storefront.py` | Planned |
| US-25 | Opens referrals | Referral link, percentage, total earned and earnings table match `/api/auth/referrals/`; `?ref=` is kept through signup | `test_storefront.py` | Planned |
| US-26 | Browses the catalog | Filter rail (All / On sale / category), pagination, category page and subcategory links | `test_storefront.py` | Planned |
| US-27 | Opens a product | Media gallery, promotion banner, related products, two searchable package dropdowns scoped by region | `test_storefront.py` | Planned |
| US-28 | Opens the home page | On-sale strip and card badges show the promoted price, struck original and end date | `test_storefront.py` | Planned |
| US-29 | Switches language | EN/FR/AR persist, `?lang=` overrides, and Arabic renders RTL | `test_account.py` | Planned |
| US-30 | Toggles the theme | Dark/light choice persists across a reload | `test_account.py` | Planned |
| US-31 | Opens the sidebar drawer | Credit balance, language and theme controls; closes via X, backdrop and Escape | `test_account.py` | Planned |
| US-32 | Uses feedback states | Buttons show spinner → tick, copy buttons report success, skeletons appear while data loads | `test_account.py` | Planned |

### Subadmin / staff

A subadmin is a staff account with `is_sub_admin=True` (which also sets
`is_staff`). These stories are about the on-demand work queue and the customer
operations a staff member performs — none of them are covered yet.

| Story | What the person does | What the test checks | File | Status |
| --- | --- | --- | --- | --- |
| US-33 | Is marked as subadmin | Saving the flag in the user admin sets `is_staff` and the account can sign in to `/admin/` | `test_staff.py` | Planned |
| US-34 | Opens on-demand processing | Open orders are listed with *Take this order*, status selector and report fields | `test_staff.py` | Planned |
| US-35 | Takes an on-demand order | It assigns the order to them, sets `in_progress`, clears the other admins' notifications and notifies the customer | `test_staff.py` | Planned |
| US-36 | Attaches a code to a demand order | The admin action attaches the next available code and the customer sees it | `test_staff.py` | Planned |
| US-37 | Flags a problem | A report is required, stays on the order and the customer is notified | `test_staff.py` | Planned |
| US-38 | Delivers the order | Status becomes delivered, the code reaches the customer and reports remain in the history | `test_staff.py` | Planned |
| US-39 | Grants a credit top-up | Creating a `Credit` row in the admin raises the balance and sends a `credit_topup` notification | `test_staff.py` | Planned |
| US-40 | Sets free spend on a customer | The storefront shows *Unlimited* and checkout writes a debt credit row instead of a negative balance | `test_staff.py` | Planned |
| US-41 | Approves or revokes an account | The user-admin checkbox and `POST /users/{id}/approval/` both work; a customer gets 403 on the API | `test_staff.py` | Planned |
| US-42 | Switches analytics to the whole shop | The staff-only switch changes `/auth/me/` counters to `/api/analytics/?scope=shop` figures | `test_staff.py` | Planned |
| US-43 | Opens the admin dashboard | The size cards show customers/categories/products/packages and link to Analytics | `test_staff.py` | Planned |
| US-44 | Copies a package code | The admin Copy and Claimed-by buttons put the full value on the clipboard and flip to *Copied!* | `test_staff.py` | Planned |
| US-45 | Checks stock worth | Adding/selling a code moves *Stock not sold* and *Codes in stock* on the cards | `test_staff.py` | Planned |

### Admin (catalog and configuration)

| Story | What the person does | What the test checks | File | Status |
| --- | --- | --- | --- | --- |
| US-46 | Manages the catalog | Categories, products, packages, package groups and codes can be created; slugs are generated from names | `test_admin.py` | Planned |
| US-47 | Creates a promotion | Percentage or discounted price fills the other field; product promotion wins over category; inactive/expired ones do not apply | `test_admin.py` | Planned |
| US-48 | Sets a coupon limit | `max_orders` closes the coupon once used up; a percentage follows the package price | `test_admin.py` | Planned |
| US-49 | Enables referrals | *Accepts referrals* and `referral_percentage` on the user admin drive the customer referral page | `test_admin.py` | Planned |
| US-50 | Builds the location tree | Creates a region, assigns wilayas later, adds dairas; the public pickers then offer them | `test_admin.py` | Scripted (extend US-12) |
| US-51 | Opens admin Analytics | Every card and chart is present, including *Owed by region* | `test_admin.py` | Scripted (US-10) |
| US-52 | Reads *Owed by region* | The chart contains the amounts owed in DA | `test_admin.py` | Scripted (US-11) |
| US-53 | Creates a percentage coupon | The admin form accepts the percentage and shows the price field | `test_admin.py` | Scripted (US-13) |
| US-54 | Uses the sidebar | Every shop model has an entry | `test_admin.py` | Scripted (US-14) |
| US-55 | Checks shop figures | The admin cards equal `/api/analytics/?scope=shop` | `test_stats.py` | Scripted (US-16) |
| US-56 | Narrows the admin period | Yearly has fewer buckets; month/year pickers work on the admin page too | `test_stats.py` | Scripted (US-17) |

### Coverage map

The plan is derived from the documented features in the root `README.md`:
Auth, Account approval, Credits/transactions/codes, On-demand order workflow,
Analytics, Stock, Coupons, Referrals, Regions/wilayas/dairas, Resale tracking,
Catalog, Promotions, Users, Admin dashboard, Analytics page and Pages.

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
