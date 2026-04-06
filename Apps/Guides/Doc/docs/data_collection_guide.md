# Guides Data Collection Guide

## Overview
This document provides guidelines for collecting, organizing, and maintaining high-quality data for the Guides travel management platform. The Data Finder role is responsible for creating a comprehensive database of destinations, tours, attractions, accommodations, and related travel information.

## Data Collection Priorities

### Phase 1 (July 15 - August 8): Destinations Database
1. **Top 20 global destinations** by tourism volume
2. **Top 5 destinations** in each major region (Europe, Asia, North America, South America, Africa, Oceania)
3. **Emerging destinations** with growing tourism interest

### Phase 2 (August 9 - August 22): Tours and Attractions
1. **Popular tours** for each Phase 1 destination
2. **Major attractions** within each destination
3. **Seasonal activities** relevant to each destination

### Phase 3 (August 23 - September 5): Transportation and Emergency Services
1. **Transportation options** between major destinations
2. **Local transportation** within destinations
3. **Emergency services** information for all destinations

### Phase 4 (September 6 - September 26): Data Verification and Enhancement
1. **Data verification** of all collected information
2. **Content enrichment** with additional details and media
3. **Data optimization** for search functionality

## Data Quality Standards

### Accuracy Requirements
- All factual information must be verified from at least two reliable sources
- Geographic coordinates must be accurate to within 100 meters
- Business information (hours, prices, etc.) should be current as of 2025
- Links to official websites must be verified as working

### Completeness Requirements
- No required fields should be left empty
- All destinations should have at least 3 high-quality photos
- All tours should have complete pricing and duration information
- All attractions should have accessibility information

### Consistency Requirements
- Use consistent naming conventions across all datasets
- Maintain consistent formatting for addresses, phone numbers, etc.
- Use standardized categories and tags
- Ensure consistent rating scales across reviews

## Data Collection Templates

### Destination Data Template
```
{
  "name": "[Official name of destination]",
  "local_name": "[Name in local language if different]",
  "slug": "[URL-friendly version of name]",
  "region": "[Region ID]",
  "country": "[Country name]",
  "continent": "[Continent name]",
  "coordinates": {
    "latitude": 00.000000,
    "longitude": 00.000000
  },
  "timezone": "[Timezone identifier, e.g., Europe/Paris]",
  "description": {
    "short": "[100-150 character summary]",
    "full": "[Comprehensive description, 500+ words]"
  },
  "climate": "[Description of climate and best times to visit]",
  "language": "[Primary language(s) spoken]",
  "currency": "[Local currency code and name]",
  "visa_requirements": "[Summary of visa requirements for major countries]",
  "safety_info": "[Safety information and travel advisories]",
  "photos": [
    {
      "url": "[URL to high-resolution image]",
      "alt": "[Descriptive alt text]",
      "credit": "[Photographer or source credit]",
      "primary": "[Boolean: true if main image]"
    }
    // Minimum 3 photos per destination
  ],
  "popular_activities": ["[List of popular activities]"],
  "best_seasons": ["[List of best seasons to visit]"]
}
```

### Attraction Data Template
```
{
  "name": "[Attraction name]",
  "destination_id": "[Related destination ID]",
  "slug": "[URL-friendly version of name]",
  "category": "[Museum, Monument, Natural Wonder, etc.]",
  "coordinates": {
    "latitude": 00.000000,
    "longitude": 00.000000
  },
  "description": "[Comprehensive description, 300+ words]",
  "hours_of_operation": {
    "monday": "[Opening hours or 'Closed']",
    "tuesday": "[Opening hours or 'Closed']",
    // etc. for all days
  },
  "admission_fees": {
    "adult": "[Price in local currency]",
    "child": "[Price in local currency]",
    "senior": "[Price in local currency]",
    "student": "[Price in local currency]"
  },
  "accessibility": "[Information about wheelchair access, etc.]",
  "contact_info": {
    "website": "[Official website URL]",
    "phone": "[Contact phone with country code]",
    "email": "[Contact email if available]"
  },
  "photos": [
    // Same structure as destination photos
    // Minimum 2 photos per attraction
  ],
  "tips": ["[Visitor tips and recommendations]"]
}
```

### Tour Package Data Template
```
{
  "name": "[Tour package name]",
  "tour_operator": "[Tour operator name]",
  "destination_ids": ["[List of destination IDs covered]"],
  "duration_days": [Number of days],
  "description": "[Comprehensive description, 300+ words]",
  "itinerary": [
    {
      "day": 1,
      "title": "[Day title]",
      "description": "[Day description]",
      "activities": ["[List of activities]"],
      "meals_included": ["breakfast", "lunch", "dinner"],
      "accommodation": "[Accommodation name or type]"
    }
    // One entry per day of tour
  ],
  "inclusions": ["[List of what's included]"],
  "exclusions": ["[List of what's not included]"],
  "price_range": {
    "currency": "[Currency code]",
    "min_price": [Minimum price],
    "max_price": [Maximum price]
  },
  "photos": [
    // Same structure as destination photos
  ],
  "departure_dates": ["[List of available departure dates]"]
}
```

## Data Collection Sources

### Recommended Primary Sources
1. **Official tourism websites** for countries and cities
2. **Official attraction websites** for hours, prices, and policies
3. **Government travel advisories** for safety information
4. **UNESCO World Heritage** for historical sites
5. **Reputable travel guides** (Lonely Planet, Fodor's, etc.)
6. **Weather services** for climate information
7. **Transportation providers** for routes and schedules

### Supplementary Sources
1. **Travel blogs** for personal experiences and tips
2. **Review platforms** for visitor feedback and ratings
3. **Social media** for current photos and trends
4. **Local news sources** for current events and cultural information

### Data Verification
- Cross-reference information between multiple sources
- Prioritize official sources over user-generated content
- Verify currency of information (check publication dates)
- Document sources for each piece of information

## Data Entry Process

### Step 1: Research and Collection
1. Identify the destination/attraction/tour to document
2. Gather information from recommended sources
3. Save temporary notes and reference links
4. Download high-quality images (with proper attribution)

### Step 2: Data Organization
1. Structure collected information according to data templates
2. Ensure all required fields have values
3. Format text consistently (grammar, style, terminology)
4. Optimize content for readability and SEO

### Step 3: Quality Check
1. Verify accuracy of factual information
2. Check completeness of all required fields
3. Review grammar and spelling
4. Ensure proper attribution for all media

### Step 4: Database Entry
1. Enter verified data into the database
2. Upload and link all media files
3. Set proper relationships between related entities
4. Document any special notes or considerations

### Step 5: Validation
1. Preview how the data appears in the application
2. Verify links and media display correctly
3. Test search functionality with the new data
4. Address any issues discovered during validation

## Media Guidelines

### Image Requirements
- **Minimum resolution**: 1920x1080 pixels
- **Preferred format**: JPEG for photos, PNG for graphics
- **Maximum file size**: 5MB per image
- **Orientation**: Landscape preferred for destination hero images
- **Quality**: Professional quality, well-lit, in focus

### Image Subjects
- Destination: Skyline/landmark, streets/culture, natural features
- Attractions: Exterior, interior, notable features
- Tours: Key activities, accommodations, transportation

### Attribution Requirements
- Photographer name or image source
- License information
- Purchase record if applicable
- Permission documentation for custom photography

## Data Maintenance

### Regular Updates
- **Attractions data**: Review every 3 months (operating hours, prices)
- **Tour packages**: Review monthly (availability, prices)
- **Emergency information**: Review monthly (contact numbers, procedures)
- **Seasonal information**: Review before each season change

### Update Process
1. Schedule regular review cycles for each data type
2. Document all changes made during updates
3. Maintain a changelog for significant information updates
4. Archive outdated information rather than deleting

## Data Security

### Personal Information Handling
- Never collect personally identifiable information from unauthorized sources
- Follow data protection regulations (GDPR, CCPA, etc.)
- Secure any credentials used to access official information sources

### Access Controls
- Use the project's secure storage for all collected data
- Never store project data on personal devices
- Report any potential data breaches immediately

## Reporting and Documentation

### Progress Reports
- Submit weekly progress reports on data collection activities
- Document challenges encountered and solutions implemented
- Track completion percentage against priority targets

### Documentation Requirements
- Maintain a data sources document with references
- Document any exceptions to the standard templates
- Keep notes on special handling required for specific destinations

## Conclusion
Following this guide will ensure high-quality, consistent data collection for the Guides platform. The Data Finder role is critical to the success of the project, as the quality and completeness of the travel information directly impacts user satisfaction and platform utility.
