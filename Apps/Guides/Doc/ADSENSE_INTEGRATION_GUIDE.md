# Google AdSense Integration Guide

This document provides a comprehensive guide to the Google AdSense integration implemented in the TravelGuide project.

## Overview

Google AdSense has been integrated into the TravelGuide website to enable monetization through display advertising. The implementation follows best practices for Django projects and is designed to be:

- **Flexible**: Ad units can be easily added, removed, or modified
- **Configurable**: Settings are managed through environment variables
- **Optimized**: Responsive ad formats adapt to different screen sizes
- **Transparent**: Clear labeling of advertisements for better user experience
- **Maintainable**: Well-documented code with clear structure

## Configuration Settings

AdSense settings are defined in `guides/settings.py`. The following settings are available:

```python
# Google AdSense Configuration
# ---------------------------
# Publisher ID for Google AdSense (replace with your actual AdSense Publisher ID)
GOOGLE_ADSENSE_PUBLISHER_ID = os.environ.get('GOOGLE_ADSENSE_PUBLISHER_ID', 'ca-pub-xxxxxxxxxxxxxxxx')

# Enable or disable AdSense globally
ADSENSE_ENABLED = os.environ.get('ADSENSE_ENABLED', 'True').lower() == 'true'

# Ad slot IDs for different positions (replace with your actual ad unit IDs)
GOOGLE_ADSENSE_SLOTS = {
    'header': os.environ.get('ADSENSE_HEADER_SLOT', 'xxxxxxxxxx'),
    'sidebar': os.environ.get('ADSENSE_SIDEBAR_SLOT', 'xxxxxxxxxx'),
    'footer': os.environ.get('ADSENSE_FOOTER_SLOT', 'xxxxxxxxxx'),
    'in_article': os.environ.get('ADSENSE_IN_ARTICLE_SLOT', 'xxxxxxxxxx'),
}
```

### Environment Variables

For production, you should set these variables in your environment:

```
GOOGLE_ADSENSE_PUBLISHER_ID=ca-pub-YOUR_ACTUAL_PUBLISHER_ID
ADSENSE_ENABLED=True
ADSENSE_HEADER_SLOT=YOUR_HEADER_AD_SLOT_ID
ADSENSE_SIDEBAR_SLOT=YOUR_SIDEBAR_AD_SLOT_ID
ADSENSE_FOOTER_SLOT=YOUR_FOOTER_AD_SLOT_ID
ADSENSE_IN_ARTICLE_SLOT=YOUR_IN_ARTICLE_AD_SLOT_ID
```

## Context Processor

The AdSense settings are made available to all templates through a context processor defined in `core/context_processors.py`:

```python
def adsense_settings(request):
    """
    Add Google AdSense configuration to the template context.
    
    Makes AdSense publisher ID and ad slots available to all templates.
    This enables displaying ads in various template locations without
    repeating configuration in each view.
    """
    return {
        'ADSENSE_ENABLED': getattr(settings, 'ADSENSE_ENABLED', False),
        'GOOGLE_ADSENSE_PUBLISHER_ID': getattr(settings, 'GOOGLE_ADSENSE_PUBLISHER_ID', ''),
        'GOOGLE_ADSENSE_SLOTS': getattr(settings, 'GOOGLE_ADSENSE_SLOTS', {})
    }
```

The context processor is registered in `settings.py`:

```python
TEMPLATES = [
    {
        # ...
        'OPTIONS': {
            'context_processors': [
                # ...
                'core.context_processors.adsense_settings',  # AdSense context processor
            ],
        },
    },
]
```

## Ad Templates

### Base AdSense Template

The main AdSense template is located at `templates/includes/adsense.html`. This template handles displaying ads with different formats and in different positions:

```html
{% if ADSENSE_ENABLED and GOOGLE_ADSENSE_PUBLISHER_ID %}
    <!-- Google AdSense {{ ad_position|title }} Ad -->
    <div class="adsense-container {{ ad_position }}-ad {{ ad_class|default:'' }}">
        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{ GOOGLE_ADSENSE_PUBLISHER_ID }}"
            crossorigin="anonymous"></script>
        <!-- {{ ad_position|title }} Ad Unit -->
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="{{ GOOGLE_ADSENSE_PUBLISHER_ID }}"
             {% if ad_position == 'header' %}
                 data-ad-slot="{{ GOOGLE_ADSENSE_SLOTS.header }}"
             {% elif ad_position == 'sidebar' %}
                 data-ad-slot="{{ GOOGLE_ADSENSE_SLOTS.sidebar }}"
             {% elif ad_position == 'footer' %}
                 data-ad-slot="{{ GOOGLE_ADSENSE_SLOTS.footer }}"
             {% elif ad_position == 'in_article' %}
                 data-ad-slot="{{ GOOGLE_ADSENSE_SLOTS.in_article }}"
             {% endif %}
             data-ad-format="{{ ad_format|default:'auto' }}"
             data-full-width-responsive="true"></ins>
        <script>
            /* Display the ad after it's been created */
            (adsbygoogle = window.adsbygoogle || []).push({});
        </script>
    </div>
{% endif %}
```

### Specialized Ad Templates

For convenience, specialized templates have been created for specific ad positions:

#### In-Article Ad (`templates/includes/in_article_ad.html`):
```html
{% if ADSENSE_ENABLED and GOOGLE_ADSENSE_PUBLISHER_ID %}
<div class="in-article-ad-wrapper my-6 {{ custom_class|default:'' }}">
    <div class="text-xs text-gray-400 text-center mb-1">Advertisement</div>
    {% include 'includes/adsense.html' with ad_position='in_article' ad_format='responsive' ad_class='in-article-ad' %}
</div>
{% endif %}
```

#### Sidebar Ad (`templates/includes/sidebar_ad.html`):
```html
{% if ADSENSE_ENABLED and GOOGLE_ADSENSE_PUBLISHER_ID %}
<div class="sidebar-ad-wrapper my-4 {{ custom_class|default:'' }}">
    <div class="text-xs text-gray-400 text-center mb-1">Advertisement</div>
    {% include 'includes/adsense.html' with ad_position='sidebar' ad_format='vertical' ad_class='sidebar-ad' %}
</div>
{% endif %}
```

## Ad Placement in Base Template

The base template (`templates/base.html`) includes:

1. **AdSense Initialization Script** in the head section:
```html
<!-- Google AdSense initialization script (automatically loads if AdSense is enabled) -->
{% if ADSENSE_ENABLED and GOOGLE_ADSENSE_PUBLISHER_ID %}
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{ GOOGLE_ADSENSE_PUBLISHER_ID }}"
     crossorigin="anonymous"></script>
{% endif %}
```

2. **Header Ad** below the navigation header:
```html
<!-- Header Ad placement - appears below navigation -->
{% if ADSENSE_ENABLED %}
<div class="max-w-7xl mx-auto px-4 py-4 mt-16">
    {% include 'includes/adsense.html' with ad_position='header' ad_format='responsive' ad_class='mb-4 bg-gray-50 rounded-md p-1' %}
</div>
{% endif %}
```

3. **Footer Ad** above the site footer:
```html
<!-- Footer Ad placement - appears above the footer -->
{% if ADSENSE_ENABLED %}
<div class="max-w-7xl mx-auto px-4 py-4">
    {% include 'includes/adsense.html' with ad_position='footer' ad_format='responsive' ad_class='mb-4 bg-gray-50 rounded-md p-1' %}
</div>
{% endif %}
```

## CSS Styling

The base template includes CSS styling for AdSense containers to ensure consistent appearance and responsiveness:

```css
/* Styles for Google AdSense containers to ensure proper display and responsiveness */
.adsense-container {
    margin: 1rem 0;
    overflow: hidden;
    text-align: center;
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 90px; /* Minimum height for ad containers */
}

/* Specific styles for different ad positions */
.header-ad {
    margin-top: 0.5rem;
    margin-bottom: 1rem;
    border-radius: 0.375rem;
}

.sidebar-ad {
    margin: 1rem 0;
    border-radius: 0.375rem;
}

.footer-ad {
    margin: 1rem auto;
    max-width: 728px;
    border-radius: 0.375rem;
}

.in-article-ad {
    margin: 2rem 0;
    padding: 1rem;
    background-color: rgba(243, 244, 246, 0.5);
    border-radius: 0.375rem;
    max-width: 100%;
    overflow: hidden;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .adsense-container {
        padding: 0.5rem;
    }
    
    .in-article-ad {
        margin: 1.5rem 0;
        padding: 0.75rem;
    }
}
```

## Usage Examples

### Adding an In-Article Ad

To include an ad within article content, use:

```html
{% include 'includes/in_article_ad.html' %}
```

### Adding a Sidebar Ad

For pages with sidebars:

```html
{% include 'includes/sidebar_ad.html' %}
```

### Custom Ad Implementation

For custom positions or formats:

```html
{% include 'includes/adsense.html' with ad_position='sidebar' ad_format='vertical' ad_class='custom-class' %}
```

## AdSense Policy Compliance

When using AdSense, ensure your implementation complies with Google's policies:

1. **Ad Placement**: Don't place ads too close together or use deceptive practices
2. **Content Guidelines**: Ensure site content complies with AdSense content policies
3. **User Experience**: Don't disrupt the user experience with too many ads
4. **Labeling**: Clearly label advertisements as shown in our templates

## Getting Started with AdSense

1. Sign up for Google AdSense at https://www.google.com/adsense/
2. Create ad units for each position (header, sidebar, footer, in-article)
3. Update your `.env` file with your publisher ID and ad unit IDs
4. Ensure `ADSENSE_ENABLED` is set to `True`

## Troubleshooting

### Ads Not Displaying
- Verify `ADSENSE_ENABLED` is `True`
- Check publisher ID and ad slot IDs are correctly set
- Ensure AdSense account is approved and active
- Check for JavaScript errors in browser console

### Low Ad Fill Rate
- Content quality affects ad display rates
- Increase site traffic for better fill rates
- Optimize ad placement for better viewability

## Support and Documentation

For more information about Google AdSense:
- [Google AdSense Help Center](https://support.google.com/adsense/)
- [AdSense Program Policies](https://support.google.com/adsense/answer/48182)
- [Ad Placement Policies](https://support.google.com/adsense/answer/1346295)
