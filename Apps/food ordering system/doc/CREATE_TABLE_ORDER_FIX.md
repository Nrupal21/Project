# Create Table Order - Bug Fix Documentation

## Issue Description
The "Create Order for Table" page was submitting **all menu items** to the order, regardless of whether the user selected them or not. This resulted in orders containing every item on the menu instead of only the items the user wanted.

## Root Cause
The HTML template had hidden inputs for `menu_items[]` hardcoded in every menu item card:

```html
<input type="hidden" name="menu_items[]" value="{{ item.id }}">
```

This meant that when the form was submitted, **all menu item IDs** were sent to the backend, not just the selected ones.

## Solution Implemented

### 1. Removed Static Hidden Inputs
**File:** `templates/restaurant/create_table_order.html`

- Removed the hardcoded `<input type="hidden" name="menu_items[]" value="{{ item.id }}">` from line 213
- Added a comment indicating that the hidden input will be dynamically added by JavaScript
- Set the quantity input to `disabled` by default (line 213)

### 2. Updated JavaScript Logic
**File:** `templates/restaurant/create_table_order.html` (JavaScript section)

#### Modified `toggleItemSelection()` function:
- **When selecting an item:**
  - Dynamically creates a hidden input with `name="menu_items[]"` and the item ID
  - Appends it to the quantity selector container
  - Enables the quantity input (removes `disabled` attribute)

- **When deselecting an item:**
  - Removes the dynamically created hidden input
  - Disables the quantity input (adds `disabled` attribute)
  - Resets quantity to 1

#### Modified `clearCart()` function:
- Properly removes all dynamically created hidden inputs
- Disables all quantity inputs
- Resets all quantities to 1

## How It Works Now

1. **Initial State:** All menu items are unselected, quantity inputs are disabled, no hidden inputs exist
2. **User Clicks Item:** JavaScript adds the item to selection, creates hidden input, enables quantity input
3. **User Changes Quantity:** Quantity is tracked in JavaScript Map and reflected in the cart
4. **User Deselects Item:** JavaScript removes hidden input, disables quantity input
5. **Form Submission:** Only selected items have their IDs in `menu_items[]` array and quantities in `quantities[]` array
6. **Backend Processing:** Backend receives only selected items and processes them correctly

## Technical Details

### Form Submission Behavior
- **Disabled inputs** are NOT submitted with the form
- Only **enabled** quantity inputs will have their values submitted
- The `zip()` function in the backend pairs up `menu_items[]` with `quantities[]` correctly

### Backend Validation
The backend already had proper validation:
```python
if not item_ids:
    messages.error(request, 'Please select at least one item.')
    return redirect('restaurant:create_table_order', table_id=table.id)
```

This validation now works correctly because `item_ids` will only contain selected items.

## Testing Checklist

- [x] Select single item - only that item is added to order
- [x] Select multiple items - only selected items are added
- [x] Change quantities - correct quantities are submitted
- [x] Deselect items - deselected items are not submitted
- [x] Clear cart - all selections are removed
- [x] Submit without selection - validation error is shown
- [x] Search functionality - still works correctly
- [x] Mobile responsive - cart and selection work on mobile

## Files Modified

1. **templates/restaurant/create_table_order.html**
   - Line 213: Removed hardcoded hidden input, added `disabled` attribute
   - Lines 350-395: Updated `toggleItemSelection()` function
   - Lines 488-507: Updated `clearCart()` function

## Impact
- **User Experience:** Users can now select only the items they want to order
- **Data Integrity:** Orders now contain only selected items with correct quantities
- **Backend:** No changes needed - existing validation works correctly
- **Performance:** No impact - same number of DOM operations

## Related Documentation
- See `doc/POS_TABLE_OPERATIONS_REDESIGN.md` for overall table ordering system
- See `templates/restaurant/create_table_order.html` for implementation details
