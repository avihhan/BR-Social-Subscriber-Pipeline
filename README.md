# Subscriber Pipeline (Flask + Google Sheets + SMTP)

A simple emailing pipeline to collect subscribers into Google Sheets, filter/export them, and send HTML email campaigns via SMTP.

## Features
- Google Sheets as the subscriber database
- Subscribe endpoint capturing name, email, timestamp, IP and rough geolocation
- Send HTML email campaigns from local HTML templates
- Unsubscribe endpoint removes a subscriber by email
- CSV-like lowercasing normalization for consistent data

---

## 1) Prerequisites
- Python 3.10/3.11 recommended
- A Google Cloud project with Google Sheets API and Google Drive API enabled
- A Google Service Account and credentials JSON file
- SMTP account (e.g., Gmail with App Password)

---

## 2) Google Cloud & Sheets Setup
1. Create/select a project in Google Cloud Console.
2. Enable APIs:
   - Google Sheets API
   - Google Drive API
3. Create a Service Account and download its key JSON file. Save it in the project root as:
   - `google-credentials.json`
4. Create a Google Sheet named (default):
   - `Subscriber List`
5. Share the sheet with your service account email (Editor access).

Optional: Run the helper to set up headers (or create them manually):
- The sheet should include headers in the first row:
  - `Name | Email | Timestamp | IP Address | Country | Region | City | Latitude | Longitude`

---

## 3) Local Configuration
Create a `.env` file in the project root:

```
# Google Sheets
GOOGLE_SHEET_NAME=Subscriber List

# SMTP (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=BullRunAI
```

Notes:
- For Gmail, enable 2FA and create an App Password.
- `GOOGLE_SHEET_NAME` can be changed to point to a different sheet.

---

## 4) Install & Run
Install dependencies:
```
pip install -r requirements.txt
```
Run the server:
```
python app.py
```
The API listens on `http://localhost:8000`.

---

## 5) Email Templates
Templates live in `templates/`. Example: `templates/intro.html`.

Images in emails:
- Most email clients block relative paths. Use absolute HTTPS URLs, or embed via CID attachments (not included by default).
- If using local images (e.g., `images/bullrun.png`, `images/page.png`), host them on a CDN and replace `src` with the CDN URL in your template.

---

## 6) API Endpoints
All responses are JSON.

### Health
- GET `/health`
- Returns service status.
```
curl -s http://localhost:8000/health
```

### Subscribe
- POST `/subscribe`
- Body (JSON):
```
{
  "name": "avi kumar",
  "email": "avihhan.official@gmail.com"
}
```
- Behavior:
  - Detects client IP (or uses `X-Forwarded-For` if present)
  - Geolocates rough `country/region/city` (IP-API)
  - Lowercases string fields and appends a row to Google Sheet
  - Duplicate emails are detected (case-insensitive) using the Email column; returns existing record if already subscribed
- Example:
```
curl -s -X POST http://localhost:8000/subscribe \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 8.8.8.8" \
  -d '{"name":"avi kumar","email":"avihhan.official@gmail.com"}'
```
- On duplicate:
```
{
  "message": "already subscribed",
  "data": { "name": "avi kumar", "email": "avihhan.official@gmail.com", "timestamp": "2025-09-01 12:34:56" }
}
```

### List Subscribers
- GET `/subscribers`
- Optional query params: `start_date`, `end_date`, `country`, `region`, `city`
- Examples:
```
# All
curl -s "http://localhost:8000/subscribers"

# Date range + country
curl -s "http://localhost:8000/subscribers?start_date=2024-01-01&end_date=2025-12-31&country=united%20states"
```

### Send Template Email Campaign
- POST `/send-template-email`
- Body (JSON):
```
{
  "template_name": "intro",    
  "subject": "BullRunAI Launch"
}
```
- Uses `templates/{template_name}.html` per subscriber with placeholders like `{{name}}`, `{{email}}`, `{{city}}`, `{{country}}`.
- Sends HTML emails via SMTP.
- Example:
```
curl -s -X POST http://localhost:8000/send-template-email \
  -H "Content-Type: application/json" \
  -d '{"template_name":"intro","subject":"BullRunAI Launch"}'
```

### Unsubscribe
- POST `/unsubscribe`
- Body (JSON):
```
{ "email": "user@example.com" }
```
- Deletes matching row from the sheet (case-insensitive match on Email column).
- Example:
```
curl -s -X POST http://localhost:8000/unsubscribe \
  -H "Content-Type: application/json" \
  -d '{"email":"avihhan.official@gmail.com"}'
```

---

## 7) Seeding (Optional)
Populate the sheet with dummy data:
```
python seed/populate_dummy_data.py
```
Notes:
- Script expects `google-credentials.json` in the project root and the sheet shared with the service account.
- Writes all string fields in lowercase.

---

## 8) Troubleshooting
- Credentials:
  - Ensure `google-credentials.json` is present and the sheet is shared with the service account
- Quota errors:
  - Free Google Drive/Sheets quotas may be exceeded. Free up space or use an existing sheet
- Emails delivered as plain text:
  - Ensure your SMTP credentials are correct and the app is using HTML path
  - Avoid emojis or ensure UTF-8 subjects/bodies
- Images not visible in email:
  - Use absolute URLs (CDN) or embed images as CID attachments

---

## 9) Security & Production Notes
- Do not commit `google-credentials.json` or `.env` to version control
- Use an environment-specific `.env` loader or secret manager in production
- Put the Flask app behind a proper WSGI server (gunicorn/uwsgi) and reverse proxy (nginx)

---

## 10) Project Structure
```
Subscriber Pipeline/
├─ app.py
├─ requirements.txt
├─ .env                  # your local environment
├─ google-credentials.json
├─ templates/
│  └─ intro.html
├─ images/
│  ├─ bullrun.png
│  └─ page.png
└─ seed/
   └─ populate_dummy_data.py
```

---

## License
MIT (c) BullRunAI
