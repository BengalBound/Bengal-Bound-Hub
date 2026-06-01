# UX Design Principles — Bengal Bound
# BengalBound Ltd | "Light. Easy. Powerful."
**Version:** 1.1 | **Updated:** June 2026

---

## Core Philosophy: iOS-Level Simplicity

> "Simple can be harder than complex. You have to work hard to get your
> thinking clean to make it simple." — Steve Jobs

Every design decision at Bengal Bound starts with one question:
**"Can a non-technical business owner do this in under 60 seconds?"**

If the answer is no — redesign it.

---

## The 7 Principles

### 1. Zero Learning Curve
- First-time users never see a blank screen
- Every empty state has a clear action: "Hire your first agent →"
- Onboarding is a 3-step wizard, not a manual
- Tooltips appear the first time a user sees a new feature
- Video tutorials are embedded — one click, no new tabs

### 2. One Tap to Everything
- Logo tap → always returns to home dashboard
- Bottom nav (mobile) or sidebar (desktop) — always visible
- Max 3 taps to reach any feature from anywhere
- Back button always works as expected (iOS swipe left, Android system back)
- Search available from every screen (Cmd+K / Ctrl+K shortcut)

### 3. Instant Feedback
- Every button tap gives haptic feedback (mobile)
- Every action shows a loading state immediately (never a frozen screen)
- Success: green toast notification slides in from top
- Error: red toast with the specific reason and what to do next
- Approval sent: real-time badge counter updates without page refresh

### 4. Light by Default
- Dark mode is default (less eye strain, premium feel)
- Light mode available in Settings → instantly toggles everywhere
- No clutter — show what matters, hide the rest
- Dense information is collapsible (agent details expand on tap)
- Charts are minimal — one key number, one trend line

### 5. Forgiveness
- Every destructive action requires confirmation (with 5-second undo)
- Deleted data goes to "Archive" before permanent deletion
- Agent misconfiguration = warning, not immediate failure
- Password reset always works within 3 clicks
- "I changed my mind" — cancel flows everywhere

### 6. Responsive to Context
```
📱 On phone:
  → Show what matters RIGHT NOW (approvals, alerts, quick stats)
  → Bottom tab navigation (thumb-friendly)
  → Cards, not tables
  → Swipe to action (approve/reject)

💻 On desktop:
  → Show the full picture (analytics, multi-panel)
  → Keyboard shortcuts for power users
  → Full data tables with sort/filter
  → Drag-and-drop where it makes sense

⌚ Notification:
  → Agent name + one-line summary
  → Two buttons: Approve / View Details
  → Never more than needed
```

### 7. Never Leave the User Stuck
- Every error page has a "What to do next" section
- 404 → smart suggestion of where they might want to go
- Server error → "Our team has been alerted" + retry button
- API timeout → automatic retry with progress indicator
- If Inspector blocks an action → plain English explanation + what to do instead

---

## Screen Design Rules

| Rule | Detail |
|---|---|
| **Maximum font sizes** | Headline: 32px · Body: 16px · Caption: 12px (never smaller) |
| **Touch targets** | Minimum 48×48px on all interactive elements |
| **Contrast ratio** | WCAG AA minimum (4.5:1 for text) |
| **Spacing** | 8px grid system — everything is a multiple of 8 |
| **Border radius** | 12px cards · 8px inputs · 999px badges/pills |
| **Animations** | 200ms for micro-interactions · 300ms for page transitions |
| **Loading** | Always use skeleton screens (not spinners) for content |
| **Empty states** | Always have an illustration + headline + action button |
| **Forms** | Inline validation (not after submit) · Show requirements upfront |

---

## Mobile-First Screens (Priority Order)

These screens must be PERFECT on mobile — this is where most users will be:

1. **Dashboard** — Agent status at a glance, approval badge count
2. **Notifications** — Approval queue with Approve/Reject in one tap
3. **Agent Activity Feed** — Real-time what each agent is doing
4. **Hire Agent** — Browse, select, pay, configure in < 5 minutes
5. **Settings** — MFA, team, profile — never hidden

---

## Performance Targets (UX-critical)

| Screen | Target Load | What Happens If Slow |
|---|---|---|
| App launch (cold) | < 3 seconds | Splash screen with animation |
| Dashboard | < 1 second | Skeleton cards shown immediately |
| Notification tap | < 0.5 seconds | Instant transition |
| Agent hire flow | < 2 seconds per step | Optimistic UI updates |
| Chart rendering | < 1 second | Progressive data loading |

---

## What "Light and Easy" Looks Like in Practice

```
❌ BAD: "Configure your agent's natural language processing parameters
         and set threshold values for your compliance enforcement pipeline."

✅ GOOD: "Set up Concierge"
          Step 1: Connect your WhatsApp number
          Step 2: Tell Concierge about your business (3 questions)
          Step 3: Go live →

---

❌ BAD: Error 422: Validation failed. Field 'company_registration_number'
         does not match expected format for jurisdiction BD.

✅ GOOD: "Company number format looks off for Bangladesh.
          It should be 6–8 digits. Example: 123456"

---

❌ BAD: Loading spinner for 8 seconds with no feedback.

✅ GOOD: "Serea is reviewing your last 48 hours of comments...
          Usually takes about 30 seconds."
         [Progress bar at 60%]
```

---

## The Apple Test

Before shipping any feature, ask:
1. Would a business owner understand this without reading docs?
2. Does it work perfectly on a 5-year-old Android phone?
3. Is there anything on this screen that doesn't need to be here?
4. What happens when it goes wrong? Is that experience also great?
5. If someone's using this at midnight on an urgent deadline, will they succeed?

If any answer is "no" — it's not ready.

---

## BengalBound Design System — Glass-Morphism (June 2026)

The entire platform UI was overhauled in June 2026 to a premium **glass-morphism** aesthetic. All new templates and components must follow these tokens.

### CSS Architecture

Two stylesheet files:
- `static/css/index.css` — global tokens and base styles
- `static/css/console.css` — console/dashboard-specific layout

### Design Tokens

```css
/* Colors */
--bb-accent-cyan:    #00F5D4;   /* primary action, logo gradient start */
--bb-accent-purple:  #7B2FBE;   /* gradient end, highlights */
--bb-glass-border:   rgba(255,255,255,0.08);  /* glass panel edge */
--text:              rgba(255,255,255,0.9);
--muted:             rgba(255,255,255,0.5);
--border:            rgba(255,255,255,0.1);

/* Typography */
--font-body:    'Inter', sans-serif;      /* weights: 300, 400, 500, 600, 700 */
--font-heading: 'Outfit', sans-serif;     /* weights: 400, 600, 700, 800 */

/* Glass Panel */
background: rgba(10, 10, 15, 0.6);
backdrop-filter: blur(24px);
-webkit-backdrop-filter: blur(24px);
border: 1px solid var(--bb-glass-border);

/* Topbar */
background: rgba(3, 3, 5, 0.7);
backdrop-filter: blur(20px);
border-bottom: 1px solid rgba(0, 245, 212, 0.15);  /* cyan glow hint */
```

### Animated Background Orbs

Every console and workspace page uses three animated orbs behind the content:

```html
<div class="bg-animated-wrapper">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
</div>
```

### Layout Structure

```
<body>
  .bg-animated-wrapper   ← animated background orbs (fixed, behind everything)
  .bb-wrap               ← flex row container
    .bb-sidebar          ← fixed left sidebar (280px), glass panel
    .bb-main             ← flex column, margin-left: 280px
      .bb-topbar         ← sticky top bar (64px), glass, cyan glow border
      .bb-content        ← scrollable content area (padding: 2rem)
```

### Gradient Text Pattern

Used on logo and key headings:

```css
background: linear-gradient(135deg, var(--bb-accent-cyan) 0%, var(--bb-accent-purple) 100%);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
```

### Card / Component Rules

| Property | Value |
|---|---|
| Card background | `rgba(255,255,255,0.03)` |
| Card border | `1px solid rgba(255,255,255,0.08)` |
| Card border-radius | `12px` |
| Hover border | `var(--bb-accent-cyan)` |
| Hover glow | `box-shadow: 0 0 15px rgba(0, 245, 212, 0.1)` |
| Transition | `all 0.2s ease` |

### Font CDN

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
```

### Dependencies

| Library | Version | Purpose |
|---|---|---|
| Bootstrap | 5.3.3 | Layout grid + components |
| Bootstrap Icons | 1.11.3 | All icons (`bi-*` classes) |
| Inter | Google Fonts | Body text |
| Outfit | Google Fonts | Headings and logo |

---

*BengalBound Ltd — UX Principles v1.1 — June 2026*
*Light. Easy. The next generation starts here.*
