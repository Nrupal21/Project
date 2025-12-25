# Design Tokens - Airbnb-Inspired UI System

## Color Palette
### Primary Colors
- **Rose-500**: `#f43f5e` - Primary buttons, links, accents
- **Rose-600**: `#e11d48` - Primary hover states

### Neutral Colors
- **Gray-50**: `#f9fafb` - Light backgrounds, footer
- **Gray-100**: `#f3f4f6` - Secondary backgrounds
- **Gray-200**: `#e5e7eb` - Borders, dividers
- **Gray-300**: `#d1d5db` - Disabled states, light borders
- **Gray-500**: `#6b7280` - Secondary text
- **Gray-600**: `#4b5563` - Body text
- **Gray-700**: `#374151` - Emphasized text
- **Gray-900**: `#111827` - Headlines, primary text

### Status Colors
- **Green-600**: `#059669` - Success states, "Open" badges
- **Red-500**: `#ef4444` - Error states, "Closed" badges

## Typography
### Headlines
- **H1**: `text-4xl md:text-5xl font-semibold text-gray-900`
- **H2**: `text-2xl md:text-3xl font-semibold text-gray-900`
- **H3**: `text-xl font-semibold text-gray-900`
- **H4**: `text-lg font-semibold text-gray-900`

### Body Text
- **Large**: `text-lg text-gray-600`
- **Base**: `text-base text-gray-600`
- **Small**: `text-sm text-gray-600`
- **XSmall**: `text-xs text-gray-500`

### Labels
- **Form Labels**: `text-xs font-semibold text-gray-900`
- **Card Labels**: `text-sm font-medium text-gray-700`

## Spacing
### Container Padding
- **Mobile**: `px-6`
- **Desktop**: `lg:px-12`

### Component Spacing
- **Section Spacing**: `py-8 md:py-12`
- **Card Spacing**: `gap-6`
- **Element Spacing**: `space-y-4`, `space-y-6`
- **Button Spacing**: `space-x-2`

## Border Radius
### Buttons & Pills
- **Primary**: `rounded-full`

### Cards & Containers
- **Small**: `rounded-lg`
- **Medium**: `rounded-xl`
- **Large**: `rounded-2xl`

## Shadows
### Interactive Elements
- **Default**: `shadow-md`
- **Hover**: `shadow-lg`, `shadow-xl`
- **Subtle**: `shadow-sm`

## Transitions
### Standard
- **Colors**: `transition-colors duration-200`
- **Shadows**: `transition-shadow duration-300`
- **Transforms**: `transition-transform duration-300`

## Component Patterns

### Buttons
```html
<!-- Primary -->
<button class="bg-rose-500 hover:bg-rose-600 text-white px-6 py-3 rounded-full font-medium transition-colors duration-200">

<!-- Secondary -->
<button class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-3 rounded-full font-medium transition-colors duration-200">

<!-- Outline -->
<button class="border border-gray-300 hover:border-gray-900 text-gray-700 hover:text-gray-900 px-6 py-3 rounded-full font-medium transition-colors duration-200">

<!-- Ghost -->
<button class="hover:bg-gray-50 text-gray-700 px-6 py-3 rounded-full font-medium transition-colors duration-200">
```

### Cards
```html
<div class="bg-white rounded-xl shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden">
    <!-- Content -->
</div>
```

### Form Inputs
```html
<input class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent">
```

### Badges
```html
<span class="bg-rose-500 text-white px-3 py-1 rounded-full text-xs font-semibold">
    Badge Text
</span>
```

## Grid Systems
### Responsive Grids
- **Cards**: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`
- **Features**: `grid-cols-1 md:grid-cols-3`
- **Footer**: `grid-cols-1 md:grid-cols-4`

## Animation Classes
### Hover Effects
- **Scale**: `hover:scale-105`
- **Translate**: `hover:-translate-y-2`
- **Underline**: `group-hover:underline`

### Loading States
- **Spinner**: `spinner` (custom CSS)
- **Pulse**: `animate-pulse`
- **Skeleton**: `bg-gray-200 animate-pulse`

## Accessibility
### Focus States
- **Ring**: `focus:ring-2 focus:ring-rose-500`
- **Outline**: `focus:outline-none`
- **Contrast**: Ensure 4.5:1 ratio for text

### Screen Readers
- **Labels**: Use proper `<label>` tags
- **ARIA**: Add `aria-label` for icon-only buttons
- **Semantic**: Use proper heading hierarchy

## Mobile Considerations
### Responsive Breakpoints
- **Small**: `sm:` (640px+)
- **Medium**: `md:` (768px+)
- **Large**: `lg:` (1024px+)
- **Extra Large**: `xl:` (1280px+)

### Touch Targets
- **Minimum**: 44px × 44px
- **Buttons**: `px-6 py-3` minimum
- **Links**: Adequate spacing for touch

## Dark Mode (Future Enhancement)
### Color Mapping
- **Background**: `bg-gray-900`
- **Surface**: `bg-gray-800`
- **Text**: `text-gray-100`
- **Border**: `border-gray-700`

## Usage Guidelines
1. **Consistency**: Always use defined tokens, avoid arbitrary values
2. **Hierarchy**: Maintain clear visual hierarchy with typography scale
3. **Whitespace**: Use consistent spacing patterns
4. **Color**: Limit color usage, focus on gray scale with rose accents
5. **Interaction**: Ensure all interactive elements have hover/focus states
6. **Mobile**: Test all components on mobile first
