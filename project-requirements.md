# Human-in-the-Loop Agent Demo — Invoice Processing and Approval Workflow

## Overview

A demo application that showcases a human-in-the-loop multi-agent system for processing invoices. The user uploads an invoice, two agents collaborate to extract and validate the data, and the user reviews, approves, corrects, or rejects the outcome.

## Domain

Invoice processing and approval workflow.

## Requirements

### User Trigger
- The user uploads an invoice (image or PDF) to kick off the workflow.

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

### Human-in-the-Loop
- The user reviews the extracted data, validation results, and confidence scores.
- The user can:
  - **Approve** the invoice for payment.
  - **Reject** the invoice.
  - **Request re-processing** — ask the agents to re-extract or re-validate.
  - **Manually correct** any extracted or validated fields before final approval.
  - **Add new rows or fields** — the user can introduce entirely new line items or data fields that the extraction agent did not capture, since invoices vary widely in structure.

### Feedback Loop and Agent Learning
- Every user correction, addition, or rejection is captured as structured feedback and stored.
- Agents use accumulated feedback to improve over time:
  - **Extraction Agent** — learns from corrections (e.g., if users consistently fix a certain field for a specific vendor, the agent incorporates that pattern into future extractions for that vendor). Past corrections are provided as few-shot examples in the agent's prompt context for similar invoices.
  - **Validation Agent** — learns from approvals and rejections to refine its business rule application and adjust its approval recommendations (e.g., if users repeatedly override a rule violation, the agent adjusts the severity of that rule).
- A feedback memory store records: the original extraction, what the user changed, the vendor, and the invoice format — so agents can retrieve relevant past corrections when processing new invoices.
- Over time, confidence scores should improve for recurring vendors and invoice formats as the agents accumulate more feedback.
- The system should surface a summary of how agent accuracy has improved (e.g., fewer corrections needed over time) to demonstrate the value of the feedback loop.

### Sample Test Invoices
- The project must include a set of sample invoices for testing and demo purposes, covering a variety of real-world scenarios:
  - **Clean digital PDFs** — well-structured, high-resolution invoices generated digitally (e.g., from accounting software).
  - **Scanned documents** — invoices that have been scanned from paper, with typical scan artifacts.
  - **Low-resolution documents** — poor quality scans or photos with noise, skew, or partial occlusion to test extraction robustness.
  - **Varying formats and vendors** — invoices from different vendors with different layouts, field names, currencies, and line item structures.
- Sample invoices should contain realistic but fictional data (vendor names, amounts, dates, line items).
- The samples should stress-test the Extraction Agent's ability to handle diverse, non-standardized inputs.