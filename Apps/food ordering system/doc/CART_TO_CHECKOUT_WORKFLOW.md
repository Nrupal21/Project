# Cart to Checkout Workflow - Complete Documentation

## Overview

This document provides comprehensive documentation for the complete cart-to-checkout workflow in the Food Ordering System. It covers all files, functions, and processes involved in taking a customer from browsing restaurants to placing a successful order.

---

## Workflow Architecture

### Key Components

1. **Session-Based Cart** (`customer/cart.py`)
2. **View Functions** (`customer/views.py`)
3. **Forms** (`customer/forms.py`)
4. **Models** (`orders/models.py`, `customer/models.py`)
5. **Templates** (`templates/customer/`)
6. **Context Processors** (`customer/context_processors.py`)
7. **Promo Code System** (`orders/models.py`, `orders/views.py`)

---

## Complete User Journey

### Step 1: Browsing and Adding Items

**User Actions:**
1. Customer browses restaurants on home page
2. Customer clicks on restaurant to view menu
3. Customer selects items and clicks "Add to Cart"

**System Flow:**
```
User clicks "Add to Cart"
    ↓
POST request to cart_add(request, menu_item_id)
    ↓
Validates menu item exists and is available
    ↓
Validates restaurant is active and approved
    ↓
Adds item to session-based cart
    ↓
Shows success message
    ↓
Redirects back to previous page
```

**Key Files:**
- `customer/views.py::cart_add()` - Handles adding items to cart
- `customer/cart.py::Cart.add()` - Session cart management
- Templates with "Add to Cart" buttons

**Validation:**
- Menu item must exist
- Item must be available (`is_available=True`)
- Restaurant must be active (`is_active=True`)
- Restaurant must be approved (`is_approved=True`)

---

### Step 2: Viewing Cart

**User Actions:**
1. Customer clicks cart icon in navigation
2. Views all cart items with quantities and prices
3. Can update quantities, remove items, or apply promo codes

**System Flow:**
```
User navigates to /cart/
    ↓
cart_detail(request) function
    ↓
Initializes Cart from session
    ↓
Checks for promo code in URL (?promo=CODE)
    ↓
If promo provided: Validates and applies
    ↓
Renders cart.html with all cart data
```

**Key Files:**
- `customer/views.py::cart_detail()` - Displays cart page
- `templates/customer/cart.html` - Cart page template
- `customer/cart.py::Cart` - Cart object with all methods

**Features:**
- Real-time cart updates via POST requests
- Promo code application via AJAX
- Progress indicator showing checkout steps
- Price breakdown with discounts
- Continue shopping or proceed to checkout

---

### Step 3: Cart Updates and Management

**Available Operations:**

#### A. Update Quantity
```
User changes quantity in cart
    ↓
POST to cart_update(request, menu_item_id)
    ↓
Validates item still available
    ↓
If quantity > 0: Updates cart
If quantity ≤ 0: Removes item
    ↓
Redirects to cart page
```

**File:** `customer/views.py::cart_update()`

#### B. Remove Item
```
User clicks remove button
    ↓
POST to cart_remove(request, menu_item_id)
    ↓
Removes item from cart completely
    ↓
Redirects to cart page
```

**File:** `customer/views.py::cart_remove()`

#### C. Apply Promo Code
```
User enters promo code and clicks Apply
    ↓
AJAX POST to /orders/apply-promo-code/
    ↓
Validates promo code (date, usage limits, minimum order)
    ↓
If valid: Stores in session and returns discount
If invalid: Returns error message
    ↓
Updates cart pricing via JavaScript
```

**Files:**
- `orders/views.py::apply_promo_code()` - AJAX endpoint
- `customer/cart.py::Cart.apply_promo_code()` - Validation logic
- `templates/customer/cart.html` - AJAX JavaScript

**Promo Code Validation:**
1. Code must exist and be active
2. Must be within valid date range
3. Cart must meet minimum order amount
4. Usage limit not exceeded (global)
5. Per-user limit not exceeded (if applicable)
6. First-time only restriction (if applicable)
7. Restaurant-specific codes must match cart restaurant

---

### Step 4: Proceeding to Checkout

**User Actions:**
1. Customer reviews cart
2. Clicks "Proceed to Checkout" button
3. Arrives at checkout page

**System Flow:**
```
User clicks "Proceed to Checkout"
    ↓
Redirects to /checkout/
    ↓
checkout(request) function - GET request
    ↓
Validates cart is not empty
    ↓
Validates all items still available and approved
    ↓
If invalid items found: Removes them and redirects to cart
    ↓
Initializes CheckoutForm
    ↓
Calculates pricing breakdown
    ↓
Renders checkout.html
```

**Key Files:**
- `customer/views.py::checkout()` - Checkout view
- `templates/customer/checkout.html` - Checkout form template
- `customer/forms.py::CheckoutForm` - Form class

---

### Step 5: Checkout Form Submission

**User Actions:**
1. Selects delivery method (Delivery or Takeaway)
2. Enters customer name and phone
3. Enters delivery address (if delivery selected)
4. Optionally adds order notes
5. Clicks "Place Order" button

**System Flow:**
```
User submits checkout form
    ↓
POST to checkout(request)
    ↓
Validates form data
    ↓
Validates delivery address (required for delivery)
    ↓
Re-validates cart is not empty
    ↓
Re-validates all items still available
    ↓
Calculates final pricing with delivery method
    ↓
Creates Order record
    ↓
Creates OrderItem records for each cart item
    ↓
Tracks promo code usage (if applied)
    ↓
Sends order confirmation email
    ↓
Clears cart from session
    ↓
Redirects to order success page
```

**Key Files:**
- `customer/views.py::checkout()` - POST handler
- `customer/forms.py::CheckoutForm` - Form validation
- `orders/models.py::Order` - Order model
- `orders/models.py::OrderItem` - Order item model

---

### Step 6: Order Creation Process

**Database Operations:**

#### A. Create Order Record
```python
Order.objects.create(
    user=request.user,                           # Link to user
    customer_name=form_data['customer_name'],    # Customer info
    customer_phone=form_data['customer_phone'],
    customer_address=form_data.get('customer_address', ''),
    delivery_method=form_data['delivery_method'], # delivery/takeaway
    total_amount=breakdown['final_total'],        # After discounts
    promo_code=applied_promo_code,               # FK to PromoCode
    discount_amount=breakdown['discount_amount'],
    delivery_charge=breakdown['delivery_charge'],
    free_delivery_applied=breakdown['free_delivery'],
    notes=form_data.get('notes', '')
)
```

#### B. Create Order Items
```python
For each item in cart:
    OrderItem.objects.create(
        order=order,
        menu_item=menu_item,
        quantity=item['quantity'],
        price=item['price']  # Price at time of order
    )
```

#### C. Track Promo Code Usage
```python
If promo code applied:
    1. Increment promo_code.times_used
    2. Create PromoCodeUsage record for analytics
```

**Fields Preserved:**
- Item price at time of order (for historical accuracy)
- Quantity ordered
- Applied discounts
- Delivery charges
- Customer contact information

---

### Step 7: Email Confirmation

**Process:**
```
Order created successfully
    ↓
send_order_confirmation_email(user, order)
    ↓
Constructs email with:
    - Order ID
    - Status
    - Delivery method
    - Total amount
    - Customer information
    - List of items with prices
    - Order notes
    ↓
Sends via Django's send_mail()
    ↓
On success: Shows "Email sent" message
On failure: Shows "Email failed" message
    ↓
(Order is still valid even if email fails)
```

**Key File:**
- `customer/views.py::send_order_confirmation_email()`

**Email Configuration:**
- From: `settings.DEFAULT_FROM_EMAIL`
- To: `user.email`
- Format: Plain text (HTML can be added)
- Encoding: UTF-8

---

### Step 8: Order Success Page

**User Actions:**
1. Customer sees order confirmation
2. Views order ID and summary
3. Can track order or return to home

**System Flow:**
```
Redirected to /order-success/<order_id>/
    ↓
order_success(request, order_id)
    ↓
Fetches order by order_id
    ↓
Renders order_success.html
```

**Key Files:**
- `customer/views.py::order_success()`
- `templates/customer/order_success.html`

---

## Data Models

### Cart (Session-Based)

**Storage:** Django session (session-based, not database)

**Structure:**
```python
session['cart'] = {
    'menu_item_id_1': {
        'quantity': 2,
        'price': '199.00'
    },
    'menu_item_id_2': {
        'quantity': 1,
        'price': '149.00'
    }
}

session['applied_promo_code'] = 'promo_code_uuid'  # Optional
```

**Methods:**
- `add(menu_item, quantity, update_quantity=False)` - Add/update item
- `remove(menu_item)` - Remove item
- `clear()` - Empty cart
- `get_total_price()` - Calculate cart total
- `apply_promo_code(code, user)` - Apply discount
- `get_discount_breakdown(delivery_method)` - Get pricing details

### Order Model

**Database Table:** `orders_order`

**Key Fields:**
```python
order_id = UUIDField            # Unique identifier
user = ForeignKey(User)         # Customer who placed order
customer_name = CharField       # Delivery name
customer_phone = CharField      # Contact phone
customer_address = TextField    # Delivery address (nullable)
delivery_method = CharField     # 'delivery' or 'takeaway'
total_amount = DecimalField     # Final total
status = CharField              # Order status
promo_code = ForeignKey         # Applied promo code
discount_amount = DecimalField  # Discount applied
delivery_charge = DecimalField  # Delivery fee
free_delivery_applied = Boolean # Free delivery flag
notes = TextField               # Order notes
created_at = DateTimeField      # Order timestamp
```

**Status Choices:**
- `pending` - Order received
- `accepted` - Restaurant accepted
- `preparing` - Food being prepared
- `out_for_delivery` - On the way
- `delivered` - Order delivered
- `cancelled` - Order cancelled

### OrderItem Model

**Database Table:** `orders_orderitem`

**Key Fields:**
```python
order = ForeignKey(Order)      # Parent order
menu_item = ForeignKey         # Menu item ordered
quantity = PositiveInteger     # Number ordered
price = DecimalField           # Price at order time
subtotal = DecimalField        # Auto-calculated
```

### PromoCode Model

**Database Table:** `orders_promocode`

**Key Fields:**
```python
code = CharField(unique=True)        # Promo code string
name = CharField                     # Display name
discount_type = CharField            # 'percentage', 'fixed', 'free_delivery'
discount_value = DecimalField        # Discount amount
minimum_order_amount = DecimalField  # Min order required
usage_limit = PositiveInteger        # Max total uses
usage_limit_per_user = PositiveInt   # Max per user
start_date = DateTimeField           # Activation date
end_date = DateTimeField             # Expiration date
restaurant = ForeignKey              # Restaurant-specific (nullable)
first_time_only = Boolean            # First-time customers only
is_active = Boolean                  # Active flag
times_used = PositiveInteger         # Usage counter
```

---

## Form Validation

### CheckoutForm

**Validation Rules:**

1. **customer_name** (required)
   - Max length: 200 characters
   - Must not be empty

2. **customer_phone** (required)
   - Regex validation: `^\+?1?\d{9,15}$`
   - 10-15 digits with optional country code

3. **customer_address** (conditional)
   - Required if `delivery_method == 'delivery'`
   - Optional if `delivery_method == 'takeaway'`
   - Validated in `clean()` method

4. **delivery_method** (required)
   - Choices: `delivery` or `takeaway`
   - Default: `delivery`

5. **notes** (optional)
   - No validation
   - Any text allowed

**File:** `customer/forms.py::CheckoutForm`

---

## Pricing Calculations

### Cart Total Breakdown

**Calculation Steps:**

1. **Subtotal**
   ```python
   subtotal = sum(item_price * quantity for all items)
   ```

2. **Discount Amount**
   ```python
   if promo_code.discount_type == 'percentage':
       discount = subtotal * (promo_value / 100)
       if max_discount:
           discount = min(discount, max_discount)
   
   elif promo_code.discount_type == 'fixed':
       discount = min(promo_value, subtotal)
   
   elif promo_code.discount_type == 'free_delivery':
       discount = 0
       free_delivery = True
   ```

3. **Delivery Charge**
   ```python
   if delivery_method == 'takeaway':
       delivery_charge = 0
   elif free_delivery:
       delivery_charge = 0
   else:
       delivery_charge = 40  # Default delivery fee
   ```

4. **Final Total**
   ```python
   final_total = subtotal - discount_amount + delivery_charge
   ```

**File:** `customer/cart.py::Cart.get_discount_breakdown()`

---

## Security Considerations

### Data Validation

1. **Menu Item Validation**
   - Verify item exists
   - Check item is available
   - Validate restaurant is active and approved
   - Re-validate at checkout (items may become unavailable)

2. **User Authentication**
   - All cart operations require login
   - Order linked to authenticated user
   - Prevents anonymous orders

3. **Promo Code Security**
   - Validate date range
   - Check usage limits
   - Verify per-user restrictions
   - Prevent code reuse beyond limits

4. **Form Validation**
   - CSRF token required
   - Server-side validation
   - Input sanitization
   - SQL injection prevention

### Session Security

- Session-based cart (not stored in database)
- Session expires after inactivity
- Cleared after successful checkout
- CSRF protection on all POST requests

---

## Error Handling

### Cart Operations

**Empty Cart:**
```python
if len(cart) == 0:
    messages.warning(request, 'Your cart is empty!')
    return redirect('customer:home')
```

**Invalid Items:**
```python
if invalid_items:
    # Remove invalid items
    # Show error message
    # Redirect to cart for review
```

**Email Failures:**
```python
try:
    send_order_confirmation_email(user, order)
    messages.success(request, 'Email sent!')
except Exception as e:
    # Log error
    # Show alternate success message
    # Order still valid
```

### Promo Code Errors

- **Code not found:** "Invalid promo code"
- **Expired:** "This promo code has expired"
- **Not started:** "This promo code is not yet active"
- **Usage limit:** "This promo code has reached its usage limit"
- **Minimum not met:** "Minimum order amount of ₹X required"
- **First-time only:** "This promo code is for first-time customers only"
- **Restaurant mismatch:** "This promo code is only valid for [Restaurant Name]"

---

## Template Structure

### Cart Template

**File:** `templates/customer/cart.html`

**Sections:**
1. Breadcrumb navigation
2. Page header with progress indicator
3. Cart items list with quantity controls
4. Order summary sidebar with:
   - Estimated delivery time
   - Promo code form (AJAX)
   - Price breakdown
   - Checkout button
   - Trust badges
5. Empty cart state (if cart is empty)

**JavaScript Features:**
- AJAX promo code application
- Real-time price updates
- Form validation
- Loading states

### Checkout Template

**File:** `templates/customer/checkout.html`

**Sections:**
1. Breadcrumb navigation
2. Page header with progress indicator (step 2)
3. Checkout form with:
   - Delivery method selection
   - Customer information fields
   - Conditional address field
   - Order notes
4. Order summary sidebar with:
   - Cart items list
   - Price breakdown
   - Payment method info
   - Trust badges

**JavaScript Features:**
- Address field visibility toggle
- Delivery method change handler
- Real-time price updates
- Form validation

---

## Context Processors

### Cart Count

**File:** `customer/context_processors.py`

**Function:** `cart_count(request)`

**Purpose:** Makes cart item count available in all templates

**Usage in templates:**
```html
<span class="badge">{{ cart_count }}</span>
```

**Integration:**
- Added to `settings.TEMPLATES.OPTIONS.context_processors`
- Available globally without passing in context
- Updates automatically with cart changes

---

## URL Patterns

### Customer URLs

```python
# Cart operations
path('cart/add/<int:menu_item_id>/', views.cart_add, name='cart_add')
path('cart/remove/<int:menu_item_id>/', views.cart_remove, name='cart_remove')
path('cart/update/<int:menu_item_id>/', views.cart_update, name='cart_update')
path('cart/', views.cart_detail, name='cart')

# Checkout
path('checkout/', views.checkout, name='checkout')
path('order-success/<uuid:order_id>/', views.order_success, name='order_success')
```

### Orders URLs

```python
# Promo code operations
path('apply-promo-code/', views.apply_promo_code, name='apply_promo_code')
path('remove-promo-code/', views.remove_promo_code, name='remove_promo_code')
```

---

## Testing Checklist

### Cart Operations
- [ ] Add item to cart
- [ ] Update item quantity
- [ ] Remove item from cart
- [ ] Apply valid promo code
- [ ] Apply invalid promo code
- [ ] Remove promo code
- [ ] Cart persists across page loads
- [ ] Cart count updates in navigation

### Checkout Process
- [ ] Empty cart redirects to home
- [ ] Invalid items removed automatically
- [ ] Delivery address required for delivery
- [ ] Delivery address optional for takeaway
- [ ] Form validation works
- [ ] Promo code discount applied correctly
- [ ] Delivery charge calculated correctly
- [ ] Order created successfully
- [ ] Order items created correctly
- [ ] Email sent successfully
- [ ] Cart cleared after order
- [ ] Redirect to success page

### Promo Code Validation
- [ ] Valid code applies discount
- [ ] Expired code rejected
- [ ] Future code rejected
- [ ] Minimum order amount enforced
- [ ] Usage limit enforced
- [ ] Per-user limit enforced
- [ ] First-time only restriction works
- [ ] Restaurant-specific codes work

---

## Best Practices

### Code Organization

1. **Separation of Concerns**
   - Cart logic in `cart.py`
   - View logic in `views.py`
   - Form validation in `forms.py`
   - Business logic in models

2. **Comprehensive Comments**
   - Function docstrings explaining purpose
   - Parameter and return value documentation
   - Workflow explanations
   - Inline comments for complex logic

3. **Error Handling**
   - Try-except blocks for external operations
   - Graceful degradation
   - User-friendly error messages
   - Logging for debugging

4. **Security**
   - CSRF protection
   - Authentication required
   - Input validation
   - SQL injection prevention

### User Experience

1. **Progress Indicators**
   - Show current step in workflow
   - Visual feedback for actions
   - Loading states for AJAX

2. **Validation Feedback**
   - Immediate field validation
   - Clear error messages
   - Success confirmations

3. **Mobile Responsiveness**
   - Tailwind CSS utilities
   - Touch-friendly buttons
   - Readable fonts and spacing

---

## File Reference Summary

### Python Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `customer/cart.py` | Session cart management | `add()`, `remove()`, `apply_promo_code()`, `get_discount_breakdown()` |
| `customer/views.py` | View functions | `cart_add()`, `cart_remove()`, `cart_update()`, `cart_detail()`, `checkout()` |
| `customer/forms.py` | Form classes | `CheckoutForm` |
| `customer/context_processors.py` | Global context | `cart_count()` |
| `orders/models.py` | Database models | `Order`, `OrderItem`, `PromoCode`, `PromoCodeUsage` |
| `orders/views.py` | Promo code views | `apply_promo_code()`, `remove_promo_code()` |

### Template Files

| File | Purpose | Features |
|------|---------|----------|
| `templates/customer/cart.html` | Cart page | Item list, quantity controls, promo form, pricing |
| `templates/customer/checkout.html` | Checkout page | Delivery form, order summary, payment info |
| `templates/customer/order_success.html` | Confirmation page | Order details, tracking link |

---

## Future Enhancements

### Potential Improvements

1. **Multiple Payment Methods**
   - Online payment integration
   - Wallet support
   - UPI payments

2. **Advanced Promo Codes**
   - BOGO (Buy One Get One)
   - Category-specific discounts
   - Time-based discounts

3. **Cart Features**
   - Save for later
   - Wishlist integration
   - Recommended items

4. **Email Improvements**
   - HTML email templates
   - Order tracking in email
   - SMS notifications

5. **Analytics**
   - Abandoned cart tracking
   - Conversion funnel analysis
   - Promo code effectiveness

---

## Conclusion

The cart-to-checkout workflow is a comprehensive, well-documented system that handles the complete order process from item selection to order confirmation. All files include detailed comments explaining functionality, parameters, return values, and business logic.

**Key Strengths:**
- ✅ Session-based cart for performance
- ✅ Comprehensive validation at multiple steps
- ✅ Flexible promo code system
- ✅ Email confirmation with error handling
- ✅ Mobile-responsive design
- ✅ Extensive inline documentation
- ✅ Security best practices

**Documentation Coverage:**
- ✅ All functions have comprehensive docstrings
- ✅ Templates have HTML comments
- ✅ JavaScript functions have JSDoc comments
- ✅ Workflow explanations included
- ✅ Error handling documented
- ✅ Security considerations noted

This workflow is production-ready and maintainable by any developer familiar with Django and the documented architecture.
