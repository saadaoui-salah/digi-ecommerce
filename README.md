# Digi Store

Digital-products storefront with an API-only Django backend and a Next.js frontend. Customers have a credit balance, browse categories, subcategories, and products, and see each product's packages and availability.

## Stack

- Django 6 + Django REST Framework
- JWT auth (`djangorestframework-simplejwt`) in httpOnly cookies
- Filtering/search with `django-filter`
- OpenAPI schema with `drf-spectacular`
- Unfold admin dashboard
- Next.js 16 (App Router) + React 19
- Tailwind CSS v4 + shadcn/ui + lucide-react

## Backend setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Admin: `http://127.0.0.1:8000/admin/`

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000`. It calls the API on the same hostname at port `8000` (`http://localhost:8000/api` when the page is opened on `localhost`).

To point it elsewhere, create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Keep the frontend and API on the same hostname (`localhost` for both, or `127.0.0.1` for both) so the browser sends the auth cookies. Extra backend origins can be added with `CORS_ALLOWED_ORIGINS`.

## Auth

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/auth/register/` | Sign up with `first_name`, `last_name`, `email`, `phone`, `password` (`username` optional) |
| POST | `/api/auth/token/` | Sign in; sets `access` and `refresh` cookies |
| POST | `/api/auth/token/refresh/` | Refresh the access cookie from the refresh cookie |
| POST | `/api/auth/logout/` | Clear both cookies |
| GET/PATCH | `/api/auth/me/` | Current user, including `credit`. `PATCH` updates `first_name`, `last_name`, `email`, `phone` |
| POST | `/api/auth/change-password/` | Change password with `current_password`, `new_password` (min 8), `confirm_password`; refreshes the auth cookies |
| GET | `/api/auth/orders/` | The customer's orders (paginated) |
| POST | `/api/auth/orders/` | Buy a package: creates the order, claims a code for instant packages, spends the credit |
| GET | `/api/auth/orders/summary/` | Total orders and total spent |
| GET | `/api/auth/notifications/` | The notifications of the signed-in user |
| POST | `/api/auth/notifications/` | Mark the notifications as read |
| POST | `/api/auth/orders/{id}/take/` | Staff takes an on-demand order (assigns it) |
| POST | `/api/auth/orders/{id}/status/` | Staff changes the status; `has_problems` needs a `report` object |
| GET/POST | `/api/auth/orders/{id}/reports/` | The reports of an order |
| GET | `/api/auth/transactions/` | The customer's credit history (paginated) |
| POST | `/api/auth/transactions/` | Staff only: create a credit movement for a customer |
| GET | `/api/auth/transactions/summary/` | Total credited, total debited, current balance |
| GET | `/api/auth/credits/` | The customer's credit rows (top-ups and free-spend debts) plus the balance, owed and granted totals |
| GET | `/api/codes/` | The codes the customer has claimed |
| POST | `/api/packages/{id}/deliver/` | Claim one unused code of an instant package |
| GET | `/api/packages/` | Packages with `codes_available` |

Register, login, and refresh set httpOnly cookies. The frontend sends them with `credentials: "include"`. API clients can still send `Authorization: Bearer <access>`.

Profile updates validate the email (case-insensitively unique) and the phone number (normalized, unique, 7–15 digits). Password changes verify the current password, require the two new passwords to match, and re-issue the auth cookies.

## Account approval

New accounts start **unapproved**. Until a staff member approves them, the customer only sees a "your account is being reviewed" notice (with a *Check again* button and sign out) instead of the catalog, orders, transactions and settings pages.

- The admin approves an account with the **is approved** checkbox on the customer page in the Django admin.
- `POST /api/auth/users/{id}/approval/` with `{"action": "approve"}` (or `revoke`) does the same from the API — staff only, customers get a 403.
- Approving (from either path) creates an `account_approved` notification, so the customer sees "Your account has been approved" in the header bell. Revoking does not notify.
- `/api/auth/me/` returns `is_approved`, which is what the frontend gates on.

## Credits, transactions and codes

- **Transactions** record every credit movement on a customer account. There are three kinds: `order` (the customer bought a product, credit goes down), `credit` (the customer bought credit, it goes up) and `refund` (it goes up again).
- **Orders** are the customer's purchases. Buying a package creates an order that is linked to the delivered code, spends the customer's credit, and writes the matching `order` transaction.
- **Package codes** are the deliverable `email|password` credentials of an instant package. Each package holds many codes; buying claims one of them and links it to the order. The **stock of an instant package is the number of codes it still holds** — the signals keep it in step (a new code adds one, a code that is sold or deleted takes one away). On-demand packages get a code attached later by staff — in the admin, use the "Attach the next available code" action — and keep the stock the admin fills in. Codes are never shown in full in the tables: the customer sees a masked value and copies the real one with the copy button. The staff codes list (**Admin → Catalog → Package codes**) has its own **Copy** column, which puts the full `email|password` on the clipboard and flips to *Copied!* for a moment; the **Claimed by** column has a copy button too, for the email of the customer who claimed the code.
- A package always follows the type of its product, so the instant / on-demand logic never drifts.

### Free spend and credit rows

The balance never reads negative — it is clamped at `0.00` for everyone.

- **Free spend** is a per-customer flag (**Admin → Users → Billing**). A flagged customer can buy with a zero balance: the storefront shows the balance as **Unlimited**, and the part of the price the balance could not cover is recorded as a **credit row** they owe instead of pushing the balance below zero. Everyone else still gets "Not enough credit".
- **Credit rows** (`Credit`) come in two kinds. A `debt` row is written by the checkout and records what a free-spend customer owes for an order. A `topup` row is written by staff in the admin (**Admin → Credits**) and adds the amount to the customer's balance — a `post_save` signal does that, so it only fires for rows the admin creates, never for the order side.
- A granted top-up also sends the customer a `credit_topup` notification, so they see it in the header bell.

The checkout locks the customer row (`select_for_update`) so two orders placed at the same moment cannot both spend the same balance or claim the same code.

`python manage.py seed_codes --per-package 8` tops up the demo codes, `python manage.py seed_transactions` creates demo credit movements, and `python manage.py seed_orders` creates demo orders (linked to codes).

## On-demand order workflow

An on-demand order walks through the admins:

1. **Placed** — the customer orders, the order is `pending`, every admin is notified and the customer gets a confirmation.
2. **Taken** — one admin takes the order: it is assigned to them (`assigned_to`), the status becomes `in_progress`, the other admins' notifications are cleared and the customer is told who is working on it.
3. **In progress** — the admin works on it and can attach the delivery code.
4. **Has problems** — the admin flags a problem; a **report** (`OrderReport`) is required, it stays attached to the order, and the customer is notified. A report is only a note: the title and the details the staff wrote down when the issue happened.
5. **Delivered** — the admin delivers the order; the customer gets the code. The reports stay on the order for the history.

Every status change creates a `Notification` for the customer, which shows up in the bell menu of the header. The staff side has a dedicated page: **Admin → Orders → On-demand processing** lists the open on-demand orders with *Take this order*, a status selector and the report fields.

### Buyer information on on-demand products

Some on-demand products need details from the buyer before staff can start (a username, a region, a brief). The admin ticks **Requires info** on the product (**Admin → Products**); it only applies to products whose type is *On demand*.

- The storefront shows a popup when the customer clicks **Buy now** — a short explanation, a required textarea, and *Cancel* / *Place the order*. The order is only sent once the field is filled in; an empty submit keeps the popup open with a translated error.
- The API enforces it too: `POST /api/auth/orders/` returns `{"buyer_info": ["Please provide the required information."]}` when the flag is set and the field is missing, so the popup can be reopened on a 400.
- The text is stored on `Order.buyer_info` and shown to staff under **Orders → Buyer information** in the admin, next to Handling and Resale.
- The flag is exposed as `requires_info` in the product serializers.

## Analytics

Every signed-in customer gets an **Analytics** page (frontend) with their own figures, and the staff sees the same page for the whole shop with one click. The admin dashboard shows the shop-wide figures.

**The figures come from two places:**

- **Counters on the rows** — `Product`, `Category`, `Package` and `User` each carry `sales_count`, `total_revenue`, `net_profit`, `total_benefit` and `pending_demand_orders`. The order signals move them whenever an order is placed, resold or deleted, so the page never walks the orders.
- **Pre-computed rows** — the daily, monthly and yearly breakdown lives in `SalesAggregate` (one row per customer, period, bucket and product). The daily rows are the base; the monthly and yearly rows are rolled up from them, so a month is always the sum of the days it contains. Every row belongs to a customer, so their figures are theirs alone; the figures of the shop are the sum of all of them.

**The three jobs** (`python manage.py …`) refresh the tables:

| Command | What it does |
| --- | --- |
| `aggregate_daily` | Recomputes the days that changed since the last run (a new order, a new resale price). `--full` rebuilds the whole history, `--lookback` widens the window. |
| `aggregate_monthly` | Rolls the daily rows up into the monthly ones. |
| `aggregate_yearly` | Rolls the daily rows up into the yearly ones. |
| `aggregate_sales` | Runs all three at once. |

**The charts:** a bar chart of the products bought by count, a line chart of the spend over time and a line chart of the benefits — what the customers earned by reselling (the resale price minus what they paid). The page has a daily / monthly / yearly switch, plus a *my figures / whole shop* switch for the staff.

**The axis of the charts follows the period:** a day is written "26 Oct", a month "Oct 2026" and a year "2026". The first and the last label lean away from the plot, so they never land on the value axis.

**The period can be narrowed down:** with the **daily** period a month picker appears — pick November and the charts show every day of that month; with the **monthly** period a year picker appears — pick 2026 and the charts show every month of that year. The same pickers are on the admin page.

**The cards** — net profit, total revenue, net profit %, orders and pending on-demand orders — read the counters of the products when the shop is shown and the counters of the account when a customer looks at their own figures. The **net profit %** is the net profit over the price of the packages sold: the margin of the shop.

**The profit** needs the cost of a package: fill in **Cost** on the package in the admin (**Admin → Catalog → Packages**) and the profit of every sale is the price minus that cost. The cost is copied onto the order when it is placed, so a later change to the package price does not rewrite the history.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/analytics/?period=day\|month\|year` | The figures of the page for the signed-in customer |
| GET | `/api/analytics/?scope=me\|shop` | Whose figures are shown; `shop` is for staff only |
| GET | `/api/analytics/?period=day&month=YYYY-MM` | The days of one month |
| GET | `/api/analytics/?period=month&year=YYYY` | The months of one year |

## Stock and the worth of the unsold stock

**The stock of an instant package is the number of codes it holds.** The signals on `PackageCode` keep it in step: a new code adds one, a code that is sold or deleted takes one away. Demand packages keep their own stock, which the admin fills in.

**The worth of the unsold stock** — the codes sitting in the store, at the price they would be sold for — is a field on the `User` model (`stock_worth`). The **quantity** of those codes is another one (`stock_quantity`). They are figures of the shop, so only the staff accounts carry them, and the admin page shows them on the **Stock not sold** and **Codes in stock** cards. The same signals move them: a code that is added adds its price and one to the count, a code that is sold takes them away. A staff account created later reads the figures from the packages, so it never starts with a wrong number.

## Coupons

A coupon is a discount for **one customer** on **one product**. The staff create it in the admin (**Admin → Accounts → Coupons**) and fill in **either a percentage or a discounted price** — the other one is filled in for them, from the price of the product.

- The **code is generated** (`DIGI4F9A2C`) and the customer sees it on the page of the product, with the real price, the price they pay and the copy button.
- **The discount is applied by the backend** when the order is placed, so the price on the page is the price that is charged.
- A coupon is used for **as many orders as its limit says** (`max_orders`); it closes itself when they are used up.
- A percentage follows the price of the package, so a 10% coupon is 10% off whatever they pick.

## Referrals

The staff tick **Accepts referrals** on the accounts that are willing to receive them (**Admin → Users → Referrals**) and say **how much of every referred order they earn** (`referral_percentage`).

- Every customer has a **referral code** (`REF0C5A4D9E`) and a **link** — `https://the-shop/?ref=REF0C5A4D9E`. The code travels in the query string of the link and is kept in a **cookie**, so a reload never loses it before the account is opened. The backend picks it up from the cookie when the account is created.
- The customer sees their link and the table of what they earned on **/referrals**.
- When a referred customer buys something, the referrer earns the percentage of the order: **what they owe is paid down first** and the rest goes to their balance. The earning is recorded as a `Transaction` of the kind *referral* and as a `Credit` row of the kind *referral*.

## Regions, wilayas and dairas

The country is divided the way it is divided in Algeria: a **region** holds **wilayas**, and every wilaya holds its **dairas**.

- Regions are **admin-only**: staff create them in the admin (**Admin → Accounts → Regions**) and assign wilayas to them later. They are never exposed to customers.
- The **sign-up form** asks for a wilaya and a daira (two select boxes). It fetches all wilayas first, then fetches the dairas of the selected wilaya.
- The admin analytics page shows an **Owed by region** bar chart: what the free-spend customers of every region still owe the shop.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/auth/wilayas/` | All active wilayas (no regions, no nested dairas) |
| GET | `/api/auth/dairas/?wilaya=<id>` | The dairas of one wilaya |
| GET | `/api/auth/referrals/` | The referral program of the customer: their code, their total and their earnings |

## Codes and simultaneous orders

A code is delivered once: `Order.code` is a one-to-one field, so the database itself refuses to give the same code to two orders. On top of that, claiming a code is a **conditional UPDATE** — `UPDATE … WHERE is_used = False` — so only one of two customers arriving at the same moment can take it; the other one is told the package is sold out. This works on SQLite and on PostgreSQL (where `select_for_update` also applies). The stock and its worth move once, for the customer who actually got the code.

## Resale tracking

Customers can record how much they resold an order for, then search and filter their orders around it.

| Method | Endpoint | Description |
| --- | --- | --- |
| PATCH | `/api/auth/orders/{id}/sold/` | Set the resale price; `{"sold_price": null}` clears it |
| GET | `/api/auth/orders/?search=` | Matches product, package, sub package, category or order id |
| GET | `/api/auth/orders/?sold=true\|false` | Only orders with (or without) a recorded resale price |
| GET | `/api/auth/orders/summary/` | Adds `total_sold` and `sold_count` |

`Order` carries `sold_price`, `sold_at` and the `is_sold` property; the price must be `>= 0` and only the owner can change it (anyone else gets a 404). It never affects credit or transactions — it is purely a resale record, and it is visible in the admin under **Orders → Resale**.

## Catalog

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/categories/` | List categories |
| GET | `/api/categories/{slug}/` | Category detail (numeric id also works) |
| GET | `/api/products/` | List products |
| GET | `/api/products/{slug}/` | Product detail with packages, `package_groups` and the related products (numeric id also works) |

Category filters: `?root=true`, `?parent=<id>`, `?search=`, `?ordering=name`.

Product filters: `?category=<id>`, `?category_slug=`, `?type=demand|immediate`, `?available=true`, `?promoted=true|false`, `?min_price=`, `?max_price=`, `?search=`, `?ordering=name|price_from|created_at`.

Products and packages are typed as `demand` or `immediate`. Prices are filtered by each product's cheapest active package. All prices are Algerian dinar (`DA`). Product detail includes active packages with `type`, `price`, `stock`, and `is_available`, plus `images` (gallery) and `video`. Categories expose `image` and `products_count` (children included); `?category=` / `?category_slug=` also match products in child categories.

Some products use two levels of packages: a `PackageGroup` (for example a country like United States) that holds duration packages (1 Month, 2 Months, …). Grouped groups and their packages are nested in `package_groups` on the product detail; ungrouped packages stay in the flat `packages` list. Groups are managed in the admin (Package groups + product inline) and package names are unique within a group.

Slugs for categories and products are generated from the name when left blank, with a numeric suffix when needed.

## Promotions

`Promotion` is its own model: an admin picks a target (a product **or** a whole category), fills in **either** the percentage **or** the discounted price, and `save()` calculates the other field from the original price. A product promotion wins over a category promotion. Optional `starts_at` / `ends_at` window plus `is_active`; the promotion only applies while it is current.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/promotions/` | Running promotions (`?product=`, `?category=`) |
| GET | `/api/products/?promoted=true` | Only the products a current promotion applies to |
| GET | `/api/admin/...` | Managed under **Catalog → Promotions** in the Django admin |

Every product response carries `price_from` (original), `price_current` (discounted) and a `promotion` object (`percentage`, `discounted_price`, `ends_at`); packages carry `price_current` too. Checkout charges `price_current` — `POST /api/auth/orders/` validates credit against the promoted price and writes the order + transaction at that amount.

## Catalog demo data

Migration `0005_seed_game_pass` creates a Gaming category and a Game Pass product with four country groups (United States, Turkey, Algeria, India), each with monthly durations. Migration `0007_seed_extras` adds 12 more products across categories so pagination is demonstrable. Existing demo data remains untouched; run `python manage.py migrate` to apply.

`python manage.py seed_media` fills demo media: a gradient cover image for every category and product, two gallery images per product, and a short MP4 demo video per product (requires the `ffmpeg` executable on PATH). The command is idempotent and skips rows that already have media. Media is served from `/media/`.

## Users

Customers have a `credit` balance. Staff can be marked `is_sub_admin` in the admin for handling on-demand orders; this sets `is_staff` automatically.

## Admin dashboard

The admin dashboard shows the size of the shop at a glance — the customers, the categories, the products and the packages — with a link to the analytics page.

**The sidebar carries every model of the shop**, grouped the way the dashboard lists them and folding down on a click: *Shop* (categories, products, packages, package groups, package codes, promotions), *Customers* (users, orders, transactions, credits, notifications, order reports), *Analytics* (the overview, the runs and the aggregates) and *Authentication and Authorization* (groups). The groups are open by default — the sidebar template is Unfold's own with the open state flipped.

## The analytics page of the admin

**Admin → Analytics** (`/admin/analytics/`) holds the figures of the shop: the cards, the bar chart of the products bought by count and the two lines (spend and benefits). A daily / monthly / yearly switch picks the period of the charts.

**The cards:**

- **Net profit** — what the shop earned: the price of the packages sold minus their cost.
- **Total revenue** — what the customers paid.
- **Net profit %** — the net profit over the price of the packages sold: the margin of the shop.
- **Orders** — how many orders were placed.
- **Pending on demand** — how many on-demand orders still wait to be delivered.
- **Stock not sold** — the worth of the codes that are still waiting to be sold.
- **Codes in stock** — how many of those codes are left.
- **Benefits** — what the customers earned by reselling.

**Every figure is a counter, never a calculation over the orders.** The signals move them as the orders come in:

| Counter | Where it lives | Moved by |
| --- | --- | --- |
| `total_revenue`, `net_profit`, `net_profit_percentage`, `total_benefit`, `orders_count`, `pending_demand_orders` | `User` | the order signals, when an order is placed, resold or deleted |
| the same counters | `Product`, `Category`, `Package` | the same order signals, so the analytics reads them from the product |
| `stock_worth`, `stock_quantity` | `User` (the staff accounts) | the code signals, when a code is added or sold |
| `stock` | `Package` (instant packages) | the code signals, the same way |
| the daily / monthly / yearly rows | `SalesAggregate` | the aggregation jobs |

The net profit percentage follows the two figures it is made of, so the page never divides anything. The chart rows are pre-computed by the jobs and read as they are.

**The indexes:** every column the admin searches in or sorts by carries an index — the names, the emails and the phones of the users, the names of the products, categories and packages, the codes of the packages, the statuses and the dates of the orders, the movements and the notifications. The flags (`is_staff`, `is_approved`, `is_active`, …) are left out: they hold a handful of values each, so an index on them would not tell the database much.

## Pages

- `/` — hero with the character carousel, how it works, a horizontal category rail (small rounded icon tiles with a short label under each), and an **On sale this week** strip when promoted products exist. Categories are only shown to signed-in users; the hero CTA gives signed-out users a locked panel.
- `/auth` — combined sign-in and sign-up page. There is no checkout flow yet.
- `/catalog` — full product listing with an icon-tile filter rail (**All products**, **On sale** and one tile per category), and pagination (signed-in only; requires the API for data). The filter is a single choice: picking a category clears **On sale**, and picking **On sale** clears the category — so a category always lists its own products and **On sale** always lists every promoted product.
- `/categories/[slug]` — category page with its related products and subcategory links (signed-in only).
- `/products/[slug]` — product detail with a media gallery (video plus image thumbnails), an amber promotion banner (badge, discounted vs. struck-through price, amount saved, end date), description, packages, and a "You may also like" section below the packages panel. The package panel holds **two searchable dropdowns** — one for the package group (the region) and one for the package (the duration) — with a sticky buy panel below them. The whole page is one API call: the product, its media, its packages, its regions with their durations and the related products all travel together. The region only says how many durations it holds; the price belongs to the duration, so the duration list shows the durations of the chosen region only. A product without packages has no dropdowns at all. If the product is on demand and flagged **Requires info**, clicking **Buy now** opens a popup asking for the buyer's details before the order is placed.
- `/orders` — the customer's orders with summary cards (total orders, total spent, **total sold for**), a debounced search box, **All / Sold / Not sold** filter chips and a paginated table. Product, package and sub package share one column; a delivered order shows its code masked (`game*****`) with a copy button next to it, while an on-demand order shows "Delivered once ready" until staff attach the code. The **Sold for** column records the resale price inline: a dashed *Record sale* button opens a small input with confirm/cancel, a recorded sale shows as a green pill (tap to edit or clear), and the totals refresh once it saves.
- `/transactions` — the credit history with summary cards (total credited, total debited, current balance) and a table of every movement.
- `/credits` — the credit rows: summary cards (current balance, owed, granted) and a table of every top-up the admin granted and every free-spend debt. A free-spend customer with a zero balance reads **Unlimited** instead of a number.
- `/referrals` — the referral program of the customer: their link (with the code), the percentage they earn, what they earned in total and the table of every earning — the customer who was referred, the order and the amount.
- `/analytics` — the figures of the signed-in customer: the net profit, total revenue, net profit %, order count and pending on-demand orders, then a bar chart of the products bought by count, a line chart of the spend and a line chart of the benefits — with a daily / monthly / yearly switch. The staff also get a *my figures / whole shop* switch.
- `/settings` — account details (username, email, phone, credit balance) plus two forms: profile information (`PATCH /api/auth/me/`) and password change (`POST /api/auth/change-password/`).

## Frontend details

- **Theme:** CSS-only dark/light switching. A hidden `#theme-dark` checkbox drives a Tailwind `dark` variant with `:has()`, true black (`#000000`) in dark mode. On a first visit there is no stored choice, so an inline script in the layout picks dark or light from `prefers-color-scheme` while the HTML is still parsing (no flash) and keeps following the system until the visitor toggles the switch. A manual toggle is saved to `localStorage` and wins on later visits.
- **Languages:** English, French, and Arabic with full RTL layout and an Arabic font. The choice persists in `localStorage`; `?lang=en|fr|ar` overrides it. Flags are inline SVG (Windows does not render emoji flags).
- **Auth validation:** Email and phone errors appear while typing through native `pattern` attributes and CSS `:invalid` — red borders plus translated inline messages, no JavaScript for the field state. Server errors remain translated in the form alert.
- **Character carousel:** Kratos, Lara Croft, and Master Chief, with manual previous/next arrows, dots, a counter, direction-aware animations, RTL-aware direction, and reduced-motion support.
- **Sidebar drawer:** Credit balance, language switcher, theme toggle, and sign-out live in a side drawer opened from the header menu button (signed-in visitors only). Showing, hiding, and the slide animation are pure CSS: a hidden `#sidebar-open` checkbox toggled by a `<label>` drives the state through `:has()`, and the drawer transitions the `translate` property (left in LTR, right in RTL). It closes via the menu button, the X, the backdrop, or Escape.
- **Language dropdown:** Also CSS-only — a hidden `.dropdown-peer` checkbox drives the open state through sibling selectors, so no JavaScript is involved in showing or hiding the list. The month and year pickers of the analytics page use the same dropdown (`components/ui/select-menu.tsx`): the CSS opens and closes the list, JavaScript only applies the choice.
- **Package dropdowns:** The product page picks a package group and a package with two searchable dropdowns (`components/ui/search-select.tsx`). The open state is CSS-only too (a hidden `.search-peer` checkbox); JavaScript only filters the list as the user types and unchecks the box once an option is picked. The duration list is scoped to the chosen region, but the search box looks through every package of the product.
- **Time zone:** The whole app runs on Algerian time (`Africa/Algiers`, UTC+1 with no daylight saving). The database stores the local wall clock itself — a row written at 15:10 is read back as 15:10 — and the frontend formats every date through `lib/datetime.ts`, which pins the zone to Algeria whatever the browser is set to.
- **Loading skeletons:** Product grids, category grids, the data tables (orders, transactions, credits) and the product detail view render skeleton placeholders while their API requests are in flight (`components/skeletons.tsx`).
- **Account approval:** Accounts waiting for an admin approval see a review notice instead of the member pages.
- **Notifications:** A bell in the header lists the order updates (polls every 20s and toasts new ones) so the customer follows the on-demand work. The dropdown is pure CSS: a hidden checkbox toggled by its label opens and closes the panel with a fade, and JavaScript only marks the notifications as read and closes it when the click lands outside.
- **Feedback:** Sign-in, sign-up and buy buttons show a spinner while the request runs, disable themselves, and swap to an animated tick when it succeeds. Toasts confirm the result (account created, order placed, code copied). Copy buttons use the clipboard API with a fallback and always report the outcome.
- **Autofill:** Every form field carries a canonical `name` and `autocomplete` token (`given-name`, `family-name`, `email`, `tel`, `new-password`, `current-password`) so browsers can autofill the forms.
- **Promotions:** Product cards show an amber badge (`-25%` / `Sale`) with the discounted price and the original struck through; the detail page adds a banner with the amount saved and the end date. Grouped packages show the discounted price per duration with the original above it. All rendered from the API — no hardcoded discounts.
- **Category rail:** The home page and the catalog filter row use one shared component (`components/category-rail.tsx`) — a horizontal rail of small rounded icon tiles with a truncated label under each, active state ringed in sky blue, with skeletons while the categories load. It scrolls horizontally on small screens and wraps on large ones.
- **Orders search and resale:** The orders search box is debounced (300 ms) inside a `role="search"` form that prevents default; the Sold / Not sold chips and the inline sale editor all call the API and refresh the summary, confirming with a toast. Empty search results offer a reset back to *All*.
- **Currency:** All prices and credit balances are formatted as `X DA`.
- **Character artwork:** Render assets are used for personal, non-commercial demo purposes only. Characters and games are trademarks of their respective owners.

## Commands

Backend:

```bash
python manage.py test
python manage.py check
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
npm start
```

## GitHub Actions

Two workflows live in `.github/workflows/`:

- **`tests.yml`** — the gate. It runs on every push to `main` and `staging` and on every pull request aimed at them:
  - *Django tests* — installs `requirements.txt`, runs `manage.py check`, checks that no migration is missing (`makemigrations --check`) and runs the test suite.
  - *Frontend checks* — `npm ci`, `npm run lint`, `npx tsc --noEmit` and `npm run build`.
- **`deploy.yml`** — the deploy. It waits for the `Tests` workflow of the same branch and only runs when it finished green, so nothing reaches the server before the tests passed. It pulls the branch on the server, installs the dependencies, applies the migrations, collects the static files, builds the frontend and restarts the two services.

The deploy reads its secrets from the environment of the branch (`staging` or `main`), so the two can point at different servers:

| Secret | What it is |
| --- | --- |
| `SSH_HOST` | The address of the server |
| `SSH_USER` | The user that deploys |
| `SSH_KEY` | The private key of that user |
| `SSH_PORT` | The port of the SSH server (22 by default) |
| `SSH_PATH` | The folder of the project on the server |

The services it restarts are `digi` (the Django app) and `digi-frontend` (the Next.js app).

## API schema

- OpenAPI YAML: `/api/schema/`

JSON is the only renderer; there is no browsable HTML API.
