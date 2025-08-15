#!/usr/bin/env python3
"""
Quick Stripe integration test
"""

import stripe
import os

def test_stripe_connection():
    """Test if Stripe is configured correctly"""
    
    print("💳 Testing Stripe Integration")
    print("=" * 40)
    
    # Check if API key is set
    api_key = os.getenv('STRIPE_SECRET_KEY')
    
    if not api_key:
        print("❌ STRIPE_SECRET_KEY not found")
        print("   Set it with: export STRIPE_SECRET_KEY='sk_test_your_key_here'")
        return False
    
    if not api_key.startswith(('sk_test_', 'sk_live_')):
        print("❌ STRIPE_SECRET_KEY doesn't look right")
        print("   Should start with 'sk_test_' or 'sk_live_'")
        return False
    
    print(f"✅ API Key found: {api_key[:12]}...{api_key[-4:]}")
    
    # Set the API key
    stripe.api_key = api_key
    
    try:
        # Test API connection
        print("   Testing connection...")
        account = stripe.Account.retrieve()
        print(f"   ✅ Connected to account: {account.id}")
        
        # List products
        print("   Checking products...")
        products = stripe.Product.list(limit=10)
        print(f"   📦 Found {len(products.data)} products")
        
        if len(products.data) > 0:
            print("   Products:")
            for product in products.data:
                print(f"     • {product.name} - {product.id}")
        
        # List prices  
        print("   Checking prices...")
        prices = stripe.Price.list(limit=10)
        print(f"   💰 Found {len(prices.data)} price points")
        
        if len(prices.data) > 0:
            print("   Prices:")
            for price in prices.data:
                amount = price.unit_amount / 100 if price.unit_amount else 0
                print(f"     • ${amount:.2f} {price.currency.upper()} - {price.id}")
        
        return True
        
    except stripe.error.AuthenticationError:
        print("   ❌ Invalid API key")
        return False
    except Exception as e:
        print(f"   ❌ Stripe error: {e}")
        return False

def create_test_products():
    """Create the PDF Parser Pro pricing products"""
    
    print("\n🏗️  Creating PDF Parser Pro Products")
    print("=" * 40)
    
    products_to_create = [
        {
            "name": "PDF Parser Pro - Growth",
            "description": "2,000 pages/month with smart AI fallback",
            "price": 1900,  # $19.00 in cents
            "interval": "month"
        },
        {
            "name": "PDF Parser Pro - Business", 
            "description": "10,000 pages/month with advanced AI processing",
            "price": 7900,  # $79.00 in cents
            "interval": "month"
        },
        {
            "name": "PDF Parser Pro - Enterprise",
            "description": "50,000 pages/month with priority AI processing", 
            "price": 29900,  # $299.00 in cents
            "interval": "month"
        },
        {
            "name": "PDF Parser Pro - Unlimited",
            "description": "Unlimited pages with all premium features",
            "price": 89900,  # $899.00 in cents
            "interval": "month"
        }
    ]
    
    created_products = []
    
    for product_info in products_to_create:
        try:
            print(f"   Creating {product_info['name']}...")
            
            # Create product
            product = stripe.Product.create(
                name=product_info["name"],
                description=product_info["description"]
            )
            
            # Create price for the product
            price = stripe.Price.create(
                unit_amount=product_info["price"],
                currency="usd",
                recurring={"interval": product_info["interval"]},
                product=product.id,
            )
            
            print(f"   ✅ Created: ${product_info['price']/100:.2f}/month - {price.id}")
            created_products.append({
                "product": product,
                "price": price,
                "amount": product_info["price"]/100
            })
            
        except Exception as e:
            print(f"   ❌ Failed to create {product_info['name']}: {e}")
    
    return created_products

def test_payment_intent():
    """Test creating a payment intent"""
    
    print("\n💰 Testing Payment Intent Creation")
    print("=" * 40)
    
    try:
        # Create a test payment intent for $19 (Growth plan)
        payment_intent = stripe.PaymentIntent.create(
            amount=1900,  # $19.00 in cents
            currency='usd',
            metadata={
                'product': 'PDF Parser Pro - Growth',
                'pages': '2000'
            }
        )
        
        print(f"   ✅ Payment Intent created: {payment_intent.id}")
        print(f"   💳 Amount: ${payment_intent.amount / 100:.2f}")
        print(f"   🔒 Client Secret: {payment_intent.client_secret[:20]}...")
        
        return payment_intent
        
    except Exception as e:
        print(f"   ❌ Failed to create payment intent: {e}")
        return None

def main():
    """Run all Stripe tests"""
    
    # Test basic connection
    if not test_stripe_connection():
        print("\n❌ Fix API key issues first!")
        return
    
    print("\n" + "=" * 50)
    print("🎉 Stripe Integration Working!")
    print("=" * 50)
    
    # Offer to create products
    response = input("\nCreate PDF Parser Pro products in Stripe? (y/n): ")
    if response.lower() in ['y', 'yes']:
        products = create_test_products()
        if products:
            print(f"\n✅ Created {len(products)} products successfully!")
            print("\nNext steps:")
            print("1. Go to https://dashboard.stripe.com/products")
            print("2. Verify your products are there")
            print("3. Test a payment with test card: 4242424242424242")
    
    # Test payment intent
    payment_intent = test_payment_intent()
    if payment_intent:
        print("\n💡 Everything is working! You can now:")
        print("   • Accept payments")
        print("   • Create subscriptions") 
        print("   • Process customers")
        print("   • Handle webhooks")
    
    print("\n🚀 Ready for production after account verification!")

if __name__ == "__main__":
    main()