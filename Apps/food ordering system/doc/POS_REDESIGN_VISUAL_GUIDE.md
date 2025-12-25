# 🎨 POS Table View - Visual Design Guide

## Color Scheme & Visual Identity

### 🎨 Primary Color Palette

```
┌─────────────────────────────────────────────────────────┐
│  HEADER & STATISTICS GRADIENT                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Indigo-600 → Purple-600 → Pink-500                     │
│  #4f46e5    → #9333ea    → #ec4899                      │
└─────────────────────────────────────────────────────────┘
```

### 📊 Section Color Themes

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  A/C SECTION     │  │  NON A/C SECTION │  │  BAR SECTION     │
│  ──────────────  │  │  ──────────────  │  │  ──────────────  │
│  🌨️ Blue Theme   │  │  ☀️ Orange Theme  │  │  🍷 Purple Theme  │
│  white → blue-50 │  │  white → orange  │  │  white → purple  │
│  Border: blue    │  │  Border: orange  │  │  Border: purple  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

### 🎯 Status Color Codes

```
┌─────────────────────────────────────────────────────────┐
│  TABLE STATUS COLORS                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                          │
│  ⚪ BLANK/AVAILABLE    →  White (#ffffff)              │
│  🔵 RUNNING ORDER      →  Blue (#3b82f6)               │
│  🟢 PRINTED KOT        →  Green (#10b981)              │
│  🟣 PAID/SETTLED       →  Purple (#a855f7)             │
│  🟡 RUNNING KOT        →  Yellow (#eab308)             │
│  🟠 NEEDS ATTENTION    →  Orange (#f97316) + Pulse     │
└─────────────────────────────────────────────────────────┘
```

---

## 📐 Layout Structure

### Desktop View (>1024px)

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER - Gradient Background with Controls                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  🍽️ POS Table Management    [Floor] [Auto] [Refresh]   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ACTION BAR - Order Types & Quick Actions                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  [Dine In] [Delivery] [Takeaway]  |  [Reserve] [QR] [Move] │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  LEGEND - Status Guide                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ⚪ Blank  🔵 Running  🟢 Printed  🟣 Paid  🟡 KOT      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┬──────────────────┬──────────────────┐
│  A/C SECTION     │  NON A/C SECTION │  BAR SECTION     │
│  ┌────────────┐  │  ┌────────────┐  │  ┌────────────┐  │
│  │ 🌨️ A/C     │  │  │ ☀️ Non A/C  │  │  │ 🍷 Bar      │  │
│  │ 12 Free    │  │  │ 7 Free     │  │  │ 6 Free     │  │
│  │ 4 Busy     │  │  │ 3 Busy     │  │  │ 0 Busy     │  │
│  ├────────────┤  │  ├────────────┤  │  ├────────────┤  │
│  │ [1][2][3]  │  │  │ [21][22]   │  │  │ [B1][B2]   │  │
│  │ [4][5][6]  │  │  │ [23][24]   │  │  │ [B3][B4]   │  │
│  └────────────┘  │  └────────────┘  │  └────────────┘  │
└──────────────────┴──────────────────┴──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  STATISTICS DASHBOARD - Gradient Background                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📊 Live Statistics Dashboard                           │   │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐              │   │
│  │  │  25  │  │  7   │  │  3   │  │ ₹500 │              │   │
│  │  │ Free │  │ Busy │  │ KOT  │  │ Rev  │              │   │
│  │  └──────┘  └──────┘  └──────┘  └──────┘              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Mobile View (<768px)

```
┌─────────────────────────────┐
│  HEADER (Stacked)           │
│  ┌─────────────────────────┐│
│  │  🍽️ POS Management      ││
│  │  [Floor Selector]       ││
│  │  [Auto] [Refresh]       ││
│  └─────────────────────────┘│
└─────────────────────────────┘

┌─────────────────────────────┐
│  ACTION BAR (Wrapped)       │
│  ┌─────────────────────────┐│
│  │  [Dine In]              ││
│  │  [Delivery] [Takeaway]  ││
│  │  [Reserve] [QR] [Move]  ││
│  └─────────────────────────┘│
└─────────────────────────────┘

┌─────────────────────────────┐
│  A/C SECTION (Full Width)   │
│  ┌─────────────────────────┐│
│  │  [1][2][3][4][5][6]     ││
│  └─────────────────────────┘│
└─────────────────────────────┘

┌─────────────────────────────┐
│  STATISTICS (2 Columns)     │
│  ┌───────────┬───────────┐  │
│  │   25      │    7      │  │
│  │   Free    │   Busy    │  │
│  ├───────────┼───────────┤  │
│  │    3      │   ₹500    │  │
│  │   KOT     │   Rev     │  │
│  └───────────┴───────────┘  │
└─────────────────────────────┘
```

---

## 🎭 Component Anatomy

### Header Component

```
┌─────────────────────────────────────────────────────────────┐
│  ╔═══════════════════════════════════════════════════════╗  │
│  ║  GRADIENT BACKGROUND (Indigo → Purple → Pink)        ║  │
│  ║  ┌─────────────────────────────────────────────────┐ ║  │
│  ║  │  Decorative Circles (Opacity 10%)               │ ║  │
│  ║  │  ○ Top-left: 256px circle                       │ ║  │
│  ║  │  ○ Bottom-right: 384px circle                   │ ║  │
│  ║  └─────────────────────────────────────────────────┘ ║  │
│  ║                                                       ║  │
│  ║  ┌────┐  POS Table Management                       ║  │
│  ║  │ 🍽️ │  Real-time order tracking & monitoring     ║  │
│  ║  └────┘                                              ║  │
│  ║                                                       ║  │
│  ║  [🏢 Main Floor ▼]  [🔄 Auto: ON]  [Refresh]       ║  │
│  ╚═══════════════════════════════════════════════════════╝  │
└─────────────────────────────────────────────────────────────┘
```

### Table Card Component

```
┌─────────────────────────────────────┐
│  TABLE CARD STATES                  │
│  ─────────────────────────────────  │
│                                      │
│  ⚪ BLANK/AVAILABLE                 │
│  ┌──────┐                           │
│  │  1   │  ← White background       │
│  │      │     Gray border           │
│  └──────┘                           │
│                                      │
│  🔵 RUNNING ORDER                   │
│  ┌──────┐                           │
│  │  2   │  ← Blue gradient          │
│  │  ●   │     Blue border           │
│  └──────┘     Status dot            │
│                                      │
│  🟡 RUNNING KOT                     │
│  ┌──────┐                           │
│  │  3   │  ← Yellow gradient        │
│  │ ● ●  │     Yellow border         │
│  └──────┘     Multiple dots         │
│                                      │
│  🟠 NEEDS ATTENTION (Pulsing)       │
│  ┌──────┐                           │
│  │  4   │  ← Orange gradient        │
│  │  ⚠️  │     Orange border         │
│  └──────┘     Pulse animation       │
└─────────────────────────────────────┘
```

### Statistics Card Component

```
┌─────────────────────────────────────────────┐
│  STATISTICS CARD ANATOMY                    │
│  ─────────────────────────────────────────  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │  ┌────────┐                          │  │
│  │  │  Icon  │  ← Gradient background   │  │
│  │  │   ✓    │     14x14 rounded        │  │
│  │  └────────┘                          │  │
│  │                                       │  │
│  │  25  ← Large number (4xl, black)     │  │
│  │                                       │  │
│  │  AVAILABLE TABLES  ← Label           │  │
│  │  ─────────────────                   │  │
│  │  Ready for customers  ← Subtitle     │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  Hover Effect:                               │
│  • Lift up 4px                              │
│  • Shadow increases                         │
│  • Smooth transition                        │
└─────────────────────────────────────────────┘
```

---

## 🎬 Animation Showcase

### Hover Animations

```
TABLE CARD HOVER:
┌──────┐         ┌──────┐
│  1   │   →     │  1   │  ↑ Lift 2px
│      │         │  ●   │  ⚡ Scale 1.1x
└──────┘         └──────┘  ✨ Shadow enhanced

BUTTON HOVER:
[Reserve Table]  →  [Reserve Table]  ↑ Lift 2px
                                      ✨ Shadow xl

STATISTICS HOVER:
┌──────┐         ┌──────┐
│  25  │   →     │  25  │  ↑ Lift 4px
│ Free │         │ Free │  ✨ Shadow 2xl
└──────┘         └──────┘
```

### Pulse Animation (Needs Attention)

```
FRAME 1 (0s):     FRAME 2 (1s):     FRAME 3 (2s):
┌──────┐         ┌──────┐         ┌──────┐
│  4   │  100%   │  4   │   80%   │  4   │  100%
│  ⚠️  │  ────→  │  ⚠️  │  ────→  │  ⚠️  │  ────→
└──────┘         └──────┘         └──────┘
                  (Fade)           (Repeat)
```

### Refresh Button Rotation

```
NORMAL:           HOVER:
  🔄        →       🔄
  0°                180°
                (500ms ease)
```

---

## 📏 Spacing & Sizing Guide

### Element Sizes

```
┌─────────────────────────────────────────┐
│  COMPONENT DIMENSIONS                   │
│  ─────────────────────────────────────  │
│                                          │
│  Table Card:                             │
│  • Desktop: 64px × 64px (4rem)          │
│  • Mobile: 48px × 48px (3rem)           │
│                                          │
│  Icon Badge:                             │
│  • Size: 56px × 56px (14 units)         │
│  • Border Radius: 12px (xl)             │
│                                          │
│  Status Dot:                             │
│  • Desktop: 12px (0.75rem)              │
│  • Mobile: 8px (0.5rem)                 │
│                                          │
│  Border Radius:                          │
│  • Cards: 24px (3xl)                    │
│  • Buttons: 12px (xl)                   │
│  • Tables: 12px (xl)                    │
└─────────────────────────────────────────┘
```

### Spacing System

```
┌─────────────────────────────────────────┐
│  SPACING SCALE                          │
│  ─────────────────────────────────────  │
│                                          │
│  Gap-2:  8px   (0.5rem)  ••             │
│  Gap-3:  12px  (0.75rem) •••            │
│  Gap-4:  16px  (1rem)    ••••           │
│  Gap-6:  24px  (1.5rem)  ••••••         │
│  Gap-8:  32px  (2rem)    ••••••••       │
│                                          │
│  Padding:                                │
│  • Cards: p-6 (24px)                    │
│  • Buttons: px-6 py-3 (24px/12px)       │
│  • Statistics: p-8 (32px)               │
└─────────────────────────────────────────┘
```

---

## 🎨 Typography Scale

```
┌─────────────────────────────────────────────────────┐
│  TEXT HIERARCHY                                     │
│  ─────────────────────────────────────────────────  │
│                                                      │
│  H1 - Page Title                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  POS Table Management                               │
│  • Size: 3xl (1.875rem)                            │
│  • Weight: Bold (700)                              │
│  • Tracking: Tight                                 │
│                                                      │
│  H2 - Section Title                                 │
│  ─────────────────────────────────────────────────  │
│  A/C Section                                        │
│  • Size: xl (1.25rem)                              │
│  • Weight: Bold (700)                              │
│                                                      │
│  H3 - Statistics Title                              │
│  ─────────────────────────────────────────────────  │
│  Live Statistics Dashboard                          │
│  • Size: 2xl (1.5rem)                              │
│  • Weight: Bold (700)                              │
│                                                      │
│  H4 - Numbers                                       │
│  ─────────────────────────────────────────────────  │
│  25                                                 │
│  • Size: 4xl (2.25rem)                             │
│  • Weight: Black (900)                             │
│  • Tracking: Tight                                 │
│                                                      │
│  Body - Labels                                      │
│  ─────────────────────────────────────────────────  │
│  AVAILABLE TABLES                                   │
│  • Size: sm (0.875rem)                             │
│  • Weight: Semibold (600)                          │
│  • Transform: Uppercase                            │
│  • Tracking: Wide                                  │
│                                                      │
│  Small - Subtitles                                  │
│  ─────────────────────────────────────────────────  │
│  Ready for customers                                │
│  • Size: xs (0.75rem)                              │
│  • Weight: Regular (400)                           │
│  • Color: Gray-500                                 │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Interactive States

### Button States

```
┌──────────────────────────────────────────────────────┐
│  BUTTON STATE TRANSITIONS                            │
│  ──────────────────────────────────────────────────  │
│                                                       │
│  DEFAULT STATE:                                      │
│  ┌─────────────────┐                                │
│  │  Reserve Table  │  ← Gradient background         │
│  └─────────────────┘     Shadow-lg                  │
│                                                       │
│  HOVER STATE:                                        │
│  ┌─────────────────┐                                │
│  │  Reserve Table  │  ← Darker gradient             │
│  └─────────────────┘     Shadow-xl                  │
│         ↑                 Lift 2px                   │
│                                                       │
│  ACTIVE STATE:                                       │
│  ┌─────────────────┐                                │
│  │  Reserve Table  │  ← Even darker                 │
│  └─────────────────┘     Scale 0.98                 │
│                                                       │
│  DISABLED STATE:                                     │
│  ┌─────────────────┐                                │
│  │  Reserve Table  │  ← Gray background             │
│  └─────────────────┘     Opacity 50%                │
│                           Cursor not-allowed        │
└──────────────────────────────────────────────────────┘
```

### Table Card States

```
┌──────────────────────────────────────────────────────┐
│  TABLE INTERACTION STATES                            │
│  ──────────────────────────────────────────────────  │
│                                                       │
│  DEFAULT:        HOVER:         ACTIVE:              │
│  ┌────┐         ┌────┐         ┌────┐              │
│  │ 1  │    →    │ 1  │    →    │ 1  │              │
│  └────┘         └────┘         └────┘              │
│  Normal          Lift+Scale     Press down          │
│  Border-gray     Border-indigo  Scale 0.95          │
│                  Shadow-lg                           │
│                                                       │
│  POPUP SHOWN (On Hover):                            │
│  ┌──────────────────┐                               │
│  │ Table 1 - John   │  ← Popup appears              │
│  │ Items: 3 | ₹450  │     Above table               │
│  └──────────────────┘     Fade in 300ms            │
│         ↓                                            │
│       ┌────┐                                        │
│       │ 1  │                                        │
│       └────┘                                        │
└──────────────────────────────────────────────────────┘
```

---

## 🎪 Visual Effects Catalog

### Gradients Used

```
1. HEADER GRADIENT:
   ┌─────────────────────────────────┐
   │ ████████████████████████████████ │
   │ Indigo-600 → Purple-600 → Pink  │
   └─────────────────────────────────┘

2. SECTION GRADIENTS:
   A/C:      ████████ (White → Blue-50)
   Non A/C:  ████████ (White → Orange-50)
   Bar:      ████████ (White → Purple-50)

3. BUTTON GRADIENTS:
   Reserve:  ████████ (Orange → Red)
   QR Menu:  ████████ (Green → Emerald)
   Move KOT: ████████ (Gray → Dark Gray)

4. ICON GRADIENTS:
   Available: ████████ (Green-400 → Emerald-500)
   Occupied:  ████████ (Blue-400 → Indigo-500)
   KOT:       ████████ (Yellow-400 → Orange-500)
   Revenue:   ████████ (Purple-400 → Pink-500)
```

### Shadow Levels

```
┌─────────────────────────────────────────┐
│  SHADOW HIERARCHY                       │
│  ─────────────────────────────────────  │
│                                          │
│  sm:  Subtle depth                      │
│  ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔  │
│  ┌──────┐                               │
│  │      │  0 1px 2px rgba(0,0,0,0.05)  │
│  └──────┘                               │
│                                          │
│  lg:  Moderate elevation                │
│  ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔  │
│  ┌──────┐                               │
│  │      │  0 10px 15px rgba(0,0,0,0.1) │
│  └──────┘                               │
│                                          │
│  xl:  High elevation                    │
│  ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔  │
│  ┌──────┐                               │
│  │      │  0 20px 25px rgba(0,0,0,0.1) │
│  └──────┘                               │
│                                          │
│  2xl: Maximum elevation                 │
│  ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔  │
│  ┌──────┐                               │
│  │      │  0 25px 50px rgba(0,0,0,0.25)│
│  └──────┘                               │
└─────────────────────────────────────────┘
```

---

## ✅ Design Checklist

### Visual Consistency
- [x] Consistent color palette throughout
- [x] Uniform border radius (xl/2xl/3xl)
- [x] Consistent spacing (gap-2/3/4/6/8)
- [x] Matching gradient directions
- [x] Unified shadow levels

### Interactive Feedback
- [x] Hover states on all clickable elements
- [x] Active states for buttons
- [x] Smooth transitions (300ms)
- [x] Visual feedback on interactions
- [x] Cursor changes appropriately

### Accessibility
- [x] Sufficient color contrast
- [x] Readable font sizes
- [x] Clear visual hierarchy
- [x] Descriptive labels
- [x] Icon + text combinations

### Responsiveness
- [x] Mobile layout (< 768px)
- [x] Tablet layout (768-1024px)
- [x] Desktop layout (> 1024px)
- [x] Flexible grids
- [x] Scalable components

---

**Design System Version:** 2.0  
**Last Updated:** December 6, 2024  
**Status:** ✅ Production Ready
