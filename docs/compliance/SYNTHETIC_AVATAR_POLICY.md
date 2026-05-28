# Synthetic Avatar & Anti-Deepfake Policy

## 1. Purpose
As BengalBound HUB expands into B2C markets (such as "AI-as-a-Friend" or customizable AI Companions), users will have the ability to design and personalize their AI's visual appearance. To strictly comply with international anti-deepfake legislation and right-of-publicity laws, this policy enforces strict constraints on avatar generation.

## 2. Legal Frameworks
This policy ensures compliance with:
*   **EU AI Act (Article 52)**: Strict transparency obligations for deepfakes and AI-generated humans.
*   **US State Laws (e.g., California AB-602)**: Prohibits the non-consensual use of a real human's likeness to create a digital replica.
*   **Right of Publicity (Personality Rights)**: Prevents the unauthorized commercialization of a real person's face.

## 3. Technical Constraints & Enforcement
To eliminate legal liability, BengalBound enforces a **"Synthetic-Only" Architecture**:

1.  **No Direct Image Uploads**: End-users are strictly prohibited from uploading raw JPEG/PNG files of faces (e.g., a photo of a celebrity or ex-partner) to generate a custom avatar.
2.  **Algorithmic Face Generation**: Users may only "design" their AI companion using text-to-image models (e.g., Stable Diffusion, Midjourney) configured to generate mathematically synthetic, non-existent humans.
3.  **Avatar Stock Library**: Users may select from a pre-approved library of legally-cleared, synthetic stock avatars provided by our Video Engine (HeyGen/D-ID).
4.  **KYC Exemption**: If an enterprise client wishes to clone a real human (e.g., a CEO for pitch presentations), they must pass the **Veritas KYC** onboarding module and sign a biometric consent release form. B2C users are universally denied this exemption.

## 4. Audit & Enforcement
Any API request to the Video Engine that attempts to bypass the synthetic generation pipeline will be automatically blocked by the Inspector middleware, and the user's account will be permanently banned.
