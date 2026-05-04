  
**MCP WEBSITE**

Agile Project Roadmap & Product Planning Document

| Music Connecting People Collective Community & Event Management Platform Version 1.0  |  2025 |
| :---: |

# **1\. Project Overview**

| Project Name | MCP Website |
| :---- | :---- |
| **Organization** | Music Connecting People (MCP) Collective |
| **Platform Type** | Community & Event Management Web Platform |
| **Long-Term Vision** | Full-featured community and event management system for cultural collectives |
| **Primary Users** | Event attendees, members, administrators, artists |
| **Document Type** | Agile Product Planning Roadmap |
| **Prepared For** | MCP Development Team |

## **Platform Purpose**

MCP Website is the central digital hub for the Music Connecting People collective. It serves as the primary interface for managing the collective's activities, enabling the team to run events, sell memberships and tickets, communicate with the community, and showcase artistic content.

## **Strategic Direction**

The platform is transitioning from a functional but basic system into a mature, feature-rich community management tool. The next development phase focuses on enhancing marketing capabilities, improving the ticketing and membership experience, expanding content offerings, and eventually introducing user accounts and ecommerce.

| P1 — Critical | P2 — High | P3 — Medium | P4 — Medium | P5 — Low | P6 — Future |
| :---: | :---: | :---: | :---: | :---: | :---: |

# **2\. Current System State**

## **Architecture Overview**

| Frontend | Next.js 13 (App Router) |
| :---- | :---- |
| **Backend** | Flask running inside Firebase Functions |
| **Database** | Firebase Firestore |
| **Authentication** | Firebase Auth |
| **File Storage** | Firebase Storage |
| **Serverless** | Firebase Functions |
| **Styling** | Global CSS (app/globals.css) |
| **Payments** | PayPal Integration |

## **Frontend Pages & Components**

* Home page

* Events listing page

* Event detail pages

* Photo gallery pages

* Admin area (management tools)

* UI components: event cards, checkout modals, informational sections

* Next.js API routes for backend integrations

## **Backend Capabilities (Flask / Firebase Functions)**

* Event management (create, update, publish)

* User and membership management

* PayPal payment integration

* Newsletter handling

* Ticket PDF generation

* Transactional email sending

## **Operational Tooling**

* Frontend development scripts

* Frontend production build scripts

* Firebase emulator management scripts

## **Currently Implemented Features**

| Feature | Status |
| :---- | :---- |
| Event publishing | ✅ Live |
| Event detail pages | ✅ Live |
| Photo galleries | ✅ Live |
| Membership sales | ✅ Live |
| Ticket sales | ✅ Live |
| PayPal checkout | ✅ Live |
| Ticket PDF generation | ✅ Live |
| Transactional emails | ✅ Live (basic) |
| Admin management tools | ✅ Live |

# **3\. Agile Roadmap**

The roadmap is organized into 6 Epics, prioritized by business value and platform maturity. Each Epic contains Features, which are broken down into concrete, developer-ready Tasks.

| EPIC 1  Marketing & Communication System   \[P1\] *Two-layer communication architecture: transactional emails (product layer, Flask backend) and marketing emails (growth layer, MailerLite). MCP internal Firestore database is the single source of truth for all contacts.* |
| :---- |

| Architecture Principle: Two Independent Systems Transactional and marketing emails must remain logically and technically independent. They use separate delivery paths, separate consent logic, and are never mixed. *MCP's internal Firestore database is the single source of truth. Only opted-in contacts are synced to MailerLite. MCP retains full data ownership.* |
| :---- |

## **System Comparison**

| Attribute | Layer 1 — Transactional | Layer 2 — Marketing |
| :---- | ----- | ----- |
| **Trigger** | User action (purchase, registration) | Admin campaign send |
| **Consent required** | No — service communication | Yes — explicit marketing opt-in |
| **Delivery via** | Flask backend (Firebase Functions) | MailerLite platform |
| **Sender domain** | MCP domain (e.g. tickets@...) | MailerLite / MCP domain |
| **Content type** | Service info only — no promo | Campaigns: events, lineups, recaps |
| **Examples** | Ticket PDF, membership confirm, reminder | Event announce, ticket launch, recap |

| Data Flow 1\.  User interacts with the website (ticket purchase, membership, newsletter signup) 2\.  MCP backend stores contact in Firestore (internal source of truth) 3a. Transactional email sent immediately via Flask — no opt-in required 3b. IF marketing opt-in present → contact synced to MailerLite 4\.  MailerLite sends segmented campaigns to opted-in audience |
| :---- |

### **Feature 1.1 — Transactional Email System (Product Layer)**

*Service-only emails triggered by user actions. No promotional content. No marketing consent required.*

| 🔷 Transactional Emails | Audit all existing transactional email types: purchase confirm, membership, ticket delivery, event reminder |
| :---- | :---- |
|  | Design branded HTML email templates with MCP visual identity (header, footer, typography) |
|  | Build ticket purchase confirmation email template with full order summary |
|  | Build membership purchase confirmation email template with membership dates |
|  | Build ticket delivery email with attached PDF (and QR code once Feature 2.1 is complete) |
|  | Build event reminder email template (configurable timing: 24h and 1h before event) |
|  | Build participant registration confirmation email template |
|  | Update Flask email sending module to use new HTML templates |
|  | Add email preview endpoint in admin (test-send to internal address per template type) |
|  | Set up transactional delivery monitoring and bounce / failure alerting |
|  | Enforce no-promotional-content policy: transactional emails contain service info only |
|  | Test all email types end-to-end in staging — verify rendering on Gmail, Outlook, and mobile |

### **Feature 1.2 — Marketing Opt-in Collection**

*Capture explicit marketing consent at key touchpoints. Store consent status in internal Firestore database.*

| 🔷 Opt-in Collection | Add marketing consent checkbox to ticket purchase checkout flow (default: unchecked) |
| :---- | :---- |
|  | Add marketing consent checkbox to membership purchase checkout flow (default: unchecked) |
|  | Build standalone newsletter signup form component (homepage, footer, event pages) |
|  | Store consent status, timestamp, and acquisition source in Firestore contact document |
|  | Implement consent update endpoint: opt-in / opt-out — updates Firestore immediately |
|  | Add unsubscribe flow: email footer link → one-click opt-out → update Firestore and MailerLite |
|  | Ensure all opt-in flows are GDPR-compliant: explicit, granular, freely revocable |

### **Feature 1.3 — Internal Contact Database (Source of Truth)**

*MCP owns and controls all audience data. Firestore is the primary contact record — not MailerLite.*

| 🔷 Contact Database | Define unified contact schema in Firestore: name, email, phone, source tags, consent status, consent timestamp |
| :---- | :---- |
|  | Implement contact deduplication logic on email (merge ticket buyer \+ newsletter subscriber records) |
|  | Tag contacts by data source: ticket\_buyer, member, newsletter\_subscriber, event\_participant |
|  | Build internal segment queries: composable filters (tag AND consent AND event\_id AND membership\_type) |
|  | Create admin contact database view: search, filter by tag/consent/segment, export to CSV |
|  | Implement anonymized/aggregated audience insight export for partner or sponsor reporting |
|  | Document data ownership policy: internal Firestore data is never deleted on MailerLite-side actions |

### **Feature 1.4 — MailerLite Integration (Growth Layer)**

*MailerLite handles marketing campaign delivery. Only opted-in contacts are synced. MCP retains data ownership.*

| 🔷 MailerLite Integration | Set up MailerLite account and configure MCP sending domain (SPF, DKIM, DMARC) |
| :---- | :---- |
|  | Implement Flask service module: mailerlite\_sync.py with API wrapper |
|  | Build contact sync: on opt-in → push contact with tags to MailerLite immediately |
|  | Build opt-out sync: on unsubscribe → update MailerLite contact status to unsubscribed |
|  | Map MCP Firestore tags to MailerLite groups and segments |
|  | Build admin campaign UI: create, preview, schedule, and send campaigns via MailerLite API |
|  | Create reusable MailerLite templates: event announcement, lineup reveal, ticket launch, countdown, post-event recap |
|  | Build campaign performance dashboard in admin: open rates, click rates, unsubscribes |
|  | Test sync accuracy end-to-end with staging data |

### **Feature 1.5 — Audience Segmentation**

*Segment opted-in contacts using MCP's internal data as the segmentation engine — independent of MailerLite.*

| 🔷 Segmentation | Define segmentation taxonomy: ticket\_buyer, member, event-specific, geographic |
| :---- | :---- |
|  | Build Firestore segment query engine with composable filters (tag AND consent AND event\_id) |
|  | Build admin segment builder UI: visual filter interface with real-time audience size preview |
|  | Sync named segments to MailerLite groups for targeted campaign sends |
|  | Enable per-campaign segment selection in admin campaign creation flow |
|  | Ensure MCP can run internal analytics and segment independently of any third-party tool |

| EPIC 2  Ticketing & Membership System Improvements   \[P2\] *Enhance the existing ticketing and membership workflows with QR code validation, entrance verification, and operational tools for event staff.* |
| :---- |

### **Feature 2.1 — QR Code Ticket Generation**

| 🔷 QR Code Tickets | Generate unique, cryptographically signed QR tokens per ticket upon purchase |
| :---- | :---- |
|  | Store QR tokens in Firestore (linked to ticket record) |
|  | Integrate QR code rendering into existing ticket PDF template |
|  | Ensure QR is correctly sized and scannable in PDF output |
|  | Add token validation endpoint in Flask backend |
|  | Write unit tests for token generation and validation logic |

### **Feature 2.2 — QR Code Membership Validation**

| 🔷 QR Membership Cards | Generate unique QR tokens for each active membership |
| :---- | :---- |
|  | Store membership QR tokens in Firestore |
|  | Design and implement digital membership card (PDF or in-app) |
|  | Add QR code to membership confirmation email |
|  | Build membership validation endpoint in backend |
|  | Support membership status check (active / expired / suspended) |

### **Feature 2.3 — Entrance Verification Workflow**

| 🔷 Entrance Verification | Build mobile-friendly QR scanner interface for event staff (web-based) |
| :---- | :---- |
|  | Implement camera access and QR code reading in browser (jsQR or ZXing) |
|  | Create real-time validation feedback: valid / invalid / already scanned |
|  | Track scan events in Firestore (timestamp, device, operator) |
|  | Build admin dashboard for real-time entrance statistics per event |
|  | Add operator authentication (role-based: door staff vs. admin) |
|  | Support offline fallback mode for poor-connectivity venues |

| EPIC 3  Content Platform   \[P3\] *Expand MCP's storytelling and cultural presence by adding artist profiles and a radio/DJ sets page, enriching the platform's content offering.* |
| :---- |

### **Feature 3.1 — Artists Page**

| 🔷 Artists Page | Define artist data model (name, bio, photo, genres, social links, event history) |
| :---- | :---- |
|  | Create artist document schema in Firestore |
|  | Build admin interface for creating and editing artist profiles |
|  | Design and implement public-facing artist listing page |
|  | Build individual artist profile page |
|  | Link artist profiles to event pages (billed artists) |
|  | Implement artist photo upload to Firebase Storage |
|  | Add search/filter by genre or name on artists listing |

### **Feature 3.2 — Radio Page (DJ Sets)**

| 🔷 Radio Page | Define DJ set data model (title, artist, date, SoundCloud URL, YouTube URL, cover image) |
| :---- | :---- |
|  | Create Firestore collection for radio/DJ set content |
|  | Build admin interface for adding and managing DJ set entries |
|  | Design and implement public Radio page with embedded players |
|  | Integrate SoundCloud embed widget |
|  | Integrate YouTube embed widget |
|  | Implement filtering by artist or date |
|  | Add lazy loading for performance optimization |

| EPIC 4  Dance for the Planet Section   \[P4\] *Dedicate a section of the platform to the Dance for the Planet project, communicating its mission, storytelling, and partner ecosystem.* |
| :---- |

### **Feature 4.1 — Dedicated Project Page**

| 🔷 Project Page | Define page content structure: mission statement, timeline, impact metrics |
| :---- | :---- |
|  | Create Firestore data model for Dance for the Planet content |
|  | Build admin content editor for project page |
|  | Design and implement public-facing project landing page |
|  | Implement hero section with visual storytelling (images/video) |

### **Feature 4.3 — Storytelling & Partners**

| 🔷 Storytelling & Partners | Define partner data model (logo, name, description, URL, category) |
| :---- | :---- |
|  | Create Firestore collection for partners |
|  | Build admin interface for managing partner entries |
|  | Design partners showcase section on project page |
|  | Implement story/update feed for project milestones |
|  | Add admin interface for publishing project updates |
|  | Integrate partner logo upload via Firebase Storage |

| EPIC 5  Ecommerce — Merchandise Store   \[P5\] *Launch an online merchandise store, allowing MCP to sell branded products and generate additional revenue for the collective.* |
| :---- |

### **Feature 5.1 — Product Catalogue**

| 🔷 Product Catalogue | Define product data model (name, description, images, variants, price, stock) |
| :---- | :---- |
|  | Create Firestore product collection with variant support |
|  | Build admin interface for product management (create, edit, archive) |
|  | Implement product image upload to Firebase Storage |
|  | Design and implement public-facing product listing page |
|  | Build individual product detail page with variant selector |

### **Feature 5.2 — Shopping Cart & Checkout**

| 🔷 Cart & Checkout | Implement client-side shopping cart (state management) |
| :---- | :---- |
|  | Build cart sidebar/modal UI |
|  | Integrate PayPal checkout for merchandise orders |
|  | Create order data model in Firestore |
|  | Implement order confirmation email |
|  | Build admin order management dashboard |
|  | Add inventory tracking and low-stock alerts |

| EPIC 6  User Accounts & Personal Dashboard   \[P6\] *Introduce user authentication and personal dashboards, giving community members a persistent identity, order history, and self-service capabilities.* |
| :---- |

### **Feature 6.1 — Authentication System**

| 🔷 Authentication System | Enable Firebase Auth email/password sign-up and login flows |
| :---- | :---- |
|  | Build login and registration UI pages |
|  | Implement social login options (Google, optional: Facebook) |
|  | Add password reset flow |
|  | Integrate auth state into Next.js App Router (middleware protection) |
|  | Link purchases and memberships to authenticated user UID |
|  | Handle account merging for existing purchasers (email match) |

### **Feature 6.2 — Personal Dashboard**

| 🔷 Personal Dashboard | Design and build personal dashboard layout |
| :---- | :---- |
|  | Implement event history section (past events attended) |
|  | Implement membership status and history section |
|  | Add ticket download functionality from dashboard |
|  | Build profile editing (name, contact info, preferences) |
|  | Implement notification preferences (email opt-ins) |
|  | Show upcoming events the user has tickets for |

# **4\. Suggested Sprint Breakdown**

Sprints are 2 weeks each. This plan assumes a small team (1-2 frontend, 1 backend developer). Adjust based on team velocity after Sprint 1 retrospective.

| Sprint | Name | Duration | Focus / Goals |
| :---: | :---- | :---- | :---- |
| **Sprint 1** | **Marketing Foundation** | Weeks 1–2 | Email provider integration, subscriber sync, basic campaign send |
| **Sprint 2** | **Email Templates & Segmentation** | Weeks 3–4 | Branded transactional emails, audience segmentation builder |
| **Sprint 3** | **QR Tickets** | Weeks 5–6 | QR token generation, PDF integration, validation endpoint |
| **Sprint 4** | **QR Memberships & Scanner** | Weeks 7–8 | Membership QR cards, entrance scanner UI, real-time dashboard |
| **Sprint 5** | **Artists Page** | Weeks 9–10 | Artist data model, admin UI, public listing and profile pages |
| **Sprint 6** | **Radio Page** | Weeks 11–12 | DJ sets model, admin UI, public radio page with embedded players |
| **Sprint 7** | **Dance for the Planet** | Weeks 13–14 | Project page, partners section, storytelling content |
| **Sprint 8** | **Merch Store — Catalogue** | Weeks 15–16 | Product model, admin UI, public product listing and detail pages |
| **Sprint 9** | **Merch Store — Checkout** | Weeks 17–18 | Cart, PayPal checkout, order management, confirmation emails |
| **Sprint 10** | **User Auth** | Weeks 19–20 | Login, registration, social auth, account linking |
| **Sprint 11** | **Personal Dashboard** | Weeks 21–22 | Dashboard UI, event/membership history, ticket downloads |
| **Sprint 12** | **Hardening & Polish** | Weeks 23–24 | QA, performance optimization, accessibility, documentation |

# **5\. Initial Backlog — Sprint 1 & 2 Ready Tasks**

The following tasks are fully defined and ready for development. These cover the first two sprints and should be imported directly into your project board (Jira / Linear / Notion).

## **Epic 1: Marketing & Communication — Sprint 1 Tasks**

### **Feature: Email Marketing Infrastructure**

* \[ \] Evaluate email providers: benchmark Brevo, Mailchimp, Sendgrid on cost, API quality, and GDPR compliance

* \[ \] Document provider decision with rationale in project wiki

* \[ \] Create accounts and obtain API credentials for chosen provider

* \[ \] Add provider API key to Firebase environment config (secret management)

* \[ \] Build Flask service module: email\_marketing.py

* \[ \] Implement POST /api/subscribers/sync endpoint to push Firestore users to provider

* \[ \] Write unit tests for subscriber sync logic

* \[ \] Test sync with staging data, verify contacts appear in provider dashboard

### **Feature: Audience Segmentation**

* \[ \] Define segmentation taxonomy (buyer, member, event-specific, geographic)

* \[ \] Create Firestore segment document schema

* \[ \] Build Firestore query logic for each segment type

* \[ \] Build admin UI component: SegmentBuilder.tsx

* \[ \] Connect segment queries to email provider list/tag system

* \[ \] Test segment accuracy with sample data

## **Epic 1: Marketing & Communication — Sprint 2 Tasks**

### **Feature: Improved Transactional Emails**

* \[ \] Audit existing transactional emails: list all types and current templates

* \[ \] Create base HTML email template with MCP branding (header, footer, typography)

* \[ \] Build ticket purchase confirmation email template

* \[ \] Build membership confirmation email template

* \[ \] Build payment receipt email template

* \[ \] Update Flask email sending module to use new templates

* \[ \] Add preview URL generation for email templates in admin

* \[ \] Test all email types via staging environment, verify rendering on Gmail / Outlook / mobile

## **Backlog Items — Upcoming Sprints (Defined, Not Yet Active)**

### **Epic 2: Ticketing — Sprint 3 Ready**

* \[ \] Research QR token signing strategy (HMAC-SHA256 with server secret)

* \[ \] Implement generate\_qr\_token(ticket\_id) function in backend

* \[ \] Store QR token in Firestore ticket document

* \[ \] Integrate qrcode Python library for image generation

* \[ \] Update ticket PDF template to include QR code image

* \[ \] Create POST /api/tickets/validate endpoint

* \[ \] Write integration tests for full QR generation \+ validation flow

| Document Notes This document is a living artifact. Review and update after each sprint retrospective. Sprint velocity should be calibrated after Sprint 1\. Epics 5 and 6 may be re-sequenced based on business priorities. |
| :---: |

