# Buttermelow — Boutique Bakery Storefront

**Buttermelow** (originally *Treats by Mimi*) is a modern, high-performance web storefront designed for a boutique dessert and celebration cake bakery. It provides an elegant, mouth-watering user experience for customers to browse treats, customize orders, and place checkout requests, alongside a secure administrative portal for the bakery owner to manage active orders, update the menu, and export sales records.

---

## Key Features

* **Customer Storefront Experience**:
  * **Interactive Menu**: Browse baked goods categorized by biscuit, muffins, cookies, or cakes, with instant category filter buttons.
  * **Persistent Cart**: Cookie-backed cart storage that preserves selections across visits.
  * **Fluid Checkout**: Form validation with pickup vs. delivery selectors, request notes, and direct contact buttons.
* **Bakery Owner Dashboard (`/owner`)**:
  * **Active & Archived Queues**: Easy tracking of new, preparing, or completed orders.
  * **Sales Analytics**: Real-time tracking of new orders, customer registrations, and total revenue.
  * **Status Updates**: Manage workflow states (New, Confirmed, Preparing, Ready, Completed, Cancelled).
  * **Cancelled Order Deletion**: Admin users can permanently delete cancelled orders. The system cleans up related items recursively (cascading database delete) and decrements the customer's order frequency count.
  * **Menu & Item Manager**: Add or edit items, upload custom cake/brownie photos, adjust pricing, and toggle item availability.
  * **Customer Directory**: Review customer order history, contact numbers, and activity logs.
  * **Excel Reports**: One-click download of all archived order records as spreadsheets.

---

## Visual & Aesthetic Enhancements

The storefront features a custom-designed visual layout built on modern, lightweight frontend principles:
* **Premium Typography**: Loaded Google Fonts—*Cormorant Garamond* for editorial serif headings and *Plus Jakarta Sans* for clean, contemporary geometric body copy.
* **Warm Bakery Color Palette**: Curated biscuit-cream backgrounds, cinnamon borders, deep espresso-chocolate text contrast, and rich velvet-berry active accents.
* **Frosted-Glass Navigation**: A sticky header with glassmorphism (`backdrop-filter`) that remains visible during scroll events.
* **Ken Burns Hero Animation**: A slow, immersive zoom-and-pan movement on the homepage hero image.
* **Interactive Micro-animations**: Underline slider states for navigation links, gentle 3D lifts and image zoom on product cards, elastic pulses on cart counter updates, elastic slide-in toast alerts, and input focus rings.
* **Form Shaking**: Form boundaries shake dynamically on checkout errors or invalid fields to provide clear user feedback.
* **Mobile-First Responsiveness**: Utilizes modern fluid CSS grids (`repeat(auto-fill, minmax(min(280px, 100%), 1fr))`) to dynamically scale layout elements from 320px mobile screens up to 4K monitors without layout breakage.

---

## Tech Stack

* **Backend**: Python 3.13, [FastAPI](https://fastapi.tiangolo.com/), Jinja2 Templates, SQLite3
* **Frontend**: Vanilla HTML5, Modern CSS Grid & Flexbox, Vanilla JavaScript (zero heavy frameworks)
* **Server**: Uvicorn (ASGI development server)
* **Reporting**: Openpyxl (Excel export utility)

---

## Project Structure

```
├── app.py                     # Core FastAPI application (routes, business logic)
├── database.py                # Database connection, schemas, and initial seeding
├── auth.py                    # Secure password hashing and verification
├── notifications.py           # SMS / Email notification triggers
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Customer base layout
│   ├── home.html              # Customer homepage
│   ├── menu.html              # Interactive menu catalog
│   ├── cart.html              # Checkout form and cart items
│   ├── order_success.html     # Post-purchase landing screen
│   ├── owner_base.html        # Owner dashboard base layout
│   ├── owner_login.html       # Owner sign-in page
│   ├── owner_dashboard.html   # Active and archived order lists & stats
│   ├── owner_menu.html        # Menu catalog manager (add, edit, hide items)
│   └── owner_customers.html   # Customer database and seen-timestamps
├── static/                    # Publicly served static assets
│   ├── css/
│   │   └── app.css            # Site-wide responsive stylesheet
│   ├── js/
│   │   ├── cart.js            # Cart cookie storage & badges
│   │   └── checkout.js        # Checkout payload handler
│   ├── img/                   # Decorative textures and background sliders
│   └── products/              # Seeded item photos
├── data/                      # SQLite database files
└── requirements.txt           # Python package requirements
```

---

## Installation & Setup

### 1. Pre-requisites
* Python 3.13+ installed on your system.

### 2. Set Up Virtual Environment
Navigate to the project root and activate a virtual environment:
```bash
# Create the environment (if not already done)
python -m venv .venv

# Activate on Mac/Linux
source .venv/bin/activate

# Activate on Windows
.venv\Scripts\activate
```

### 3. Install Dependencies
Install the required packages using the virtual environment's pip:
```bash
python -m pip install -r requirements.txt
```

*(Note: If building legacy dependencies, pip will use your virtual environment's compiler configurations natively).*

### 4. Start the Application
Start the Uvicorn development server:

```bash
# Run with code-reload enabled (ignoring virtualenv writes)
uvicorn app:app --reload --reload-exclude ".venv/*"
```

Once started, the application will be running locally at:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## Owner Dashboard Credentials

The administrative workspace is accessible at `/owner`.
* **URL**: `http://127.0.0.1:8000/owner`
* **Default Username**: `owner`
* **Default Password**: `*******` *(configurable via the `.env` file)*

---

## ☁️ Deployment on Render

This project is configured for easy, production-ready deployment on [Render](https://render.com) using **Render Blueprints** (`render.yaml`).

### 1. Setup a Persistent Disk (Critical for SQLite)
Since SQLite stores data in a local file (`treats_by_mimi.db`), and Render containers have an ephemeral filesystem, any database changes (orders, customers, menu updates) will be lost when the web service restarts or updates.

To prevent this:
* We mount a **Persistent Volume** disk to the container.
* The `render.yaml` defines a 1 GB disk named `buttermelow-data` mounted at `/data`.
* The `DATABASE_PATH` environment variable is configured as `/data/treats_by_mimi.db`, directing the application to write data directly to the persistent disk.

### 2. Configure Environment Variables
You should set the following environment variables in the Render Dashboard or during blueprint creation:

| Variable | Description | Default / Example |
|---|---|---|
| `ADMIN_USERNAME` | Owner dashboard username | `owner` |
| `ADMIN_PASSWORD` | Owner dashboard password | *A strong, secure password* |
| `SESSION_SECRET` | Secret key for signing session cookies | *A long random string* |
| `COOKIE_SECURE` | Set to `true` to restrict session cookies to HTTPS | `true` |
| `OWNER_PHONE` | Twilio notification recipient (owner) | `+91XXXXXXXXXX` |
| `TWILIO_ACCOUNT_SID` | Twilio account identifier | *Your Twilio Account SID* |
| `TWILIO_AUTH_TOKEN` | Twilio authentication token | *Your Twilio Auth Token* |
| `TWILIO_SMS_FROM` | Twilio purchased SMS number | `+1XXXXXXXXXX` |
| `TWILIO_WHATSAPP_FROM` | Twilio WhatsApp sandbox/business number | `whatsapp:+1XXXXXXXXXX` |

### 3. Deploying via GitHub
1. Push your repository to **GitHub**.
2. Go to **Render Dashboard** -> **Blueprints** -> **New Blueprint Instance**.
3. Connect your GitHub repository.
4. Render will automatically detect `render.yaml` and provision:
   * **Web Service**: Powered by `gunicorn` with high-performance `uvicorn` worker processes.
   * **Persistent Disk (1 GB)**: Linked to the Web Service for database storage.
5. Approve the blueprint creation. Render will deploy the site and provide a public URL (e.g. `https://buttermelow.onrender.com`).

### 4. Continuous Keep-Alive Cron Job (Free Tier)
Render's free tier web services automatically spin down (suspend) after 15 minutes of inactivity. When a new visitor accesses the suspended site, it can take 50 seconds or longer to spin back up.

To keep your storefront fast and warm:
1. We have included a GitHub Actions workflow in `.github/workflows/keep_alive.yml` that pings the application's `/health` endpoint every 14 minutes.
2. In your GitHub repository settings, go to **Settings** -> **Secrets and variables** -> **Actions**.
3. Create a new Repository Secret named `RENDER_APP_URL`.
4. Set its value to your Render app URL (e.g. `https://buttermelow.onrender.com`).

Once configured, GitHub will automatically ping your application on a regular schedule, preventing it from spinning down.


# Balaji_Buttermelow_Bakery
