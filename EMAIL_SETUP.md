# Email Configuration Guide

Scarica Azioni can automatically send EOD stock reports via email.

## Quick Setup

### 1. Create SMTP Configuration File

Copy the example file and fill in your details:

```bash
cp smtp_config.example.json smtp_config.json
```

### 2. Edit smtp_config.json

```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "use_ssl": false,
  "username": "your-email@gmail.com",
  "password": "your-app-password",
  "recipients": [
    "recipient1@example.com",
    "recipient2@example.com"
  ],
  "subject": "MAIL AUTOM CHECK ADVFN"
}
```

### 3. Run with Email Enabled

**Python:**
```python
import lambda_handler

event = {
    "stock_file": "titoli_check.txt",
    "send_email": True,
    "smtp_config_file": "smtp_config.json"
}

response = lambda_handler.handler(event, None)
```

**Lambda Event:**
```json
{
  "stock_file": "titoli_check.txt",
  "send_email": true,
  "smtp_config_file": "smtp_config.json"
}
```

## SMTP Provider Configuration

### Gmail

1. **Enable 2-Factor Authentication** in your Google Account
2. **Create App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Copy the 16-character password
3. **Configuration:**
   ```json
   {
     "smtp_server": "smtp.gmail.com",
     "smtp_port": 587,
     "use_ssl": false,
     "username": "your-email@gmail.com",
     "password": "your-16-char-app-password"
   }
   ```

### Outlook / Office 365

```json
{
  "smtp_server": "smtp.office365.com",
  "smtp_port": 587,
  "use_ssl": false,
  "username": "your-email@outlook.com",
  "password": "your-password"
}
```

### Yahoo Mail

```json
{
  "smtp_server": "smtp.mail.yahoo.com",
  "smtp_port": 587,
  "use_ssl": false,
  "username": "your-email@yahoo.com",
  "password": "your-app-password"
}
```

### Custom SMTP Server

```json
{
  "smtp_server": "mail.yourdomain.com",
  "smtp_port": 465,
  "use_ssl": true,
  "username": "you@yourdomain.com",
  "password": "your-password"
}
```

**Note:** 
- Port 587 = TLS (use `"use_ssl": false`)
- Port 465 = SSL (use `"use_ssl": true`)

## Email Format

The email will be sent in HTML format with:

### Subject
```
MAIL AUTOM CHECK ADVFN
```
(or custom subject from `smtp_config.json`)

### Body Header
```
Date, Open, High, Low, Close
```

### Stock Data
For each stock:
```
A2A - a2a
2026-04-21, Open: 2.5330, High: 2.5440, Low: 2.4950, Close: 2.5110

AZM - azimut
2026-04-21, Open: 34.9400, High: 35.1600, Low: 34.5100, Close: 35.0100
...
```

## Security Best Practices

### ⚠️ Never Commit smtp_config.json

The file is already in `.gitignore`. Never add it to git:

```bash
# WRONG - don't do this!
git add smtp_config.json

# Correct - it's automatically ignored
git status  # should not show smtp_config.json
```

### 🔒 Use App Passwords

For Gmail, Yahoo, and other providers, use **App Passwords** instead of your main account password.

### 🔐 Environment Variables (Optional)

For production/Lambda, consider using environment variables:

```python
import os

smtp_config = {
    "smtp_server": os.getenv("SMTP_SERVER"),
    "smtp_port": int(os.getenv("SMTP_PORT", 587)),
    "username": os.getenv("SMTP_USERNAME"),
    "password": os.getenv("SMTP_PASSWORD"),
    "recipients": os.getenv("SMTP_RECIPIENTS").split(",")
}
```

## Testing Email

### Test Locally

```bash
# Create smtp_config.json with your settings
cp smtp_config.example.json smtp_config.json
# Edit smtp_config.json

# Run with email enabled
python -c "
import lambda_handler
event = {'send_email': True}
lambda_handler.handler(event, None)
"
```

### Test in Lambda

Upload `smtp_config.json` with your Lambda deployment:

```bash
# Edit deploy_lambda.sh to include smtp_config.json
cp smtp_config.json lambda-package/
```

Then invoke with:
```bash
aws lambda invoke \
  --function-name scarica-azioni \
  --payload '{"send_email": true}' \
  output.json
```

## Troubleshooting

### "Authentication failed"
- Check username and password
- Use App Password for Gmail/Yahoo
- Enable "Less secure apps" (not recommended)

### "Connection refused"
- Check SMTP server and port
- Verify firewall settings
- Try different port (587 vs 465)

### "SSL/TLS error"
- Set correct `use_ssl` value:
  - Port 587 → `"use_ssl": false`
  - Port 465 → `"use_ssl": true`

### Email not received
- Check spam folder
- Verify recipient email addresses
- Check email server logs

### "SMTP config not found"
- Make sure `smtp_config.json` exists
- Verify file path in event
- For Lambda, ensure file is in deployment package

## Disabling Email

To fetch data without sending email:

**Python:**
```python
event = {"send_email": False}  # or just omit it
lambda_handler.handler(event, None)
```

**Lambda:**
```json
{
  "send_email": false
}
```

Default is `false` if not specified.
