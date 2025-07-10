# Google AdSense Integration Guide

This document explains how to set up and customize Google AdSense on the TravelGuide website.

## Overview

Google AdSense has been integrated into the TravelGuide website with the following components:

1. **Base Template Integration**: The main script and ad units are in `templates/base.html`
2. **Configuration File**: Ad settings are centralized in `static/js/ads-config.js`
3. **Ad Placements**: Currently implemented at the top of content and bottom of content

## Setup Instructions

### 1. Create a Google AdSense Account

If you don't already have one:
1. Go to [Google AdSense](https://www.google.com/adsense)
2. Sign up and verify your website ownership
3. Wait for Google's approval (typically takes 1-3 days)

### 2. Update Publisher ID

Once your account is approved:
1. Get your Publisher ID from your AdSense dashboard (format: `ca-pub-XXXXXXXXXXXXXXXX`)
2. Replace `YOUR_PUBLISHER_ID` in the following files:
   - `static/js/ads-config.js` (update the `ADSENSE_PUBLISHER_ID` constant)
   - `templates/base.html` (update the script tag's `client` parameter)

### 3. Create Ad Units

1. In your AdSense dashboard, go to "By ad unit" → "Create new ad unit"
2. Create separate ad units for different placements (e.g., top banner, bottom banner)
3. Get the ad slot IDs for each unit
4. Update the `AD_SLOTS` object in `static/js/ads-config.js`

## Customization Options

### Ad Placement

Currently, ads are placed at:
- Top of the page (below navigation)
- Bottom of the page (above footer)

To add more ad placements:

1. Insert a new ad container in the appropriate template:
```html
<div class="w-full flex justify-center bg-gray-100 rounded-lg p-2 shadow-sm overflow-hidden ad-container">
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="ca-pub-YOUR_PUBLISHER_ID"
         data-ad-slot="YOUR_NEW_AD_SLOT_ID"
         data-ad-format="auto"
         data-full-width-responsive="true"
         id="your-ad-id"></ins>
</div>
```

2. Add the new slot ID to the `AD_SLOTS` object in `ads-config.js`

### Ad Display Types

Google AdSense supports various ad formats:

- **Responsive Ads** (current implementation): Set with `data-ad-format="auto"` and `data-full-width-responsive="true"`
- **Fixed Size Ads**: Specify exact dimensions with inline CSS
- **In-article Ads**: Use `data-ad-format="fluid"` and `data-ad-layout="in-article"`

To change the format, modify the `ins` element's data attributes.

### Advanced Features

The implementation includes:

1. **Ad Blocker Detection**: Uses `checkAdBlocker()` in `ads-config.js` to display alternative content
2. **Lazy Loading**: Framework for loading additional ads as users scroll
3. **Responsive Behavior**: Adjusts ads based on screen size

## Troubleshooting

Common issues and solutions:

1. **Ads Not Showing**: 
   - Ensure your AdSense account is approved
   - Check browser console for errors
   - Wait 24-48 hours for Google's systems to start serving ads

2. **Policy Violations**: 
   - Review Google's AdSense program policies
   - Ensure your content complies with Google's guidelines

3. **Performance Issues**:
   - If ads slow down your site, consider reducing the number of ad units
   - Implement lazy loading for ads below the fold

## Best Practices

1. **Balance**: Don't overload pages with too many ads (recommended: 3-4 maximum)
2. **Placement**: Position ads where they're visible but don't disrupt user experience
3. **Testing**: A/B test different ad placements to optimize performance
4. **Mobile**: Ensure ads display properly on mobile devices
5. **Loading**: Use the provided lazy-loading functionality for ads not in the viewport

## Compliance

Ensure your site complies with:
- Google AdSense Program Policies
- GDPR requirements (for European users)
- CCPA requirements (for California users)

Consider adding a cookie consent banner for compliance with privacy regulations.
