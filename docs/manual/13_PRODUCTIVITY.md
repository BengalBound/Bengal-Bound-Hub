# Productivity & Communication — Module Manual

**Modules covered:** Business Mail · Video Meet · Business Calendar · Cloud Drive · Docs · Sheets · Slides · Forms Builder · Team Chat · Announcements · Task Board · Projects

---

## Business Mail (`/hub/<slug>/mail/`)

Business email on your own domain.

### Mail Accounts
Each team member can have a linked email address (e.g. john@yourcompany.com).

### Folders
Messages are organised in: Inbox, Sent, Drafts, Trash, Spam. Threaded replies.

### Messages
- From, To, CC addresses
- HTML and plain text body
- Attachments with file size tracking
- Starred and read flags

---

## Video Meet (`/hub/<slug>/meet/`)

Built-in video conferencing.

### Meeting Rooms
Persistent rooms with unique codes. Capacity-limited. Generate direct meeting URLs.

### Meetings
- Organiser, start/end time, agenda
- Status: `scheduled` → `in progress` → `completed` / `cancelled`
- Recurring meetings with recurrence rules
- Attendee invite list with RSVP status (invited / accepted / declined / tentative)

**AI Integration:** Hire **Scribe** to join meetings as a notetaker, transcribe via Recall.ai, and produce structured summaries + action items automatically.

---

## Business Calendar (`/hub/<slug>/calendar/`)

Shared team calendar.

### Calendars
Multiple named calendars per business (e.g. "Marketing", "Operations", "HR"). Colour-coded.

### Events
- All-day or timed events
- Recurrence rules (daily, weekly, monthly)
- Status, location, colour override

### Attendees
Invite team members — they receive RSVP prompts (accepted / declined / tentative).

### Reminders
Auto-reminders X minutes/hours/days before the event. Tracks whether sent.

**AI Integration:** Hire **Atlas** (executive calendar management), **Concierge** (client meeting scheduling), **Tempo** (event coordination).

---

## Cloud Drive (`/hub/<slug>/drive/`)

Secure file storage with folder hierarchy.

### Folders
Hierarchical folder structure. Colour-coded. Created by any team member.

### Files
Upload any file type. Each file tracks:
- Size, MIME type, tags
- Starred and trashed flags

### Sharing
Share individual files with specific team members:
- Access levels: view, edit, download

---

## Docs (`/hub/<slug>/docs/`)

Collaborative rich-text document editor.

### Documents
Rich HTML content editor (similar to Google Docs):
- Created by, last edited by
- Shared flag — visible to all employees when shared
- Template flag — reusable document templates

### Sharing
Share individual docs with specific users at view or edit level.

**AI Integration:** Hire **Dox** for auto-generating SOPs, technical guides, and documentation. Hire **Sage** for contract review.

---

## Sheets (`/hub/<slug>/sheets/`)

Built-in spreadsheet application.

Spreadsheet data stored as a 2D JSON array with configurable column widths.

- Created by, shared flag
- Collaborative editing by team members

---

## Slides (`/hub/<slug>/slides/`)

Presentation builder.

### Presentations
Themed presentations with shared access.

### Slides
Individual slides with:
- Layout types: title, content, two-column, blank, image
- Title, body text, speaker notes
- Background colour and image

**AI Integration:** Hire **Sylvia (Pitch Presenter)** to auto-generate pitch decks from a brief, including AI-narrated video via HeyGen.

---

## Forms Builder (`/hub/<slug>/forms/`)

No-code form and survey builder.

### Forms
Public or private forms with a shareable embed URL.

### Form Fields
Types: text, textarea, email, phone, number, date, dropdown, checkbox, radio, file upload, star rating, yes/no.

Required flag and placeholder text per field. Field ordering by drag.

### Responses
Each submission stored as a `FormResponse` with individual field answers.

**AI Integration:** Hire **Clarity** to analyse form responses, extract themes, and surface actionable insights.

---

## Team Chat (`/hub/<slug>/chat/`)

Real-time team messaging.

### Channels
Named channels: public (visible to all), private (invite-only), announcement (admin-post only).

### Messages
Threaded replies. Edited/deleted tracking. Emoji reactions (M2M per message per user).

### Direct Messages
1:1 messages between any two team members. Read receipts.

---

## Announcements (`/hub/<slug>/announcements/`)

Broadcast messages across the business.

### Announcements
- Types: general, policy, event, emergency, achievement, reminder
- Target: entire business, specific departments, or specific roles
- Priority (normal / high / urgent)
- Pinned to top, expiry date

### Engagement
- Read receipts per user
- Comment threads per announcement
- Pin individual comments

---

## Task Board (`/hub/<slug>/board/`)

Kanban project management (Trello-style).

### Boards
Named boards per project or team. Colour-coded. Archivable.

### Lists (Columns)
Ordered columns with optional WIP limits (e.g. "To Do", "In Progress", "Review", "Done").

### Cards
Task cards within lists:
- Title, description, colour, due date, story points
- Multiple assignees
- Labels (coloured tags)
- Checklists with completion tracking
- Comments and activity log
- Attachment support

---

## Projects (`/hub/<slug>/projects/`)

Full project management with milestones and time tracking.

### Projects
- Status: `planning` → `active` → `on hold` → `completed` / `cancelled`
- Budget, client name, start/end dates

### Milestones
Key project checkpoints with due dates and completion tracking.

### Tasks
Detailed tasks linked to milestones:
- Status: `todo` → `in progress` → `review` → `done`
- Assignee, due date, estimated vs actual hours

### Time Entries
Log hours against specific tasks. Date and description per entry.
