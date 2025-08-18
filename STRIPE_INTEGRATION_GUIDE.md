# 🚀 PDF Parser Pro - Complete Integration Guide

## ✅ AUTHENTICATION & BILLING SYSTEM COMPLETE!

Your PDF Parser now has **full user authentication, usage tracking, and Stripe billing integration**. Here's how everything works:

---

## 🔄 **Complete Customer Journey**

### **Step 1: Customer Registration**
```bash
POST /auth/register
{
  "email": "customer@example.com",
  "plan_type": "growth"
}
```
**Response**: Customer gets API key for authentication

### **Step 2: Payment via Stripe**
```bash
POST /create-checkout-session/
{
  "plan_type": "growth",
  "customer_email": "customer@example.com",
  "success_url": "https://yoursite.com/success",
  "cancel_url": "https://yoursite.com/cancel"
}
```
**Response**: Stripe checkout URL

### **Step 3: Webhook Auto-Setup**
When customer pays → Stripe sends webhook → Your app automatically:
- ✅ Creates user account (if needed)
- ✅ Sets usage limits (e.g., 2,500 pages for Growth)
- ✅ Activates subscription

### **Step 4: Customer Uses Service**
```bash
POST /parse/
Headers: Authorization: Bearer pdf_parser_ABC123...
Body: PDF file
```
**Your app automatically**:
- ✅ Checks authentication
- ✅ Verifies usage limits
- ✅ Processes PDF
- ✅ Tracks usage for billing

---

## 💳 **How Usage Limits Work**

| Plan | Monthly Pages | Overage Rate | What Happens |
|------|---------------|--------------|--------------|
| Free (no auth) | 5 per upload | N/A | Library processing only |
| Student | 500 | $0.01/page | Full AI features |
| Growth | 2,500 | $0.008/page | Priority processing |
| Business | 10,000 | $0.008/page | Advanced features |
| Enterprise | 50,000 | $0.006/page | Dedicated resources |

### **Access Control Logic**:
1. **Unauthenticated users**: Max 5 pages, basic processing only
2. **Authenticated users**: Full limits based on their plan
3. **Over limit**: Automatic overage billing via Stripe

---

## 🔧 **Stripe Setup Instructions**

### **BEFORE Hosting (Recommended)**

#### **1. Create Stripe Account**
- Go to [stripe.com](https://stripe.com)
- Create account → Get test keys

#### **2. Set Environment Variables**
```bash
# Add to your .env file or hosting platform
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
JWT_SECRET_KEY=your-random-secret-key

# Optional: Add these for production
STRIPE_STUDENT_PRICE_ID=price_...
STRIPE_GROWTH_PRICE_ID=price_...
STRIPE_BUSINESS_PRICE_ID=price_...
STRIPE_ENTERPRISE_PRICE_ID=price_...
```

#### **3. Create Products in Stripe Dashboard**
1. **Products & Pricing** → **Create Product**
2. Create 4 products: Student, Growth, Business, Enterprise
3. Set monthly recurring prices: $4.99, $19.99, $79.99, $299.99
4. Copy the `price_id` for each → Add to env vars

#### **4. Set Up Webhooks**
1. **Developers** → **Webhooks** → **Add endpoint**
2. **Endpoint URL**: `https://yourdomain.com/stripe-webhook/`
3. **Events to send**:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`

#### **5. Test Locally**
```bash
# Use Stripe test cards
4242 4242 4242 4242  # Visa
4000 0000 0000 0002  # Declined

# Test webhook with Stripe CLI
stripe listen --forward-to localhost:8000/stripe-webhook/
```

---

## 🌐 **Deployment Instructions**

### **Option 1: Railway (Recommended)**
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and deploy
railway login
railway link  # Link to existing project or create new
railway up

# 3. Set environment variables in Railway dashboard
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
JWT_SECRET_KEY=your-production-secret
```

### **Option 2: Render**
1. Connect GitHub repo
2. Set environment variables in dashboard
3. Deploy automatically

### **Option 3: Docker**
```bash
docker build -t pdf-parser-pro .
docker run -p 8000:8000 pdf-parser-pro
```

---

## 🧪 **Testing the Complete Flow**

### **1. Test User Registration**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "plan_type": "growth"}'
```

### **2. Test PDF Processing (with auth)**
```bash
curl -X POST http://localhost:8000/parse/ \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@sample.pdf"
```

### **3. Test Usage Tracking**
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## 🔒 **Security Features Built-In**

- ✅ **API Key Authentication**: Each user gets unique key
- ✅ **Usage Limits**: Automatic enforcement per plan
- ✅ **Webhook Verification**: Stripe signature validation
- ✅ **SQL Injection Protection**: SQLite with parameterized queries
- ✅ **File Validation**: PDF-only uploads
- ✅ **Temporary Files**: Auto-cleanup after processing

---

## 📊 **Available API Endpoints**

| Endpoint | Method | Auth Required | Purpose |
|----------|--------|---------------|---------|
| `/` | GET | No | Web interface |
| `/pricing` | GET | No | Pricing page |
| `/auth/register` | POST | No | Create account |
| `/auth/login` | POST | No | Verify credentials |
| `/auth/me` | GET | Yes | User info & usage |
| `/parse/` | POST | Optional | Process PDF |
| `/create-checkout-session/` | POST | No | Start payment |
| `/stripe-webhook/` | POST | No | Handle payments |
| `/usage/{user_id}` | GET | Yes | Usage details |

---

## 🚨 **Switch to Production**

When ready to go live:

1. **Update Stripe keys** to live mode (`sk_live_...`)
2. **Update webhook endpoint** to production URL
3. **Test with real payment** (small amount)
4. **Monitor logs** for any issues

---

## 💡 **Pro Tips**

1. **Start with test mode** - Use Stripe test cards first
2. **Monitor webhooks** - Check Stripe dashboard for delivery status
3. **Handle failures gracefully** - Webhook retries are automatic
4. **Keep API keys secure** - Never commit to git
5. **Use HTTPS in production** - Required for webhooks

---

Your app is now **production-ready** with full authentication, billing, and usage tracking! 🎉