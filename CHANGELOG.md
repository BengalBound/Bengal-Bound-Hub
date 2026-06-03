# Changelog — Sprint G & Sprint H Implementation

This document logs all changes made during the AI Agent Platform Migration sprints for Stripe Billing Integration (Sprint G) and Firebase Authentication Bridge (Sprint H).

---

## [Sprint H] Firebase Authentication Bridge

Allows external client surfaces (such as mobile applications or modern web frontends) to authenticate against Firebase, sync their user accounts with the Django backend, auto-provision initial workspaces, and retrieve Django Session + DRF SimpleJWT token credentials.

### 1. Database Schema Extensions
- **Modified** [accounts/models.py](file:///d:/Bengal%20bound/dev-backoffice/accounts/models.py):
  - Added `firebase_uid = models.CharField(max_length=128, unique=True, blank=True, null=True)` on the custom `User` model.
- **Created** [accounts/migrations/0005_user_firebase_uid.py](file:///d:/Bengal%20bound/dev-backoffice/accounts/migrations/0005_user_firebase_uid.py):
  - Database schema migration applying the new `firebase_uid` field.

### 2. ID Token Verification & User Synchronization
- **Modified** [accounts/views.py](file:///d:/Bengal%20bound/dev-backoffice/accounts/views.py):
  - Implemented `verify_firebase_token(id_token)`: fetches Google's public x509 cert configurations dynamically, processes signature verification using RS256, and checks issuer/audience claims.
  - Implemented `firebase_token_sync(request)`: a POST API view accepting a Firebase `id_token`. Performs account lookups (via `firebase_uid` then `email`), creates new users on the fly if needed, automatically provisions a default `BusinessInstance` + `BusinessEmployee` owner record + active `freemium` subscription, establishes the Django session, and returns simplejwt token pairs. Swapped out the deprecated `BaseUserManager.make_random_password()` password generator with modern and secure `secrets.token_urlsafe(16)` to clean up Django 5.1 deprecation warnings.
- **Modified** [accounts/urls.py](file:///d:/Bengal%20bound/dev-backoffice/accounts/urls.py):
  - Registered route `/accounts/firebase-sync/` pointing to the synchronization endpoint.

### 3. Settings Configurations
- **Modified** [bengalbound_core/settings/base.py](file:///d:/Bengal%20bound/dev-backoffice/bengalbound_core/settings/base.py):
  - Registered `FIREBASE_PROJECT_ID` parameter.
- **Modified** [bengalbound_core/settings/testing.py](file:///d:/Bengal%20bound/dev-backoffice/bengalbound_core/settings/testing.py):
  - Added `TESTING = True` to enable local mock token parsing during tests.

### 4. Automated Tests
- **Modified** [tests/test_auth.py](file:///d:/Bengal%20bound/dev-backoffice/tests/test_auth.py):
  - Added `FirebaseAuthBridgeTests` testing sync registration, email alignment mapping, UID matching logins, and invalid/empty token payloads.
  - Configured mock JWT encoding to use a 32+ character HMAC key to prevent PyJWT's `InsecureKeyLengthWarning` warning.

---

## [Sprint G] Stripe Billing Integration

Replaces the manual pricing modifications with automated Stripe Checkout flows and secure webhook event processing.

### 1. Plan Upgrade Redirects
- **Modified** [hub/views.py](file:///d:/Bengal%20bound/dev-backoffice/hub/views.py):
  - Modified the `hub_subscription` change plan action: redirects switches to paid tiers (`standard`, `premium`) to Stripe Checkout via `/billing/checkout/<plan>/?cycle=<cycle>&business_id=<id>` instead of immediately updating the local database.
- **Modified** [billing/services.py](file:///d:/Bengal%20bound/dev-backoffice/billing/services.py):
  - Corrected plan pricing calculations from `base_price_monthly` to the valid model fields `monthly_price_usd` and `annual_price_usd`.
- **Modified** [billing/views.py](file:///d:/Bengal%20bound/dev-backoffice/billing/views.py):
  - Updated checkout and portal redirection targets to resolve the company context via the `business_id` query parameter.

### 2. Premium Templates
- **Created** [templates/billing/success.html](file:///d:/Bengal%20bound/dev-backoffice/templates/billing/success.html):
  - Dark glassmorphic layout displaying a green checkout checkmark, payment details, and returns links back to the hub.
- **Created** [templates/billing/cancel.html](file:///d:/Bengal%20bound/dev-backoffice/templates/billing/cancel.html):
  - Dark glassmorphic cancel page notifying the user that payment was aborted.
- **Modified** [billing/views.py](file:///d:/Bengal%20bound/dev-backoffice/billing/views.py):
  - Set `success_view` and `cancel_view` to render the new UI templates with complete sidebar context.

### 3. Webhook Logic and SDK Corrections
- **Modified** [billing/views.py](file:///d:/Bengal%20bound/dev-backoffice/billing/views.py):
  - Wrapped Stripe SDK attributes with `getattr()` to resolve errors where `StripeObject` instances raised errors on `.get()`.
  - Parsed incoming raw payload streams (`json.loads`) to store a serialized Python dict instead of the `StripeObject` inside `BillingEvent.payload` JSONField.
  - Handled `customer.subscription.deleted` checks gracefully without throwing errors on missing subscription item configs.

### 4. Tests
- **Modified** [billing/tests.py](file:///d:/Bengal%20bound/dev-backoffice/billing/tests.py):
  - Implemented unit tests for invalid signature rejects, checkout redirects, portal redirects, and webhook updates.
- **Modified** [tests/test_hub_views.py](file:///d:/Bengal%20bound/dev-backoffice/tests/test_hub_views.py):
  - Refactored `test_hub_subscription` to verify redirect upgrades and immediate downgrades.
