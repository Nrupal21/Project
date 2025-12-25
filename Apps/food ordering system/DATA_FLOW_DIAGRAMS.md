# Data Flow Diagrams for Food Ordering System

## Table of Contents

1. [Context Level DFD (Level 0)](#1-context-level-dfd-level-0)
   - Purpose
   - External Entities
   - Data Flows
   - Data Flow Descriptions

2. [Level 1 DFD - System Overview](#2-level-1-dfd---system-overview)
   - Purpose
   - Major Processes
   - Data Stores
   - Level 1 DFD Diagram

3. [Level 2 DFDs](#3-level-2-dfds)
   - Process 1.0 - User Management
   - Process 2.0 - Restaurant Management
   - Process 3.0 - Menu Management
   - Process 4.0 - Order Processing
   - Process 5.0 - Payment Processing
   - Process 6.0 - Notification System

4. [Data Store Descriptions](#4-data-store-descriptions)
   - D1: User Database
   - D2: Restaurant Database
   - D3: Menu Database
   - D4: Order Database
   - D5: Payment Database

---

## Overview
This document contains the Data Flow Diagrams (DFDs) for the Food Ordering System, showing the flow of data through the system at different levels of abstraction.

---

## 1. Context Level DFD (Level 0)

### Purpose
Shows the entire system as a single process and its interaction with external entities.

### External Entities
- **Customer**: Places orders and makes payments
- **Restaurant Owner**: Manages restaurant profile and menu
- **System Administrator**: Manages system configuration
- **Payment Gateway**: Processes payment transactions
- **Email Service**: Sends notifications and confirmations

### Data Flows
```
┌─────────────────┐    Order Details    ┌──────────────────┐
│    Customer     │────────────────────►│                  │
│                 │                     │   Food Ordering  │
│                 │   Order Confirmation│      System      │
│                 │◄────────────────────│                  │
└─────────────────┘                     │                  │
                                        │                  │
┌─────────────────┐  Restaurant Info    │                  │  Menu Items
│ Restaurant Owner│────────────────────►│                  │◄─────────────
│                 │                     │                  │
│                 │   Order Updates     │                  │
│                 │◄────────────────────│                  │
└─────────────────┘                     │                  │
                                        │                  │
┌─────────────────┐  Admin Commands     │                  │  System Reports
│  System Admin   │────────────────────►│                  │◄─────────────
│                 │                     │                  │
│                 │   Admin Results     │                  │
│                 │◄────────────────────│                  │
└─────────────────┘                     └──────────────────┘
                                                │
                                                │ Payment Data
                                                ▼
                                        ┌──────────────────┐
                                        │  Payment Gateway │
                                        │                  │
                                        │  Payment Status  │
                                        │◄─────────────────
                                        └──────────────────┘
                                                │
                                                │ Email Data
                                                ▼
                                        ┌──────────────────┐
                                        │   Email Service  │
                                        │                  │
                                        │  Delivery Status │
                                        │◄─────────────────
                                        └──────────────────┘
```

### Data Flow Descriptions
1. **Order Details**: Customer places order with menu items, delivery address, and special instructions
2. **Order Confirmation**: System confirms order receipt with order ID and estimated delivery time
3. **Restaurant Info**: Restaurant owner updates profile, menu, and availability
4. **Menu Items**: System displays available restaurants and menu items to customers
5. **Order Updates**: System notifies restaurant of new orders and status changes
6. **Admin Commands**: Administrator manages users, restaurants, and system settings
7. **System Reports**: System generates analytics and operational reports
8. **Payment Data**: Payment processing requests and confirmations
9. **Email Data**: Order confirmations, status updates, and promotional emails

---

## 2. Level 1 DFD - System Overview

### Purpose
Decomposes the system into major processes and shows data flow between them.

### Major Processes
1. **User Management** (Process 1.0)
2. **Restaurant Management** (Process 2.0)
3. **Menu Management** (Process 3.0)
4. **Order Processing** (Process 4.0)
5. **Payment Processing** (Process 5.0)
6. **Notification System** (Process 6.0)

### Data Stores
- **D1: User Database**
- **D2: Restaurant Database**
- **D3: Menu Database**
- **D4: Order Database**
- **D5: Payment Database**

### Level 1 DFD Diagram
```
┌─────────────────┐
│    Customer     │
│                 │
└─────────┬───────┘
          │ Login/Registration
          ▼
    ┌─────────────────┐    User Data    ┌──────────────────┐
    │   Process 1.0   │◄─────────────── │        D1        │
    │ User Management │                 │   User Database  │
    └─────────┬───────┘                 └──────────────────┘
              │ User Info
              ▼
┌─────────────────┐    Restaurant    ┌──────────────────┐
│ Restaurant Owner│   Management     │                  │
│                 │─────────────────►│   Process 2.0    │
└─────────┬───────┘                  │ Restaurant Mgmt  │
          │ Menu Updates             └─────────┬────────┘
          ▼                                    │ Menu Data
    ┌─────────────────┐    Menu Data    ┌──────▼─────────┐
    │   Process 3.0   │◄─────────────── │      D2        │
    │ Menu Management │                 │Restaurant DB   │
    └─────────┬───────┘                 └────────────────┘
              │ Available Menu
              ▼
    ┌─────────────────┐    Order Data    ┌──────────────────┐
    │   Process 4.0   │◄───────────────  │        D3        │
    │Order Processing │                  │   Menu Database  │
    └─────────┬───────┘                  └──────────────────┘
              │ Order Info
              ▼
    ┌──────────────────┐    Payment Info  ┌──────────────────┐
    │   Process 5.0    │◄───────────────  │        D4        │
    │Payment Processing│                  │   Order Database │
    └─────────┬────────┘                  └──────────────────┘
              │ Payment Status
              ▼
    ┌─────────────────┐    Notification ┌──────────────────┐
    │   Process 6.0   │    Data         │        D5        │
    │Notification Sys │◄─────────────── │ Payment Database │
    └─────────┬───────┘                 └──────────────────┘
              │ Notifications
              ▼
   ┌─────────────────┐
   │  Email Service  │
   │                 │
   └─────────────────┘
```

---

## 3. Level 2 DFDs

### 3.1 Process 1.0 - User Management

#### Purpose
Shows detailed data flow for user registration, authentication, and profile management.

#### Sub-processes
- **1.1 User Registration**
- **1.2 User Authentication**
- **1.3 Profile Management**
- **1.4 Password Management**

#### Data Flow Diagram
```
┌─────────────────┐
│    Customer     │
│                 │
└─────────┬───────┘
          │ Registration Data
          ▼
    ┌─────────────────┐    User Info    ┌──────────────────┐
    │   Process 1.1   │────────────────►│        D1        │
    │   Registration  │                 │   User Database  │
    └─────────┬───────┘                 └──────────────────┘
              │ Validation
              ▼
    ┌─────────────────┐    Login Data    ┌──────────────────┐
    │   Process 1.2   │◄──────────────── │        D1        │
    │ Authentication  │                  │   User Database  │
    └─────────┬───────┘                  └──────────────────┘
              │ Auth Token
              ▼
    ┌─────────────────┐    Profile Data  ┌──────────────────┐
    │   Process 1.3   │◄──────────────── │        D1        │
    │Profile Mgmt     │                  │   User Database  │
    └─────────┬───────┘                  └──────────────────┘
              │ Updated Profile
              ▼
    ┌─────────────────┐    Password Data ┌──────────────────┐
    │   Process 1.4   │◄──────────────── │        D1        │
    │Password Mgmt    │                  │   User Database  │
    └─────────────────┘                  └──────────────────┘
```

### 3.2 Process 2.0 - Restaurant Management

#### Purpose
Details restaurant registration, profile management, and approval workflow.

#### Sub-processes
- **2.1 Restaurant Registration**
- **2.2 Profile Management**
- **2.3 Approval Process**
- **2.4 Rating Management**

#### Data Flow Diagram
```
┌─────────────────┐
│ Restaurant Owner│
│                 │
└─────────┬───────┘
          │ Restaurant Data
          ▼
    ┌─────────────────┐    Restaurant   ┌──────────────────┐
    │   Process 2.1   │      Info       │        D2        │
    │   Registration  │────────────────►│ Restaurant DB    │
    └─────────┬───────┘                 └──────────────────┘
              │ Profile Updates
              ▼
    ┌─────────────────┐    Updated Info  ┌──────────────────┐
    │   Process 2.2   │◄──────────────── │        D2        │
    │Profile Mgmt     │                  │ Restaurant DB    │
    └─────────┬───────┘                  └──────────────────┘
              │ Approval Request
              ▼
    ┌─────────────────┐    Approved     ┌──────────────────┐
    │   Process 2.3   │   Restaurants   │        D2        │
    │Approval Process │◄─────────────── │ Restaurant DB    │
    └─────────┬───────┘                 └──────────────────┘
              │ Rating Data
              ▼
    ┌─────────────────┐    Updated       ┌──────────────────┐
    │   Process 2.4   │    Ratings       │        D2        │
    │Rating Mgmt      │─────────────────►│ Restaurant DB    │
    └─────────────────┘                  └──────────────────┘
```

### 3.3 Process 3.0 - Menu Management

#### Purpose
Shows menu creation, item management, and pricing workflow.

#### Sub-processes
- **3.1 Category Management**
- **3.2 Menu Item Creation**
- **3.3 Price Management**
- **3.4 Availability Management**

#### Data Flow Diagram
```
┌─────────────────┐
│ Restaurant Owner│
│                 │
└─────────┬───────┘
          │ Category Data
          ▼
    ┌─────────────────┐    Categories   ┌──────────────────┐
    │   Process 3.1   │                 │        D3        │
    │Category Mgmt    │─────────────────►│   Menu Database  │
    └─────────┬───────┘                 └──────────────────┘
              │ Item Data
              ▼
    ┌─────────────────┐    Menu Items   ┌──────────────────┐
    │   Process 3.2   │─────────────────►│        D3        │
    │Item Creation    │                 │   Menu Database  │
    └─────────┬───────┘                 └──────────────────┘
              │ Price Updates
              ▼
    ┌─────────────────┐    Updated      ┌──────────────────┐
    │   Process 3.3   │   Prices        │        D3        │
    │Price Mgmt       │◄──────────────── │   Menu Database  │
    └─────────┬───────┘                 └──────────────────┘
              │ Availability
              ▼
    ┌─────────────────┐    Status       ┌──────────────────┐
    │   Process 3.4   │   Updates       │        D3        │
    │Availability Mgmt │─────────────────►│   Menu Database  │
    └─────────────────┘                 └──────────────────┘
```

### 3.4 Process 4.0 - Order Processing

#### Purpose
Details the complete order lifecycle from placement to delivery.

#### Sub-processes
- **4.1 Order Placement**
- **4.2 Order Validation**
- **4.3 Order Tracking**
- **4.4 Order Completion**

#### Data Flow Diagram
```
┌─────────────────┐
│    Customer     │
│                 │
└─────────┬───────┘
          │ Order Request
          ▼
    ┌─────────────────┐    Order Data   ┌──────────────────┐
    │   Process 4.1   │────────────────►│        D4        │
    │Order Placement  │                 │   Order Database │
    └─────────┬───────┘                 └──────────────────┘
              │ Validation
              ▼
    ┌─────────────────┐    Validated    ┌──────────────────┐
    │   Process 4.2   │    Orders       │        D4        │
    │Order Validation │◄─────────────── │   Order Database │
    └─────────┬───────┘                 └──────────────────┘
              │ Status Updates
              ▼
    ┌─────────────────┐    Tracking     ┌──────────────────┐
    │   Process 4.3   │    Data         │        D4        │
    │Order Tracking   │◄─────────────── │   Order Database │
    └─────────┬───────┘                 └──────────────────┘
              │ Completion
              ▼
    ┌─────────────────┐    Completed    ┌──────────────────┐
    │   Process 4.4   │    Orders       │        D4        │
    │Order Completion │────────────────►│   Order Database │
    └─────────────────┘                 └──────────────────┘
```

### 3.5 Process 5.0 - Payment Processing

#### Purpose
Shows payment transaction flow and financial data management.

#### Sub-processes
- **5.1 Payment Initiation**
- **5.2 Payment Validation**
- **5.3 Transaction Processing**
- **5.4 Payment Confirmation**

#### Data Flow Diagram
```
┌─────────────────┐
│    Customer     │
│                 │
└─────────┬───────┘
          │ Payment Request
          ▼
    ┌─────────────────┐    Payment      ┌──────────────────┐
    │   Process 5.1   │    Request      │        D5        │
    │Payment Initiate │─────────────────►│ Payment Database │
    └─────────┬───────┘                 └──────────────────┘
              │ Validation
              ▼
    ┌─────────────────┐    Valid        ┌──────────────────┐
    │   Process 5.2   │    Payments     │        D5        │
    │Payment Validate │◄──────────────── │ Payment Database │
    └─────────┬───────┘                 └──────────────────┘
              │ Transaction
              ▼
    ┌─────────────────┐    Transaction  ┌──────────────────┐
    │   Process 5.3   │    Data         │        D5        │
    │Transaction Proc │─────────────────►│ Payment Database │
    └─────────┬───────┘                 └──────────────────┘
              │ Confirmation
              ▼
    ┌─────────────────┐    Confirmed    ┌──────────────────┐
    │   Process 5.4   │    Payments     │        D5        │
    │Payment Confirm  │◄──────────────── │ Payment Database │
    └─────────────────┘                 └──────────────────┘
```

### 3.6 Process 6.0 - Notification System

#### Purpose
Details notification generation and delivery to various stakeholders.

#### Sub-processes
- **6.1 Notification Generation**
- **6.2 Email Processing**
- **6.3 SMS Processing**
- **6.4 Push Notification**

#### Data Flow Diagram
```
┌─────────────────┐
│   System Events │
│                 │
└─────────┬───────┘
          │ Event Data
          ▼
    ┌─────────────────┐    Notification  ┌──────────────────┐
    │   Process 6.1   │    Templates     │ Notification DB  │
    │Notification Gen │◄──────────────── │ (Internal)       │
    └─────────┬───────┘                 └──────────────────┘
              │ Email Data
              ▼
    ┌─────────────────┐
    │   Process 6.2   │
    │Email Processing │
    └─────────┬───────┘
              │ SMS Data
              ▼
    ┌─────────────────┐
    │   Process 6.3   │
    │ SMS Processing  │
    └─────────┬───────┘
              │ Push Data
              ▼
    ┌─────────────────┐
    │   Process 6.4   │
    │Push Notification│
    └─────────────────┘
```

---

## 4. Data Dictionary

### Data Stores Description

#### D1: User Database
- **Purpose**: Stores user information and authentication data
- **Key Fields**: user_id, username, email, password, role, profile_data
- **Relationships**: 1:M with orders, 1:M with restaurants

#### D2: Restaurant Database
- **Purpose**: Maintains restaurant information and operational data
- **Key Fields**: restaurant_id, name, address, cuisine_type, rating, owner_id
- **Relationships**: 1:M with menu items, 1:M with orders

#### D3: Menu Database
- **Purpose**: Stores menu items, categories, and pricing information
- **Key Fields**: item_id, restaurant_id, category_id, name, price, availability
- **Relationships**: M:1 with restaurants, M:1 with categories, M:N with orders

#### D4: Order Database
- **Purpose**: Tracks all order information and status
- **Key Fields**: order_id, user_id, restaurant_id, status, total_amount, timestamp
- **Relationships**: M:1 with users, M:1 with restaurants, M:N with menu items

#### D5: Payment Database
- **Purpose**: Records all payment transactions and financial data
- **Key Fields**: payment_id, order_id, amount, status, payment_method, timestamp
- **Relationships**: 1:1 with orders

---

## 5. Implementation Notes

### Technology Considerations
- **Django ORM** for database abstraction and relationship management
- **REST API** for data exchange between frontend and backend
- **WebSocket** for real-time order tracking and notifications
- **Redis** for caching frequently accessed data
- **Celery** for background task processing (notifications, emails)

### Security Considerations
- **Data Encryption**: Sensitive data encrypted at rest and in transit
- **Access Control**: Role-based permissions for different user types
- **Input Validation**: All user inputs validated and sanitized
- **Audit Trail**: Complete audit log for all data modifications

### Performance Considerations
- **Database Indexing**: Strategic indexing on frequently queried fields
- **Caching Strategy**: Multi-level caching for improved response times
- **Load Balancing**: Horizontal scaling for high-traffic scenarios
- **Query Optimization**: Efficient database queries to minimize response times

---

**Document Version: 1.0**
**Created: December 2024**
**Author: Food Ordering System Development Team**
**Format: Digital (Mermaid/Diagrams.net compatible)**
