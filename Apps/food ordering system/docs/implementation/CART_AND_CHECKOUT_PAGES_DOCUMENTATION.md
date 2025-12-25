# Cart and Checkout Pages - Complete Documentation

## Overview

This document provides comprehensive documentation for the shopping cart and checkout pages in the Food Ordering System. Both pages are fully documented with HTML comments, JavaScript JSDoc, and detailed explanations for programmers.

---

## File Locations

- **Cart Page**: `templates/customer/cart.html`
- **Checkout Page**: `templates/customer/checkout.html`

---

## Shopping Cart Page (`cart.html`)

### Page Structure

```
cart.html
├── Breadcrumb Navigation
├── Page Header with Progress Indicator
├── Main Content (Grid Layout)
│   ├── Cart Items Section (2 columns on desktop)
│   │   └── Individual Item Cards
│   │       ├── Product Image
│   │       ├── Item Information
│   │       ├── Quantity Controls
│   │       ├── Remove Button
│   │       └── Price Display
│   └── Order Summary Sidebar (1 column, sticky)
│       ├── Estimated Delivery Time
│       ├── Promo Code Section
│       ├── Price Breakdown
│       ├── Checkout Button
│       └── Trust Badges
└── Empty Cart State (Alternative View)
```

### Key Features

#### 1. **Breadcrumb Navigation**
```html
<!-- Helps users understand their location in the checkout flow -->
<nav aria-label="Breadcrumb">
    <ol>
        <li>Home</li>
        <li>Cart (Current)</li>
    </ol>
</nav>
```

**Purpose**: Provides navigational context and allows users to easily return home.

#### 2. **Progress Indicator**
```html
<!-- Visual representation of checkout steps -->
Step 1: Cart (Active) → Step 2: Checkout → Step 3: Confirmation
```

**Purpose**: Shows users where they are in the checkout process.

**Design**: 
- Active step: Rose circle with white text
- Completed steps: Green circle with checkmark
- Upcoming steps: Gray circle

#### 3. **Cart Items Display**

Each item card includes:
- **Product Image** (96x96px)
  - Fallback image on error
  - Hover scale animation (110%)
  
- **Item Information**
  - Name (Bold, large text)
  - Category badge (Gray background)
  - Unit price (₹XX each)

- **Quantity Controls**
  - Decrease button (-)
  - Current quantity display
  - Increase button (+)
  - POST form submission on each change

- **Remove Button**
  - Red color scheme
  - Icon with text
  - POST form submission

- **Price Display**
  - Shows subtotal (price × quantity)
  - Large, bold font

**Code Example**:
```html
<div class="cart-item">
    <img src="item-image.jpg" alt="Item Name">
    <h3>Item Name</h3>
    <span class="category-badge">Category</span>
    <form method="post" action="/cart/update/123/">
        <button name="quantity" value="1">-</button>
        <span>2</span>
        <button name="quantity" value="3">+</button>
    </form>
    <p>₹398 (₹199 × 2)</p>
</div>
```

#### 4. **Order Summary Sidebar**

**Features**:
- Sticky positioning on desktop
- Estimated delivery time banner
- Promo code application form
- Price breakdown
- Action buttons
- Trust badges

**Promo Code Section**:
```html
<form id="promo-code-form">
    <input type="text" id="promo-code-input" 
           placeholder="Enter promo code"
           maxlength="20">
    <button type="submit">Apply</button>
</form>

<!-- Success/Error Messages -->
<div id="applied-promo-display">✓ Promo code applied</div>
<div id="promo-error-display">✗ Invalid code</div>
```

**Price Breakdown**:
```
Items (3)          ₹597
Discount          -₹50 (if applied)
Delivery          Free / ₹40
────────────────────────
Total              ₹547
```

#### 5. **Empty Cart State**

When cart is empty:
- Large cart icon
- "Your Cart is Empty" heading
- Descriptive message
- Browse Restaurants button (Primary)
- View Full Menu button (Secondary)
- Popular categories grid (4 items)
- "Why Order With Us?" section

**Popular Categories**:
```html
<div class="category-grid">
    <a>🍕 Pizza</a>
    <a>🍔 Burgers</a>
    <a>🍜 Noodles</a>
    <a>🍰 Desserts</a>
</div>
```

### JavaScript Functionality

#### Promo Code Management

**File**: Inline `<script>` section at end of template

**Functions**:

1. **`promoForm.addEventListener('submit')`**
   - Handles promo code application
   - Sends AJAX POST to `/orders/apply-promo-code/`
   - Updates pricing on success
   - Shows error message on failure

2. **`removeBtn.addEventListener('click')`**
   - Removes applied promo code
   - Sends AJAX POST to `/orders/remove-promo-code/`
   - Resets pricing display

3. **`showSuccess(message)`**
   - Displays success message
   - Shows applied promo badge
   - Hides error message

4. **`showError(message)`**
   - Displays error message
   - Auto-hides after 5 seconds
   - Hides success badge

5. **`updatePricing(breakdown)`**
   - Updates all price elements
   - Shows/hides discount row
   - Updates delivery charge
   - Recalculates total

6. **`promoInput.addEventListener('input')`**
   - Auto-formats input to uppercase
   - Removes spaces automatically

**AJAX Request Example**:
```javascript
fetch('/orders/apply-promo-code/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrfToken
    },
    body: `code=${encodeURIComponent(code)}`
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        updatePricing(data.cart_breakdown);
    }
});
```

**Response Format**:
```json
{
    "success": true,
    "message": "Promo code applied!",
    "cart_breakdown": {
        "subtotal": "597",
        "discount_amount": "50",
        "delivery_charge": "0",
        "final_total": "547",
        "free_delivery": true,
        "applied_promo_code": {
            "code": "SAVE50",
            "name": "Special Discount",
            "discount_type": "fixed",
            "discount_value": "50"
        }
    }
}
```

### Tailwind CSS Classes Used

**Layout**:
- `grid grid-cols-1 lg:grid-cols-3 gap-8` - Responsive grid
- `lg:col-span-2` - 2 columns for cart items
- `lg:col-span-1` - 1 column for sidebar
- `lg:sticky lg:top-6` - Sticky sidebar

**Cards**:
- `bg-white rounded-2xl shadow-sm` - White card with rounded corners
- `p-6 border-b border-gray-100` - Padding and bottom border
- `hover:bg-gray-50 transition-all` - Hover effect

**Buttons**:
- `bg-gradient-to-r from-rose-500 to-pink-500` - Gradient background
- `hover:from-rose-600 hover:to-pink-600` - Hover gradient
- `rounded-xl font-bold` - Rounded corners and bold text
- `transform hover:scale-105` - Hover scale effect

**Colors**:
- Rose/Pink: Primary actions (checkout, apply)
- Gray: Secondary actions (continue shopping)
- Green: Success states (applied promo, delivery)
- Red: Error states, remove actions

---

## Checkout Page (`checkout.html`)

### Page Structure

```
checkout.html
├── Breadcrumb Navigation (Home → Cart → Checkout)
├── Page Header with Progress Indicator
├── Main Content (Grid Layout)
│   ├── Checkout Form Section (2 columns on desktop)
│   │   ├── Delivery Method Selection
│   │   ├── Customer Name Field
│   │   ├── Phone Number Field
│   │   ├── Delivery Address Field (Conditional)
│   │   ├── Order Notes Field
│   │   ├── Place Order Button
│   │   └── Back to Cart Button
│   └── Order Summary Sidebar (1 column, sticky)
│       ├── Cart Items List
│       ├── Price Breakdown
│       ├── Payment Method Info
│       └── Trust Badges
└── JavaScript for Form Handling
```

### Key Features

#### 1. **Progress Indicator**

Shows current step as active:
```
Step 1: Cart (Completed ✓) → Step 2: Checkout (Active) → Step 3: Confirmation
```

**Visual States**:
- Completed: Green circle with checkmark icon
- Active: Rose circle with number, pulsing animation
- Upcoming: Gray circle with number

#### 2. **Checkout Form**

**Delivery Method Selection**:
```html
<div class="delivery-method">
    <label>
        <input type="radio" name="delivery_method" value="delivery">
        🏠 Delivery - Get it delivered to your doorstep
    </label>
    <label>
        <input type="radio" name="delivery_method" value="takeaway">
        🥡 Takeaway - Pick up from restaurant
    </label>
</div>
```

**Form Fields**:

1. **Customer Name** (Required)
   - Icon: User profile
   - Placeholder: "Enter your full name"
   - Help text: "Enter your full name for delivery"
   - Validation: Server-side validation

2. **Phone Number** (Required)
   - Icon: Phone
   - Placeholder: "Enter your phone number"
   - Help text: "We'll call you if there are any issues"
   - Validation: Phone number format

3. **Delivery Address** (Conditional)
   - Shown only for delivery method
   - Hidden for pickup/takeaway
   - Icon: Location pin
   - Multi-line textarea
   - Help text: "Include apartment/floor number, building name, street address"
   - Validation: Required for delivery

4. **Order Notes** (Optional)
   - Icon: Chat bubble
   - Placeholder: "Any special instructions"
   - Help text: "Add special instructions, preferences, or dietary requirements"
   - No validation

**Error Display**:
```html
{% if form.field_name.errors %}
<div class="error-message">
    <svg><!-- Error Icon --></svg>
    {{ form.field_name.errors.0 }}
</div>
{% endif %}
```

**Field Styling**:
- All inputs have icon on the left
- Focus ring: Rose color
- Border: Gray, changes to rose on focus
- Padding: Generous for mobile touch targets

#### 3. **Order Summary Sidebar**

**Cart Items List**:
- Scrollable container (max-height: 288px)
- Custom scrollbar (6px wide, rose gradient)
- Each item shows:
  - Item name (bold)
  - Quantity
  - Item total

**Price Breakdown**:
```
Subtotal              ₹597
Discount             -₹50  (if applied)
[Promo Code Badge]
Delivery/Pickup       Free / ₹40
────────────────────────────
Total                 ₹547
```

**Promo Code Display** (if applied):
```html
<div class="promo-badge">
    🎟️ Special Discount (₹50 off)
</div>
```

**Payment Method**:
- Cash on Delivery card
- Green gradient background
- Icon and description
- "Safe & Secure" badge

**Trust Badges**:
- 🛡️ 100% Secure Checkout
- 🔒 Your Data is Protected
- 🎧 24/7 Customer Support

### JavaScript Functionality

#### Form Field Management

**Functions**:

1. **`toggleAddressField()`**
   - Toggles address field visibility
   - Based on delivery method selection
   - Updates required attribute
   - Clears field when switching to pickup

2. **`updatePricingForDeliveryMethod(deliveryMethod)`**
   - Recalculates delivery charge
   - Updates total display
   - Changes delivery label (Delivery/Pickup)
   - Respects free delivery from promo codes

**Event Listeners**:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Set initial state
    toggleAddressField();
    
    // Listen for delivery method changes
    const radios = document.querySelectorAll('input[name="delivery_method"]');
    radios.forEach(radio => {
        radio.addEventListener('change', toggleAddressField);
    });
});
```

**Logic Flow**:
```
User selects delivery method
    ↓
toggleAddressField() called
    ↓
If "delivery": Show address field, set required=true
If "takeaway": Hide address field, set required=false, clear value
    ↓
updatePricingForDeliveryMethod() called
    ↓
Calculate delivery charge (₹40 for delivery, ₹0 for pickup)
Unless free delivery from promo code
    ↓
Update total = subtotal - discount + delivery charge
    ↓
Update UI elements
```

### Custom CSS

**Scrollbar Styling**:
```css
.custom-scrollbar::-webkit-scrollbar {
    width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #f43f5e, #ec4899);
    border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, #e11d48, #db2777);
}

/* Firefox support */
.custom-scrollbar {
    scrollbar-width: thin;
    scrollbar-color: #f43f5e #f1f1f1;
}
```

---

## Common Design Patterns

### 1. **Gradient Buttons**

Primary action buttons use consistent gradient:
```css
bg-gradient-to-r from-rose-500 to-pink-500
hover:from-rose-600 hover:to-pink-600
```

### 2. **Card Shadows**

Consistent shadow system:
- Default: `shadow-sm`
- Cards: `shadow-lg`
- Hover: `hover:shadow-xl`

### 3. **Rounded Corners**

Consistent border radius:
- Large cards: `rounded-2xl` (16px)
- Medium elements: `rounded-xl` (12px)
- Small elements: `rounded-lg` (8px)
- Pills/Badges: `rounded-full`

### 4. **Spacing System**

Based on Tailwind's spacing scale:
- Small gaps: `gap-2` or `gap-3` (8-12px)
- Medium gaps: `gap-4` or `gap-6` (16-24px)
- Large gaps: `gap-8` (32px)

### 5. **Icon System**

Using Heroicons (outline style):
- Size: `w-5 h-5` for inline icons
- Size: `w-6 h-6` for prominent icons
- Stroke width: `stroke-width="2"`

### 6. **Color Palette**

**Primary Colors**:
- Rose: `#f43f5e` (Primary actions)
- Pink: `#ec4899` (Accent)

**Semantic Colors**:
- Green: Success, delivery, promo applied
- Red: Errors, remove actions
- Blue: Information
- Purple: Support
- Gray: Neutral, secondary actions

### 7. **Responsive Design**

**Breakpoints**:
- Mobile: < 640px (sm)
- Tablet: 640px - 1024px (md)
- Desktop: > 1024px (lg)

**Grid Layout**:
```html
<!-- Mobile: 1 column -->
<!-- Desktop: 2 columns (form) + 1 column (summary) -->
<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
    <div class="lg:col-span-2">Form</div>
    <div class="lg:col-span-1">Summary</div>
</div>
```

---

## Form Validation

### Client-Side Validation

1. **Promo Code Input**:
   - Auto-uppercase conversion
   - Space removal
   - Max length: 20 characters

2. **Address Field**:
   - Required attribute toggled based on delivery method
   - Cleared when switching to pickup

### Server-Side Validation

Handled by Django `CheckoutForm`:

1. **Customer Name**:
   - Required field
   - Max length: 200 characters

2. **Phone Number**:
   - Required field
   - Regex pattern validation
   - 10-15 digits

3. **Address**:
   - Required if delivery_method == 'delivery'
   - Custom clean() method validates this

4. **Notes**:
   - Optional field
   - No validation

**Form Processing Flow**:
```
User submits form
    ↓
POST to /checkout/
    ↓
Django validates form
    ↓
If valid:
    - Create Order object
    - Create OrderItem objects
    - Apply promo code (if any)
    - Send confirmation email
    - Clear cart
    - Redirect to success page
    ↓
If invalid:
    - Re-render checkout with errors
    - Show field-specific error messages
```

---

## AJAX Endpoints

### 1. Apply Promo Code

**URL**: `/orders/apply-promo-code/`  
**Method**: POST  
**Headers**:
```
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <csrf_token>
```

**Request Body**:
```
code=SAVE50
```

**Response** (Success):
```json
{
    "success": true,
    "message": "Promo code 'SAVE50' applied successfully!",
    "cart_breakdown": {
        "subtotal": "597.00",
        "discount_amount": "50.00",
        "delivery_charge": "0.00",
        "final_total": "547.00",
        "free_delivery": true,
        "applied_promo_code": {
            "code": "SAVE50",
            "name": "Special Discount",
            "discount_type": "fixed",
            "discount_value": "50.00"
        },
        "delivery_method": "delivery"
    }
}
```

**Response** (Error):
```json
{
    "success": false,
    "message": "Invalid promo code."
}
```

### 2. Remove Promo Code

**URL**: `/orders/remove-promo-code/`  
**Method**: POST  
**Headers**: Same as above

**Response**:
```json
{
    "success": true,
    "message": "Promo code removed successfully.",
    "cart_breakdown": {
        "subtotal": "597.00",
        "discount_amount": "0.00",
        "delivery_charge": "40.00",
        "final_total": "637.00",
        "free_delivery": false,
        "applied_promo_code": null,
        "delivery_method": "delivery"
    }
}
```

---

## User Experience Features

### 1. **Loading States**

Promo code apply button:
```javascript
// Before request
applyBtn.disabled = true;
applyBtn.textContent = 'Applying...';

// After request
applyBtn.disabled = false;
applyBtn.textContent = 'Apply';
```

### 2. **Error Handling**

- Network errors caught and displayed
- 5-second auto-hide for errors
- Clear, user-friendly error messages

### 3. **Visual Feedback**

- Hover animations (scale, shadow)
- Transition effects (200-300ms)
- Color changes on state
- Pulse animation on active step

### 4. **Accessibility**

- ARIA labels on navigation
- Semantic HTML structure
- Keyboard navigation support
- Focus states clearly visible
- Error messages associated with fields

### 5. **Mobile Optimization**

- Touch-friendly button sizes (min 44px)
- Readable font sizes
- Adequate spacing between elements
- Responsive images
- Bottom navigation accessible

---

## Testing Checklist

### Cart Page

- [ ] Items display correctly
- [ ] Quantity increase works
- [ ] Quantity decrease works
- [ ] Remove item works
- [ ] Promo code application works
- [ ] Invalid promo code shows error
- [ ] Promo code removal works
- [ ] Price updates correctly
- [ ] Empty cart state shows
- [ ] Continue shopping button works
- [ ] Proceed to checkout button works
- [ ] Responsive on mobile
- [ ] Images load with fallback

### Checkout Page

- [ ] Form displays correctly
- [ ] Delivery method selection works
- [ ] Address field shows/hides correctly
- [ ] Required fields validated
- [ ] Error messages display
- [ ] Price calculation correct
- [ ] Order summary matches cart
- [ ] Place order button works
- [ ] Back to cart button works
- [ ] Successful order redirects
- [ ] Email confirmation sent
- [ ] Cart cleared after order
- [ ] Responsive on mobile
- [ ] Payment method displays

---

## Performance Optimizations

1. **Image Loading**:
   - Lazy loading for cart item images
   - Fallback images for missing items
   - Optimized image sizes (96x96px thumbnails)

2. **JavaScript**:
   - Event delegation where applicable
   - Debounced input handlers
   - Cached DOM element references

3. **CSS**:
   - Tailwind JIT compilation
   - Purged unused styles
   - Optimized animations

4. **Network**:
   - AJAX for promo codes (no page reload)
   - Minimal payload in requests
   - Cached static assets

---

## Future Enhancements

### Potential Improvements

1. **Cart Page**:
   - Saved for later functionality
   - Recently viewed items
   - Recommended items
   - Bulk quantity adjustment
   - Multiple promo code support

2. **Checkout Page**:
   - Address autocomplete
   - Save address for future
   - Multiple delivery addresses
   - Scheduled delivery time
   - Online payment options
   - Order gift options

3. **Both Pages**:
   - Real-time inventory check
   - Estimated delivery time API
   - Live chat support
   - Accessibility improvements
   - Progressive Web App features

---

## Troubleshooting

### Common Issues

**1. Promo Code Not Applying**:
- Check CSRF token is included
- Verify code is uppercase
- Check expiration date
- Verify minimum order amount met
- Check usage limits not exceeded

**2. Address Field Not Showing/Hiding**:
- Check JavaScript is loaded
- Verify delivery method value
- Check element IDs match
- Console for JavaScript errors

**3. Price Not Updating**:
- Check AJAX response format
- Verify breakdown object structure
- Check element IDs in updatePricing()
- Inspect network tab for errors

**4. Form Validation Errors**:
- Check required fields filled
- Verify address for delivery method
- Check phone number format
- Review server logs for validation

---

## Conclusion

Both the cart and checkout pages are fully documented with:
- ✅ Comprehensive HTML comments
- ✅ JSDoc-style JavaScript documentation
- ✅ CSS comments for custom styles
- ✅ Clear code structure
- ✅ Consistent Tailwind CSS usage
- ✅ Accessible markup
- ✅ Responsive design
- ✅ Error handling
- ✅ Loading states
- ✅ User feedback

The pages follow best practices for:
- Code organization
- Comment standards
- Naming conventions
- Design patterns
- User experience
- Performance
- Accessibility

This documentation serves as a complete reference for any developer working on or maintaining these pages.
