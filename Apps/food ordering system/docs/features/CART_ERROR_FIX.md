# Cart "Unexpected Token '<'" Error Fix

## Problem
The error "Unexpected token '<'" occurs when JavaScript receives HTML instead of JSON from the server. This typically happens when:
1. Django returns an HTML error page (like 404) instead of JSON
2. AJAX requests aren't properly detected
3. CSRF token issues prevent proper request handling

## Solutions Implemented

### 1. **Fixed Django Views to Always Return JSON for AJAX**

**File:** `customer/views.py`

**Changes Made:**
- Wrapped `get_object_or_404()` calls in try-except blocks
- Return JSON error responses for AJAX requests instead of HTML 404 pages
- Applied to both `cart_update` and `cart_remove` views

**Before:**
```python
menu_item = get_object_or_404(MenuItem, id=menu_item_id)
# This raises Http404 which returns HTML error page
```

**After:**
```python
try:
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
except Exception as e:
    error_msg = "Item not found or no longer available"
    if is_ajax:
        return JsonResponse({'success': False, 'message': error_msg})
    messages.error(request, error_msg)
    return redirect('customer:cart')
```

### 2. **Enhanced CSRF Token Handling**

**File:** `static/js/cart.js`

**Changes Made:**
- Added `getCookie()` helper function to retrieve CSRF token from cookies
- Implemented fallback mechanism: try to get token from DOM first, then from cookie
- Applied to all AJAX functions: `updateQuantityOnServer`, `removeItemFromCart`, `addToCart`

**Implementation:**
```javascript
// Get CSRF token with fallback
let csrfToken = adjuster.querySelector('[name=csrfmiddlewaretoken]')?.value;
if (!csrfToken) {
    // Fallback: try to get from cookie
    csrfToken = getCookie('csrftoken');
}
```

**Helper Function:**
```javascript
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

### 3. **Improved Error Response Handling**

**Both Backend and Frontend:**

**Backend (Django):**
- All AJAX requests now return consistent JSON format:
  ```json
  {
      "success": false,
      "message": "User-friendly error message"
  }
  ```

**Frontend (JavaScript):**
- Proper error handling in fetch promises
- Checks response status codes (401, 403 for auth errors)
- Displays user-friendly notifications
- Handles network errors gracefully

## Testing the Fix

### 1. **Test Cart Update:**
```javascript
// Open browser console and test
CartManager.updateQuantityOptimistic('1', 5, document.querySelector('.quantity-adjuster'));
```

### 2. **Test Cart Remove:**
```javascript
// Test remove functionality
const removeBtn = document.querySelector('.remove-item-btn');
if (removeBtn) removeBtn.click();
```

### 3. **Check Network Tab:**
- Open browser DevTools → Network tab
- Perform cart operations
- Verify responses are JSON, not HTML
- Check for proper status codes (200 for success, not 404)

## Common Issues and Solutions

### Issue 1: Still Getting HTML Responses
**Solution:** Clear browser cache and Django's session cache
```bash
python manage.py clearsessions
```

### Issue 2: CSRF Token Missing
**Solution:** Ensure Django middleware is properly configured in `settings.py`:
```python
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
    # ... other middleware
]
```

### Issue 3: 404 Errors for Valid Items
**Solution:** Check that menu items meet all criteria:
- `is_available = True`
- `restaurant.is_active = True`
- `restaurant.is_approved = True`

## Files Modified

1. **customer/views.py**
   - `cart_update()` - Added try-except for get_object_or_404
   - `cart_remove()` - Added try-except for get_object_or_404

2. **static/js/cart.js**
   - Added `getCookie()` helper function
   - Updated `updateQuantityOnServer()` with CSRF fallback
   - Updated `removeItemFromCart()` with CSRF fallback
   - Updated `addToCart()` with CSRF fallback

## Verification Checklist

- [x] Django views return JSON for AJAX requests
- [x] CSRF token retrieval has fallback mechanism
- [x] Error responses are properly formatted as JSON
- [x] 404 errors return JSON instead of HTML
- [x] Authentication errors are handled gracefully
- [x] Network errors show user-friendly messages
- [x] Cart operations work without page reload
- [x] Browser console shows no JavaScript errors

## Additional Improvements

1. **Version Control:** Cart operations now include version tracking to prevent race conditions
2. **Session Expiry Handling:** Automatic redirect to login when session expires
3. **Optimistic UI:** Immediate visual feedback with server sync
4. **Comprehensive Error Messages:** User-friendly notifications for all error scenarios

## Deployment Notes

After deploying these changes:
1. Clear Django cache: `python manage.py clearsessions`
2. Collect static files: `python manage.py collectstatic --noinput`
3. Restart Django server
4. Clear browser cache or use hard refresh (Ctrl+Shift+R)
5. Test all cart operations thoroughly

## Support

If you still encounter the "Unexpected token '<'" error after implementing these fixes:
1. Check browser console for the actual response content
2. Verify CSRF token is present in cookies
3. Ensure Django middleware is properly configured
4. Check that the cart.js file is loaded correctly
5. Verify URL patterns match the fetch requests
