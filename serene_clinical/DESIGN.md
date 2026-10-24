---
name: Serene Clinical
colors:
  surface: '#f8f9ff'
  surface-dim: '#cddbf2'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d5e3fb'
  on-surface: '#0e1c2d'
  on-surface-variant: '#44474d'
  inverse-surface: '#243143'
  inverse-on-surface: '#eaf1ff'
  outline: '#74777e'
  outline-variant: '#c4c6ce'
  surface-tint: '#4c5f7c'
  primary: '#000207'
  on-primary: '#ffffff'
  primary-container: '#071d36'
  on-primary-container: '#7386a4'
  inverse-primary: '#b4c8e8'
  secondary: '#555f6b'
  on-secondary: '#ffffff'
  secondary-container: '#d9e3f1'
  on-secondary-container: '#5b6571'
  tertiary: '#090000'
  on-tertiary: '#ffffff'
  tertiary-container: '#430002'
  on-tertiary-container: '#f73b36'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d4e3ff'
  primary-fixed-dim: '#b4c8e8'
  on-primary-fixed: '#061c35'
  on-primary-fixed-variant: '#354863'
  secondary-fixed: '#d9e3f1'
  secondary-fixed-dim: '#bdc7d5'
  on-secondary-fixed: '#131c26'
  on-secondary-fixed-variant: '#3e4853'
  tertiary-fixed: '#ffdad6'
  tertiary-fixed-dim: '#ffb4ab'
  on-tertiary-fixed: '#410002'
  on-tertiary-fixed-variant: '#93000b'
  background: '#f8f9ff'
  on-background: '#0e1c2d'
  surface-variant: '#d5e3fb'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
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
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  metric-display:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.02em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-mobile: 0.75rem
  margin: 1.5rem
  margin-mobile: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system embodies a calm, authoritative, and deeply reassuring presence tailored for family caregiving and health management. It bridges high-end clinical precision with accessible domestic care, instilling immediate emotional calm, clarity, and trust in high-stakes health environments.

The visual style blends **Contemporary Minimalism** with **Tonal Glass and Soft Depth**. Surfaces are dominated by expansive off-white fields, crisp white content cards, sculpted deep navy anchor elements, and soft atmospheric ice-blue tints. Visual weight is established not through harsh outlines, but via delicate layer segregation, refined 24px corner radii, and hyper-diffused, cool-toned shadows.

## Colors

The palette establishes an immediate sensation of clinical composure, hygiene, and deliberate restraint:

- **Primary (`#071D36`)**: Deep navy anchor. Used for high-emphasis containers, hero schedule cards, primary pill actions, active navigational states, and bold typography.
- **Secondary (`#E4EEFC`)**: Soft, clinical powder blue. Serves as a soothing background tint for metric tiles, quick-access icon containers, subtle badges, and inactive structural indicators.
- **Tertiary (`#DC2626`)**: Critical alert crimson. Strictly isolated to emergency SOS triggers, acute health threshold warnings, and urgent clinical escalations. It must never appear as a routine decorative element.
- **Neutral (`#172536`)**: Dense charcoal-slate. Provides optimal contrast for long-form reading, primary clinical metrics, and contextual body copy, paired with `#F5F7FA` as the canvas foundation and pure white (`#FFFFFF`) for stacked surfaces.

## Typography

The typography couples the welcoming geometric balance of **Plus Jakarta Sans** for titles, numerical displays, and interactive controls with the systematic legibility of **Inter** for clinical data and body copy.

- **Legibility Standard**: Body typography stays generously scaled between 16px and 18px to facilitate effortless readability under stress or across intergenerational family caregiver devices.
- **Visual Cadence**: Headings deploy tight letter-spacing and heavy weights (600–700) to project definitive authority, while supporting subtexts use lighter slate values with relaxed line heights.

## Layout & Spacing

The layout employs a responsive, fluid grid that adapts dynamically while preserving clear negative space to diminish cognitive strain.

- **Mobile Viewports**: Relies on a single-column stacking structure with `1.25rem` outer canvas padding and `0.75rem` internal component gutters. Cards sit proud of the `#F5F7FA` surface with consistent `1.5rem` internal padding.
- **Tablet & Desktop**: Evolves into a multi-column fluid container system (8 columns for tablet, 12 columns for desktop) capped at a comfortable reading max-width of 1200px, flanked by `1.5rem` gutters.
- **Rhythm**: All vertical and horizontal separation operates on a strict 4px base rhythm, favoring larger increments (`1rem`, `1.5rem`, `2rem`) between distinct clinical widgets to prevent visual clutter.

## Elevation & Depth

Visual depth is achieved through layered tonal surfaces and whisper-soft ambient diffusion, avoiding harsh drop shadows or rigid black outlines:

- **Canvas Foundation**: Tinted pale grey-blue (`#F5F7FA`) acts as the base zero-plane.
- **Tier 1 (Surface Cards)**: Pristine `#FFFFFF` surfaces featuring a 1px border rendered in `rgba(7, 29, 54, 0.05)` and an ambient shadow: `0 8px 24px -4px rgba(7, 29, 54, 0.04), 0 2px 6px -1px rgba(7, 29, 54, 0.02)`.
- **Tier 2 (Hero Floating Cards & Modals)**: Deep navy `#071D36` containers or high-focus dialogs, cast with `0 16px 36px -6px rgba(7, 29, 54, 0.16)`.
- **Floating Controls & Bottom Navigation**: Elevated dock positioned above the canvas edge, utilizing high background opacity (95% white) paired with a 20px backdrop-filter blur and `0 12px 32px -4px rgba(7, 29, 54, 0.08)`.

## Shapes

The shape vocabulary prioritizes softness, safety, and high touchability:

- **Cards & Primary Modules**: Standardized on a generous 24px (`1.5rem`) corner radius. This curved silhouette eliminates visual sharpness and enhances the organic, comforting aesthetic.
- **Buttons & Control Pills**: Full pill geometry (`rounded-full`, 9999px) across primary CTAs, icon circular capsules, search bars, and floating docks.
- **Media & Embedded Imagery**: Medical equipment imagery, doctor portraits, and clinical facility showcases share the matching 20px–24px outer curvature or circular masks to integrate seamlessly with the surface architecture.

## Components

### Buttons & Action Controls
- **Primary Pill CTA**: Pill-shaped container (`border-radius: 9999px`) in solid `#071D36` with `#FFFFFF` label text. Includes a circular white trailing arrow disk (`#FFFFFF` with `#071D36` icon) offset inside the right boundary.
- **Emergency Action**: Saturated `#DC2626` background, pill-shaped, crisp `#FFFFFF` semi-bold text, paired with immediate tactile feedback.
- **Secondary / Ghost Actions**: Clean `#E4EEFC` background pill with `#071D36` text, or transparent with a fine 1px border of `rgba(7, 29, 54, 0.1)`.

### Cards & Metrics
- **Clinical Hero Tile**: Deep navy (`#071D36`) card featuring white primary typography, muted blue metadata, and integrated high-clarity diagnostic photography with subtle organic overlap.
- **Health Overview / Metrics Card**: Pure white background, 24px radius, subtle border. Splits vital metrics (Heart Rate, Blood Pressure, SpO2) into balanced vertical sections with small circular `#E4EEFC` icon backdrops.

### Quick Access Chips & Service Grids
- **Quick Access Circles**: Perfectly circular buttons (56px × 56px) clad in `#E4EEFC` with restrained 1.5px stroke outline icons in `#071D36`. Below sits a centered, two-line `label-sm` description.

### Input Fields & Search Bars
- **Search Pill**: Fully rounded pill input featuring a pure white background, subtle border, placeholder text in `#172536` at 40% opacity, and embedded circular trailing action button for filtering.

### Floating Bottom Navigation
- **Detached Navigation Capsule**: Floats 16px above the viewport base. Curved pill structure with pure white fill and frosted blur, framing minimalist stroke icons. Active state is encased in a compact `#071D36` pill pill with an icon in pure `#FFFFFF`.