# Online Payment Implementation Guide

## Overview
Successfully implemented **Razorpay Payment Gateway** integration for secure online payments in the food ordering system. Customers can now choose between Cash on Delivery and Online Payment options during checkout.

---

## Features Implemented

### 1. Payment Options
- **Cash on Delivery (COD)**: Pay with cash upon order delivery
- **Online Payment**: Secure payment via Razorpay supporting:
  - UPI (Google Pay, PhonePe, Paytm, etc.)
  - Credit/Debit Cards (Visa, Mastercard, RuPay, American Express)
  - Net Banking
  - Wallets (Paytm, MobiKwik, Freecharge, etc.)

### 2. Security Features
- **Payment Signature Verification**: HMAC-SHA256 signature validation
- **SSL/TLS Encryption**: All payment data encrypted in transit
- **PCI DSS Compliance**: Razorpay handles sensitive card data
- **Order Ownership Verification**: Users can only pay for their own orders
- **CSRF Protection**: Django CSRF tokens prevent request forgery
- **No Sensitive Data Storage**: Only transaction IDs stored, not card details

### 3. User Experience
- **Seamless Checkout Flow**: Choose payment method before placing order
- **Real-time Payment Processing**: Immediate payment confirmation
- **Multiple Payment Methods**: Support for all major payment methods in India
- **Payment Retry**: Failed payments can be retried
- **Order Tracking**: Payment status tracked throughout order lifecycle

---

## Files Modified/Created

### Backend Files

#### 1. **orders/models.py**
- Added payment-related fields to `Order` model:
  ```python
  - payment_method: Choice between 'cod' and 'online'
  - payment_status: Tracks payment state (pending, processing, completed, failed, refunded)
  - razorpay_order_id: Razorpay order identifier
  - razorpay_payment_id: Payment transaction ID
  - razorpay_signature: Payment signature for verification
  ```

#### 2. **customer/forms.py**
- Added `payment_method` field to `CheckoutForm`
- Radio button selection with visual card-style UI

#### 3. **core/payment_utils.py** (NEW)
- `create_razorpay_order()`: Creates Razorpay payment order
- `verify_razorpay_payment()`: Verifies payment signature (critical security function)
- `get_payment_details()`: Fetches payment information from Razorpay
- `refund_payment()`: Processes refunds for cancelled orders
- `convert_to_rupees()` / `convert_to_paise()`: Currency conversion helpers

#### 4. **customer/views.py**
- Updated `checkout()` view to handle payment method selection
- Added `process_payment()` view for payment page
- Added `verify_payment()` view for payment verification callback
- Payment flow logic:
  - COD: Create order → Send email → Clear cart → Success page
  - Online: Create order → Create Razorpay order → Payment page → Verify → Success page

#### 5. **customer/urls.py**
- Added payment processing URL patterns:
  ```python
  path('payment/<uuid:order_id>/', views.process_payment, name='process_payment')
  path('payment/verify/', views.verify_payment, name='verify_payment')
  ```

### Frontend Files

#### 6. **templates/customer/checkout.html**
- Added payment method selection UI
- Visual card-style radio buttons for payment options
- Payment method icons and descriptions
- Razorpay security badge

#### 7. **templates/customer/process_payment.html** (NEW)
- Payment processing page with Razorpay integration
- Razorpay Checkout script integration
- Order summary display
- Payment instructions
- Security badges (SSL, PCI DSS, Verified)
- JavaScript payment handling and verification

### Configuration Files

#### 8. **requirements.txt**
- Added `razorpay==1.4.1` package

#### 9. **.env**
- Added Razorpay API credentials:
  ```env
  RAZORPAY_KEY_ID=rzp_test_XXXXXXXXX
  RAZORPAY_KEY_SECRET=your_secret_key_here
  ```

#### 10. **food_ordering/settings.py**
- Added Razorpay configuration:
  ```python
  RAZORPAY_KEY_ID
  RAZORPAY_KEY_SECRET
  RAZORPAY_CURRENCY = 'INR'
  RAZORPAY_PAYMENT_TIMEOUT = 900  # 15 minutes
  ```

---

## Setup Instructions

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Get Razorpay API Keys
1. Sign up at [Razorpay Dashboard](https://dashboard.razorpay.com/)
2. Navigate to Settings → API Keys
3. Generate Test API Keys for development
4. For production, generate Live API Keys

### Step 3: Configure Environment Variables
Update `.env` file with your Razorpay credentials:
```env
RAZORPAY_KEY_ID=rzp_test_YOUR_KEY_ID
RAZORPAY_KEY_SECRET=YOUR_SECRET_KEY
```

### Step 4: Create Database Migrations
```bash
python manage.py makemigrations orders
python manage.py migrate
```

### Step 5: Test Payment Flow
1. Start development server: `python manage.py runserver`
2. Add items to cart
3. Proceed to checkout
4. Select "Online Payment" method
5. Complete checkout form
6. On payment page, click "Proceed to Pay"
7. Use Razorpay test cards:
   - **Success**: 4111 1111 1111 1111
   - **Failure**: 4000 0000 0000 0002
   - CVV: Any 3 digits
   - Expiry: Any future date

---

## Payment Flow Diagram

```
Customer Cart
    ↓
Checkout Page (Select Payment Method)
    ↓
    ├─ Cash on Delivery
    │   ├─ Create Order
    │   ├─ Send Confirmation Email
    │   ├─ Clear Cart
    │   └─ Order Success Page
    │
    └─ Online Payment
        ├─ Create Order (pending)
        ├─ Create Razorpay Order
        ├─ Payment Processing Page
        ├─ Razorpay Checkout Modal
        │   ├─ Select Payment Method
        │   ├─ Enter Payment Details
        │   └─ Complete Payment
        ├─ Verify Payment Signature ✓
        ├─ Update Order Status (completed)
        ├─ Send Confirmation Email
        ├─ Clear Cart
        └─ Order Success Page
```

---

## Security Considerations

### 1. Payment Signature Verification
**Critical**: Always verify Razorpay payment signature server-side using HMAC-SHA256.
```python
# This prevents payment tampering and ensures authenticity
is_valid = verify_razorpay_payment(order_id, payment_id, signature)
```

### 2. Never Trust Client-Side Data
- Payment verification MUST happen server-side
- Never accept payment confirmation from client without verification
- All payment data validated against Razorpay's signature

### 3. Order Ownership Verification
```python
# Ensure user can only pay for their own orders
order = get_object_or_404(Order, order_id=order_id, user=request.user)
```

### 4. Sensitive Data Handling
- Never store card numbers or CVV
- Only store transaction IDs and signatures
- Use environment variables for API keys
- Never commit API secrets to version control

### 5. HTTPS in Production
- **REQUIRED**: Use HTTPS in production
- Razorpay requires SSL/TLS for live transactions
- Update CSRF_TRUSTED_ORIGINS for your domain

---

## Testing

### Test Cards (Razorpay Test Mode)

| Card Number         | Type   | Result  |
|---------------------|--------|---------|
| 4111 1111 1111 1111 | Visa   | Success |
| 5555 5555 5555 4444 | Master | Success |
| 4000 0000 0000 0002 | Visa   | Failure |

- **CVV**: Any 3 digits
- **Expiry**: Any future date
- **OTP**: 0000 for UPI test mode

### Test Payment Flow
1. Create test order with "Online Payment"
2. Use test card on payment page
3. Verify order status updated to "completed"
4. Check payment_id and signature saved
5. Verify confirmation email sent

---

## Production Deployment Checklist

- [ ] Replace Test API Keys with Live API Keys
- [ ] Enable HTTPS/SSL certificate
- [ ] Update CSRF_TRUSTED_ORIGINS with production domain
- [ ] Test live payment with small amount
- [ ] Set up payment success webhook (optional)
- [ ] Configure payment failure notifications
- [ ] Set up refund policy and process
- [ ] Enable 2FA on Razorpay dashboard
- [ ] Review PCI compliance requirements
- [ ] Set up monitoring and alerts

---

## Troubleshooting

### Issue: Payment verification fails
**Solution**: Check Razorpay secret key in `.env` file matches dashboard

### Issue: Razorpay checkout doesn't open
**Solution**: Ensure `razorpay_key_id` passed to template correctly

### Issue: "CSRF verification failed" error
**Solution**: Ensure CSRF token included in payment verification request

### Issue: Order created but payment not captured
**Solution**: Check payment status in Razorpay dashboard, verify webhook configuration

### Issue: Amount mismatch error
**Solution**: Ensure amount converted to paise (multiply by 100)

---

## API Reference

### Razorpay Order Creation
```python
razorpay_order = create_razorpay_order(
    amount=499.50,  # Amount in rupees
    order_id=uuid_obj,  # Your order UUID
    receipt_id="RECEIPT_001"  # Optional receipt ID
)
```

### Payment Verification
```python
is_valid = verify_razorpay_payment(
    razorpay_order_id="order_xxxxx",
    razorpay_payment_id="pay_yyyyy",
    razorpay_signature="signature_hash"
)
```

### Get Payment Details
```python
payment = get_payment_details("pay_xxxxxxxxxxxxx")
print(payment['status'])  # 'captured'
print(payment['method'])  # 'card', 'upi', 'wallet', etc.
```

### Process Refund
```python
refund = refund_payment(
    payment_id="pay_xxxxx",
    amount=50000,  # Amount in paise (optional for partial refund)
    notes={'reason': 'Customer request'}
)
```

---

## Support & Resources

- **Razorpay Documentation**: https://razorpay.com/docs/
- **Razorpay API Reference**: https://razorpay.com/docs/api/
- **Razorpay Support**: https://razorpay.com/support/
- **Test Cards**: https://razorpay.com/docs/payments/payments/test-card-details/

---

## Future Enhancements

1. **Payment Webhooks**: Real-time payment status updates
2. **Recurring Payments**: Subscription-based meal plans
3. **EMI Options**: Monthly payment installments
4. **Saved Cards**: Store customer cards for faster checkout
5. **Payment Analytics**: Dashboard for payment metrics
6. **Auto-refunds**: Automated refund processing for cancellations
7. **Multiple Currency Support**: International payments
8. **Payment Links**: Share payment links via SMS/Email

---

## Conclusion

The online payment system is now fully functional and production-ready. Customers can securely pay for their orders using multiple payment methods, with all transactions properly verified and tracked. The implementation follows industry best practices for security and user experience.

**Status**: ✅ Complete and Ready for Production (after switching to Live API keys)
