# Travel — Module Manual

**Modules covered:** Travel CRM · Travel Desk · Group Bookings

---

## Travel CRM (`/hub/<slug>/travel-crm/`)

Client management for travel agencies and tour operators.

### Travel Clients
Rich traveller profiles:
- Passport number and nationality
- Preferred airline and frequent flyer numbers
- Dietary requirements and special needs
- Assigned agent for relationship management

### Itineraries
Full trip planning per client:
- Destination, travel dates, status (`draft` → `confirmed` → `in progress` → `completed` / `cancelled`)
- Total budget and currency

### Itinerary Items
Day-by-day trip components:
- Types: flight, hotel, transfer, activity, tour, meal, other
- Supplier, confirmation code, start/end times, cost
- Detailed notes per item

### Travel Bookings
Individual bookings within an itinerary:
- Types: flight, hotel, package, cruise, transfer, activity
- Booking reference, supplier, travel/return dates
- Amount, currency, status
- Commission amount tracked per booking

**AI Integration:** Hire **Atlas** for executive briefings and itinerary scheduling. Hire **Concierge** for VIP client management.

---

## Travel Desk (`/hub/<slug>/travel-desk/`)

Corporate travel request and policy management.

### Corporate Accounts
Company-level travel accounts:
- Credit limit and currency
- Travel policy document URL
- Active/inactive status

### Travel Policies
Define spending rules per company:
- Maximum hotel rate per night
- Maximum flight class (economy/business)
- Minimum advance booking days
- Approval required above a threshold amount

### Travel Requests
Employee travel request workflow:
- Request number, requester, corporate account
- Trip purpose, origin/destination, departure/return dates
- Travel type: business, client meeting, conference, training
- Estimated and actual costs
- Status: `draft` → `submitted` → `approved` / `rejected` → `booked` → `completed`
- Approval trail with rejection reason

### Travel Expenses
Expenses claimed against a travel request:
- Expense type, description, amount, receipt upload
- Approval status

---

## Group Bookings (`/hub/<slug>/groups/`)

Primarily covered in the Hospitality manual, but equally applicable to:
- **Tour operators:** Group tour packages with fixed rooming lists
- **Event companies:** Conference and retreat accommodation blocks
- **Corporate travel desks:** Team off-site and company retreat coordination

See [Hospitality Manual](07_HOSPITALITY.md#group-bookings) for full feature detail.
