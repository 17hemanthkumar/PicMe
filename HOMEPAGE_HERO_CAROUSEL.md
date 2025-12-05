# Homepage Hero Carousel Enhancement

## Overview
Replaced the static "Summer Beats" placeholder in the hero section with a dynamic carousel that displays real events from the database with smooth transition effects.

## Features Implemented

### 1. Dynamic Event Carousel
- **Auto-Rotating Slides**: Displays up to 5 most recent events
- **Smooth Transitions**: 1-second fade transition between slides
- **Auto-Play**: Changes slides every 5 seconds
- **Manual Navigation**: Click indicators to jump to specific events

### 2. Event Information Display
- **Event Name**: Prominently displayed
- **Category & Date**: Shows event type and formatted date
- **Photo Count**: Displays number of available photos
- **Call-to-Action**: "View Event" button links to event detail page

### 3. Visual Design
- **Full-Height Image**: Event image fills the carousel area
- **Gradient Overlay**: Dark gradient for text readability
- **Decorative Elements**: Colored circles for visual interest
- **Responsive**: Adapts to different screen sizes

### 4. Carousel Controls
- **Indicators**: Dots at bottom showing current slide
- **Active Indicator**: Elongated white dot for current slide
- **Inactive Indicators**: Semi-transparent dots for other slides
- **Click to Navigate**: Click any indicator to jump to that slide

## Technical Implementation

### Frontend Changes (`frontend/pages/homepage.html`)

#### HTML Structure:
```html
<div id="hero-carousel" class="relative rounded-xl overflow-hidden shadow-2xl h-96">
    <!-- Dynamic slides inserted here -->
</div>
<div id="carousel-indicators" class="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2 z-10">
    <!-- Dynamic indicators inserted here -->
</div>
```

#### JavaScript Functionality:

**State Management**:
- `heroEvents`: Array of events to display
- `currentSlide`: Index of currently visible slide
- `carouselInterval`: Timer for auto-rotation

**Key Functions**:

1. **`initHeroCarousel(events)`**:
   - Takes events array from API
   - Selects 5 most recent events
   - Generates HTML for slides and indicators
   - Starts auto-rotation if multiple events exist

2. **`goToSlide(index)`**:
   - Hides current slide with fade-out
   - Shows target slide with fade-in
   - Updates indicator states
   - Resets auto-rotation timer

3. **`startCarousel()`**:
   - Sets interval to change slides every 5 seconds
   - Automatically loops back to first slide

**Slide HTML Template**:
```html
<div class="carousel-slide absolute inset-0 transition-opacity duration-1000">
    <img src="[event.image]" class="w-full h-full object-cover">
    <div class="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent"></div>
    <div class="absolute bottom-0 left-0 p-6 text-white">
        <p class="text-sm">[category] • [date]</p>
        <h3 class="text-2xl font-bold">[event name]</h3>
        <p class="text-sm">[photo count] photos available</p>
        <a href="/event_detail?event_id=[id]">View Event →</a>
    </div>
</div>
```

**Indicator HTML Template**:
```html
<button class="carousel-indicator w-2 h-2 rounded-full transition-all duration-300" 
        onclick="goToSlide([index])"></button>
```

### CSS Classes Used:

**Transitions**:
- `transition-opacity duration-1000`: Smooth 1-second fade
- `transition-all duration-300`: Smooth indicator animations

**Opacity States**:
- `opacity-100`: Visible slide
- `opacity-0`: Hidden slide

**Indicator States**:
- Active: `bg-white w-8` (white, elongated)
- Inactive: `bg-white/50` (semi-transparent, small)

## User Experience Flow

1. **Page Load**: 
   - Fetches events from `/events` API
   - Displays loading message while fetching
   - Initializes carousel with recent events

2. **Auto-Play**:
   - First event shown immediately
   - After 5 seconds, fades to next event
   - Continues rotating through all events
   - Loops back to first event

3. **Manual Navigation**:
   - User clicks indicator dot
   - Carousel immediately transitions to that event
   - Auto-play timer resets
   - Continues auto-playing from new position

4. **Interaction**:
   - User can click "View Event" button on any slide
   - Navigates to event detail page
   - Can browse event photos and scan face

## Fallback Scenarios

### No Events Available:
```html
<div class="bg-gradient-to-br from-indigo-500 to-purple-600">
    <h3>No Events Yet</h3>
    <p>Check back soon for upcoming events!</p>
</div>
```

### API Error:
```html
<div class="bg-gray-200">
    <p>Failed to load events</p>
</div>
```

### Single Event:
- Shows event without indicators
- No auto-rotation
- Static display

### Image Load Error:
- Falls back to default Unsplash concert image
- Uses `onerror` attribute on img tags

## Performance Considerations

### Optimization:
- Only loads 5 most recent events (not all events)
- Uses CSS transitions (GPU-accelerated)
- Lazy loading for images with `loading="lazy"` attribute
- Clears and resets interval on manual navigation

### Memory Management:
- Single interval timer (cleared and recreated as needed)
- No memory leaks from event listeners
- Efficient DOM manipulation

## Customization Options

### Timing:
```javascript
// Change slide duration (currently 5000ms = 5 seconds)
carouselInterval = setInterval(() => {
    // ...
}, 5000);
```

### Number of Events:
```javascript
// Change number of events shown (currently 5)
heroEvents = events.slice(-5).reverse();
```

### Transition Speed:
```html
<!-- Change transition duration (currently 1000ms = 1 second) -->
<div class="transition-opacity duration-1000">
```

## Browser Compatibility

- **Modern Browsers**: Full support (Chrome, Firefox, Safari, Edge)
- **CSS Transitions**: Widely supported
- **JavaScript ES6**: Supported in all modern browsers
- **Fallback**: Graceful degradation to static display

## Testing Checklist

- [x] Carousel loads with real events from database
- [x] Slides transition smoothly with fade effect
- [x] Auto-rotation works (5-second intervals)
- [x] Manual navigation via indicators works
- [x] Active indicator highlights correctly
- [x] "View Event" button links to correct event
- [x] Event information displays correctly
- [x] Image fallback works for missing images
- [x] Handles empty events array gracefully
- [x] Handles API errors gracefully
- [x] Single event displays without indicators
- [x] Responsive design works on mobile
- [x] No console errors
- [x] Memory leaks prevented

## Future Enhancements

Potential improvements:
- Add prev/next arrow buttons
- Pause on hover
- Swipe gestures for mobile
- Keyboard navigation (arrow keys)
- Preload next image for smoother transitions
- Add animation effects (slide, zoom, etc.)
- Show multiple slides at once on large screens

## Files Modified

1. **frontend/pages/homepage.html**
   - Replaced static hero image with dynamic carousel
   - Added carousel container and indicators
   - Implemented JavaScript carousel logic
   - Added auto-rotation and manual navigation

## Dependencies

- No additional dependencies required
- Uses existing Tailwind CSS classes
- Pure JavaScript (no jQuery or frameworks)
- Existing `/events` API endpoint

## Notes

- Carousel automatically adapts to number of available events
- Maintains existing page layout and styling
- Fully responsive and mobile-friendly
- Accessible with keyboard navigation (via indicator buttons)
- SEO-friendly with proper alt tags and semantic HTML
