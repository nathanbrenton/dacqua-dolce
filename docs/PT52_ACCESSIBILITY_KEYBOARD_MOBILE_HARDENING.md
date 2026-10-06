# PT52 — Accessibility + Keyboard/Mobile Hardening

## Purpose

PT52 hardens existing D'Acqua Dolce interfaces without changing business rules,
commerce behavior, product content, or visual branding. The milestone focuses on
concrete keyboard, focus, touch, and small-screen defects found in the current
React UI.

## Implemented

### Skip navigation and SPA route focus

- A keyboard-visible `Skip to main content` link is the first application
  control.
- Every routed page exposes one focusable `main#main-content` target.
- Client-side route changes move focus to the new main content after navigation,
  while the initial page load does not steal focus.

### Modal focus continuity

- Authentication credentials initially focus the email field.
- Authentication stage transitions move focus to the updated dialog heading so
  email-verification and MFA state changes are announced in context.
- Quote/inquiry dialogs initially focus the name field.
- Successful quote submission moves focus to the success status region instead
  of leaving focus on a form control that was removed from the DOM.

### Customer Inbox keyboard continuity

- Archiving a conversation from the Inbox list moves focus to the automatically
  selected neighboring conversation.
- If the final visible conversation is archived, focus returns to the Inbox
  search field.
- Inbox errors are exposed as alerts and refresh/loading state is exposed with
  `aria-busy`.

### Mobile navigation and touch targets

- The previous mobile rule that hid all `nav a` elements is removed. Primary
  navigation and policy links therefore remain available on small screens.
- The primary mobile navigation wraps beneath the logo and can scroll
  horizontally when needed rather than dropping links.
- Inbox tabs/archive actions and coarse-pointer interactive controls use a
  minimum 44px target height.

### Focus visibility and reduced motion

- Native `summary` controls and textareas share the site's explicit focus-ring
  treatment with buttons, links, selects, and inputs.
- Existing global `prefers-reduced-motion` behavior remains authoritative; PT52
  does not add motion that bypasses it.

## Non-goals

PT52 does not claim a formal WCAG certification or legal accessibility audit.
It does not change checkout readiness, tax/payment logic, legal text, catalog
rules, roles, authentication policy, or Operations permissions.

## Acceptance focus

Browser acceptance should cover keyboard-only navigation on desktop, the mobile
header at narrow width, authentication and quote dialogs, route changes between
Home/Support/Account/Operations, Customer Inbox archiving, visible focus rings,
and reduced-motion mode.
