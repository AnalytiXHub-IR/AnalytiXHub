# Render Deployment Guide - OpenChain IR

## Free Deployment on Render ✅

Your Flask application is now configured for **FREE deployment** on Render!

### Step 1: Prepare Your GitHub Repository

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Render deployment ready"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/openchain-ir.git
   git push -u origin main
   ```

### Step 2: Create Render Account & Deploy

1. **Go to [Render.com](https://render.com)**
2. **Sign up with GitHub** (free tier available)
3. **Create a New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `openchain-ir` repo

### Step 3: Configure Render

**In the Render dashboard, set these values:**

| Setting | Value |
|---------|-------|
| Name | `openchain-ir` |
| Environment | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Instance Type | **Free** ✅ |

### Step 4: Add Environment Variables

In Render dashboard → Environment:

```
ETHERSCAN_API_KEY=<your-etherscan-api-key>
GEMINI_API_KEY=<your-gemini-api-key>
FLASK_ENV=production
```

**Get Free API Keys:**
- **Etherscan:** [https://etherscan.io/apis](https://etherscan.io/apis) (free tier)
- **Google Gemini:** [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) (free tier)

### Step 5: Deploy!

1. Click **"Deploy"** button
2. Wait ~2-5 minutes for build & deployment
3. Your app will be live at: `https://openchain-ir.onrender.com` (or similar)

---

## Files Created for Render

✅ **render.yaml** - Render configuration  
✅ **Procfile** - Process file for web service  
✅ **build.sh** - Build script  
✅ **requirements.txt** - Updated with gunicorn  
✅ **app.py** - Updated for dynamic port binding  

---

## Free Tier Limitations

| Feature | Free Tier |
|---------|-----------|
| Deployment | ✅ Yes |
| Custom Domain | ✅ Yes (with paid tier) |
| Database | ✅ PostgreSQL available (paid) |
| Sleep Mode | May sleep after 15 min inactivity |
| Bandwidth | Limited |

**For Production:** Upgrade to paid tier ($7/month minimum)

---

## Troubleshooting

### "Build failed"
- Check `requirements.txt` has no conflicting versions
- Ensure all imports in Python files are available

### "App keeps crashing"
- Check environment variables are set correctly
- Review app logs in Render dashboard
- Ensure port is using `os.getenv("PORT", 5000)`

### "Database connection issues"
- You may need to use Render's PostgreSQL service (free tier: limited)
- Or use cloud-hosted PostgreSQL alternative

---

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Connect Render to GitHub
3. ✅ Add environment variables
4. ✅ Deploy!
5. Test your live app at the provided URL

**Your app is now production-ready! 🚀**
