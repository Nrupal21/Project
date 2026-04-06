# TravelGuide Rewards System Documentation

## Overview

The TravelGuide Rewards System is a comprehensive points-based loyalty program that rewards users for various activities within the platform. This document explains the database structure, key components, and functionality of the rewards system.

The rewards system is designed to increase user engagement, encourage platform loyalty, and provide additional value to frequent users. It follows a tiered approach where users can progress through different membership levels (Bronze, Silver, Gold, Platinum) as they accumulate points, with each tier offering increased benefits and point earning potential.

The system is fully integrated with the TravelGuide platform's indigo/violet color scheme, ensuring visual consistency across all user interfaces and admin panels.

## Database Structure

### Tables

#### 1. `rewards_rewardtier`

Stores membership tier levels with associated benefits and requirements.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary key for the reward tier |
| name | varchar(20) | Name of the tier (e.g., BRONZE, SILVER, GOLD) |
| min_points | integer | Minimum points required to reach this tier |
| point_multiplier | double precision | Multiplier applied to point earnings for users in this tier |
| benefits | jsonb | JSON object containing tier benefits |
| icon | varchar(50) | Icon identifier for the tier |
| color | varchar(20) | Color code for the tier (indigo/violet palette) |
| is_active | boolean | Whether the tier is currently active |
| created_at | timestamp | When the tier was created |
| updated_at | timestamp | When the tier was last updated |

#### 2. `rewards_rewardpoints`

Tracks all point transactions for users.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary key for the reward points transaction |
| user_id | integer | Foreign key to the user who earned/spent points |
| activity | varchar(50) | Type of activity that generated the points |
| points | integer | Number of points earned or spent (negative for redemptions) |
| description | varchar(255) | Human-readable description of the transaction |
| expiration_date | timestamp | Date when these points expire, if applicable |
| is_expired | boolean | Flag indicating if points have expired |
| created_at | timestamp | Timestamp when the points were earned or spent |
| reference_id | uuid | UUID reference to related entity (booking, review, etc.) |
| reference_type | varchar(50) | Type of entity referenced by reference_id |

#### 3. `rewards_rewardredemption`

Records of reward point redemptions by users.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | UUID primary key for the redemption |
| user_id | integer | Foreign key to the user who redeemed points |
| redemption_type | varchar(50) | Type of redemption (discount, upgrade, etc.) |
| points_used | integer | Number of points used for this redemption |
| redemption_value | numeric(10,2) | Monetary value of the redemption if applicable |
| status | varchar(20) | Current status (pending, approved, rejected, used) |
| code | varchar(50) | Redemption code if applicable |
| expiry_date | timestamp | Date when the redemption expires |
| created_at | timestamp | Timestamp when the redemption was created |
| updated_at | timestamp | Timestamp when the redemption was last updated |
| notes | text | Additional notes or comments about the redemption |

### Views

#### 1. `rewards_user_point_balance`

Provides current point balances and statistics for all users.

| Column | Description |
|--------|-------------|
| user_id | User's ID |
| username | User's username |
| current_points | Current active (non-expired) point balance |
| total_points_earned | Total points earned (including expired) |
| earning_transactions | Count of transactions where points were earned |
| spending_transactions | Count of transactions where points were spent |

#### 2. `rewards_user_tier_status`

Shows current tier status for each user with progress to next tier.

| Column | Description |
|--------|-------------|
| user_id | User's ID |
| username | User's username |
| current_points | Current active point balance |
| current_tier | Name of the user's current tier |
| point_multiplier | Current tier's point multiplier |
| benefits | JSON object with current tier benefits |
| icon | Icon for current tier |
| color | Color code for current tier (indigo/violet palette) |
| next_tier | Name of the next tier user can achieve |
| points_to_next_tier | Points needed to reach next tier |

## Key Components

### Models

1. **RewardTier**: Defines the different membership tiers and their benefits
2. **RewardPoints**: Tracks point transactions (earning and spending)
3. **RewardRedemption**: Records redemption requests and their status

### Views

1. **Dashboard**: Overview of user's rewards status
2. **Points History**: List of all point transactions
3. **Redemption History**: List of all redemption requests
4. **Redeem Points**: Form for redeeming points
5. **Tier Benefits**: Information about different tier levels

## Point Earning Activities

Users can earn points through various activities:

- Completing bookings
- Writing reviews
- Referring friends
- Completing profile information
- Annual loyalty bonuses
- Special promotions
- Daily logins

### Signal Handlers Implementation

The rewards system uses Django's signal framework to automatically award points when certain actions occur. Each signal handler is thoroughly documented with inline comments explaining its purpose, logic, and configuration options.

#### Registration Points

```python
@receiver(post_save, sender=User)
def award_registration_points(sender, instance, created, **kwargs):
    # Awards points when a new user registers
    # Points value configurable via settings.REWARD_POINTS_REGISTRATION
    # Points do not expire (no expiry_days parameter)
```

#### Booking Points

```python
@receiver(post_save, sender=Booking)
def award_booking_points(sender, instance, created, **kwargs):
    # Awards points based on booking value
    # Base points + percentage of booking value
    # Points expire after 365 days
```

#### Review Points

```python
@receiver(post_save, sender=Review)
def award_review_points(sender, instance, created, **kwargs):
    # Awards base points + bonuses for content and photos
    # Content bonus if review has detailed text
    # Photo bonus if review includes images
    # Points expire after 180 days
```

#### Daily Login Points

```python
# Called from view when user logs in
def award_daily_login_points(user):
    # Awards points once per day when user logs in
    # Checks if points already awarded today
    # Points expire after 90 days
```

#### Profile Completion Points

```python
# Called when user completes their profile
def award_profile_completion_points(user):
    # Awards one-time bonus for completing profile
    # Checks if already awarded to prevent duplicates
    # Points expire after 365 days
```

#### Referral Points

```python
# Called when a referred user registers
def award_referral_points(referrer, new_user):
    # Awards points to the referrer when new user registers
    # Records reference to the new user
    # Points expire after 180 days
```

All point values and expiration periods are configurable through Django settings with sensible defaults provided.

## Redemption Options

Users can redeem points for:

- Discounts on bookings
- Free upgrades
- Exclusive experiences
- Partner rewards
- Merchandise

## Color Scheme

The rewards system uses the indigo/violet color palette:

- Primary colors: indigo-500/600 to violet-600/700
- Accent colors: violet-400 for highlights
- Background gradients: indigo-500 to violet-700
- Text: white on dark backgrounds, indigo-900 on light backgrounds

## Implementation Notes

1. Points expire after 24 months by default
2. Tier status is recalculated nightly
3. Redemption requests require approval for high-value items
4. Point multipliers apply based on user's current tier
5. All database tables include comprehensive comments for developer reference

## Code Structure and Organization

### Core Files

1. **models.py**: Contains all database models with comprehensive docstrings
   - `RewardActivity`: Enum defining all point-earning activities
   - `RewardRedemptionType`: Enum defining redemption categories
   - `RewardTier`: Model for membership tiers and benefits
   - `RewardPoints`: Model for point transactions
   - `RewardRedemption`: Model for redemption requests

2. **views.py**: Contains all view classes with detailed comments
   - `RewardsHomeView`: Dashboard showing points, tier status, and available rewards
   - `PointsHistoryView`: Paginated history of point transactions
   - `RedemptionHistoryView`: List of past redemption requests
   - `RedeemPointsView`: Form for redeeming points
   - `TierBenefitsView`: Information about tier levels and benefits

3. **forms.py**: Contains form classes with validation logic
   - `RedemptionForm`: Form for redeeming points with validation

4. **signals.py**: Contains signal handlers for automatic point awards
   - `award_registration_points`: Awards points on user registration
   - `award_booking_points`: Awards points when bookings are created
   - `award_review_points`: Awards points when reviews are submitted
   - `award_profile_completion_points`: Awards points for profile completion
   - `award_daily_login_points`: Awards points for daily logins
   - `award_referral_points`: Awards points for referring new users

5. **admin.py**: Admin interface customizations
   - `RewardTierAdmin`: Admin interface for managing tiers
   - `RewardPointsAdmin`: Admin interface for point transactions
   - `RewardRedemptionAdmin`: Admin interface for processing redemptions

6. **urls.py**: URL routing for the rewards app

7. **apps.py**: App configuration and initialization

### Templates

1. **rewards_home.html**: Main dashboard template
2. **points_history.html**: Point transaction history
3. **redemption_history.html**: Redemption request history
4. **redeem_points.html**: Form for redeeming points
5. **tier_benefits.html**: Information about tier levels

All templates follow the indigo/violet color scheme and include comprehensive comments explaining their structure and functionality.

## Database Indexes

The following indexes improve query performance:

- `rewards_rewardpoints_user_id_idx`: For quick lookup of user's points
- `rewards_rewardpoints_created_at_idx`: For efficient date-based filtering
- `rewards_rewardredemption_user_id_idx`: For quick lookup of user's redemptions
- `rewards_rewardredemption_status_idx`: For filtering by redemption status

## API Endpoints

The rewards system exposes several API endpoints:

- `GET /api/rewards/points/`: Get user's current points balance
- `GET /api/rewards/tier/`: Get user's current tier information
- `GET /api/rewards/history/`: Get user's point transaction history
- `POST /api/rewards/redeem/`: Submit a redemption request

## Frontend Components

The rewards system includes several frontend components:

- Points balance display
- Tier progress bar
- Redemption form
- Transaction history table
- Tier benefits comparison chart

All components use the indigo/violet color palette for consistency with the overall site design.
