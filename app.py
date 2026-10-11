import os, sqlite3, json, secrets
from datetime import datetime
from functools import wraps
from flask import Flask, render_template,render_template_string,request, redirect, url_for, session, flash, render_template, abort
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.environ.get('NS_INSURANCE_DB', os.path.join(BASE_DIR, 'ns_insurance.db'))
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY must be configured")
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_PERMANENT=False,
    PERMANENT_SESSION_LIFETIME=900
)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD must be configured")
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

PROVIDERS = ['Tata AIA Life Insurance', 'LIC', 'Care Health Insurance']
LIFE_REQUIREMENTS = ['Term Insurance', 'Savings Plan', 'Investment Plan', 'Child Plan', 'Retirement Plan', 'Other']
HEALTH_REQUIREMENTS = ['Family Floater Health Insurance', 'Individual Health Insurance', 'Senior Citizen Health Insurance', 'Other']


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            full_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            city TEXT NOT NULL,
            provider TEXT NOT NULL,
            insurance_type TEXT NOT NULL,
            requirement TEXT NOT NULL,
            coverage_amount TEXT,
            payment_frequency TEXT,
            members_json TEXT,
            existing_insurance TEXT,
            notes TEXT,
            status TEXT NOT NULL DEFAULT 'New'
        )''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS insurance_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            insurance_type TEXT NOT NULL,
            website_url TEXT,
            logo_url TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS insurance_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            benefits TEXT,
            eligibility TEXT,
            exclusions TEXT,
            brochure_url TEXT,
            is_published INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES insurance_companies(id)
        )''')

        conn.executemany(
            '''INSERT OR IGNORE INTO insurance_companies
               (name, insurance_type, website_url, logo_url, is_active, created_at)
               VALUES (?, ?, ?, ?, 1, ?)''',
            [
                (
                    'Tata AIA Life Insurance',
                    'Life Insurance',
                    'https://www.tataaia.com/',
                    '',
                    datetime.now().strftime('%Y-%m-%d %H:%M')
                ),
                (
                    'LIC',
                    'Life Insurance',
                    'https://licindia.in/',
                    '',
                    datetime.now().strftime('%Y-%m-%d %H:%M')
                ),
                (
                    'Care Health Insurance',
                    'Health Insurance',
                    'https://www.careinsurance.com/',
                    '',
                    datetime.now().strftime('%Y-%m-%d %H:%M')
                )
            ]
        )

init_db()


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login', next=request.path))
        return fn(*args, **kwargs)
    return wrapper


def safe_text(value, max_len=160):
    return (value or '').strip()[:max_len]

BASE = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="NS Insurance helps you enquire about life insurance from Tata AIA and LIC, and health insurance from Care Health Insurance.">
<title>{{ title }} | NS Insurance</title><link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}"></head><body>
<header class="topbar"><a class="brand" href="{{ url_for('home') }}"><span class="brand-mark">NS</span><span><b>NS Insurance</b><small>Secure Today, Brighter Tomorrow</small></span></a><button class="menu-toggle" aria-label="Toggle navigation" onclick="document.querySelector('.nav-links').classList.toggle('open')">☰</button><nav class="nav-links"><a href="{{ url_for('home') }}#home">Home</a><a href="{{ url_for('home') }}#plans">Our Providers</a><a href="{{ url_for('home') }}#why-us">Why Choose Us</a><a href="{{ url_for('home') }}#quote">Get a Quote</a></nav><a class="button button-small" href="tel:9347684905">Call 9347684905</a></header>
{% with messages = get_flashed_messages(with_categories=true) %}{% if messages %}<div class="flash-wrap">{% for category, message in messages %}<div class="flash {{ category }}">{{ message }}</div>{% endfor %}</div>{% endif %}{% endwith %}
{{ body|safe }}
<footer class="footer"><div><a class="brand footer-brand" href="{{ url_for('home') }}"><span class="brand-mark">NS</span><span><b>NS Insurance</b><small>Personal guidance for your insurance needs</small></span></a><p>Enquiries and assistance for selected life and health insurance products.</p></div><div><b>Contact</b><p><a href="tel:9347684905">9347684905</a></p><p><a href="https://wa.me/919347684905" target="_blank" rel="noopener">WhatsApp us</a></p></div><div><b>Quick links</b><p><a href="{{ url_for('home') }}#plans">Insurance providers</a></p><p><a href="{{ url_for('home') }}#quote">Request a quote</a></p><p><a href="{{ url_for('admin_login') }}">Admin login</a></p></div><p class="disclaimer">NS Insurance is an independent insurance enquiry and assistance website, not the official website of Tata AIA, LIC, or Care Health Insurance. Product availability, premiums, eligibility, benefits and claims are subject to the insurer's policy terms and assessment. Do not submit sensitive medical records through this form.</p><div class="copyright">© {{ year }} NS Insurance. All rights reserved.</div></footer>
<script src="{{ url_for('static', filename='main.js') }}"></script></body></html>'''

HOME_BODY = '''<main><section class="hero" id="home"><div class="hero-copy"><span class="eyebrow">LIFE & HEALTH INSURANCE GUIDANCE</span><h1>Protect what matters most.<br><em>Plan for tomorrow.</em></h1><p>Explore selected life and health insurance options with personal guidance from NS Insurance.</p><div class="hero-actions"><a class="button" href="#quote">Request a Free Quote <span>→</span></a><a class="button button-ghost" href="tel:9347684905">Call us: 9347684905</a></div><div class="trust-points"><span>✓ Personal guidance</span><span>✓ Clear information</span><span>✓ Enquiry follow-up</span></div></div><div class="hero-art"><div class="sun"></div><div class="art-card"><div class="family-icon">♡</div><h3>Protection for every stage</h3><p>Life plans and family health cover enquiries in one place.</p><div class="art-line"><span></span><span></span><span></span></div></div><div class="floating-badge">Your future<br><b>matters</b></div></div></section>
<section class="provider-section section" id="plans"><div class="section-heading"><span class="eyebrow">OUR INSURANCE PROVIDERS</span><h2>Choose the right place to start</h2><p>We currently promote enquiries for these three providers only.</p></div><div class="provider-grid"><article class="provider-card tata"><div class="provider-logo logo-tata">TATA <span>AIA</span></div><span class="tag">LIFE INSURANCE</span><h3>Tata AIA Life Insurance</h3><p>Explore life protection, savings and long-term planning options.</p><a href="#quote" class="text-link" data-select-provider="Tata AIA Life Insurance">Enquire about Tata AIA <span>↗</span></a></article><article class="provider-card lic"><div class="provider-logo logo-lic">LIC</div><span class="tag">LIFE INSURANCE</span><h3>Life Insurance Corporation of India</h3><p>Ask about available life insurance and future-planning options.</p><a href="#quote" class="text-link" data-select-provider="LIC">Enquire about LIC <span>↗</span></a></article><article class="provider-card care"><div class="provider-logo logo-care">care<span> health insurance</span></div><span class="tag">HEALTH INSURANCE</span><h3>Care Health Insurance</h3><p>Share details for four people and enquire about suitable health cover.</p><a href="#quote" class="text-link" data-select-provider="Care Health Insurance">Enquire about Care Health <span>↗</span></a></article></div></section>
<section class="quote-section section" id="quote"><div class="quote-intro"><span class="eyebrow">LET'S GET STARTED</span><h2>Request a free quote</h2><p>Tell us a little about what you need. We’ll use your enquiry details to follow up and discuss suitable options.</p><div class="quote-note"><span>✦</span><div><b>One form, the right questions</b><p>The form adapts to life or health insurance so you only see relevant fields.</p></div></div><div class="contact-mini"><span class="contact-icon">☎</span><div><small>Prefer to talk?</small><b>9347684905</b></div></div></div>
<form class="quote-form" id="quote-form" method="post" action="{{ url_for('submit_enquiry') }}"><input type="hidden" name="csrf_token" value="{{ csrf_token }}"><div class="form-heading"><span class="step">01</span><div><h3>Your enquiry</h3><p>Fields marked * are required.</p></div></div><div class="form-grid"><label>Full name *<input name="full_name" required maxlength="100" autocomplete="name" placeholder="Enter your full name"></label><label>Mobile number *<input name="mobile" required inputmode="tel" pattern="[0-9 +()-]{10,16}" maxlength="16" autocomplete="tel" placeholder="10-digit mobile number"></label><label>City *<input name="city" required maxlength="100" autocomplete="address-level2" placeholder="Your city"></label><label>Insurance provider *<select name="provider" id="provider" required><option value="">Select provider</option><option>Tata AIA Life Insurance</option><option>LIC</option><option>Care Health Insurance</option></select></label></div>
<div id="life-fields" class="conditional-fields" hidden><div class="subheading"><span class="step">02</span><div><h3>Life insurance details</h3><p>Tell us what kind of plan you want to explore.</p></div></div><div class="form-grid"><label>Insurance requirement *<select name="life_requirement" id="life_requirement"><option value="">Select requirement</option><option>Term Insurance</option><option>Savings Plan</option><option>Investment Plan</option><option>Child Plan</option><option>Retirement Plan</option><option>Other</option></select></label><label>Date of birth / age *<input name="life_age" id="life_age" maxlength="40" placeholder="e.g. 15/08/1990 or 35 years"></label><label>Desired coverage amount<select name="coverage_amount"><option value="">Select amount</option><option>₹10 lakh</option><option>₹25 lakh</option><option>₹50 lakh</option><option>₹1 crore</option><option>Need guidance</option></select></label><label>Premium payment frequency<select name="payment_frequency"><option value="">Select frequency</option><option>Monthly</option><option>Quarterly</option><option>Half-yearly</option><option>Yearly</option><option>Need guidance</option></select></label></div></div>
<div id="health-fields" class="conditional-fields" hidden><div class="subheading"><span class="step">02</span><div><h3>Family health insurance details</h3><p>Choose the family combination and enter details for all four members.</p></div></div><label class="full-label">Who needs to be covered? *<select name="family_type" id="family_type"><option value="">Choose family combination</option><option value="2 Adults + 2 Children">2 Adults + 2 Children</option><option value="4 Adults">4 Adults</option></select></label><div id="members-container" class="members-grid"></div><div class="form-grid"><label>Preferred coverage amount<select name="health_coverage"><option value="">Select amount</option><option>₹5 lakh</option><option>₹10 lakh</option><option>₹15 lakh</option><option>₹25 lakh</option><option>Need guidance</option></select></label><label>Existing health insurance? *<select name="existing_insurance" id="existing_insurance"><option value="">Select</option><option>Yes</option><option>No</option><option>Not sure</option></select></label></div></div>
<label class="full-label">Additional information (optional)<textarea name="notes" rows="3" maxlength="1000" placeholder="Anything else you'd like us to know? Please do not include medical records or sensitive health details."></textarea></label><label class="consent"><input type="checkbox" name="consent" value="yes" required><span>I agree that NS Insurance may contact me about this enquiry. I have read the privacy notice in the website footer.</span></label><button type="submit" class="button submit-button">Get a Free Quote <span>→</span></button><p class="form-footnote">Submitting this form does not purchase a policy or guarantee eligibility, premium or claim approval.</p></form></section>
<section class="why-section section" id="why-us"><div class="section-heading"><span class="eyebrow">WHY NS INSURANCE</span><h2>Guidance that puts you first</h2><p>We help you understand the next steps without making promises about policy outcomes.</p></div><div class="benefit-grid"><article><span class="benefit-icon">✧</span><h3>Personalized guidance</h3><p>Discuss your needs and get help understanding relevant options.</p></article><article><span class="benefit-icon">⇄</span><h3>Compare suitable plans</h3><p>Review available benefits, costs and terms before deciding.</p></article><article><span class="benefit-icon">✓</span><h3>Application support</h3><p>Get guidance on the application steps and documents required.</p></article><article><span class="benefit-icon">♡</span><h3>Claim-related guidance</h3><p>Understand where to find claim processes and insurer support.</p></article><article><span class="benefit-icon">◎</span><h3>Transparent communication</h3><p>Clear explanations of terms, exclusions and next steps.</p></article><article><span class="benefit-icon">☏</span><h3>Easy follow-up</h3><p>Contact us by phone or WhatsApp for your enquiry.</p></article></div></section>
<section class="closing-cta"><div><span class="eyebrow">START WITH A CONVERSATION</span><h2>Your next step can start today.</h2><p>Talk with NS Insurance about Tata AIA, LIC or Care Health Insurance enquiries.</p></div><div class="hero-actions"><a class="button button-light" href="#quote">Request a Quote</a><a class="button button-outline-light" href="https://wa.me/919347684905" target="_blank" rel="noopener">WhatsApp us</a></div></section></main>'''

LOGIN_BODY = '''<main class="admin-page"><section class="login-card"><span class="eyebrow">NS INSURANCE</span><h1>Admin login</h1><p>Sign in to review and manage customer enquiries.</p><form method="post" action="{{ url_for('admin_login') }}"><input type="hidden" name="csrf_token" value="{{ csrf_token }}"><label>Username<input name="username" required autocomplete="username"></label><label>Password<input type="password" name="password" required autocomplete="current-password"></label><button class="button submit-button" type="submit">Sign in</button></form><p class="form-footnote">For local testing only, default credentials are shown in README.md. Change them before any deployment.</p><a class="text-link" href="{{ url_for('home') }}">← Back to website</a></section></main>'''

DASH_BODY = '''<main class="admin-dashboard"><div class="dashboard-top"><div><span class="eyebrow">PRIVATE ADMIN AREA</span><h1>Enquiry dashboard</h1><p>Manage incoming life and health insurance enquiries.</p></div><div class="dashboard-actions"><a class="button button-ghost" href="{{ url_for('export_csv') }}">Export CSV ↓</a><a class="button button-ghost" href="{{ url_for('manage_policies') }}">Manage Policies</a><form method="post" action="{{ url_for('admin_logout') }}"><input type="hidden" name="csrf_token" value="{{ csrf_token }}"><button class="button button-small" type="submit">Log out</button></form></div></div><div class="stats-grid"><div class="stat-card"><small>Total enquiries</small><strong>{{ counts.total }}</strong></div><div class="stat-card"><small>New enquiries</small><strong>{{ counts.new }}</strong></div><div class="stat-card"><small>Life insurance</small><strong>{{ counts.life }}</strong></div><div class="stat-card"><small>Health insurance</small><strong>{{ counts.health }}</strong></div></div><form class="filter-bar" method="get"><input name="q" value="{{ q }}" placeholder="Search name, mobile or city"><select name="status"><option value="">All statuses</option>{% for s in statuses %}<option value="{{ s }}" {% if status == s %}selected{% endif %}>{{ s }}</option>{% endfor %}</select><button class="button button-small" type="submit">Filter</button><a class="text-link" href="{{ url_for('admin_dashboard') }}">Reset</a></form><div class="table-wrap"><table><thead><tr><th>ID / Date</th><th>Customer</th><th>Provider / Type</th><th>Requirement</th><th>Details</th><th>Status</th><th>Update</th></tr></thead><tbody>{% for e in enquiries %}<tr><td><b>#{{ e.id }}</b><small>{{ e.created_at }}</small></td><td><b>{{ e.full_name }}</b><small>{{ e.mobile }}</small><small>{{ e.city }}</small></td><td>{{ e.provider }}<small>{{ e.insurance_type }}</small></td><td>{{ e.requirement }}{% if e.coverage_amount %}<small>Cover: {{ e.coverage_amount }}</small>{% endif %}</td><td>{% if e.members %}<details><summary>View 4 members</summary><ul>{% for m in e.members %}<li>{{ m.name }} — {{ m.age }}, {{ m.relationship }}</li>{% endfor %}</ul></details>{% endif %}{% if e.notes %}<details><summary>Notes</summary><p>{{ e.notes }}</p></details>{% endif %}{% if e.existing_insurance %}<small>Existing insurance: {{ e.existing_insurance }}</small>{% endif %}</td><td><span class="status status-{{ e.status|lower|replace(' ', '-') }}">{{ e.status }}</span></td><td><form class="status-form" method="post" action="{{ url_for('update_status', enquiry_id=e.id) }}"><input type="hidden" name="csrf_token" value="{{ csrf_token }}"><select name="status" aria-label="Update status">{% for s in statuses %}<option {% if e.status == s %}selected{% endif %}>{{ s }}</option>{% endfor %}</select><button class="button button-small" type="submit">Save</button></form></td></tr>{% else %}<tr><td colspan="7" class="empty-state">No enquiries match these filters yet.</td></tr>{% endfor %}</tbody></table></div><p class="admin-note">Customer information is private. Only authorized staff should access this dashboard. Delete records when no longer needed and follow applicable privacy requirements.</p></main>'''

SUCCESS_BODY = '''<main class="success-page"><div class="success-card"><div class="success-icon">✓</div><span class="eyebrow">ENQUIRY RECEIVED</span><h1>Thank you, {{ customer_name }}.</h1><p>Your enquiry has been saved. NS Insurance can follow up using the contact details you provided.</p><div class="hero-actions"><a class="button" href="{{ url_for('home') }}">Back to home</a><a class="button button-ghost" href="https://wa.me/919347684905" target="_blank" rel="noopener">WhatsApp us</a></div><p class="form-footnote">This is an enquiry only, not an insurance application or policy confirmation.</p></div></main>'''

@app.before_request
def ensure_csrf():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(24)

@app.context_processor
def inject_globals():
    return {'year': datetime.now().year, 'csrf_token': session.get('csrf_token', '')}

@app.route('/')
def home():
    return render_template('page.html', title='Life & Health Insurance', body=render_template_string(HOME_BODY))

@app.route('/submit-enquiry', methods=['POST'])
def submit_enquiry():
    if not secrets.compare_digest(request.form.get('csrf_token', ''), session.get('csrf_token', '')):
        abort(400, 'Invalid form token. Please refresh and try again.')
    full_name = safe_text(request.form.get('full_name'), 100)
    mobile = safe_text(request.form.get('mobile'), 16)
    city = safe_text(request.form.get('city'), 100)
    provider = safe_text(request.form.get('provider'), 80)
    consent = request.form.get('consent') == 'yes'
    if not full_name or not mobile or not city or provider not in PROVIDERS or not consent:
        flash('Please complete all required fields and provide consent.', 'error')
        return redirect(url_for('home') + '#quote')
    digits = ''.join(ch for ch in mobile if ch.isdigit())
    if len(digits) < 10 or len(digits) > 13:
        flash('Please enter a valid mobile number.', 'error')
        return redirect(url_for('home') + '#quote')
    members = []
    notes = safe_text(request.form.get('notes'), 1000)
    coverage = ''
    frequency = ''
    existing = ''
    if provider in ('Tata AIA Life Insurance', 'LIC'):
        requirement = safe_text(request.form.get('life_requirement'), 80)
        age = safe_text(request.form.get('life_age'), 40)
        if requirement not in LIFE_REQUIREMENTS or not age:
            flash('Please complete the life insurance requirement and age fields.', 'error')
            return redirect(url_for('home') + '#quote')
        insurance_type = 'Life Insurance'
        coverage = safe_text(request.form.get('coverage_amount'), 40)
        frequency = safe_text(request.form.get('payment_frequency'), 40)
        requirement = requirement + ' (age: ' + age + ')'
    else:
        family_type = safe_text(request.form.get('family_type'), 40)
        if family_type not in ('2 Adults + 2 Children', '4 Adults'):
            flash('Please choose a family combination for health insurance.', 'error')
            return redirect(url_for('home') + '#quote')
        for i in range(1, 5):
            name = safe_text(request.form.get(f'member_{i}_name'), 100)
            age = safe_text(request.form.get(f'member_{i}_age'), 40)
            relationship = safe_text(request.form.get(f'member_{i}_relationship'), 50)
            gender = safe_text(request.form.get(f'member_{i}_gender'), 30)
            if not name or not age or not relationship:
                flash('Please enter the name, age and relationship for all four members.', 'error')
                return redirect(url_for('home') + '#quote')
            members.append({'name': name, 'age': age, 'relationship': relationship, 'gender': gender})
        if family_type == '2 Adults + 2 Children' and sum(1 for m in members if m['relationship'].lower() in ('child', 'son', 'daughter')) < 2:
            flash('For 2 Adults + 2 Children, mark two member relationships as Child, Son or Daughter.', 'error')
            return redirect(url_for('home') + '#quote')
        if family_type == '4 Adults' and any(m['relationship'].lower() in ('child', 'son', 'daughter') for m in members):
            flash('For 4 Adults, please choose adult relationships for all four members.', 'error')
            return redirect(url_for('home') + '#quote')
        insurance_type = 'Health Insurance'
        requirement = family_type
        coverage = safe_text(request.form.get('health_coverage'), 40)
        existing = safe_text(request.form.get('existing_insurance'), 30)
        if existing not in ('Yes', 'No', 'Not sure'):
            flash('Please tell us whether the family already has health insurance.', 'error')
            return redirect(url_for('home') + '#quote')
    with db() as conn:
        conn.execute('''INSERT INTO enquiries (created_at, full_name, mobile, city, provider, insurance_type, requirement, coverage_amount, payment_frequency, members_json, existing_insurance, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (datetime.now().strftime('%Y-%m-%d %H:%M'), full_name, mobile, city, provider, insurance_type, requirement, coverage, frequency, json.dumps(members, ensure_ascii=False) if members else '', existing, notes))
    return render_template('page.html', title='Enquiry received', body=render_template_string(SUCCESS_BODY, customer_name=full_name))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        if not secrets.compare_digest(request.form.get('csrf_token', ''), session.get('csrf_token', '')):
            abort(400, 'Invalid form token. Please refresh and try again.')
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if secrets.compare_digest(username, ADMIN_USERNAME) and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session.clear()
            session['admin_logged_in'] = True
            session['csrf_token'] = secrets.token_urlsafe(24)
            return redirect(request.args.get('next') if request.args.get('next', '').startswith('/admin') else url_for('admin_dashboard'))
        flash('Incorrect username or password.', 'error')
    return render_template('page.html', title='Admin login', body=render_template_string(LOGIN_BODY))

@app.route('/admin/logout', methods=['POST'])
@admin_required
def admin_logout():
    if not secrets.compare_digest(request.form.get('csrf_token', ''), session.get('csrf_token', '')):
        abort(400, 'Invalid form token. Please refresh and try again.')
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    q = safe_text(request.args.get('q'), 100)
    status = safe_text(request.args.get('status'), 30)
    statuses = ['New', 'Contacted', 'Follow-up', 'Completed']
    sql = 'SELECT * FROM enquiries WHERE 1=1'
    params = []
    if q:
        sql += ' AND (full_name LIKE ? OR mobile LIKE ? OR city LIKE ?)'
        params += [f'%{q}%'] * 3
    if status in statuses:
        sql += ' AND status = ?'
        params.append(status)
    sql += ' ORDER BY id DESC LIMIT 500'
    with db() as conn:
        rows = conn.execute(sql, params).fetchall()
        total = conn.execute('SELECT COUNT(*) FROM enquiries').fetchone()[0]
        new_count = conn.execute("SELECT COUNT(*) FROM enquiries WHERE status='New'").fetchone()[0]
        life_count = conn.execute("SELECT COUNT(*) FROM enquiries WHERE insurance_type='Life Insurance'").fetchone()[0]
        health_count = conn.execute("SELECT COUNT(*) FROM enquiries WHERE insurance_type='Health Insurance'").fetchone()[0]
    enquiries = []
    for row in rows:
        item = dict(row)
        try: item['members'] = json.loads(item['members_json'] or '[]')
        except (TypeError, json.JSONDecodeError): item['members'] = []
        enquiries.append(item)
    counts = {'total': total, 'new': new_count, 'life': life_count, 'health': health_count}
    return render_template('page.html', title='Admin dashboard', body=render_template_string(DASH_BODY, enquiries=enquiries, counts=counts, q=q, status=status, statuses=statuses))

@app.route('/admin/enquiry/<int:enquiry_id>/status', methods=['POST'])
@admin_required
def update_status(enquiry_id):
    if not secrets.compare_digest(request.form.get('csrf_token', ''), session.get('csrf_token', '')):
        abort(400, 'Invalid form token. Please refresh and try again.')
    status = request.form.get('status', '')
    if status not in ('New', 'Contacted', 'Follow-up', 'Completed'):
        abort(400, 'Invalid status')
    with db() as conn:
        conn.execute('UPDATE enquiries SET status=? WHERE id=?', (status, enquiry_id))
    flash('Enquiry status updated.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/export.csv')
@admin_required
def export_csv():
    import csv, io
    from flask import Response
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Created at', 'Full name', 'Mobile', 'City', 'Provider', 'Insurance type', 'Requirement', 'Coverage', 'Payment frequency', 'Existing insurance', 'Members', 'Notes', 'Status'])
    with db() as conn:
        rows = conn.execute('SELECT * FROM enquiries ORDER BY id DESC').fetchall()
    for r in rows:
        writer.writerow([r['id'], r['created_at'], r['full_name'], r['mobile'], r['city'], r['provider'], r['insurance_type'], r['requirement'], r['coverage_amount'], r['payment_frequency'], r['existing_insurance'], r['members_json'], r['notes'], r['status']])
    return Response('\ufeff' + output.getvalue(), mimetype='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment; filename=ns-insurance-enquiries.csv'})

@app.route('/admin/policies')
@admin_required
def manage_policies():
    with db() as conn:
        policies = conn.execute('''
            SELECT p.*, c.name AS company_name
            FROM insurance_policies p
            JOIN insurance_companies c ON c.id = p.company_id
            ORDER BY p.id DESC
        ''').fetchall()
        companies = conn.execute(
            'SELECT * FROM insurance_companies ORDER BY name'
        ).fetchall()

    body = '''
    <main class="admin-dashboard">
      <h1>Manage Policies</h1>
      <p><a class="text-link" href="{{ url_for('admin_dashboard') }}">← Back to enquiries</a></p>
      <h2>Add a policy</h2>
      <form method="post" action="{{ url_for('add_policy') }}" class="quote-form">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <label>Insurance company
          <select name="company_id" required>
            <option value="">Choose company</option>
            {% for c in companies %}
              <option value="{{ c.id }}">{{ c.name }} — {{ c.insurance_type }}</option>
            {% endfor %}
          </select>
        </label>
        <label>Policy name
          <input name="name" required maxlength="160">
        </label>
        <label>Category
          <select name="category" required>
            <option>Life Insurance - Savings Plan</option>
            <option>Life Insurance - Term Plan</option>
            <option>Life Insurance - Child Plan</option>
            <option>Life Insurance - Retirement Plan</option>
            <option>Health Insurance - Individual</option>
            <option>Health Insurance - Family Floater</option>
            <option>Health Insurance - Senior Citizen</option>
            <option>Health Insurance - Top-up</option>
          </select>
        </label>
        <label>Description
          <textarea name="description" required maxlength="2000"></textarea>
        </label>
        <label>Benefits (verify with insurer)
          <textarea name="benefits" maxlength="3000"></textarea>
        </label>
        <label>Eligibility
          <textarea name="eligibility" maxlength="2000"></textarea>
        </label>
        <label>Exclusions
          <textarea name="exclusions" maxlength="2000"></textarea>
        </label>
        <label>Official brochure URL
          <input name="brochure_url" type="url" maxlength="500">
        </label>
        <label><input type="checkbox" name="is_published" value="yes"> Publish on website</label>
        <button class="button submit-button" type="submit">Save policy</button>
      </form>
      <h2>Existing policies</h2>
      <div class="table-wrap"><table>
        <thead><tr><th>Company</th><th>Policy</th><th>Category</th><th>Status</th></tr></thead>
        <tbody>
        {% for p in policies %}
          <tr>
            <td>{{ p.company_name }}</td>
            <td>{{ p.name }}</td>
            <td>{{ p.category }}</td>
            <td>{{ 'Published' if p.is_published else 'Hidden' }}</td>
          </tr>
        {% else %}
          <tr><td colspan="4">No policies added yet.</td></tr>
        {% endfor %}
        </tbody>
      </table></div>
    </main>
    '''
    return render_template(
        'page.html',
        title='Manage Policies',
        body=render_template_string(body, policies=policies, companies=companies)
    )


@app.route('/admin/policies/add', methods=['POST'])
@admin_required
def add_policy():
    if not secrets.compare_digest(
        request.form.get('csrf_token', ''),
        session.get('csrf_token', '')
    ):
        abort(400, 'Invalid form token. Please refresh and try again.')

    company_id = request.form.get('company_id', type=int)
    name = safe_text(request.form.get('name'), 160)
    category = safe_text(request.form.get('category'), 100)
    description = safe_text(request.form.get('description'), 2000)
    benefits = safe_text(request.form.get('benefits'), 3000)
    eligibility = safe_text(request.form.get('eligibility'), 2000)
    exclusions = safe_text(request.form.get('exclusions'), 2000)
    brochure_url = safe_text(request.form.get('brochure_url'), 500)
    is_published = 1 if request.form.get('is_published') == 'yes' else 0

    allowed_categories = {
        'Life Insurance - Savings Plan',
        'Life Insurance - Term Plan',
        'Life Insurance - Child Plan',
        'Life Insurance - Retirement Plan',
        'Health Insurance - Individual',
        'Health Insurance - Family Floater',
        'Health Insurance - Senior Citizen',
        'Health Insurance - Top-up'
    }

    if not company_id or not name or not description or category not in allowed_categories:
        abort(400, 'Please enter a valid company, policy name, category and description.')

    with db() as conn:
        company = conn.execute(
            'SELECT id FROM insurance_companies WHERE id=? AND is_active=1',
            (company_id,)
        ).fetchone()
        if not company:
            abort(400, 'Please select an active insurance company.')

        conn.execute('''
            INSERT INTO insurance_policies
            (company_id, name, category, description, benefits, eligibility,
             exclusions, brochure_url, is_published, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            company_id, name, category, description, benefits, eligibility,
            exclusions, brochure_url, is_published,
            datetime.now().strftime('%Y-%m-%d %H:%M')
        ))

    flash('Policy saved successfully.', 'success')
    return redirect(url_for('manage_policies'))
@app.route('/policies')
def public_policies():
    with db() as conn:
        policies = conn.execute('''
            SELECT p.*, c.name AS company_name
            FROM insurance_policies p
            JOIN insurance_companies c ON c.id = p.company_id
            WHERE p.is_published=1 AND c.is_active=1
            ORDER BY c.name, p.category, p.name
        ''').fetchall()

    body = '''
    <main class="section">
      <div class="section-heading">
        <span class="eyebrow">INSURANCE POLICY DIRECTORY</span>
        <h1>Explore Life & Health Policies</h1>
        <p>Review official policy documents and confirm terms with the insurer.</p>
      </div>
      <div class="provider-grid">
      {% for p in policies %}
        <article class="provider-card">
        
{% if 'Tata AIA Fortune Guarantee Supreme' in p.name %}
  <img
    src="{{ url_for('static', filename='NS Insurance Family Protection Brochure.png') }}"
    alt="NS Insurance family protection brochure for Tata AIA Fortune Guarantee Supreme"
    style="width:100%;height:auto;border-radius:12px;margin-bottom:16px;"
  >
{% endif %}

          <span class="tag">{{ p.category }}</span>
          <h2>{{ p.name }}</h2>
          <p><b>Company:</b> {{ p.company_name }}</p>
          <p>{{ p.description }}</p>
          {% if p.benefits %}<p><b>Benefits:</b> {{ p.benefits }}</p>{% endif %}
          {% if p.eligibility %}<p><b>Eligibility:</b> {{ p.eligibility }}</p>{% endif %}
          {% if p.exclusions %}<p><b>Exclusions:</b> {{ p.exclusions }}</p>{% endif %}
          {% if p.brochure_url %}
            <p><a class="text-link" href="{{ p.brochure_url }}" target="_blank" rel="noopener noreferrer">View brochure ↗</a></p>
          {% endif %}
        </article>
      {% else %}
        <p>No policies are currently published.</p>
      {% endfor %}
      </div>
      <p class="form-footnote">Policy details are summaries only. Refer to the insurer's official policy wording for terms, exclusions and benefits.</p>
    </main>
    '''
    return render_template(
        'page.html',
        title='Insurance Policies',
        body=render_template_string(body, policies=policies)
    )
if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1', host='127.0.0.1', port=int(os.environ.get('PORT', '5000')))
