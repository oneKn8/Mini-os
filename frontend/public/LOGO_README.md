# Logo Assets

This directory contains the logo and icon assets for Personal Ops Center.

## Files

- **`logo.svg`** - Full logo with animated pulse effects (200x200px). Use for headers, splash screens, or marketing materials.
- **`logo-icon.svg`** - Simplified icon version (64x64px) with animation. Use for app icons, favicons, or compact spaces.
- **`favicon.svg`** - Minimal favicon (32x32px) optimized for browser tabs. Static version without animations.

## Usage

### In React Components

```tsx
import Logo from './components/Logo'

// Full logo with text
<Logo showText={true} size="lg" />

// Icon only
<Logo showText={false} size="md" />
```

### Direct Image Reference

In Vite, public assets are referenced with absolute paths:

```tsx
<img src="/logo.svg" alt="Ops Center Logo" />
<img src="/logo-icon.svg" alt="Ops Center Icon" />
```

## Design

The logo features:
- **Activity icon** - Represents system monitoring and operations
- **Gradient colors** - Blue to purple (#4c6ef5 to #845ef7) matching the app theme
- **Pulse animations** - Animated rings and bars for a dynamic, tech-forward feel
- **Glass morphism** - Designed to work with the app's glass-panel aesthetic

## Converting to PNG (Optional)

If you need PNG versions for specific use cases (e.g., app stores), you can convert the SVG files:

```bash
# Using ImageMagick
convert -background none -density 300 logo.svg logo.png

# Using Inkscape
inkscape logo.svg --export-filename=logo.png --export-width=512
```

Recommended PNG sizes:
- App icon: 512x512, 256x256, 128x128, 64x64, 32x32
- Logo: 1024x1024, 512x512, 256x256

