# NetBox Dark Mode — Visual Patterns for Textual TUI

This document captures every color, layout, and visual pattern from NetBox's dark mode UI.
Use it as the authoritative reference when mapping NetBox's appearance to Textual CSS/TCSS.

---

## 1. Brand Color Palette

NetBox defines its own brand colors on top of Tabler (Bootstrap-based framework).

```scss
// Source: netbox/project-static/styles/_variables.scss

$rich-black:          #001423   // Primary dark bg — html, navbar, cards, table headers
$rich-black-light:    #081B2A   // Secondary dark bg — .page, active tab panels
$rich-black-lighter:  #0D202E   // Tertiary dark bg (available, less used in UI)
$rich-black-lightest: #1A2C39   // Quaternary dark bg (available, less used in UI)
$bright-teal:         #00F2D4   // PRIMARY ACCENT in dark mode — links, active nav, focus rings
$dark-teal:           #00857D   // Primary color in light mode (not used in dark)
```

### Textual TCSS mapping

```css
/* Textual near-equivalents */
$rich-black:          #001423;
$rich-black-light:    #081B2A;
$rich-black-lighter:  #0D202E;
$bright-teal:         #00F2D4;
```

---

## 2. Color Layer Hierarchy (Dark Mode)

From deepest background to foreground surfaces:

| Layer | Hex | Usage |
|-------|-----|-------|
| **Base** | `#001423` | `<html>`, navbar, page-header, cards, table headers |
| **Page** | `#081B2A` | `.page` content area, active tab panels |
| **Surface secondary** | `#1F2937` | Secondary surface (Tabler `--tblr-secondary-bg`) |
| **Surface tertiary** | `#18212F` | Card headers, tertiary bg (≈ `rgb(24,33,47)`) |
| **Body bg** | `#111827` | Tabler base (overridden to `#001423` by NetBox) |
| **Text** | `#E5E7EB` | Main body text (`--tblr-body-color`) |
| **Accent** | `#00F2D4` | Primary accent — links, active indicators, focus |

### Visual depth model

```
#001423  ← outermost (html bg, navbar, cards)
  #081B2A  ← page content background
    #18212F  ← card headers, nested surfaces
      #1F2937  ← secondary surfaces, dropdowns
```

---

## 3. Typography Colors

```
Main text:          #E5E7EB   (--tblr-body-color in dark)
Emphasis/headings:  #FFFFFF   (--tblr-emphasis-color)
Secondary text:     rgba(229,231,235, 0.75)   (~#E5E7EB at 75%)
Muted/tertiary:     rgba(229,231,235, 0.50)   (~#E5E7EB at 50%)
Secondary label:    #9CA3AF   (gray-400, used for .text-secondary)
Code text:          #D1D5DB   (gray-300)
Link color:         #00F2D4   (bright-teal, overrides Tabler computed value)
Link hover color:   #00F2D4   (same — no color change on hover, only decoration)
```

---

## 4. Gray Scale

Used throughout for borders, muted text, disabled states:

```
gray-100:  #F3F4F6   (lightest — borders in light mode)
gray-200:  #E5E7EB   (body text in dark mode)
gray-300:  #D1D5DB   (code text, subtle emphasis)
gray-400:  #9CA3AF   (secondary text, disabled row tint)
gray-500:  #6B7280   (muted, secondary color in light mode)
gray-600:  #4B5563
gray-700:  #374151   (light-border-subtle in dark)
gray-800:  #1F2937   (secondary bg in dark, light-bg-subtle)
gray-900:  #111827   (Tabler body-bg base)
```

---

## 5. Semantic Status Colors

### Base values (applied in both themes, dark mode uses lightened text variants)

| Status | Base Hex | Purpose |
|--------|----------|---------|
| **primary** | `#00F2D4` | (dark mode override to bright-teal) |
| **success** | `#2FB344` | Connected, OK, active |
| **info** | `#4299E1` | Informational, planned |
| **warning** | `#F59F00` | Warning, decommissioning |
| **danger** | `#D63939` | Error, failed, critical |
| **secondary** | `#9CA3AF` | Neutral, disabled |

### Dark mode text emphasis (lightened for readability on dark bg)

| Status | Text Color | Hex (approx) |
|--------|-----------|--------------|
| primary | `rgb(102, 181.8, 177)` → **overridden to `#00F2D4`** | `#00F2D4` |
| success | `rgb(130.2, 209.4, 142.8)` | `#82D18E` |
| info | `rgb(141.6, 193.8, 237)` | `#8DC1ED` |
| warning | `rgb(249, 197.4, 102)` | `#F9C566` |
| danger | `rgb(230.4, 136.2, 136.2)` | `#E68888` |
| secondary | `rgb(166.2, 170.4, 178.8)` | `#A6AAB2` |

### Dark mode subtle backgrounds (very dark tints for badges/alerts)

| Status | Approx Hex |
|--------|-----------|
| primary | `#001A19` |
| success | `#09230D` |
| info | `#0D1E2D` |
| warning | `#311F00` |
| danger | `#2B0B0B` |
| secondary | `#151720` |
| light | `#1F2937` |

### Dark mode subtle borders

| Status | Approx Hex |
|--------|-----------|
| primary | `#004F4B` |
| success | `#1C6B28` |
| info | `#275B87` |
| warning | `#935F00` |
| danger | `#802222` |
| secondary | `#40444C` |
| light | `#374151` |

---

## 6. Navigation Sidebar

```
Background gradient:
  linear-gradient(
    180deg,
    rgba(0, 242, 212, 0.00) 0%,    ← transparent bright-teal at top
    rgba(0, 242, 212, 0.10) 100%   ← 10% bright-teal at bottom
  ), #001423                        ← over rich-black base

Nav link icons:        #FFFFFF  (white)
Nav link titles:       #FFFFFF  (white)
Section headers:       #00F2D4  (bright-teal — .text-secondary override)
Active dropdown border:#00F2D4  (bright-teal — left border on active item)
Menu item hover bg:    rgba(255,255,255, ~0.06)   ≈ #FFFFFF0F
Menu item active bg:   rgba(255,255,255, ~0.06)   ≈ #FFFFFF0F
Dropdown link text:    #FFFFFF
Sidebar width:         18rem (288px)
```

### Textual TUI equivalent structure

```
Sidebar (Left panel, width: 18)
├── Background: $rich-black (#001423)
├── Teal gradient overlay at bottom (simulate with border/rule color)
├── App title / logo: bright-teal (#00F2D4)
├── Section headers: bright-teal (#00F2D4)
├── Nav items (default): white text, transparent bg
├── Nav item hover: white bg at ~6% opacity → dark hover highlight
└── Nav item active: left accent bar in bright-teal (#00F2D4)
```

---

## 7. Page Layout

```
Page header:     background #001423 (same as navbar)
Page body:       background #081B2A ($rich-black-light)
Active tab panel:background #081B2A ($rich-black-light)
Inactive tabs:   background transparent / surface-tertiary
```

---

## 8. Cards

```
Card background (dark mode): #001423 ($rich-black) — all cards
Card header background:      #18212F (surface-tertiary ≈ rgb(24,33,47))
Card header font-size:       h5 equivalent
Card padding:                0.75rem (header, body, footer)
Card bottom margin:          1rem
List-group item padding:     0.5rem 0.75rem
```

### Textual equivalent

```
ContentSwitcher / Static widget:
  background: #001423
  border: #2D3C51  (border-color in dark)
  padding: 1

  Header label:
    background: #18212F
    color: #E5E7EB
```

---

## 9. Tables

```
Table header background:  #001423 ($rich-black)
Table header font-size:   0.625rem (very small uppercase)
Table border color:       rgb(45.7, 60.45, 81.09)  ≈ #2D3C51
Table body background:    transparent (inherits page bg #081B2A)
Attr-table row borders:   dashed style
Last row border:          hidden
Table-primary rows:       rgba(secondary-rgb, 0.48)  ≈ #1F2937 at 48%
```

### Interface / cable status row tinting (15% opacity overlays)

| Status | Row Tint | Base Color |
|--------|----------|-----------|
| `connected` | green at 15% | `rgba(#2FB344, 0.15)` |
| `planned` | blue at 15% | `rgba(#4299E1, 0.15)` |
| `decommissioning` | yellow at 15% | `rgba(#F59F00, 0.15)` |
| `mark-connected` | success at 15% | `rgba(#2FB344, 0.15)` |
| `virtual` | primary/teal at 15% | `rgba(#00F2D4, 0.15)` |
| `disabled` | gray at 15% | `rgba(#9CA3AF, 0.15)` |

---

## 10. Borders

```
Default border:             rgb(45.7, 60.45, 81.09)  ≈ #2D3C51
Translucent border:         rgba(72, 110, 149, 0.14)  ≈ #486E95 at 14%
Light border subtle:        #374151  (gray-700)
Dark border subtle:         #1F2937  (gray-800)
Color label border:         #303030  (hardcoded in misc.scss)
Thumbnail border:           #606060  (hardcoded)
```

---

## 11. Buttons

```
Primary button text:        #001423  (rich-black on bright-teal bg)
Primary button bg:          #00F2D4  (bright-teal)
Primary button focus:       border 1px solid $rich-black + outline 2px solid #00F2D4
Active pagination link:     color #001423 (rich-black text on teal bg)
Button sizes:               padding 0.25rem 0.5rem (reduced from default)
```

---

## 12. Badges

```
Badge text color:     inherits from context (no override)
Badge links:          color: inherit (no underline)
Badge user-select:    text (copyable)
Semantic badge colors: use status colors from section 5
```

### Dark mode badge colors (text on subtle bg)

```
success badge: text #82D18E on bg #09230D, border #1C6B28
info badge:    text #8DC1ED on bg #0D1E2D, border #275B87
warning badge: text #F9C566 on bg #311F00, border #935F00
danger badge:  text #E68888 on bg #2B0B0B, border #802222
primary badge: text #001423 on bg #00F2D4  (inverted — teal fills)
```

---

## 13. Code / Diff Blocks

```
Change added line:   bg #83D28E (green-300), text dark (#1F2937)
Change removed line: bg #ED8C8C (red-300),   text dark (#1F2937)
Code text color:     #D1D5DB  (gray-300, --tblr-code-color in dark)
Highlight bg:        rgb(98, 63.6, 0)  ≈ #623F00  (dark gold)
Block pre border:    1px solid var(--border-color)  ≈ #2D3C51
```

---

## 14. Alerts / Toasts

```
Alert background:    var(--tblr-bg-surface)   (surface-level bg)
Alert text:          var(--tblr-body-color)   (#E5E7EB)
Toast text color:    var(--tblr-body-color)   (#E5E7EB)
```

---

## 15. Forms

```
Validation success color: rgb(130.2, 209.4, 142.8)  ≈ #82D18E
Validation error color:   rgb(230.4, 136.2, 136.2)  ≈ #E68888
Error border:             $red  (#D63939)
Input background:         inherits surface bg
```

---

## 16. Selection / Focus

```
Text selection bg:   rgba(0, 242, 212, 0.48)   (bright-teal at 48%)
```

---

## 17. Extended Color Tokens (full Tabler palette in dark mode)

These are the full named color variables available via `--tblr-<name>-*`:

```
blue:    #066FD1    azure:  #4299E1    indigo: #4263EB
purple:  #AE3EC9   pink:   #D6336C    red:    #D63939
orange:  #F76707   yellow: #F59F00    lime:   #74B816
green:   #2FB344   teal:   #0CA678    cyan:   #17A2B8
```

---

## 18. Textual TCSS — Quick Reference Palette

Copy-paste ready variables for `.tcss` files:

```css
/* === NetBox Dark Mode Palette === */

/* Backgrounds */
$bg-base:            #001423;   /* outermost: html, navbar, cards */
$bg-page:            #081B2A;   /* content area */
$bg-surface-2:       #1F2937;   /* secondary surface, dropdowns */
$bg-surface-3:       #18212F;   /* card headers, nested panels */
$bg-tabler-base:     #111827;   /* Tabler body bg (ref only) */

/* Brand */
$bright-teal:        #00F2D4;   /* PRIMARY ACCENT */
$dark-teal:          #00857D;   /* light-mode primary (ref only) */

/* Text */
$text-primary:       #E5E7EB;   /* main body text */
$text-emphasis:      #FFFFFF;   /* headings, strong emphasis */
$text-secondary:     #9CA3AF;   /* muted/secondary labels */
$text-link:          #00F2D4;   /* links = bright-teal */

/* Borders */
$border-default:     #2D3C51;   /* standard border */
$border-subtle:      #374151;   /* subtle/light border */

/* Status — text (lightened for dark bg) */
$status-success-text:   #82D18E;
$status-info-text:      #8DC1ED;
$status-warning-text:   #F9C566;
$status-danger-text:    #E68888;
$status-secondary-text: #A6AAB2;

/* Status — subtle backgrounds */
$status-success-bg:     #09230D;
$status-info-bg:        #0D1E2D;
$status-warning-bg:     #311F00;
$status-danger-bg:      #2B0B0B;

/* Status — border */
$status-success-border: #1C6B28;
$status-info-border:    #275B87;
$status-warning-border: #935F00;
$status-danger-border:  #802222;

/* Code diff */
$diff-added-bg:         #83D28E;
$diff-removed-bg:       #ED8C8C;
$diff-text-dark:        #1F2937;
```

---

## 19. Key UI Patterns to Mirror in Textual

### 19.1 Sidebar navigation

- Dark navy base (`#001423`) with a subtle teal gradient fade at the bottom
- Section group labels in bright-teal (`#00F2D4`)
- All nav item text/icons in white
- Active item: left-side accent line in bright-teal
- Hover: extremely subtle white overlay (~6%)

### 19.2 Content layout

- Sidebar on the left (fixed, ~18rem wide)
- Content area to the right with darker bg (`#081B2A`)
- Page header bar matches sidebar bg (`#001423`)
- Cards sit on `#001423` with header area in `#18212F`

### 19.3 Status/badge visual language

- Use lightened text colors on very dark colored backgrounds
- Always maintain bright-teal as the primary accent for interactive/active states
- Avoid pure white for semantic status; use the lightened palette variants

### 19.4 Table pattern

- Column headers: bold, small caps, on `#001423` bg
- Rows: transparent on `#081B2A` page bg, subtle row hover
- Dashed borders for attribute tables (key-value pairs)
- Status rows: 15% opacity semantic color tint on the row bg

### 19.5 Focus and interactivity

- Focus ring: `2px solid #00F2D4` (bright-teal outline)
- Selected text: `rgba(0, 242, 212, 0.48)` background
- Primary buttons: bright-teal bg with `#001423` (rich-black) text
- Pagination active: bright-teal bg with rich-black text (same inversion)

---

## Sources

All patterns extracted from:
- `netbox/project-static/styles/_variables.scss` — brand color definitions
- `netbox/project-static/styles/overrides/_tabler.scss` — dark mode overrides and component tweaks
- `netbox/project-static/styles/transitional/_navigation.scss` — sidebar styling
- `netbox/project-static/styles/transitional/_tables.scss` — table styling
- `netbox/project-static/styles/transitional/_cards.scss` — card styling
- `netbox/project-static/styles/transitional/_badges.scss` — badge behavior
- `netbox/project-static/styles/custom/_interfaces.scss` — interface row tinting
- `netbox/project-static/styles/custom/_code.scss` — diff/code block colors
- `netbox/project-static/styles/custom/_misc.scss` — miscellaneous UI elements
- `netbox/project-static/dist/netbox.css` — compiled output (confirms computed values)
