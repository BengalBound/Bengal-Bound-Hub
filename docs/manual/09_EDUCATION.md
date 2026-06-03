# Education — Module Manual

**Modules covered:** SIS · LMS · Assessments · Timetable · Parent Portal

---

## SIS — Student Information System (`/sis/` — suite prefix)

Central student records for schools and universities.

### Students
Full student record:
- Enrollment number, name, DOB, gender, photo
- Class group and section
- Status: `active` / `graduated` / `suspended` / `withdrawn` / `transferred`
- Contact: email, phone, address
- Notes and special requirements

### Parent/Guardian Records
Link multiple guardians to a student:
- Relationship, contact details
- Primary guardian flag

### Grades
Subject grades per student per period:
- Score, max score, grade letter
- Recorded by teacher with notes

**AI Integration:** Hire **Nova** to analyse grade trends and identify at-risk students.

---

## LMS — Learning Management System (`/lms/` — suite prefix)

Online course delivery platform.

### Courses
- Title, code, level (beginner / intermediate / advanced)
- Self-paced or instructor-led
- Pass score % for certification
- Target audience: students, employees, or both
- Status: `draft` → `published` → `archived`

### Course Modules
Structured content sections within a course:
- Content types: text, video, file, external link, quiz
- Required flag — must complete before advancing
- Duration in minutes

### Lessons
Individual learning units within modules. Preview flag for guest access.

### Enrollments
Track learner progress:
- Status: `enrolled` → `in progress` → `completed` / `dropped`
- Progress % auto-calculated from completed modules
- Certificate auto-issued on passing

**AI Integration:** Hire **Nexus** for auto-generating courses from skills gap analysis.

---

## Assessments (`/assessments/` — suite prefix)

Online examination and quiz engine.

### Quizzes
- Time limit (minutes), pass score %
- Maximum attempts allowed
- Shuffle questions per attempt

### Questions
Types: multiple choice, true/false, short answer, essay.

Each question has: points, explanation text shown after attempt.

### Multiple Choice Options
Mark the correct option(s). Distractors help measure understanding depth.

### Attempts
Each student attempt is recorded:
- Started and submitted timestamps
- Total score, pass/fail result
- Per-question answer correctness

---

## Timetable (`/timetable/` — suite prefix)

Academic class scheduling.

### Rooms
Classrooms, labs, halls, sports facilities — with capacity and equipment.

### Time Slots
Named periods per day of week (e.g. "Period 1 — Mon 08:00–08:45").

### Class Sessions
Link: subject + class group + instructor + room + time slot.

Active date range (effective from / until) allows semester scheduling.

### Schedule Exceptions
Cancellations, substitutions, room changes — logged per specific date.

---

## Parent Portal (`/parent-portal/` — suite prefix)

Parent-facing transparency into their child's school progress.

### Progress Reports
Issued per term:
- Overall grade, GPA, attendance %
- Teacher comments
- Subject-by-subject breakdown with scores and grades
- Shareable via secure token link

### Parent Messages
Direct messages from teachers or admin:
- Subject, body, sent timestamp
- Urgent flag for time-sensitive communication

### Announcements
School notices published to parents:
- Audience: all parents, specific class, or individual
- Pinned flag for important notices
