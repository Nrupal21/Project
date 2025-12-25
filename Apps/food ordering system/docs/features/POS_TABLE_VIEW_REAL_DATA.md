# POS Table View - Real-time Order Management

## Overview
The POS Table View has been updated to display **real-time data from the database** instead of static sample data. This provides restaurant staff with accurate, live information about table statuses, active orders, and kitchen operations.

## Key Features Implemented

### ✅ Real-time Data Integration
- **Live table status updates** from database
- **Active order information** with customer details
- **Order duration tracking** in real-time
- **Automatic refresh** every 30 seconds
- **Manual refresh** capability

### ✅ API Endpoint
**Endpoint:** `/restaurant/api/table-status/`  
**Method:** GET  
**Authentication:** Required (Restaurant Owner)

**Response Structure:**
```json
{
  "sections": {
    "ac": {
      "tables": [...],
      "available_count": 12,
      "occupied_count": 4,
      "attention_count": 1
    },
    "non_ac": {...},
    "bar": {...}
  },
  "totals": {
    "available": 25,
    "occupied": 7,
    "running_kot": 3
  },
  "timestamp": "14:30:45"
}
```

### ✅ Table Status Categories
1. **Available (Blank)** - No active orders, ready for customers
2. **Occupied (Running)** - Active orders in progress
3. **Needs Attention** - Order completed, payment pending
4. **Running KOT** - Kitchen Order Ticket being prepared

### ✅ Real-time Information Display
Each table shows:
- **Table number** and section
- **Customer name** (for occupied tables)
- **Order duration** in minutes
- **Item count** in current order
- **Total amount** for the order
- **Order status** (pending, accepted, preparing, etc.)
- **Table capacity** and location

## Technical Implementation

### Backend Components

#### 1. API View Function
**File:** `restaurant/views.py`  
**Function:** `get_table_status_api(request)`

```python
@restaurant_owner_required
def get_table_status_api(request):
    """
    API endpoint to get real-time table status data.
    
    Returns JSON data with current status of all tables including:
    - Table availability status
    - Active orders information
    - Customer details
    - Order duration
    - Total amounts
    """
```

**Key Features:**
- Queries active orders from database
- Calculates order duration dynamically
- Organizes tables by section (A/C, Non A/C, Bar)
- Returns comprehensive JSON response
- Includes error handling

#### 2. URL Configuration
**File:** `restaurant/urls.py`

```python
# API Endpoints for Real-time Updates
path('api/table-status/', views.get_table_status_api, name='table_status_api'),
```

### Frontend Components

#### 1. POS Table View Template
**File:** `templates/restaurant/components/pos_table_view.html`

**Key JavaScript Functions:**

##### `loadTableData()`
- Fetches real-time data from API endpoint
- Handles network errors gracefully
- Updates UI with fresh data
- Shows error notifications if API fails

```javascript
function loadTableData() {
    fetch('{% url "restaurant:table_status_api" %}')
        .then(response => response.json())
        .then(data => {
            updateTableStatuses(data);
            updateStatistics(data);
            updateLastRefreshTime(data.timestamp);
        })
        .catch(error => {
            showNotification('Failed to load table data', 'error');
        });
}
```

##### `updateTableStatuses(data)`
- Processes API response data
- Updates table card visual states
- Applies appropriate CSS classes
- Updates status indicators
- Refreshes popup information

##### `updateStatistics(data)`
- Updates available tables counter
- Updates occupied tables counter
- Updates running KOT counter
- Displays real-time totals

##### `updateTablePopup(tableCard, tableData)`
- Shows order details on hover
- Displays customer information
- Shows order duration and amount
- Updates dynamically with each refresh

##### `showNotification(message, type)`
- Displays success/error messages
- Auto-dismisses after 3 seconds
- Provides visual feedback to users

#### 2. Auto-refresh Mechanism
```javascript
// Auto-refresh every 30 seconds
function startAutoRefresh() {
    refreshInterval = setInterval(function() {
        loadTableData();
    }, 30000);
}
```

**Features:**
- Configurable refresh interval (default: 30 seconds)
- Toggle on/off capability
- Manual refresh button
- Last update timestamp display

## Data Flow

### 1. Initial Page Load
```
User Opens Dashboard
    ↓
Dashboard View (restaurant/views.py)
    ↓
Queries Database for Table Data
    ↓
Passes Context to Template
    ↓
Template Renders with Initial Data
    ↓
JavaScript Initializes POS View
```

### 2. Real-time Updates
```
Auto-refresh Timer Triggers (30s)
    ↓
JavaScript calls loadTableData()
    ↓
AJAX Request to /api/table-status/
    ↓
API View Queries Database
    ↓
Returns JSON Response
    ↓
JavaScript Updates UI Elements
    ↓
User Sees Updated Information
```

## Database Queries

### Tables Query
```python
tables = RestaurantTable.objects.filter(
    restaurant=restaurant,
    is_active=True
).order_by('table_number')
```

### Active Orders Query
```python
active_orders = Order.objects.filter(
    table=table,
    status__in=['pending', 'accepted', 'preparing']
).distinct().count()
```

### Completed Orders Query
```python
completed_orders = Order.objects.filter(
    table=table,
    status='delivered',
    payment_status='pending'
).distinct().count()
```

### Order Information Query
```python
latest_order = Order.objects.filter(
    table=table,
    status__in=['pending', 'accepted', 'preparing']
).order_by('-created_at').first()
```

## Section Assignment Logic

Tables are automatically assigned to sections based on:

1. **Table Section Field** (if available)
   ```python
   if hasattr(table, 'section'):
       section_key = table.section.lower()
   ```

2. **Table Number Prefix**
   ```python
   elif table.table_number.startswith('B'):
       section_key = 'bar'
   ```

3. **Table Number Range**
   ```python
   if int(table.table_number) > 20:
       section_key = 'non_ac'
   ```

## User Interface Features

### Visual Status Indicators
- **Green Badge** - Available tables count
- **Blue Badge** - Occupied tables count
- **Yellow Badge** - Running KOT count
- **Purple Badge** - Today's revenue

### Table Card States
- **Blank (White)** - Available table
- **Running (Blue gradient)** - Active order
- **Printed (Green gradient)** - KOT printed
- **Paid (Purple gradient)** - Bill settled
- **Running KOT (Yellow gradient)** - Kitchen active

### Interactive Elements
- **Click on table** - View order details or create new order
- **Hover on table** - See popup with order information
- **Auto-refresh toggle** - Enable/disable automatic updates
- **Floor plan selector** - Switch between different floors
- **Order type buttons** - Dine-in, Delivery, Take Away

## Performance Optimizations

### 1. Efficient Database Queries
- Uses `distinct()` to avoid duplicate counts
- Filters by restaurant to limit data
- Orders by creation date for latest orders
- Minimal database hits per request

### 2. Frontend Optimizations
- Updates only changed elements
- Uses data attributes for efficient DOM queries
- Implements debouncing for rapid updates
- Caches DOM element references

### 3. Network Optimizations
- Lightweight JSON responses
- Compressed data structure
- Error handling with fallbacks
- Configurable refresh intervals

## Error Handling

### Backend Errors
```python
if not restaurant:
    return JsonResponse({'error': 'No restaurant found'}, status=400)
```

### Frontend Errors
```javascript
.catch(error => {
    console.error('Error loading table data:', error);
    showNotification('Failed to load table data. Please refresh the page.', 'error');
});
```

## Security Features

### Authentication
- `@restaurant_owner_required` decorator on API endpoint
- Session-based authentication
- Restaurant ownership verification

### Data Validation
- Validates restaurant ownership
- Filters tables by active status
- Ensures order belongs to restaurant

## Future Enhancements

### Planned Features
1. **WebSocket Integration** - Real-time push updates without polling
2. **Sound Notifications** - Audio alerts for new orders
3. **Table Reservation System** - Book tables in advance
4. **Contactless Ordering** - QR code integration
5. **Move KOT/Items** - Transfer orders between tables
6. **Kitchen Display System** - Separate view for kitchen staff
7. **Analytics Dashboard** - Table utilization metrics
8. **Multi-floor Support** - Different floor plans

### Performance Improvements
1. **Redis Caching** - Cache table statuses for faster responses
2. **Database Indexing** - Optimize query performance
3. **Lazy Loading** - Load sections on demand
4. **Progressive Updates** - Update only changed tables

## Testing Recommendations

### Manual Testing
1. Create test tables in different sections
2. Create test orders with various statuses
3. Verify real-time updates work correctly
4. Test auto-refresh functionality
5. Check error handling with network issues

### Automated Testing
```python
def test_table_status_api():
    """Test the table status API endpoint"""
    # Create test restaurant and tables
    # Create test orders
    # Call API endpoint
    # Verify response structure
    # Check data accuracy
```

## Troubleshooting

### Common Issues

#### Tables Not Showing
- Check if tables are marked as `is_active=True`
- Verify restaurant ownership
- Check section assignment logic

#### Orders Not Updating
- Verify order status is in correct state
- Check if order has items
- Ensure order belongs to restaurant

#### Auto-refresh Not Working
- Check browser console for errors
- Verify API endpoint is accessible
- Check network connectivity

## Conclusion

The POS Table View now provides **real-time, database-driven information** for restaurant operations. All data is fetched from the database via a secure API endpoint, ensuring accuracy and reliability for restaurant staff managing dine-in orders.

**Key Benefits:**
- ✅ Real-time order tracking
- ✅ Accurate table availability
- ✅ Live customer information
- ✅ Automatic updates
- ✅ Comprehensive order details
- ✅ Professional POS interface

---

**Last Updated:** December 6, 2024  
**Version:** 1.0  
**Status:** Production Ready
