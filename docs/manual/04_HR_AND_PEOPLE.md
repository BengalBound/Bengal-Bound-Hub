# HR & People — Module Manual

**Modules covered:** HR · Recruitment · Attendance · Shift Planning · Training · LMS · Assessments

---

## HR (`/hub/<slug>/hr/`)

Core employee lifecycle management.

### Departments & Positions
- Create department hierarchy with named managers
- Define job positions linked to departments

### Employee Records
Each employee record contains:
- Personal: name, DOB, gender, national ID, photo, address, emergency contact
- Work: employee ID, department, position, manager, contract type (full-time / part-time / contractor / intern)
- Employment: hire date, termination date, status (active / inactive / on leave / terminated)
- Pay: salary, currency, bank details

### Leave Management
- Define leave types: annual, sick, maternity, unpaid — with days allowed per year
- Leave requests flow: `pending` → `approved` / `rejected` / `cancelled`
- Reviewer adds comments when deciding

### Performance Reviews
Periodic performance appraisals:
- Ratings (1–5 scale), goals achieved, strengths, areas to improve
- Status: `draft` → `submitted` → `completed`

**AI Integration:** Hire **Hera** for onboarding automation, policy queries, and weekly HR digests. Hire **Nexus** for skills gap analysis and course recommendations.

---

## Recruitment (`/hub/<slug>/recruitment/`)

Applicant tracking system for open positions.

### Job Postings
- Title, department, location, type (full-time / part-time / remote / internship)
- Salary range, application deadline, number of openings
- Status: `draft` → `open` → `closed`

### Applicant Pipeline
Stage progression: `applied` → `screening` → `interview` → `assessment` → `offer` → `hired` / `rejected`

### Interviews
- Types: phone screen, video, onsite, technical, panel
- Multiple interviewers per interview
- Status: `scheduled` → `completed` / `no show`
- Feedback and rating recorded post-interview

---

## Attendance (`/hub/<slug>/attendance/`)

Time tracking and absence management.

### Work Schedules
Define named schedules (e.g. "Standard 9-5") with hours per day and working days.

### Attendance Records
Daily records per employee:
- Check-in / check-out times
- Hours worked, overtime hours
- Status: `present` / `absent` / `late` / `half day` / `leave`

### Timesheets
Weekly summaries with project/task time breakdown:
- Billable vs non-billable hours
- Status: `draft` → submitted → approved by manager

---

## Shift Planning (`/hub/<slug>/shifts/`)

Rota creation and shift management.

### Shift Templates
Reusable shift definitions: name, start/end time, break minutes, department, colour.

### Schedule Periods
Weekly rota published by manager. Employees can see their shifts once published.

### Shifts
Individual shift assignments:
- Status: `scheduled` → `confirmed` → `completed` / `absent`
- Actual start/end times logged for payroll

### Swap Requests
Employees can request to swap a shift with a colleague. Requires manager approval.

---

## Training (`/hub/<slug>/training/`)

Internal corporate training programme management.

### Courses
- Title, category, level (beginner / intermediate / advanced)
- Target departments and mandatory flag
- Status: `draft` → `published` → `archived`

### Course Modules
Content delivery per module:
- Types: video, article, quiz, assignment, document
- Required flag — learner must complete before advancing

### Enrollments
Track per-employee progress:
- Status: `enrolled` → `in progress` → `completed` / `dropped`
- Progress %, score, certificate issued flag

**AI Integration:** Hire **Nexus** to auto-generate training plans based on skills gaps and employee performance data.

---

## LMS (`/lms/` — suite prefix)

Full Learning Management System for clients or students.

### Courses
- Self-paced with pass score and certificate on completion
- Audience: employees, students, or both

### Lessons
Content types: text, video, file, external link, quiz. Duration in minutes.

### Enrollments
Same flow as Training module. Certificate issued on passing.

---

## Assessments (`/assessments/` — suite prefix)

Online quiz and examination engine.

### Quizzes
- Time limit, pass score %, allow retakes, shuffle questions

### Questions
- Types: multiple choice, true/false, short answer, essay
- Points per question, explanatory notes shown after attempt

### Attempts
Student attempts are recorded with score, pass/fail, time taken. Per-answer correctness logged.
