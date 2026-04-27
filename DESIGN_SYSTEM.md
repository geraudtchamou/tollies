# 🎨 Community Safety App - Design System

## Overview

This application features a modern, accessible design system combining **Neumorphism** and **Glassmorphism** design trends for an exceptional user experience.

---

## 🌈 Color Palette

### Primary Colors
- **Primary**: `#4f46e5` (Indigo)
- **Primary Light**: `#818cf8`
- **Primary Dark**: `#3730a3`

### Secondary Colors
- **Secondary**: `#ec4899` (Pink)
- **Secondary Light**: `#f472b6`
- **Accent**: `#06b6d4` (Cyan)
- **Accent Light**: `#67e8f9`

### Status Colors
- **Success**: `#10b981` (Green)
- **Warning**: `#f59e0b` (Amber)
- **Danger**: `#ef4444` (Red)

### Neumorphism Base
- **Background**: `#e0e5ec`
- **Text Main**: `#2d3748`
- **Text Secondary**: `#4a5568`
- **Text Light**: `#718096`

---

## ✨ Design Effects

### Neumorphism
Soft, extruded plastic look created using light and shadow:

```css
.neu-flat {
  background: #e0e5ec;
  box-shadow: 
    -8px -8px 20px rgba(255, 255, 255, 0.7),
    8px 8px 20px rgba(166, 171, 189, 0.35);
}

.neu-pressed {
  box-shadow: 
    inset 6px 6px 12px rgba(166, 171, 189, 0.25),
    inset -6px -6px 12px rgba(255, 255, 255, 0.9);
}
```

### Glassmorphism
Frosted glass effect with backdrop blur:

```css
.glass-panel {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.2);
}
```

---

## 🎬 Animations

### Available Animations

| Animation | Description | Duration |
|-----------|-------------|----------|
| `animate-float` | Gentle floating motion | 6s infinite |
| `animate-pulse-red` | Red alert pulse | 2s infinite |
| `animate-pulse-green` | Success pulse | 2s infinite |
| `animate-slide-up` | Slide from bottom | 0.6s |
| `animate-scale-in` | Scale up entrance | 0.5s |
| `animate-shake` | Error shake | 0.5s |
| `animate-shimmer` | Loading shimmer | 2s infinite |

### Usage Example

```jsx
<div className="animate-slide-up">
  Content slides in from bottom
</div>

<button className="neu-btn animate-pulse-green">
  Active Button
</button>
```

---

## 🧩 UI Components

### NeuButton
```jsx
import { NeuButton } from './components/UIComponents';

<NeuButton 
  variant="primary" 
  size="large" 
  icon="🚀"
  loading={false}
  onClick={handleClick}
>
  Submit
</NeuButton>
```

**Variants**: `primary`, `secondary`, `success`, `danger`  
**Sizes**: `small`, `medium`, `large`

### NeuCard
```jsx
import { NeuCard } from './components/UIComponents';

<NeuCard hoverable onClick={handleClick}>
  Card content here
</NeuCard>
```

### NeuInput
```jsx
import { NeuInput } from './components/UIComponents';

<NeuInput 
  type="email" 
  placeholder="Enter email" 
  icon="📧"
  value={email}
  onChange={handleChange}
/>
```

### GlassPanel
```jsx
import { GlassPanel } from './components/UIComponents';

<GlassPanel>
  Frosted glass content
</GlassPanel>
```

### Badge
```jsx
import { Badge } from './components/UIComponents';

<Badge variant="success">✓ Verified</Badge>
```

### StatusIndicator
```jsx
import { StatusIndicator } from './components/UIComponents';

<StatusIndicator status="validated" size="large" />
```

---

## 📐 Typography

### Font Family
```css
font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### Font Sizes
- **XS**: `0.75rem` (12px)
- **SM**: `0.875rem` (14px)
- **Base**: `1rem` (16px)
- **LG**: `1.125rem` (18px)
- **XL**: `1.25rem` (20px)
- **2XL**: `1.5rem` (24px)
- **3XL**: `1.875rem` (30px)
- **4XL**: `2.25rem` (36px)

---

## 📏 Spacing System

| Token | Value | Pixels |
|-------|-------|--------|
| `--spacing-xs` | 0.25rem | 4px |
| `--spacing-sm` | 0.5rem | 8px |
| `--spacing-md` | 1rem | 16px |
| `--spacing-lg` | 1.5rem | 24px |
| `--spacing-xl` | 2rem | 32px |
| `--spacing-2xl` | 3rem | 48px |

---

## 🔘 Border Radius

- **SM**: `8px`
- **MD**: `12px`
- **LG**: `16px`
- **XL**: `20px`
- **Full**: `9999px` (circular)

---

## ♿ Accessibility Features

### Reduced Motion
Respects user's motion preferences:
```css
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; }
}
```

### Focus States
Clear focus indicators for keyboard navigation:
```css
button:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
```

### High Contrast Mode
Enhanced shadows for high contrast preference:
```css
@media (prefers-contrast: high) {
  :root {
    --shadow-light: -2px -2px 8px rgba(255, 255, 255, 0.9);
    --shadow-dark: 2px 2px 8px rgba(0, 0, 0, 0.5);
  }
}
```

---

## 🎯 Best Practices

1. **Consistency**: Use utility classes instead of inline styles when possible
2. **Performance**: Leverage CSS transitions over JavaScript animations
3. **Accessibility**: Always include proper ARIA labels and focus states
4. **Responsiveness**: Test designs on multiple screen sizes
5. **Motion**: Provide alternatives for users who prefer reduced motion

---

## 🚀 Quick Start

Import the design system in your main CSS file:
```css
@import './styles/index.css';
```

Use components in React:
```jsx
import { NeuButton, NeuCard, NeuInput } from './components/UIComponents';

function MyComponent() {
  return (
    <NeuCard>
      <h1>Welcome</h1>
      <NeuInput placeholder="Enter text" icon="✏️" />
      <NeuButton variant="primary" icon="✨">
        Get Started
      </NeuButton>
    </NeuCard>
  );
}
```

---

## 📱 Responsive Design

All components are mobile-first and responsive:
```jsx
// Automatically adjusts on mobile
<NeuCard className="responsive-card">
  Content adapts to screen size
</NeuCard>
```

---

## 🎨 Theme Customization

Override CSS variables in your component:
```jsx
<div style={{ '--primary': '#your-color' }}>
  Themed content
</div>
```

---

**Built with ❤️ for the Community Safety App**
