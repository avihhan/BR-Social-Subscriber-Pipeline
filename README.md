# Subscriber Pipeline (Flask + Google Sheets + SMTP + Google Drive Templates)

A modern emailing pipeline to collect subscribers into Google Sheets, automatically send welcome emails, and send HTML email campaigns using templates stored in Google Drive.

## Features
- **Google Sheets as the subscriber database** - Store subscriber data with automatic IP geolocation
- **Automatic welcome emails** - New subscribers receive personalized welcome emails immediately
- **Google Drive template storage** - HTML templates stored in Google Drive for easy management
- **Flexible subscription** - Name field is optional (defaults to "Anonymous")
- **Smart duplicate detection** - Prevents duplicate subscriptions with case-insensitive email matching
- **IP geolocation** - Automatically captures country, region, city, latitude, longitude
- **Unsubscribe management** - Easy removal of subscribers by email
- **Data normalization** - All string fields stored in lowercase for consistency

---

## System Architecture & Pipeline Flow

### Data Flow Overview
```
1. User submits email → 2. Flask API processes → 3. IP geolocation (ip-api.com) →
4. Google Sheets storage → 5. Welcome email via SMTP → 6. Campaign emails via Google Drive templates
```

### Core Components
- **Flask API Server**: Main application handling HTTP requests and routing
- **Google Sheets**: Primary database for subscriber data storage
- **Google Drive**: Template storage for HTML email campaigns
- **SMTP Server**: Email delivery system (Gmail/custom SMTP)
- **IP Geolocation API**: Automatic location detection for analytics
- **Cloud Functions/Docker**: Deployment options for production

### API Architecture
The system exposes 5 main REST endpoints with JSON responses:
- `GET /health` - Service health check
- `POST /subscribe` - New subscriber registration with automatic welcome email
- `GET /subscribers` - Retrieve subscriber list with optional filtering
- `POST /send-template-email` - Campaign email distribution
- `POST /unsubscribe` - Subscriber removal

---

## 1) Prerequisites & Required Accounts

### Development Environment
- **Python 3.10/3.11** recommended
- **Git** for version control
- **Code editor** (VS Code, PyCharm, etc.)

### Required Service Accounts

#### 1. Google Cloud Platform Account
- **Purpose**: Google Sheets API, Google Drive API, Cloud Functions deployment
- **Required APIs**:
  - Google Sheets API
  - Google Drive API v3  
  - Cloud Functions API (for deployment)
- **Service Account**: JSON credentials file required
- **Project ID**: `brsocial` (current project)

#### 2. SMTP Email Account
- **Gmail (Recommended)**:
  - Enable 2-Factor Authentication
  - Generate App Password (16-character)
  - Use App Password instead of regular password
- **Alternative SMTP Providers**:
  - SendGrid, Mailgun, AWS SES, etc.

#### 3. IP Geolocation Service
- **Service**: ip-api.com (Free tier: 1000 requests/month)
- **No account required** for basic usage
- **Alternative**: IPStack, MaxMind, etc.

#### 4. Google Drive Account
- **Purpose**: HTML template storage
- **Required**: "Html Templates" folder shared with service account
- **Templates needed**: `subscribed.html`, `intro.html`, `newsletter.html`

---

## 2) Google Cloud Setup (Step-by-Step)

### 2.1 Google Cloud Project Setup
1. **Create/Select Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing: `brsocial`
   - Note your Project ID for deployment

2. **Enable Required APIs**:
   ```bash
   gcloud services enable sheets.googleapis.com
   gcloud services enable drive.googleapis.com
   gcloud services enable cloudfunctions.googleapis.com
   ```
   Or enable via Console:
   - Google Sheets API
   - Google Drive API v3
   - Cloud Functions API (for deployment)

3. **Create Service Account**:
   - Go to IAM & Admin → Service Accounts
   - Create new service account: `subscriber-pipeline`
   - Assign roles: `Editor` or `Sheets Editor` + `Drive Viewer`
   - Generate JSON key → Download as `google-credentials.json`
   - **Important**: Save in project root directory

### 2.2 Google Sheets Setup
1. **Create Spreadsheet**:
   - Create new Google Sheet named: `Subscriber List`
   - **Current Sheet ID**: `1G47eBaTt1nAjj0N5w5oO-Z6wWX7Z3Gtf-wvkmuLs33c`
   - Share with service account email (Editor access)

2. **Set Headers** (automatic via setup script):
   ```bash
   python seed/setup_google_sheets.py
   ```
   Or create manually:
   - Row 1: `Name | Email | Timestamp | IP Address | Country | Region | City | Latitude | Longitude`

### 2.3 Google Drive Template Setup
1. **Create Template Folder**:
   - Create folder: "Html Templates" in Google Drive
   - Share with service account email (Viewer access)

2. **Upload Required Templates**:
   - `subscribed.html` - Welcome email template
   - `intro.html` - General campaign template  
   - `newsletter.html` - Newsletter template
   - Use `{{name}}` placeholder for personalization

---

## 3) Local Development Setup

### 3.1 Environment Configuration
Create `.env` file in project root:

```bash
# Google Sheets Configuration
GOOGLE_SHEET_NAME=Subscriber List

# SMTP Configuration (Gmail Example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=BullRunAI

# Optional: Override default sheet ID
# GOOGLE_SHEET_ID=1G47eBaTt1nAjj0N5w5oO-Z6wWX7Z3Gtf-wvkmuLs33c
```

### 3.2 SMTP Setup (Gmail)
1. **Enable 2-Factor Authentication**:
   - Go to Google Account settings
   - Security → 2-Step Verification → Turn On

2. **Generate App Password**:
   - Security → App passwords
   - Select app: "Mail", device: "Other"
   - Copy 16-character password to `.env` file

### 3.3 Installation & Running
```bash
# Clone repository
git clone <repository-url>
cd "Subscriber Pipeline"

# Install dependencies
pip install -r requirements.txt

# Set up Google Sheets (optional)
python seed/setup_google_sheets.py

# Populate dummy data (optional)
python seed/populate_dummy_data.py

# Run development server
python main.py
```

**Server Access**: `http://localhost:8000`

### 3.4 Local Testing
```bash
# Health check
curl http://localhost:8000/health

# Test subscription
curl -X POST http://localhost:8000/subscribe \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com"}'

# View subscribers
curl http://localhost:8000/subscribers
```

---

## 4) API Endpoints Reference

The system provides 5 REST API endpoints with comprehensive functionality:

### 4.1 Health Check
**Endpoint**: `GET /health`
**Purpose**: Service health monitoring and uptime verification

```bash
curl -X GET http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "message": "Subscriber Pipeline is running"
}
```

### 4.2 Subscribe User
**Endpoint**: `POST /subscribe`
**Purpose**: Register new subscribers with automatic welcome email

**Request Body**:
```json
{
  "name": "John Doe",        // Optional - defaults to "Anonymous"
  "email": "john@example.com" // Required
}
```

**Process Flow**:
1. Validates email format and requirement
2. Captures client IP address (supports X-Forwarded-For)
3. Performs IP geolocation via ip-api.com
4. Checks for duplicate email (case-insensitive)
5. Stores data in Google Sheets (normalized to lowercase)
6. Sends personalized welcome email using embedded template
7. Returns confirmation with location data

**Response (Success)**:
```json
{
  "message": "Subscriber added successfully",
  "data": {
    "name": "john doe",
    "email": "john@example.com",
    "timestamp": "2025-01-09 14:30:15",
    "ip_address": "192.168.1.100",
    "location": {
      "country": "united states",
      "region": "california",
      "city": "san francisco",
      "lat": 37.7749,
      "lon": -122.4194
    }
  }
}
```

**Response (Duplicate)**:
```json
{
  "message": "already subscribed",
  "data": {
    "name": "john doe",
    "email": "john@example.com",
    "timestamp": "2025-01-08 10:15:30"
  }
}
```

### 4.3 List Subscribers
**Endpoint**: `GET /subscribers`
**Purpose**: Retrieve subscriber data with optional filtering

**Query Parameters** (all optional):
- `start_date`: Filter by date (YYYY-MM-DD)
- `end_date`: Filter by date (YYYY-MM-DD)
- `country`: Filter by country name
- `region`: Filter by region/state
- `city`: Filter by city name

**Examples**:
```bash
# All subscribers
curl "http://localhost:8000/subscribers"

# Date range filtering
curl "http://localhost:8000/subscribers?start_date=2024-01-01&end_date=2025-12-31"

# Location filtering
curl "http://localhost:8000/subscribers?country=united%20states&region=california"
```

**Response**:
```json
{
  "subscribers": [
    {
      "Name": "john doe",
      "Email": "john@example.com",
      "Timestamp": "2025-01-09 14:30:15",
      "IP Address": "192.168.1.100",
      "Country": "united states",
      "Region": "california",
      "City": "san francisco",
      "Latitude": 37.7749,
      "Longitude": -122.4194
    }
  ]
}
```

### 4.4 Send Campaign Email
**Endpoint**: `POST /send-template-email`
**Purpose**: Distribute HTML email campaigns to all subscribers

**Request Body**:
```json
{
  "template_name": "intro",                    // Required: template filename (without .html)
  "subject": "Welcome to BullRunAI!",         // Required: email subject
  "advertisement_html": "<p>Special offer!</p>" // Optional: additional content
}
```

**Process Flow**:
1. Validates template name and subject
2. Connects to Google Drive API
3. Loads template from "Html Templates" folder
4. Retrieves all subscribers from Google Sheets
5. Personalizes content using `{{name}}` placeholder
6. Sends individual emails via SMTP
7. Returns success/failure statistics

**Available Templates**:
- `subscribed.html` - Welcome email (auto-sent on subscription)
- `intro.html` - General campaign template
- `newsletter.html` - Newsletter format

**Response**:
```json
{
  "message": "Email campaign completed",
  "success_count": 150,
  "failed_count": 2
}
```

### 4.5 Unsubscribe User
**Endpoint**: `POST /unsubscribe`
**Purpose**: Remove subscriber from database

**Request Body**:
```json
{
  "email": "john@example.com" // Required: exact email to remove
}
```

**Process Flow**:
1. Normalizes email to lowercase
2. Searches Google Sheets for matching email
3. Removes entire row if found
4. Returns confirmation with deleted data

**Response (Success)**:
```json
{
  "message": "unsubscribed successfully",
  "data": {
    "email": "john@example.com",
    "deleted_row_content": ["john doe", "john@example.com", "2025-01-09 14:30:15", ...]
  }
}
```

**Response (Not Found)**:
```json
{
  "message": "email not found"
}
```

### 4.6 Error Handling
All endpoints return appropriate HTTP status codes and JSON error messages:

```json
{
  "error": "Error description here"
}
```

**Common Error Codes**:
- `400`: Bad Request (missing required fields)
- `404`: Not Found (subscriber/template not found)
- `500`: Internal Server Error (service connection issues)

---

## 5) Email Templates
**Templates are now stored in Google Drive** for easy management and updates without redeployment.

### Template Setup:
1. **Google Drive Folder**: Create a folder called "Html Templates" in your Google Drive
2. **Required Templates**:
   - `subscribed.html` - Welcome email sent automatically to new subscribers
   - `intro.html` - General email template for campaigns
   - `newsletter.html` - Newsletter template
3. **Template Features**:
   - Use `{{name}}` placeholder for subscriber personalization
   - Support for HTML, CSS, and embedded images
   - Easy to update without redeploying the function

### Template Examples:
- **subscribed.html**: Welcome message with `{{name}}` placeholder
- **intro.html**: Campaign template with customizable content
- **newsletter.html**: Newsletter format with branding

### Images in Emails:
- Most email clients block relative paths. Use absolute HTTPS URLs, or embed via CID attachments
- If using local images (e.g., `images/bullrun.png`, `images/page.png`), host them on a CDN and replace `src` with the CDN URL in your template

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
  "name": "avi kumar",  // Optional - defaults to "Anonymous" if not provided
  "email": "avihhan.official@gmail.com"
}
```
- **NEW**: Name field is now optional! If not provided, it defaults to "Anonymous"
- **NEW**: Automatic welcome email sent using `subscribed.html` template from Google Drive
- Behavior:
  - Detects client IP (or uses `X-Forwarded-For` if present)
  - Geolocates rough `country/region/city` (IP-API)
  - Lowercases string fields and appends a row to Google Sheet
  - **Automatically sends personalized welcome email** using `subscribed.html` template
  - Duplicate emails are detected (case-insensitive) using the Email column; returns existing record if already subscribed
- Examples:
```
# Subscribe with name
curl -s -X POST http://localhost:8000/subscribe \
  -H "Content-Type: application/json" \
  -d '{"name":"avi kumar","email":"avihhan.official@gmail.com"}'

# Subscribe without name (will use "Anonymous")
curl -s -X POST http://localhost:8000/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email":"anonymous@example.com"}'
```
- On duplicate:
```
{
  "message": "already subscribed",
  "data": { "name": "avi kumar", "email": "avihhan.official@gmail.com", "timestamp": "2025-09-01 12:34:56" }
}
```
- On success (with welcome email sent):
```
{
  "message": "Subscriber added successfully",
  "data": { "name": "avi kumar", "email": "avihhan.official@gmail.com", "timestamp": "2025-09-01 12:34:56", "ip_address": "192.168.1.1", "location": {...} }
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
  "subject": "BullRunAI Launch",
  "advertisement_html": "<p>Special offer: Get 20% off!</p>"  // Optional
}
```
- **NEW**: Templates are now loaded from Google Drive "Html Templates" folder
- Uses `{template_name}.html` from Google Drive per subscriber with placeholders like `{{name}}`
- Sends personalized HTML emails via SMTP
- **No need to redeploy** when updating templates - just update files in Google Drive
- Example:
```
curl -s -X POST http://localhost:8000/send-template-email \
  -H "Content-Type: application/json" \
  -d '{"template_name":"intro","subject":"BullRunAI Launch","advertisement_html":"<p>Special offer: Get 20% off!</p>"}'
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
- **NEW**: All string data (name, email, IP, location) is normalized to lowercase for consistency.

---

## 8) Troubleshooting
- **Credentials**:
  - Ensure `google-credentials.json` is present and the sheet is shared with the service account
  - Make sure the "Html Templates" folder in Google Drive is shared with your service account
- **Quota errors**:
  - Free Google Drive/Sheets quotas may be exceeded. Free up space or use an existing sheet
- **Emails delivered as plain text**:
  - Ensure your SMTP credentials are correct and the app is using HTML path
  - Avoid emojis or ensure UTF-8 subjects/bodies
- **Images not visible in email**:
  - Use absolute URLs (CDN) or embed images as CID attachments
- **Welcome emails not sending**:
  - Check that `subscribed.html` exists in your Google Drive "Html Templates" folder
  - Verify the folder is shared with your service account
  - Check function logs for detailed error messages
- **Template loading errors**:
  - Ensure the "Html Templates" folder name is exactly as specified
  - Check that template files have `.html` extension
  - Verify Google Drive API permissions

---

## 9) Security & Production Notes
- Do not commit `google-credentials.json` or `.env` to version control
- Use an environment-specific `.env` loader or secret manager in production
- Put the Flask app behind a proper WSGI server (gunicorn/uwsgi) and reverse proxy (nginx)
- **Google Drive templates**: Ensure proper sharing permissions for the "Html Templates" folder
- **Service account security**: Use least-privilege access for your service account

---

## 10) Project Structure
```
Subscriber Pipeline/
├─ main.py              # Main application (Cloud Functions compatible)
├─ requirements.txt     # Dependencies including Google Drive API
├─ .env                 # Your local environment variables
├─ google-credentials.json
├─ templates/           # Local templates (legacy - now using Google Drive)
│  └─ intro.html
├─ images/
│  ├─ bullrun.png
│  └─ page.png
└─ seed/
   └─ populate_dummy_data.py
```

**Note**: Templates are now primarily stored in Google Drive "Html Templates" folder for easier management.

---

## 10) Production Deployment

### 10.1 Google Cloud Functions Deployment

**Prerequisites**:
- Google Cloud CLI installed and authenticated
- Project ID: `brsocial`
- Service account credentials configured

**Deploy Command**:
```bash
# Deploy the function with current project settings
gcloud functions deploy subscriber-pipeline \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point subscriber_pipeline \
  --source . \
  --region us-central1 \
  --memory 512MB \
  --timeout 540s \
  --project brsocial
```

**Set Environment Variables**:
```bash
# Google Sheets configuration
gcloud functions deploy subscriber-pipeline \
  --update-env-vars GOOGLE_SHEET_NAME="Subscriber List" \
  --region us-central1 \
  --project brsocial

# SMTP configuration (Gmail)
gcloud functions deploy subscriber-pipeline \
  --update-env-vars SMTP_SERVER=smtp.gmail.com,SMTP_PORT=587,FROM_NAME="BullRunAI" \
  --region us-central1 \
  --project brsocial

# SMTP credentials (use your actual credentials)
gcloud functions deploy subscriber-pipeline \
  --update-env-vars SMTP_USERNAME="your-email@gmail.com",SMTP_PASSWORD="your-app-password",FROM_EMAIL="your-email@gmail.com" \
  --region us-central1 \
  --project brsocial

# Google credentials (service account JSON as environment variable)
gcloud functions deploy subscriber-pipeline \
  --update-env-vars GOOGLE_CREDENTIALS='{"type":"service_account",...}' \
  --region us-central1 \
  --project brsocial
```

**Production URL**: `https://us-central1-brsocial.cloudfunctions.net/subscriber-pipeline`

### 10.2 Docker Deployment (Alternative)

**Using Cloud Build**:
```bash
# Build and deploy using cloudbuild.yaml
gcloud builds submit --config cloudbuild.yaml .

# Deploy to Cloud Run
gcloud run deploy subscriber-pipeline \
  --image us-central1-docker.pkg.dev/brsocial/subscriber/subscriber:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

**Local Docker Build**:
```bash
# Build image
docker build -t subscriber-pipeline .

# Run container locally
docker run -p 8080:8080 \
  -e GOOGLE_CREDENTIALS='{"type":"service_account",...}' \
  -e SMTP_USERNAME="your-email@gmail.com" \
  -e SMTP_PASSWORD="your-app-password" \
  subscriber-pipeline
```

### 10.3 Production Testing

**Health Check**:
```bash
curl -X GET "https://us-central1-brsocial.cloudfunctions.net/subscriber-pipeline/health"
```

**Test Subscription**:
```bash
curl -X POST "https://us-central1-brsocial.cloudfunctions.net/subscriber-pipeline/subscribe" \
  -H "Content-Type: application/json" \
  -d '{"name":"Production Test","email":"test@example.com"}'
```

**Test Campaign Email**:
```bash
curl -X POST "https://us-central1-brsocial.cloudfunctions.net/subscriber-pipeline/send-template-email" \
  -H "Content-Type: application/json" \
  -d '{"template_name":"intro","subject":"Production Test Campaign"}'
```

### 10.4 Production Configuration

**Current Production Settings**:
- **Project ID**: `brsocial`
- **Region**: `us-central1`
- **Runtime**: Python 3.11
- **Memory**: 512MB (Cloud Functions) / 1GB (Cloud Run)
- **Timeout**: 540s
- **Sheet ID**: `1G47eBaTt1nAjj0N5w5oO-Z6wWX7Z3Gtf-wvkmuLs33c`

**Security Configuration**:
- Service account: `subscriber-pipeline@brsocial.iam.gserviceaccount.com`
- Required permissions: Sheets Editor, Drive Viewer
- HTTPS-only access
- CORS enabled for all origins

---

## 11) Monitoring & Analytics

### Data Structure in Google Sheets
The system automatically collects and stores:
- **Subscriber Information**: Name, email, timestamp
- **Geographic Data**: IP address, country, region, city, coordinates
- **Analytics Ready**: Easy export to analyze subscriber demographics

### Key Metrics Available
- Subscriber growth over time
- Geographic distribution of subscribers
- Email campaign performance (success/failure rates)
- Popular signup periods and trends

### Monitoring Production Health
```bash
# Set up monitoring script
while true; do
  curl -s https://us-central1-brsocial.cloudfunctions.net/subscriber-pipeline/health
  sleep 300 # Check every 5 minutes
done
```

---

## 12) Summary: Complete System Overview

### What This System Does
The **Subscriber Pipeline** is a complete email marketing automation system that:

1. **Collects Subscribers**: Web form submissions → Google Sheets database
2. **Geographic Analytics**: Automatic IP geolocation for subscriber insights
3. **Welcome Automation**: Instant personalized welcome emails
4. **Campaign Management**: HTML email campaigns via Google Drive templates
5. **Data Management**: Easy subscriber removal and duplicate prevention

### Key Integration Points

#### External Services Used
- **Google Sheets**: `1G47eBaTt1nAjj0N5w5oO-Z6wWX7Z3Gtf-wvkmuLs33c` - Subscriber database
- **Google Drive**: "Html Templates" folder - Email template storage
- **Gmail SMTP**: Email delivery service
- **ip-api.com**: IP geolocation service (1000 free requests/month)
- **Google Cloud Functions**: Production hosting (`brsocial` project)

#### Data Flow Summary
```
Frontend Form → POST /subscribe → IP Geolocation → Google Sheets → Welcome Email
                     ↓
Admin Dashboard → GET /subscribers → Analytics & Filtering
                     ↓
Campaign Manager → POST /send-template-email → Google Drive Templates → Mass Email Distribution
```

### Production Deployment Status
- **Live URL**: `https://us-central1-brsocial.cloudfunctions.net/subscriber-pipeline`
- **Region**: us-central1
- **Runtime**: Python 3.11
- **Auto-scaling**: Enabled
- **HTTPS**: Enforced
- **Monitoring**: Health endpoint available

### Local Development Ready
- **Setup Time**: ~15 minutes with proper credentials
- **Dependencies**: All managed via `requirements.txt`
- **Environment**: Fully configured via `.env` file
- **Testing**: Built-in test endpoints and dummy data population

---

## License
MIT (c) BullRunAI
