# ⚡ Quick Deploy Reference Card

## 🚀 Deploy in 5 Minutes

### 1. Configure Environment (2 min)
```bash
cp .env.production.example .env
nano .env  # Update: DEBUG, SECRET_KEY, ALLOWED_HOSTS, DB_*, EMAIL_*, RAZORPAY_*
```

### 2. Run Deployment Script (2 min)
```bash
# Linux/Mac
chmod +x deploy.sh
./deploy.sh

# Windows
.\deploy.ps1
```

### 3. Create Admin User (1 min)
```bash
python manage.py createsuperuser
```

### 4. Start Application
```bash
# Development
python manage.py runserver

# Production
gunicorn food_ordering.wsgi:application --bind 0.0.0.0:8000
```

---

## 🐳 Docker Quick Deploy

```bash
# 1. Configure .env
cp .env.production.example .env

# 2. Build and start
docker-compose up -d --build

# 3. Migrate and create admin
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# 4. Access at http://localhost:8000
```

---

## ☁️ Heroku Quick Deploy

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
heroku open
```

---

## 🔍 Health Check

```bash
curl http://localhost:8000/health/
# Expected: {"status": "healthy", "checks": {"database": "ok"}}
```

---

## 📚 Full Documentation

- **Comprehensive Guide**: `PRODUCTION_DEPLOYMENT.md`
- **Checklist**: `HOSTING_READY_CHECKLIST.md`
- **Summary**: `HOSTING_READY_SUMMARY.md`

---

## ⚠️ Critical Settings

```bash
# Production .env must have:
DEBUG=False
SECRET_KEY=<new-generated-key>
ALLOWED_HOSTS=yourdomain.com
DB_PASSWORD=<strong-password>
RAZORPAY_KEY_ID=rzp_live_XXXXXXXX  # NOT test keys!
```

---

## 🎯 Access Points

- **Home**: `http://yourdomain.com/`
- **Admin**: `http://yourdomain.com/admin/`
- **Health**: `http://yourdomain.com/health/`
- **API Docs**: See `PRODUCTION_DEPLOYMENT.md`

---

**Status**: ✅ PRODUCTION READY
