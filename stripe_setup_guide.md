# 💳 Stripe Account Setup Guide - PDF Parser Pro

## Complete Step-by-Step Instructions for Payment Processing

---

## **PHASE 1: Create Stripe Account (5 minutes)**

### **Step 1: Sign Up**
1. Go to: **https://stripe.com**
2. Click **"Start now"** or **"Sign up"**
3. Enter your email and create password
4. Choose **"I'm creating an account for my own business"**

### **Step 2: Business Information**
Fill out these details:
```
Business Name: PDF Parser Pro (or your company name)
Business Type: Software/Technology Services
Country: United States (or your country)
Business Structure: LLC/Corporation/Sole Proprietorship
```

### **Step 3: Personal Information**
```
Full Name: [Your legal name]
Date of Birth: [Your DOB]
Address: [Your business/home address]
Phone: [Your phone number]
SSN: [Last 4 digits - US only]
```

### **Step 4: Bank Account**
```
Routing Number: [Your bank's routing number]
Account Number: [Your checking account number]
Account Holder Name: [Must match your legal name]
```

### **Step 5: Verify Email**
- Check your email for Stripe verification
- Click the verification link
- Complete email verification

---

## **PHASE 2: Configure Products & Pricing (10 minutes)**

### **Step 1: Create Products**

1. **Go to Dashboard** → **Products**
2. **Click "Add product"**
3. **Create each pricing tier:**

#### **Product 1: Growth Plan**
```
Name: PDF Parser Pro - Growth
Description: 2,000 pages/month with AI fallback
Pricing Model: Recurring
Price: $19.00 USD
Billing Period: Monthly
```

#### **Product 2: Business Plan**
```
Name: PDF Parser Pro - Business  
Description: 10,000 pages/month with advanced AI
Pricing Model: Recurring
Price: $79.00 USD
Billing Period: Monthly
```

#### **Product 3: Enterprise Plan**
```
Name: PDF Parser Pro - Enterprise
Description: 50,000 pages/month with priority AI
Pricing Model: Recurring  
Price: $299.00 USD
Billing Period: Monthly
```

#### **Product 4: Unlimited Plan**
```
Name: PDF Parser Pro - Unlimited
Description: Unlimited pages with all features
Pricing Model: Recurring
Price: $899.00 USD  
Billing Period: Monthly
```

### **Step 2: Get API Keys**
1. **Go to** → **Developers** → **API Keys**
2. **Copy these keys:**
   - **Publishable Key** (starts with `pk_test_`)
   - **Secret Key** (starts with `sk_test_`)

**⚠️ Important:** These are TEST keys. You'll get LIVE keys after account activation.

---

## **PHASE 3: Configure Webhooks (5 minutes)**

### **Step 1: Create Webhook Endpoint**
1. **Go to** → **Developers** → **Webhooks**
2. **Click "Add endpoint"**
3. **Endpoint URL:** `https://your-domain.com/webhook/stripe`
   - For testing: `https://yourdomain.ngrok.io/webhook/stripe`
4. **Events to send:**
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`

### **Step 2: Get Webhook Secret**
- After creating webhook, click on it
- Copy the **Signing secret** (starts with `whsec_`)

---

## **PHASE 4: Add Stripe to Your Code (10 minutes)**

### **Step 1: Install Stripe Library**
```bash
cd /Users/dronebassan/Desktop/pdf_parser
pip install stripe
```

### **Step 2: Add Environment Variables**
```bash
# Add these to your environment (replace with your actual keys)
export STRIPE_PUBLISHABLE_KEY="pk_test_your_key_here"
export STRIPE_SECRET_KEY="sk_test_your_key_here"
export STRIPE_WEBHOOK_SECRET="whsec_your_webhook_secret_here"
```

### **Step 3: Test Stripe Integration**
```bash
# Test that Stripe is working
python -c "
import stripe
import os
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_...')
print('✅ Stripe configured successfully!')
try:
    products = stripe.Product.list(limit=3)
    print(f'📦 Found {len(products.data)} products')
except Exception as e:
    print(f'❌ Stripe error: {e}')
"
```

---

## **PHASE 5: Account Verification (24-72 hours)**

### **Step 1: Identity Verification**
Stripe will ask for:
- **Government ID** (Driver's License/Passport)
- **Business Documents** (if applicable)
- **Bank Account Verification** (micro-deposits)

### **Step 2: Enable Live Mode**
After verification:
1. **Dashboard** → **Activate account**
2. **Switch to Live mode** (toggle in sidebar)
3. **Get Live API keys**:
   - `pk_live_...` (Publishable)
   - `sk_live_...` (Secret)

### **Step 3: Update Production Keys**
```bash
# Replace test keys with live keys
export STRIPE_PUBLISHABLE_KEY="pk_live_your_live_key"
export STRIPE_SECRET_KEY="sk_live_your_live_key"
```

---

## **PHASE 6: Test Payment Flow (5 minutes)**

### **Step 1: Create Test Customer**
```bash
curl -X POST https://api.stripe.com/v1/customers \
  -u sk_test_your_key: \
  -d email="test@example.com" \
  -d name="Test Customer"
```

### **Step 2: Test Subscription**
Use Stripe's test card numbers:
- **Success:** `4242424242424242`
- **Decline:** `4000000000000002`
- **CVV:** `123`, **Expiry:** `12/26`

### **Step 3: Monitor Dashboard**
- Check **Dashboard** → **Payments**
- Verify test transactions appear

---

## **PHASE 7: Production Checklist**

### **Security Settings**
- [ ] **Enable 2FA** on your Stripe account
- [ ] **Restrict API keys** to specific IP addresses (production)
- [ ] **Set up webhook signature verification**
- [ ] **Enable fraud protection** (Radar)

### **Business Settings**
- [ ] **Set business name** and logo
- [ ] **Configure receipt emails**
- [ ] **Set up tax collection** (if required)
- [ ] **Configure refund policy**

### **Integration Testing**
- [ ] **Test successful payments**
- [ ] **Test failed payments**
- [ ] **Test subscription creation**
- [ ] **Test subscription cancellation**
- [ ] **Test webhook handling**

---

## **PHASE 8: Go Live Checklist**

### **Before Launch:**
1. ✅ **Account verified** and activated
2. ✅ **Live API keys** configured
3. ✅ **Webhook endpoints** working
4. ✅ **SSL certificate** installed
5. ✅ **Test transactions** successful
6. ✅ **Customer support** process ready

### **Launch Day:**
1. **Switch to live keys**
2. **Update webhook URLs**
3. **Test one real payment**
4. **Monitor for issues**
5. **Have support ready**

---

## **Expected Timeline:**

```
Day 1: Account creation + Product setup (15 minutes)
Day 1-3: Identity verification (automatic)
Day 3: Account activation + Live keys
Day 3: Production deployment
Day 4: Launch! 🚀
```

---

## **Common Issues & Solutions:**

### **❌ "Account Under Review"**
- **Solution:** Wait 24-72 hours, provide requested documents
- **Speed up:** Contact Stripe support with business details

### **❌ "Invalid API Key"**
- **Solution:** Double-check you're using the right key for test/live mode
- **Check:** Key format (`pk_test_` vs `pk_live_`)

### **❌ "Webhook Signature Mismatch"**
- **Solution:** Verify webhook secret is correct
- **Check:** Endpoint URL is accessible and uses HTTPS

### **❌ "Payment Failed"**
- **Solution:** Use test card numbers in test mode
- **Live mode:** Check customer's actual card details

---

## **Cost Structure:**

### **Stripe Fees:**
- **2.9% + 30¢** per successful charge
- **No monthly fees**
- **No setup fees**

### **Your Revenue After Fees:**
```
Growth Plan ($19):    $18.45 after Stripe fees
Business Plan ($79):  $76.61 after Stripe fees  
Enterprise ($299):    $290.33 after Stripe fees
Unlimited ($899):     $872.39 after Stripe fees
```

### **Break-even Analysis:**
- **$19 plan:** Covers ~1,900 pages of Gemini AI processing
- **$79 plan:** Covers ~7,900 pages of Gemini AI processing
- **$299 plan:** Massive profit margin with page-by-page optimization

---

## **Next Steps After Stripe Setup:**

1. ✅ **Test payment flow** with real card
2. 🚀 **Deploy to production** server
3. 📢 **Launch marketing** campaigns
4. 💰 **Start making money!**

---

## **Support Resources:**

- **Stripe Documentation:** https://stripe.com/docs
- **Stripe Support:** https://support.stripe.com
- **Test Cards:** https://stripe.com/docs/testing
- **Webhook Testing:** https://stripe.com/docs/webhooks/test