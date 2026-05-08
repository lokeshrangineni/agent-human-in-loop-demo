# Human-in-the-Loop Agent Demo — Invoice Processing and Approval Workflow

## Overview

A demo application that showcases a human-in-the-loop multi-agent system for processing invoices. The user uploads an invoice, two agents collaborate to extract and validate the data, and the user reviews, approves, corrects, or rejects the outcome.

## Domain

Invoice processing and approval workflow.

## Requirements

### User Trigger
- The user uploads an invoice (image or PDF) to kick off the workflow.
- Uploaded documents may be:
  - **Low-resolution** images or photos (blurry, noisy, poorly lit).
  - **Scanned paper documents** with scan artifacts (skew, shadows, folds, stamps).
  - **Unpredictable formats** containing extraneous or irrelevant information (e.g., handwritten notes, marketing content, terms and conditions, logos) alongside the actual invoice data.
- The system must handle all of these gracefully — extracting useful data while ignoring noise and irrelevant content.

### Agents

**Agent 1 — Extraction Agent**
- Parses the uploaded invoice and extracts structured data: vendor name, line items, amounts, tax, due date, invoice number, etc.
- The extracted schema must be flexible — invoices come from different vendors in varying formats and structures. The agent should not assume a fixed schema; it should dynamically discover and extract whatever fields are present.
- Maintains its own state: raw extraction results, confidence scores, and flagged anomalies (e.g., missing fields, unreadable sections).

**Agent 2 — Validation Agent**
- Receives the structured data from the Extraction Agent.
- Cross-references the extracted data against business rules (e.g., budget limits, approved vendor list, duplicate invoice detection).
- Maintains its own state: validation results, rule violations, and an overall approval recommendation.

### Agent Communication
- The Extraction Agent passes structured invoice data to the Validation Agent.
- The Validation Agent can request the Extraction Agent to re-extract or clarify low-confidence fields.

### Flexible Schema
- Invoices are not standardized — they come from different vendors in any structure or format.
- The data model must be flexible enough to accommodate arbitrary fields and line items that vary from invoice to invoice.
- No fixed schema should be enforced; the system should handle whatever the extraction agent discovers.

### Confidence Scores
- Every extracted field and line item must include a confidence score indicating how certain the agent is about the extracted value.
- Confidence scores should be visually surfaced to the user (e.g., color-coded: high/medium/low) so they can quickly identify which fields need attention.
- Low-confidence fields should be highlighted or flagged so the user knows where to focus their review.
- The Validation Agent should also provide an overall confidence score for the invoice as a whole, factoring in extraction confidence and business rule compliance.

### Workflow 1: Data Review and Approval (Human-in-the-Loop)
- The user reviews the extracted data, validation results, and confidence scores.
- The user can:
  - **Approve** the invoice for payment.
  - **Reject** the invoice.
  - **Request re-processing** — ask the agents to re-extract or re-validate.
  - **Manually correct** any extracted or validated fields.
  - **Add new rows or fields** — the user can introduce entirely new line items or data fields that the extraction agent did not capture, since invoices vary widely in structure.
- If the user modifies, corrects, or adds any data, the changes do **not** take effect immediately. They are submitted for **admin approval**.
- The admin reviews the user's proposed changes, can approve them as-is, modify them further, or reject them.
- Only after admin approval are the changes applied to the final extracted data.

### Workflow 2: Feedback to Agents (Agent Learning)
- This is a separate workflow from data corrections. Its purpose is to improve how the agents perform in the future.
- The user can submit feedback on the extraction and validation results (e.g., "this vendor always puts the invoice number in the top-right corner" or "tax field was misread as a line item").
- User-submitted feedback goes into a **pending review queue** — it is not applied to the agents directly.
- The admin reviews pending feedback, can modify it, approve it, or reject it.
- Only admin-approved feedback is stored in the feedback memory and used by the agents for learning.
- Agents use accumulated approved feedback to improve over time:
  - **Extraction Agent** — learns from corrections (e.g., if users consistently fix a certain field for a specific vendor, the agent incorporates that pattern into future extractions for that vendor). Past corrections are provided as few-shot examples in the agent's prompt context for similar invoices.
  - **Validation Agent** — learns from approvals and rejections to refine its business rule application and adjust its approval recommendations (e.g., if users repeatedly override a rule violation, the agent adjusts the severity of that rule).
- A feedback memory store records: the original extraction, what the user changed, the vendor, and the invoice format — so agents can retrieve relevant past corrections when processing new invoices.
- Over time, confidence scores should improve for recurring vendors and invoice formats as the agents accumulate more approved feedback.
- The system should surface a summary of how agent accuracy has improved (e.g., fewer corrections needed over time) to demonstrate the value of the feedback loop.

### Roles and Permissions

**User Role**
- Can upload invoices and trigger the extraction workflow.
- Can review extracted data, validation results, and confidence scores.
- Can propose corrections, add rows/fields, approve, reject, or request re-processing (Workflow 1) — but modifications require admin approval before taking effect.
- Can submit feedback to improve agent behavior (Workflow 2) — but feedback requires admin approval before it is applied to the agents.
- Can view all past extractions in a tabular format and drill into the details of any individual extraction.

**Admin Role**
- Has all User permissions.
- **Workflow 1 approval:** Reviews user-proposed data corrections/additions and approves, modifies, or rejects them before they are applied to the final extracted data.
- **Workflow 2 approval:** Reviews user-submitted feedback and approves, modifies, or rejects it before it is stored and used by the agents for learning.
- Can view all past extractions in a tabular format and drill into the details of any individual extraction.
- Can see pending approval queues for both workflows.

**Authentication (Initial Implementation)**
- For the initial demo, user and admin accounts are hardcoded and selectable from a dropdown (no login flow).
- The dropdown should include at least one admin and one user (e.g., "Admin - Jane" and "User - John").
- The system should be designed so that SSO integration can replace the dropdown in the future without major refactoring.

### Extraction History
- Both admin and user roles can view a table of all past invoice extractions.
- The table should show key summary columns: invoice ID, vendor, date, status (approved/rejected/pending), confidence score, and who processed it.
- Clicking a row opens a detail view showing the full extracted data, validation results, confidence scores, user corrections, and feedback history.

### Sample Test Invoices
- The project must include a set of sample invoices for testing and demo purposes, covering a variety of real-world scenarios:
  - **Clean digital PDFs** — well-structured, high-resolution invoices generated digitally (e.g., from accounting software).
  - **Scanned documents** — invoices that have been scanned from paper, with typical scan artifacts.
  - **Low-resolution documents** — poor quality scans or photos with noise, skew, blur, or partial occlusion to test extraction robustness.
  - **Varying formats and vendors** — invoices from different vendors with different layouts, field names, currencies, and line item structures.
  - **Documents with extraneous content** — invoices that include unnecessary information such as marketing text, terms and conditions, handwritten notes, stamps, or unrelated data mixed in with the actual invoice fields.
- Sample invoices should contain realistic but fictional data (vendor names, amounts, dates, line items).
- The samples should stress-test the Extraction Agent's ability to handle diverse, non-standardized, and noisy inputs — filtering out irrelevant content and extracting only the meaningful invoice data.