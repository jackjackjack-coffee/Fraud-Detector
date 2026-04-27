# 🔍 ForensiQ v2 — Project Context for Claude

> **This file is the single source of truth for all Claude/Claude Code work on this project.**
> Read this before writing any code, suggesting any architecture, or generating any UI.
> All conventions defined here are mandatory unless explicitly overridden in the task prompt.

---

## 1. Project Identity

| Field | Detail |
|---|---|
| **Project name** | ForensiQ — Forensic Accounting Fraud Detection System |
| **Owner background** | MAcc (Master of Accounting) + EY Audit Intern |
| **Primary goal** | Portfolio piece demonstrating accounting domain knowledge + engineering ability |
| **Target audience** | Big 4 / forensic accounting recruiters viewing it on LinkedIn |
| **Success metric** | Recruiter spends >60 seconds on the live site and understands what it does without reading a README |

This is not a SaaS product. It does not need onboarding flows, pricing pages, or marketing copy. Every design and engineering decision should be evaluated through the lens of: *"Does this make the project look more credible to an audit professional?"*

---

## 2. Migration: v1 → v2

### What v1 is (current state)
- **Stack**: Python + Streamlit + scikit-learn + Plotly
- **Status**: 4 detectors working, deployed on GitHub
- **Keep from v1**:
  - All algorithm parameters — MAD thresholds (6%/10%), RSF > 3.0, IF contamination=0.05. These match ACFE standards. Do not change without documented justification.
  - Composite Risk Score weighting logic
  - Dark forensic color palette (see Section 6)
  - Privacy-first approach: client-side processing, no data stored by default
- **What v1 gets wrong**:
  - Streamlit looks like a Python notebook to a recruiter, not a shipped product
  - No TypeScript means no visible data modeling — a key signal for accounting + engineering roles
  - Can't integrate external APIs or authentication cleanly

### What v2 is (target state)
- **Stack**: Next.js 14 (App Router) + TypeScript (strict) + shadcn/ui + Tailwind CSS + Supabase
- **Why this stack**: It's the closest thing to what a real fintech audit tool looks like. TypeScript forces explicit data modeling, which proves accounting data structure understanding in the code itself.
- **Current progress**: UI shell generated via v0.dev, being integrated into the repo

---

## 3. Detection Logic — Full Specification

All 9 detectors are organized into 3 layers. v1 detectors are ported to TypeScript. New detectors are added on top.

### Layer 1 — Statistical Analysis
| Detector | What it catches | Threshold | Status |
|---|---|---|---|
| Benford's Law (1st digit) | Fabricated amounts with unnatural first-digit distribution | MAD > 6% marginal, > 10% non-conforming | ✅ Port from v1 |
| Benford's Law (2nd digit) | More sensitive to subtle manipulation than 1st digit alone | Same MAD scale | 🆕 New in v2 |
| Round Number Test | Artificially round amounts ($1,000 / $5,000 / $10,000) suggesting human-chosen rather than natural figures | >15% of transactions ending in 000 | 🆕 New in v2 |

### Layer 2 — Transaction Pattern Analysis
| Detector | What it catches | Threshold | Status |
|---|---|---|---|
| Isolation Forest | Statistically anomalous transaction amounts | contamination=0.05, 200 estimators | ✅ Port from v1 |
| RSF (Relative Size Factor) | One vendor billing far above their historical norm | RSF > 3.0 | ✅ Port from v1 |
| Exact Duplicate Check | Double-billing: same date + amount + vendor | count > 1 | ✅ Port from v1 |
| Fuzzy Duplicate Match | Near-duplicate invoices using slightly altered invoice IDs or vendor name typos | Levenshtein distance < 2 | 🆕 New in v2 |
| Split Invoice Detection | Payments clustered just below approval thresholds (e.g., $9,800 + $9,900 from same vendor same week) | Configurable threshold | 🆕 New in v2 |

### Layer 3 — Text & External Verification
| Detector | What it catches | Source | Status |
|---|---|---|---|
| Description Audit | Vague descriptions: "Consulting", "Misc", "Other", "Services" — common in billing fraud | Keyword dictionary + amount weighting | 🆕 New in v2 |
| SEC EDGAR Cross-reference | Vendor names that don't appear in any SEC filings when they should | SEC EDGAR API (free, no key) | 🆕 New in v2 |
| OFAC Sanctions Check | Vendor names matching US Treasury sanctioned entities list | OFAC SDN list (free, no key) | 🆕 New in v2 |
| Address Verification | Vendor addresses that don't exist or resolve to residential/virtual office locations | Nominatim / OpenStreetMap (free, no key) | 🆕 New in v2 |

**Accounting basis**: ACFE 2024 Report on Occupational Fraud identifies billing fraud as the most frequent asset misappropriation scheme. All detectors map to procedures in AICPA AU-C 240 and PCAOB AS 2401. Reference these on the Methodology page.

---

## 4. External APIs — Approved List

Only these three APIs are approved. All are free, require no credit card, and will not expire or go paid.

| API | Purpose | Auth | Cost |
|---|---|---|---|
| **SEC EDGAR** (`data.sec.gov`) | Cross-reference vendor names against registered US entities and public filings | None — no key required | Free, unlimited |
| **OFAC SDN List** (US Treasury) | Check vendor names against sanctioned entities | None — downloadable XML/JSON | Free, unlimited |
| **Nominatim** (OpenStreetMap) | Address existence verification for ghost vendor detection | None — User-Agent header required | Free, 1 req/sec |

**APIs explicitly rejected:**
| API | Reason |
|---|---|
| Google Maps | Requires billing setup even for free tier |
| BizVerify | Exits beta and goes paid Q3 2026 — will break the demo |
| OpenCorporates | 200 req/month free tier is too low for a meaningful demo |
| Middesk, Cobalt Intelligence, D&B | Enterprise pricing, not appropriate for portfolio |

**Rule**: All external API calls go through Supabase Edge Functions. No credentials in client-side code under any circumstances.

---

## 5. Technical Stack

### Frontend
```
Next.js 14 (App Router)
├── TypeScript — strict mode, zero `any`
├── shadcn/ui — Card, Table, Tabs, Dialog, Badge, Progress
├── Tailwind CSS — dark forensic theme (see Section 6)
├── Recharts — all charts (replaces Plotly from v1)
├── react-dropzone — CSV upload UX
└── papaparse — client-side CSV parsing
```

### Backend
```
Supabase
├── Edge Functions — external API proxy (SEC EDGAR, OFAC, Nominatim)
└── Postgres — optional report saving (user opt-in only, off by default)
```

Supabase Auth is intentionally excluded. This is a public portfolio demo — adding login creates friction for recruiters. The "Save Report" feature uses anonymous sessions only.

### Deployment
- **Production**: Vercel
- **CI**: GitHub Actions — lint + typecheck + unit tests on every push

### Folder Structure
```
forensiq-v2/
├── app/
│   ├── page.tsx                    # Landing / upload screen
│   ├── dashboard/page.tsx          # Main analysis dashboard
│   ├── report/[id]/page.tsx        # Saved report (optional)
│   ├── methodology/page.tsx        # Audit basis, ACFE/AICPA citations
│   └── api/
│       └── verify/route.ts         # External API proxy
├── components/
│   ├── ui/                         # shadcn primitives (auto-generated)
│   ├── charts/
│   │   ├── BenfordChart.tsx
│   │   ├── OutlierMap.tsx
│   │   ├── RsfScatter.tsx
│   │   └── RiskDonut.tsx
│   ├── detectors/                  # Per-detector result panels
│   ├── upload/
│   │   └── CsvUploader.tsx
│   └── layout/
│       └── RiskScoreBadge.tsx
├── lib/
│   ├── fraud-logic/                # ⭐ All detection logic — zero React imports
│   │   ├── benford.ts
│   │   ├── isolation-forest.ts
│   │   ├── rsf.ts
│   │   ├── duplicate.ts
│   │   ├── fuzzy-match.ts
│   │   ├── split-invoice.ts
│   │   ├── description-audit.ts
│   │   ├── composite-score.ts
│   │   └── index.ts
│   ├── types/
│   │   └── transaction.ts          # ⭐ All domain types live here
│   ├── parsers/
│   │   └── csv.ts
│   └── external/
│       ├── edgar.ts
│       ├── ofac.ts
│       └── nominatim.ts
├── public/
│   └── sample-invoices.csv         # Pre-loaded demo data
└── tests/
    └── fraud-logic/                # Unit tests per detector
```

---

## 6. Design System

### Philosophy
Target aesthetic: **Bloomberg Terminal meets forensic audit console.** Dense, data-first, monospaced numbers, no decorative elements. This signals "serious analytical tool" to a recruiter who has spent their career in SAP, IDEA, and ACL. Do not let it drift toward generic SaaS or startup aesthetics.

### Color Palette (mandatory — matches v1)
```css
--bg:        #0a0c0f;   /* Page background */
--surface:   #111418;   /* Card / panel background */
--border:    #1e2530;   /* All borders */
--accent:    #00e5ff;   /* Primary interactive, headings */
--danger:    #ff3b5c;   /* CRITICAL risk, errors */
--warn:      #ffb800;   /* HIGH / MEDIUM risk, warnings */
--ok:        #00e676;   /* LOW risk, success states */
--text:      #cdd6e0;   /* Body text */
--text-dim:  #5a6a7a;   /* Labels, metadata, secondary text */
```

### Typography
- **IBM Plex Mono** — all numbers, metric values, risk scores, tab labels, column headers
- **IBM Plex Sans** — body copy, descriptions, longer text
- Numbers must always render in monospace. A risk score of "73.4" in a proportional font looks like a blog. In IBM Plex Mono it looks like an instrument.

### The 4 Screens

**Screen 1 — Upload** (`/`)
- Drag-and-drop CSV zone, centered
- Column mapping inputs (amount, date, vendor)
- "Try with demo data" button — loads `sample-invoices.csv` instantly, no upload required
- No auth, no signup, no friction whatsoever

**Screen 2 — Dashboard** (`/dashboard`)
- Top row: 5 KPI cards (Portfolio Risk Score, Total Transactions, Anomalies, RSF Flags, Duplicates)
- Large risk score badge (0–100, color-coded by tier) — the most visually prominent element
- Tabbed interface: one tab per detector layer
- Each tab: chart + flagged transactions table + expandable methodology note

**Screen 3 — Methodology** (`/methodology`)
- Static page. No data. Pure credibility signal.
- Explain each detector with its accounting basis in plain English
- Cite: ACFE 2024 Report, AICPA AU-C 240, PCAOB AS 2401, ACFE Fraud Examiners Manual
- This page is disproportionately high-value for recruiting. Most portfolio projects don't have one. Audit professionals will read it carefully.

**Screen 4 — Report** (`/report/[id]`) *(Phase 5, optional)*
- Saved analysis results
- Exportable as PDF in audit workpaper format

### Screenshot optimization
Key dashboard views must look good cropped at **1200×630px** (LinkedIn share card dimensions). Keep the most important information — risk score badge + top chart — visible in the top portion of every screen.

---

## 7. Tooling Decisions

### Approved tools

| Tool | Role | Notes |
|---|---|---|
| **v0.dev** | Generate initial UI layout per screen | Outputs shadcn + Tailwind + Next.js directly into the stack |
| **Claude (this chat)** | Architecture, code review, type design, logic, API questions | |
| **Claude Code** | File-level editing, wiring logic to UI, tests, Figma MCP if needed | Primary development tool |

### Rejected tools

| Tool | Reason |
|---|---|
| **Figma** | Overkill for 4 screens with no co-designer. Add in v3 if needed. |
| **Lovable / Bolt / Replit Agent** | Opinionated full-app output fights the chosen stack. "Built with Lovable" undermines the portfolio signal. |
| **Tremor** | Redundant with Recharts — removed to reduce bundle size |
| **Plotly** | Replaced by Recharts (React-native, SSR compatible) |

### v0.dev usage rules

v0 is good at visual layout. It is bad at domain specificity. Always use detailed prompts.

**Prompt template for v0:**
```
Dark forensic accounting dashboard in Next.js with shadcn/ui and Tailwind CSS.
[Describe the specific screen and its data]
Color palette: bg #0a0c0f, surface #111418, accent #00e5ff, danger #ff3b5c, warn #ffb800, ok #00e676, text #cdd6e0.
Typography: IBM Plex Mono for all numbers and labels, IBM Plex Sans for body copy.
[List the specific components needed: charts, tables, badges, metrics]
No marketing copy. No pricing. No onboarding. Data-dense analyst tool aesthetic.
```

**After generating from v0 — mandatory steps:**
1. Copy code into repo immediately
2. Replace ALL mock data with real TypeScript types from `lib/types/transaction.ts`
3. Replace all generic SaaS labels with audit terminology (see Section 8)
4. Never ship v0 output verbatim — the generic aesthetic is recognizable

### Build sequence
```
1. Paper sketch (30 min)
   → What lives on each of the 4 screens

2. v0.dev per screen (~1–2 hrs total)
   → Use domain-specific prompt template

3. Copy into repo, run locally

4. Claude Code (bulk of time)
   → Wire lib/fraud-logic/* to UI
   → Replace mock data with real types
   → Add accounting terminology
   → Build Methodology page
   → Connect external APIs via Edge Functions

5. Test with sample-invoices.csv
   → All injected fraud patterns must be caught

6. Deploy to Vercel
```

---

## 8. Domain Language

Use audit terminology consistently. This is the single highest-ROI thing that separates this project from generic portfolio work.

| ❌ Never use | ✅ Always use |
|---|---|
| Users | Auditors / Reviewers |
| Dashboard | Audit Dashboard / Engagement View |
| Total Revenue | Portfolio Risk Score |
| Active Users | Flagged Transactions |
| Items | Transactions / Invoices / Ledger Entries |
| Issues found | Exceptions noted / Red flags identified |
| Settings | Engagement Parameters |
| Upload file | Import ledger / Upload invoice data |
| Error | Exception |
| Check | Procedure |
| Results | Findings |

Apply in: UI labels, chart titles, table column headers, button text, page titles, README, JSDoc comments.

---

## 9. Type Definitions

All domain types live in `lib/types/transaction.ts`. No exceptions.

```typescript
// RULE: No `any`. External data enters as `unknown`, narrowed via type guards.

export interface RawTransaction {
  invoice_id: string;
  date: string;           // ISO 8601 — YYYY-MM-DD
  vendor: string;
  category?: string;
  amount: number;         // Always positive. Strip negatives on parse.
  description?: string;
  approved_by?: string;
}

export interface AnalyzedTransaction extends RawTransaction {
  // Layer 1 — Statistical
  benford_first_digit: number;
  benford_second_digit: number;
  is_round_number: boolean;

  // Layer 2 — Pattern
  isolation_score: number;        // 0–100, higher = more suspicious
  is_outlier: boolean;
  rsf: number;
  rsf_flag: boolean;
  rsf_zscore: number;
  is_exact_duplicate: boolean;
  fuzzy_dup_group: string | null; // group ID if part of a fuzzy cluster
  is_split_invoice: boolean;

  // Layer 3 — Text & External
  description_risk: number;       // 0–100
  edgar_verified: boolean | null; // null = not yet checked
  ofac_hit: boolean | null;
  address_valid: boolean | null;

  // Composite
  composite_risk: number;         // 0–100
  risk_tier: RiskTier;
  triggered_detectors: DetectorName[];
}

export type RiskTier = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type DetectorName =
  | 'BENFORD_1ST'
  | 'BENFORD_2ND'
  | 'ROUND_NUMBER'
  | 'ISOLATION_FOREST'
  | 'RSF'
  | 'EXACT_DUPLICATE'
  | 'FUZZY_DUPLICATE'
  | 'SPLIT_INVOICE'
  | 'DESCRIPTION_AUDIT'
  | 'EDGAR_UNVERIFIED'
  | 'OFAC_HIT'
  | 'ADDRESS_INVALID';

export interface BenfordResult {
  observed: Record<number, number>;
  expected: Record<number, number>;
  chi_square: number;
  mad: number;
  conformity: 'ACCEPTABLE' | 'MARGINAL' | 'NON_CONFORMING';
  total_records: number;
}

export interface PortfolioRiskSummary {
  score: number;
  tier: RiskTier;
  outlier_rate: number;
  rsf_flag_rate: number;
  duplicate_rate: number;
  benford_mad: number;
  total_transactions: number;
  flagged_transactions: number;
  estimated_exposure: number;     // sum of flagged transaction amounts
}
```

---

## 10. Coding Conventions

### Type safety (absolute)
- `any` is banned
- External/unknown data uses `unknown` + type guards
- All function signatures have explicit return types

### Modularity (absolute)
- `lib/fraud-logic/*` — zero React imports. Must run in Node without a browser.
- One file per detector. `composite-score.ts` imports and combines all of them.
- Order of operations when adding a detector: `DetectorName` type → detector file → composite weighting → UI tab

### JSDoc on every detector function
Document the accounting meaning. Recruiters who are CPAs will read this.

```typescript
/**
 * Relative Size Factor: transaction amount ÷ median amount for the same vendor.
 *
 * Accounting basis: A $100k payment is suspicious from a $10k/transaction
 * office supply vendor — but normal from a law firm. RSF normalizes for
 * vendor-specific pricing to surface disproportionate charges.
 *
 * Red flag: Vendor historically billing $5k/month submits a $75k invoice
 * → RSF = 15 → immediate escalation warranted.
 *
 * Standard: ACFE Fraud Examiners Manual — Billing Schemes chapter.
 * Threshold: RSF > 3.0 triggers flag.
 */
export function computeRsf(
  transactions: RawTransaction[]
): Pick<AnalyzedTransaction, 'rsf' | 'rsf_flag' | 'rsf_zscore'>[] { ... }
```

### Privacy (mandatory, inherited from v1)
- Default mode: 100% client-side, zero server storage
- "Save Report": opt-in only, requires explicit user action
- State this clearly in UI and README
- Never log uploaded CSV content anywhere

### File path references
Always format as `lib/fraud-logic/rsf.ts:28` when referencing code locations.

---

## 11. Implementation Roadmap

### Phase 1 — Logic Foundation (Week 1)
- [ ] `lib/types/transaction.ts` — full type system as defined above
- [ ] `lib/parsers/csv.ts` — parser with column mapping
- [ ] Port v1 detectors to TypeScript: `benford.ts`, `isolation-forest.ts`, `rsf.ts`, `duplicate.ts`
- [ ] `composite-score.ts` — combine all signals, assign risk tiers
- [ ] Unit tests for 4 ported detectors using v1's labeled sample data as fixture

### Phase 2 — UI Integration (Week 2)
- [ ] Generate all 4 screens in v0.dev using domain-specific prompts
- [ ] Copy into repo, replace all mock data with real types
- [ ] Wire 4 detectors to dashboard UI
- [ ] "Try with demo data" button — preloads `sample-invoices.csv` in one click
- [ ] Recharts implementations of all 4 core charts

### Phase 3 — New Detectors (Week 3)
- [ ] `fuzzy-match.ts` — Levenshtein on invoice_id and vendor name
- [ ] `split-invoice.ts` — threshold clustering detection
- [ ] `description-audit.ts` — keyword dictionary + scoring
- [ ] 2nd digit Benford + Round Number test added to `benford.ts`

### Phase 4 — External Verification (Week 4)
- [ ] `lib/external/edgar.ts` — SEC EDGAR company name search
- [ ] `lib/external/ofac.ts` — OFAC SDN list download + fuzzy name matching
- [ ] `lib/external/nominatim.ts` — address geocoding (respect 1 req/sec limit)
- [ ] Supabase Edge Function wrapping all three external calls

### Phase 5 — Polish & Launch (Week 5)
- [ ] `app/methodology/page.tsx` — full audit basis with ACFE/AICPA/PCAOB citations
- [ ] PDF export in audit workpaper format
- [ ] GitHub README v2 with architecture diagram
- [ ] 30-second demo video for LinkedIn
- [ ] Archive v1 Streamlit repo with note pointing to v2

---

## 12. Definition of Done

Ready to post on LinkedIn when all of these pass:

- [ ] All 9 detectors working with passing unit tests
- [ ] Upload CSV → full analysis in under 30 seconds
- [ ] "Try with demo data" works in one click, no upload needed
- [ ] Methodology page live with ACFE, AICPA AU-C 240, PCAOB AS 2401 citations
- [ ] Zero `any` in TypeScript, zero ESLint warnings
- [ ] All charts readable on mobile
- [ ] Dashboard looks good cropped at 1200×630px
- [ ] Lighthouse 90+ on Performance and Accessibility
- [ ] README explains the accounting basis in plain English with an architecture diagram

---

## 13. TL;DR for Claude

1. **Types first, logic second, UI last.** Define the interface → write the pure function → connect to UI. Never skip steps.
2. **Document the accounting meaning.** Every detector gets a JSDoc block with the fraud pattern it catches and the ACFE/AICPA standard it maps to.
3. **v1 algorithm parameters are trusted.** MAD thresholds, RSF=3.0, contamination=0.05 are ACFE-validated. Don't change without a documented accounting reason.
4. **Replace v0 mock data immediately.** No placeholder data survives in the repo.
5. **No API credentials in client code.** EDGAR and Nominatim need no keys. If anything ever needs a key, it goes through Supabase Edge Functions.
6. **Use audit terminology everywhere.** Exceptions, engagements, ledger entries — not errors, dashboards, items.
7. **Always specify file paths** in the format `lib/fraud-logic/rsf.ts:28`.

---

*Last updated: 2026-04-26 · Full English rewrite — tooling, API, and design decisions finalized*
