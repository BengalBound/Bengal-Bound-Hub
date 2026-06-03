# Healthcare & Personal Care — Module Manual

**Modules covered:** Care Manager · Booking

---

## Care Manager (`/hub/<slug>/care/`)

Client/patient management for care facilities, clinics, salons, and personal care businesses.

### Care Clients
Comprehensive client records:
- Personal: full name, DOB, gender, contact info
- Care level: `independent` / `assisted` / `full` / `specialist`
- Status: `active` / `on leave` / `discharged` / `inactive`
- Medical notes and dietary requirements (stored securely)
- Assigned care staff

### Care Plans
Structured plans per client:
- Care type: personal, medical, social, dietary, mobility, other
- Frequency (e.g. daily, twice weekly)
- Assigned staff, start date, review date

### Care Sessions
Individual session records:
- Linked to client and care plan
- Performed by, date/time, duration
- Status: `completed` / `missed` / `cancelled`
- Session notes

### Staff Rota
Shift assignments for care staff — shift date, time, role, confirmed status.

### Compliance Documents
Policy, procedure, certificate, training record, risk assessment, incident report storage:
- Document type classification
- Review date and active status
- Required for CQC / regulatory compliance

**AI Integration:** Hire **MediBook** to manage appointment scheduling, send patient reminders, and triage appointment urgency.

---

## Booking (`/hub/<slug>/booking/`)

Appointment scheduling for clinics, salons, spas, and practitioners.

### Services
Define bookable services: consultation, treatment, therapy session — each with duration, price, and buffer time.

### Staff Availability
Set weekly availability per practitioner. Block out unavailable times.

### Booking Flow
Clients book online or via phone:
1. Select service
2. Choose staff member (or any available)
3. Pick date and time slot
4. Confirm booking

Status: `pending` → `confirmed` → `completed` / `cancelled` / `no show` / `rescheduled`

### Use Cases

| Business Type | How Booking is Used |
|---------------|---------------------|
| Medical clinic | Doctor appointments, follow-ups, procedures |
| Dental | Treatment sessions, hygiene appointments |
| Salon / Spa | Haircuts, treatments, massages |
| Physiotherapy | Therapy sessions |
| Personal trainer | One-to-one sessions |

**AI Integration:** Hire **MediBook** to:
- Send automated appointment reminders (1 hour and 24 hours before)
- Manage waitlists
- Triage appointment urgency from patient descriptions
- Send post-appointment follow-up messages
