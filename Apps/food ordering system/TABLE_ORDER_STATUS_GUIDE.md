# 🍽️ Table Order Status Guide

## Quick Reference for Restaurant Staff

---

## 📊 Order Status Flow Chart

```
┌─────────────────────────────────────────────────────────────────┐
│                    TABLE ORDER WORKFLOW                          │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────┐
    │ PENDING  │  ← Customer places order via QR code or staff
    └────┬─────┘
         │
         ▼
    ┌──────────┐
    │ ACCEPTED │  ← Restaurant confirms order
    └────┬─────┘
         │
         ▼
    ┌──────────┐
    │PREPARING │  ← Kitchen is cooking the food
    └────┬─────┘
         │
         ▼
    ┌──────────┐
    │ SERVING  │  ← 🆕 Food is being served to table
    └────┬─────┘
         │
         ▼
    ┌──────────┐
    │DELIVERED │  ← Customers finished, payment processed
    └──────────┘

         OR

    ┌──────────┐
    │CANCELLED │  ← Order cancelled at any stage
    └──────────┘
```

---

## 🎯 When to Use Each Status

### 1️⃣ **PENDING** 🟡
**When:** Order just received
**Action:** Review order details
**Next:** Accept or Cancel

### 2️⃣ **ACCEPTED** 🟢
**When:** Order confirmed by restaurant
**Action:** Send to kitchen
**Next:** Start preparing

### 3️⃣ **PREPARING** 🔵
**When:** Kitchen is cooking
**Action:** Monitor cooking progress
**Next:** Food ready to serve

### 4️⃣ **SERVING** 🟣 (NEW!)
**When:** Food is being brought to table
**Action:** Server delivering food to customers
**Next:** Customers eating

### 5️⃣ **DELIVERED** ✅
**When:** Customers finished eating
**Action:** Process payment, clear table
**Next:** Table available for new customers

### 6️⃣ **CANCELLED** ❌
**When:** Order needs to be cancelled
**Action:** Refund if applicable
**Next:** Table available

---

## 🔄 Status Update Instructions

### **How to Update Order Status:**

1. **Go to Order Detail Page:**
   - Click on order from Table Orders List
   - Or click on table from Table Layout view

2. **Find Status Update Section:**
   - Scroll to "Order Actions" card
   - Look for "Update Status" dropdown

3. **Select New Status:**
   - Choose appropriate status from dropdown
   - Click "Update Status" button

4. **Confirmation:**
   - Success message appears
   - Order status updated immediately
   - Table status reflects change

---

## 📱 Quick Actions by Status

### **PENDING Orders:**
```
✅ Accept Order    → Changes to ACCEPTED
❌ Cancel Order    → Changes to CANCELLED
```

### **ACCEPTED Orders:**
```
👨‍🍳 Start Preparing → Changes to PREPARING
❌ Cancel Order     → Changes to CANCELLED
```

### **PREPARING Orders:**
```
🍽️ Start Serving   → Changes to SERVING
❌ Cancel Order     → Changes to CANCELLED
```

### **SERVING Orders:**
```
✅ Mark Delivered  → Changes to DELIVERED
```

### **DELIVERED Orders:**
```
💰 Process Payment → Order complete, table available
```

---

## 🏷️ Status Indicators

### **Visual Indicators on Table Cards:**

| Status | Color | Icon | Meaning |
|--------|-------|------|---------|
| Pending | Yellow | ⏳ | Waiting for confirmation |
| Accepted | Green | ✅ | Order confirmed |
| Preparing | Blue | 👨‍🍳 | Kitchen cooking |
| **Serving** | **Purple** | **🍽️** | **Food being served** |
| Delivered | Gray | ✔️ | Order complete |
| Cancelled | Red | ❌ | Order cancelled |

---

## ⏱️ Typical Time in Each Status

### **Average Duration:**

```
Pending:    2-5 minutes   (Quick review and accept)
Accepted:   1-2 minutes   (Send to kitchen)
Preparing:  15-30 minutes (Cooking time)
Serving:    5-10 minutes  (Bring food to table)
Delivered:  30-60 minutes (Customers eating)
```

**Total Order Time:** ~50-100 minutes from order to payment

---

## 🎯 Best Practices

### **For Servers:**

1. **Update to SERVING when:**
   - Food is plated and ready
   - You're walking to the table
   - Before placing food on table

2. **Update to DELIVERED when:**
   - Customers have finished eating
   - Table is cleared
   - Ready to process payment

### **For Kitchen Staff:**

1. **Update to PREPARING when:**
   - Order ticket received
   - Cooking has started

2. **Notify server when:**
   - Food is ready
   - Ready to move to SERVING

### **For Managers:**

1. **Monitor SERVING status:**
   - Ensure timely service
   - Track service efficiency
   - Identify bottlenecks

2. **Review status times:**
   - Optimize workflow
   - Improve customer experience

---

## 🚨 Common Issues & Solutions

### **Issue: Order stuck in PREPARING**
**Solution:** 
- Check with kitchen on progress
- Update to SERVING when ready
- Communicate with customers if delayed

### **Issue: Forgot to update to SERVING**
**Solution:**
- Update status as soon as noticed
- Helps track actual service times
- Important for analytics

### **Issue: Customer wants to add items**
**Solution:**
- Use "Add Items" button on order detail
- Items added to existing order
- Status remains unchanged

---

## 📊 Status Reports

### **Available Reports:**

1. **Active Orders by Status:**
   - See all orders in each status
   - Filter by status on Table Orders page

2. **Table Occupancy:**
   - View which tables have active orders
   - See current status of each table

3. **Service Time Analysis:**
   - Track time spent in each status
   - Identify slow stages

---

## 💡 Tips for Efficiency

### **Speed Up Service:**

1. ✅ Update status immediately when changing
2. ✅ Use Table Layout view for quick overview
3. ✅ Filter by status to prioritize orders
4. ✅ Check "Active Tables" for real-time status

### **Avoid Delays:**

1. ❌ Don't forget to update status
2. ❌ Don't skip SERVING status
3. ❌ Don't leave orders in wrong status
4. ❌ Don't delay payment processing

---

## 🎓 Training Checklist

### **New Staff Training:**

- [ ] Understand all 6 status types
- [ ] Know when to use each status
- [ ] Practice updating order status
- [ ] Learn to use Table Layout view
- [ ] Understand status indicators
- [ ] Know how to handle issues

---

## 📞 Quick Help

### **Need Help?**

1. **Can't find order:**
   - Use search on Table Orders page
   - Filter by table number
   - Check order ID

2. **Wrong status selected:**
   - Update to correct status immediately
   - No harm in changing status

3. **System not responding:**
   - Refresh page
   - Check internet connection
   - Contact manager

---

## 🎉 Benefits of Using SERVING Status

### **For Restaurant:**
✅ Better service tracking
✅ Improved efficiency
✅ Clear communication
✅ Accurate timing data

### **For Customers:**
✅ Know when food is coming
✅ Better service experience
✅ Reduced wait time confusion

### **For Staff:**
✅ Clear workflow
✅ Easy to track progress
✅ Less confusion
✅ Better coordination

---

**Remember:** Accurate status updates = Better service = Happy customers! 🌟

---

**Last Updated:** December 7, 2025
**Version:** 1.0.0
