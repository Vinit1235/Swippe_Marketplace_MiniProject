# 🔑 API Keys Setup Guide

Complete guide for obtaining and configuring all API keys required for Swippe.

---

## 🤖 Gemini AI API Key (For RAG Chatbot)

### Step-by-Step Instructions

1. **Visit Google AI Studio**
   - URL: https://ai.google.dev/
   - Click the **"Get API key"** button

2. **Sign In**
   - Use your Google account
   - If you don't have one, create a free Gmail account

3. **Create or Select Project**
   - You'll see "Create API key" dialog
   - Choose "Create API key in new project" OR select existing Google Cloud project
   - Click **"Create API key"**

4. **Copy Your API Key**
   - You'll see a key starting with `AIza...`
   - Example: `AIzaSyBXXXXXXXXXXXXXXXXXXXXXXXXX`
   - **⚠️ IMPORTANT**: Copy this key immediately (you won't see it again)

5. **Add to .env File**
   ```env
   GEMINI_API_KEY=AIzaSyBXXXXXXXXXXXXXXXXXXXXXXXXX
   ```

### Free Tier Limits
- ✅ **1,500 requests per day**
- ✅ **1 million tokens per month**
- ✅ **Perfect for testing and demos**
- ✅ **No credit card required**

### Troubleshooting
- ❌ "API key not valid": Make sure you copied the entire key
- ❌ "Quota exceeded": Wait 24 hours or upgrade to paid tier
- ❌ "API not enabled": Visit Google Cloud Console and enable Gemini API

---

## 📧 Gmail App Password (For Email System)

### Prerequisites
- Gmail account
- 2-Step Verification **must be enabled**

### Step-by-Step Instructions

1. **Enable 2-Step Verification** (if not already enabled)
   - Go to: https://myaccount.google.com/
   - Click **Security** (left sidebar)
   - Scroll to "How you sign in to Google"
   - Click **2-Step Verification**
   - Click **Get Started** and follow the prompts

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Or: Google Account → Security → 2-Step Verification → App passwords
   
3. **Create New App Password**
   - Select app: **Mail**
   - Select device: **Other (Custom name)**
   - Name it: **Swippe**
   - Click **Generate**

4. **Copy the 16-Character Password**
   - You'll see something like: `abcd efgh ijkl mnop`
   - Example: `xmyl zyxw vuts rqpo`
   - **⚠️ IMPORTANT**: Copy this password (you won't see it again)

5. **Add to .env File**
   ```env
   EMAIL_SMTP_SERVER=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_SENDER=your-email@gmail.com
   EMAIL_PASSWORD=abcd efgh ijkl mnop
   ```

### Security Notes
- ✅ App passwords are more secure than your main password
- ✅ You can revoke app passwords anytime
- ✅ Each app gets its own unique password
- ⚠️ Never share your app password publicly

### Troubleshooting
- ❌ "App passwords option not showing": Enable 2-Step Verification first
- ❌ "Authentication failed": Check that you copied the entire password (with spaces)
- ❌ "Less secure app access": Use App Password, not your regular password
- ❌ "SMTPAuthenticationError": Verify email and app password are correct

---

## 🗄️ Database Configuration (Optional - For PostgreSQL on Render)

### When to Use
- Only needed if deploying to Render or other cloud platforms
- Local development uses SQLite (no configuration needed)

### Render PostgreSQL Setup

1. **Create Render Account**
   - Go to: https://render.com/
   - Sign up with GitHub account (free)

2. **Create PostgreSQL Database**
   - Dashboard → **New +** → **PostgreSQL**
   - Name: `swippe-db`
   - Database: `swippe`
   - User: `swippe_user`
   - Region: Choose closest to you
   - Plan: **Free** (500MB storage)
   - Click **Create Database**

3. **Copy External Database URL**
   - After creation, find **External Database URL**
   - Example: `postgresql://user:pass@host.render.com:5432/dbname`

4. **Add to .env File** (for local testing)
   ```env
   DATABASE_URL=postgresql://user:pass@host.render.com:5432/dbname
   ```

### Free Tier Limits
- ✅ 500 MB storage
- ✅ Expires after 90 days (free tier)
- ✅ Automatic backups
- ⚠️ Database will be deleted if inactive

---

## 🔐 Flask Secret Key (Required for Production)

### For Local Development
The default key is fine:
```env
SECRET_KEY=dev-secret-key-change-in-production
```

### For Production (Render, Heroku, etc.)

1. **Generate Secure Random Key**
   
   **Option A: Python**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   
   **Option B: PowerShell**
   ```powershell
   -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | % {[char]$_})
   ```

2. **Add to .env File**
   ```env
   SECRET_KEY=your-super-secret-random-key-here-64-characters-long
   ```

### Security Notes
- ✅ Use at least 32 characters
- ✅ Include letters, numbers, and symbols
- ✅ Never commit to Git
- ⚠️ Changing this will log out all users

---

## 📋 Complete .env File Template

Here's what your `.env` file should look like:

```env
# ==================================================
# SWIPPE ENVIRONMENT CONFIGURATION
# ==================================================

# ===== GEMINI AI (RAG Chatbot) =====
# Get from: https://ai.google.dev/
GEMINI_API_KEY=your_gemini_api_key_here

# ===== EMAIL SYSTEM =====
# Gmail SMTP Configuration
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password-here
EMAIL_SENDER_NAME=Swippe Quick Commerce

# ===== DATABASE (Optional - for Render deployment) =====
# Leave empty for local SQLite
# DATABASE_URL=postgresql://user:pass@host:5432/database

# ===== FLASK CONFIGURATION =====
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development

# ===== OPENAI (Optional - if using ChatGPT instead of Gemini) =====
# OPENAI_API_KEY=sk-your-openai-key-here
```

---

## ✅ Verification Checklist

Run this test to verify all API keys:

```bash
python test_systems.py
```

Expected output:
```
✅ PASSED: Database Connection
✅ PASSED: RAG Chatbot System
✅ PASSED: Email System
✅ PASSED: Routine Delivery System

Results: 4/4 systems operational
🎉 All systems operational!
```

---

## 🚫 What You DON'T Need

These are **NOT required** for Swippe:

- ❌ OpenAI API Key (we use Gemini instead)
- ❌ AWS Credentials
- ❌ Azure Keys
- ❌ Stripe/Payment Gateway (demo project)
- ❌ Twilio/SMS Services
- ❌ Google Maps API (using OSM)

---

## 💰 Cost Breakdown

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Gemini AI** | 1,500 req/day | $0.00025/1K tokens |
| **Gmail SMTP** | Free forever | N/A |
| **Render PostgreSQL** | 500MB (90 days) | $7/month |
| **Render Web Service** | 750 hours/month | $7/month |
| **TOTAL** | **$0/month** | ~$14/month (optional) |

**For LinkedIn demo**: Everything is **FREE**! ✅

---

## 🔒 Security Best Practices

### DO ✅
- Keep `.env` file in `.gitignore`
- Use app passwords instead of main passwords
- Regenerate keys if accidentally exposed
- Use different keys for dev/production
- Enable 2FA on all accounts

### DON'T ❌
- Commit `.env` to Git
- Share API keys in screenshots
- Use production keys in development
- Hard-code keys in source code
- Share keys on LinkedIn posts

---

## 🆘 Troubleshooting

### "GEMINI_API_KEY not found"
**Solution**: Check `.env` file has `GEMINI_API_KEY=AIza...`

### "Email authentication failed"
**Solution**: 
1. Verify 2-Step Verification is enabled
2. Generate new App Password
3. Copy password with spaces: `xxxx xxxx xxxx xxxx`

### "Database connection error"
**Solution**: 
- Local: No DATABASE_URL needed (uses SQLite)
- Render: Check External Database URL is correct

### "ModuleNotFoundError"
**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 📚 Additional Resources

- **Gemini API Docs**: https://ai.google.dev/docs
- **Gmail App Passwords**: https://support.google.com/accounts/answer/185833
- **Render Docs**: https://render.com/docs
- **Flask Security**: https://flask.palletsprojects.com/en/3.0.x/config/

---

## 🎯 Quick Start

1. **Copy template** above to `.env` file
2. **Get Gemini key** from https://ai.google.dev/
3. **Get Gmail app password** from Google Account
4. **Run tests**: `python test_systems.py`
5. **Start server**: `python app.py`
6. **Record demo**: http://127.0.0.1:5000

---

**Last Updated**: November 2025  
**For**: LinkedIn Demo (Copyright-Safe)  
**Status**: Production Ready ✅

---

**Need Help?** All API keys are free for testing! No credit card required. 🎉
