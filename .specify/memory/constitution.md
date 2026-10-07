<!--
Sync Impact Report
Version change: uninitialized -> 1.0.0
Modified principles: none; this establishes the five principles in the initial scaffold.
Added sections: Financial and Data Protection; API and Client Architecture.
Removed sections: none.
Follow-up TODO: Record the original ratification date.
-->

# Simple Bank Constitution

## Core Principles

### I. Exact Monetary Arithmetic
All monetary values MUST use Decimal and MUST be rounded to two decimal places. Tests
MUST verify monetary representation and rounding behavior. Exact decimal arithmetic
avoids binary floating-point errors in financial calculations.

### II. Account Data Confidentiality
Logs and other operational output MUST NOT contain full account numbers. When an
account number is displayed, only its last four digits may be shown, prefixed with
`XXXX` (for example, `XXXX1234`). Tests MUST verify masking wherever account numbers
can enter output. This limits exposure of sensitive account identifiers.

### III. Every Rule Has a Test
Every rule in this constitution and in product requirements MUST have at least one
automated test that verifies it. Changes to any rule MUST update or add the relevant
test. Tests make requirements observable and help prevent accidental rule changes.

### IV. Versioned API Contract
All application API routes MUST begin with `/api/v1`. Tests MUST verify route
versioning and the externally visible API contract. A stable, explicit prefix keeps
the supported API boundary identifiable.

### V. React Web Client Uses the API
The customer web app MUST use React with Vite and MUST communicate with application
services only through the `/api/v1` API. It MUST NOT bypass that API to access backend
services or data directly. Tests MUST verify this integration boundary. Keeping a
single client-to-service boundary makes the API contract enforceable.

## Financial and Data Protection

Transfer behavior MUST follow `docs/requirement-fund-transfer.md`, which is the
source of truth for documented transfer requirements. No implementation or test
MUST invent, weaken, or silently change financial rules defined there. Every such
rule MUST be covered by an automated test, as required by Principle III.

## API and Client Architecture

The `/api/v1` prefix and React/Vite client requirements in Principles IV and V apply
to all customer-facing application development. Tests MUST cover API route prefixes
and verify that the customer web app uses only this API boundary.

## Governance

Amendments MUST be proposed as changes to this constitution and reviewed by project
maintainers before adoption. An amendment MUST state its rationale and assess its
impact on existing rules and tests.

The version follows semantic versioning: MAJOR for backward-incompatible governance
changes, MINOR for new or materially expanded principles or sections, and PATCH for
clarifications or non-semantic refinements. The version and last-amended date MUST
be updated with every adopted amendment.

Project changes MUST be reviewed for compliance with applicable principles and
documented requirements. Reviews MUST verify that each affected rule has a passing
automated test. Any proposed exception MUST be documented and approved by project
maintainers before adoption.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): original adoption date unknown | **Last Amended**: 2026-10-06
