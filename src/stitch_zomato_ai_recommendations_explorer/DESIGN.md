---
name: Culinary Discovery System
colors:
  surface: '#f9f9f9'
  surface-dim: '#dadada'
  surface-bright: '#f9f9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3f3'
  surface-container: '#eeeeee'
  surface-container-high: '#e8e8e8'
  surface-container-highest: '#e2e2e2'
  on-surface: '#1a1c1c'
  on-surface-variant: '#5b403f'
  inverse-surface: '#2f3131'
  inverse-on-surface: '#f1f1f1'
  outline: '#8f6f6e'
  outline-variant: '#e4bebc'
  surface-tint: '#bb162c'
  primary: '#b7122a'
  on-primary: '#ffffff'
  primary-container: '#db313f'
  on-primary-container: '#fffbff'
  inverse-primary: '#ffb3b1'
  secondary: '#5f5e5e'
  on-secondary: '#ffffff'
  secondary-container: '#e2dfde'
  on-secondary-container: '#636262'
  tertiary: '#006762'
  on-tertiary: '#ffffff'
  tertiary-container: '#00837c'
  on-tertiary-container: '#f3fffd'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b1'
  on-primary-fixed: '#410007'
  on-primary-fixed-variant: '#92001c'
  secondary-fixed: '#e5e2e1'
  secondary-fixed-dim: '#c8c6c5'
  on-secondary-fixed: '#1b1b1b'
  on-secondary-fixed-variant: '#474746'
  tertiary-fixed: '#8ef4eb'
  tertiary-fixed-dim: '#71d7cf'
  on-tertiary-fixed: '#00201e'
  on-tertiary-fixed-variant: '#00504c'
  background: '#f9f9f9'
  on-background: '#1a1c1c'
  surface-variant: '#e2e2e2'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1200px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 32px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

This design system is built for a premium yet accessible restaurant discovery experience. The personality is vibrant, appetizing, and highly organized, focusing on high-quality food photography and clear utility. 

The style utilizes a **Corporate Modern** approach with a focus on high-clarity information architecture. It balances the energy of a "Warm Red" primary brand color with the stability of a clean, structured interface. The emotional goal is to evoke hunger and excitement while maintaining a sense of reliability and ease of use, ensuring the user feels confident in their dining choices.

## Colors

The palette is anchored by a flagship **Warm Red**, used strategically for primary actions, branding, and highlighting essential restaurant metrics (like ratings or "open" status). 

- **Primary (#E23744):** Reserved for high-priority CTAs and brand identifiers.
- **Secondary/Text (#1C1C1C):** Used for headlines and primary body copy to ensure WCAG AA compliance against white backgrounds.
- **Surface (#F8F8F8):** Used for subtle panel backgrounds to separate content sections without adding visual weight.
- **Success/Rating:** Use a deep green (#24963F) for positive ratings to provide clear semantic contrast against the red brand color.

## Typography

The system uses **Inter** exclusively to maintain a functional, systematic, and modern aesthetic. The scale prioritizes legibility in data-dense environments (like menu lists and search results). 

Headlines use tighter letter-spacing and heavier weights to create a strong visual anchor. Body text uses standard tracking to ensure maximum readability during long-form review reading. Special attention is paid to `label` styles, which are used for secondary metadata like "Cuisine Type" or "Price Range."

## Layout & Spacing

The design system employs a **Fluid Grid** with a 12-column structure for desktop and a 4-column structure for mobile. 

The rhythm is governed by an 8px baseline grid. Content containers utilize generous internal padding (24px to 32px) to prevent the UI from feeling cluttered, which is a common risk in information-heavy discovery apps. 
- **Desktop:** 32px outer margins with a 24px gutter between cards.
- **Mobile:** 16px outer margins. Vertical spacing between restaurant cards should be a consistent 24px to provide clear breathing room.

## Elevation & Depth

Visual hierarchy is established using **Ambient Shadows** and **Tonal Layers**. 

1. **Base:** The primary page background is pure white (#FFFFFF).
2. **Surface:** Secondary content areas (like filters or sidebars) use the light gray neutral (#F8F8F8) without shadows to suggest a recessed or background position.
3. **Elevated (Cards):** Restaurant cards and search bars use a soft, diffused shadow: `box-shadow: 0px 4px 12px rgba(28, 28, 28, 0.08)`. This makes the interactive elements feel tactile and tappable.
4. **Floating:** Overlays, such as modals or "Sort/Filter" buttons on mobile, use a more pronounced shadow to indicate they are at the highest Z-index.

## Shapes

The shape language is **Rounded**, reflecting a friendly and modern consumer brand. 

- **Standard Cards:** 0.5rem (8px) corner radius provides a polished, professional look.
- **Interactive Elements:** Buttons and Input fields follow the 0.5rem standard.
- **High-Emphasis Shapes:** Search bars and specific "Category" chips use a `rounded-xl` or pill-shape to distinguish them from structural content cards.
- **Images:** All restaurant thumbnails and gallery images must inherit the 8px corner radius to maintain the soft visual rhythm.

## Components

### Buttons
- **Primary:** Warm Red background with White text. Bold weight.
- **Secondary:** White background with Warm Red border and text. 
- **Ghost:** Transparent background with Dark Text (#1C1C1C) for low-priority actions.

### Cards
- **Restaurant Card:** White background, 8px border radius, subtle ambient shadow. Images should occupy the top half of the card. Text content should have 16px-20px of internal padding.

### Chips & Tags
- **Cuisine Tags:** Light gray background (#F8F8F8) with dark text. 
- **Status Tags:** Use Primary Red for "Promoted" and Green for "High Rating."

### Input Fields
- White background with a 1px border (#E8E8E8). On focus, the border shifts to the Primary Red color.

### Lists
- Menu items should use thin horizontal dividers (#E8E8E8) with generous 16px vertical padding between items to ensure easy scanning on mobile devices.

### Rating Badges
- A distinctive component featuring a Green background (#24963F) with White bold text and a star icon, usually placed in the top right of cards or next to the restaurant name.