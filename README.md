# NS Insurance website (local starter)

A responsive Flask + SQLite website for enquiries about **Tata AIA Life Insurance, LIC, and Care Health Insurance only**. It includes a dynamic life insurance form, a four-member health insurance form, an admin dashboard, enquiry status updates, and CSV export.

## Requirements
- Python 3.10 or newer
- Internet connection only if you want Google Fonts to load; the site works without them

## Run locally on Windows
1. Extract the ZIP folder.
2. Open Command Prompt or PowerShell in the `ns_insurance_website` folder.
3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

5. Set admin credentials for your local session (recommended):

   ```powershell
   $env:ADMIN_USERNAME="admin"
   $env:ADMIN_PASSWORD="Choose-A-Strong-Password"
   $env:FLASK_SECRET_KEY="replace-this-with-a-long-random-secret"
   ```

6. Start the website:

   ```powershell
   python app.py
   ```

7. Open `http://127.0.0.1:5000` in your browser.
8. Admin dashboard: `http://127.0.0.1:5000/admin/login`.

For a quick local test only, if you do not set environment variables, the default login is username `admin` and password `ChangeMe123!`. **Change this before sharing or deploying the site.** The SQLite database file `ns_insurance.db` is created automatically beside `app.py` when the app starts.

## Test the flows
- Select Tata AIA or LIC in the quote form: life insurance fields appear.
- Select Care Health Insurance: choose either `2 Adults + 2 Children` or `4 Adults`, then fill in all four member cards.
- Submit a test enquiry, sign into `/admin/login`, check the dashboard, update its status, and try Export CSV.

## Important before publishing
This is a local starter, not a production-hardened deployment. Before going public, configure strong unique credentials and a random secret key, use HTTPS, disable debug mode, add rate limiting and backups, review privacy/consent wording, and restrict access to customer information. Avoid collecting sensitive medical records through this form. The provider names are text labels, not official logos; use approved logo assets only if you have permission. NS Insurance is presented as an independent enquiry website, not an official insurer website.

Update the phone number `9347684905` and WhatsApp URL in `app.py`'s page template if you want to use a different business number.
