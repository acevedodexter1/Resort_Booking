# 📧 Email Setup — Paradise Resort

## ✅ Easiest Method (Recommended — works on Windows, Mac, Linux)

### Step 1 — Find the `.env.example` file in your `resort_flask/` folder

### Step 2 — Copy it and rename the copy to `.env`
```
resort_flask/
  ├── .env.example   ← original (keep this)
  ├── .env           ← your copy (fill this in)
  ├── run.py
  └── app/
```

### Step 3 — Open `.env` with Notepad (or VS Code) and fill in your details:
```
SMTP_USER=acevedodexter1@gmail.com
SMTP_PASS=degv sdjn updw hbjw
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM=Paradise Resort
```
> ⚠️ The App Password spaces are fine — just paste it as-is.

### Step 4 — Save the `.env` file, then restart:
```
python run.py
```

You should see:
```
✅ Email: Configured (acevedodexter1@gmail.com)
```

---

## How to get a Gmail App Password

1. Go to your Google Account → **Security**
2. Make sure **2-Step Verification is ON**
3. Go to: https://myaccount.google.com/apppasswords
4. App: **Mail** · Device: **Other** → type `Paradise Resort`
5. Click **Generate** — copy the 16-character password
6. Paste it into your `.env` file as `SMTP_PASS=xxxx xxxx xxxx xxxx`

---

## What emails are sent automatically

| When | Email Subject |
|------|--------------|
| New account registered | Welcome to Paradise Resort! |
| Booking confirmed | Booking Confirmed — Paradise Resort #ID |
| Booking cancelled | Booking Cancelled & Refund Initiated — #ID |

## Notes
- Guests need an email saved in **My Profile** to receive emails
- If `.env` is missing or incomplete, the app still works — emails are just skipped
- The booking receipt modal will show whether the email was sent successfully
