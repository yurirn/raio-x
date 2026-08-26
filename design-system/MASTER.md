# Raio X Design System

## Direction

Corporate operational dashboard with a clean, data-first visual language. Use cool neutral surfaces, deep navy navigation, cyan/teal accents, restrained shadows, and clear status colors. Avoid decorative gradients, glass effects, emojis, and dense walls of controls.

## Tokens

- Primary: `#0F766E`; primary hover: `#115E59`; accent: `#06B6D4`.
- Canvas: `#F4F7F9`; surface: `#FFFFFF`; navigation: `#0B172A`.
- Text: `#172033`; muted: `#64748B`; border: `#DCE4EA`.
- Success: `#15803D`; warning: `#B45309`; danger: `#B91C1C`.
- Radius: 10px controls, 14px cards. Shadow only for elevated surfaces.
- Spacing follows a 4/8px rhythm. Interactive targets are at least 44px high.

## Typography

Use Geist Sans for interface text and Geist Mono for tabular figures. Page titles are 28–32px/700, section titles 18px/650, body 14–16px/400–500, labels 13px/600. Numbers use tabular figures.

## Layout & Interaction

Desktop uses a persistent 248px sidebar and a maximum content width of 1440px. Below 1024px, use a compact top bar and slide-out navigation. Cards collapse from six to two and then one column. Tables use horizontal overflow only inside their own container.

All fields have visible labels, focus rings, inline errors, and disabled/loading states. Destructive actions require confirmation. Use 150–250ms opacity/color transitions and honor `prefers-reduced-motion`. Charts must include labels/tooltips and adjacent tabular data.

## Login Brand Override

The login route may use the supplied official Vivo logo unchanged from `frontend/public/logo-vivo.webp`. Use a purple palette (`#7F00B2` primary, `#5F008C` hover, `#F6ECFB` soft) with white form surfaces. The supplied nature image is stored at `frontend/public/vivo-background.png` and is reserved for the login visual. Keep the administrative portal monochrome: white canvas and sidebar, graphite text, soft gray borders and active navigation. Purple is reserved only for primary action buttons and their focus treatment. Green is reserved strictly for success statuses. Keep the Raio X product name visible, labels explicit, a 44px minimum control height, keyboard focus feedback, and a single primary submit action. Do not imitate third-party authentication pages or copy their text, layout, or security indicators.
