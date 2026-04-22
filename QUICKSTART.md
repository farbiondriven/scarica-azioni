# Quick Start

## 1. Run Locally

```bash
# No config needed - uses defaults
python lambda_handler.py
```

Output: `eod_data.csv`

---

## 2. Enable Email

**Create config.json:**
```json
{
  "send_email": true,
  "smtp": {
    "server": "smtp.gmail.com",
    "port": 587,
    "username": "you@gmail.com",
    "password": "your-app-password",
    "recipients": ["recipient@example.com"]
  }
}
```

**Run:**
```bash
python lambda_handler.py
```

---

## 3. Windows .exe

**Build:**
```bash
uv run pyinstaller scarica-azioni.spec
```

**Use:**
- Copy `dist/scarica-azioni.exe` to Windows
- Add `titoli_check.txt` (required)
- Add `config.json` (optional - for email)
- Double-click `.exe`

---

## 4. AWS Lambda

**Deploy:**
```bash
./deploy_lambda.sh
```

**Invoke:**
```bash
aws lambda invoke --function-name scarica-azioni output.json
```

---

## That's it!

- No config? → Saves to CSV
- With config + `send_email: true`? → Saves CSV + sends email
- One file (`config.json`) for everything
