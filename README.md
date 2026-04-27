[README.md](https://github.com/user-attachments/files/27111845/README.md)
# 🔍 ForensiQ — Forensic Accounting Fraud Detection System

> A production-grade fraud detection web application built with Python & Streamlit.
> Detects financial anomalies using four independent forensic accounting techniques.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate sample data with injected fraud
python generate_sample_data.py

# 3. Run the app
streamlit run app.py
```

Upload `sample_invoices.csv` and explore the results.

---

## 🔬 Core Detection Algorithms

### 1. Benford's Law Analysis
**What it does**: Compares the first-digit distribution of all invoice amounts against the
theoretical Benford distribution (P(d) = log₁₀(1 + 1/d)).

**Why it works**: Natural financial data follows Benford's Law. Fraudsters fabricating
invoices tend to choose "random-looking" numbers that produce a *uniform* distribution —
a statistically detectable deviation.

**Implementation**:
- Extract leading digit from each transaction
- Compute Mean Absolute Deviation (MAD) vs. expected frequencies
- Chi-square test for conformity
- Flag datasets with MAD > 6% as marginal; > 10% as non-conforming

**Red flag example**: Unusually high frequency of "9" as first digit indicates amounts
clustered just below approval thresholds ($9,999, $9,500, etc.) — a classic **rounding down** scheme.

---

### 2. Isolation Forest (ML Outlier Detection)
**What it does**: Uses scikit-learn's `IsolationForest` to score each transaction by how
"easy" it is to isolate from the rest of the data.

**Why it works**: Anomalous transactions are structurally different — fewer random splits
are needed to isolate them. A contamination rate of ~5% is typical for corporate ledgers.

**Implementation**:
- Log-transform amounts to handle right-skewed financial distributions
- Standardize with `StandardScaler`
- IsolationForest with 200 estimators for stability
- Normalize anomaly scores to 0–100 risk scale

**Red flag example**: A $750,000 payment to a consulting firm when all similar
payments are in the $5k–$20k range will score near 100.

---

### 3. Relative Size Factor (RSF) Analysis
**What it does**: RSF = Transaction Amount ÷ Median Amount for the same vendor.

**Why it works**: It normalizes for vendor-specific pricing. A $100k payment is suspicious
from a $10k/transaction office supply vendor — but normal from a law firm.

**Implementation**:
- Group by vendor, compute median and standard deviation
- Calculate RSF and Z-score per transaction
- Flag RSF > 3.0 (3× median) as anomalous

**Red flag example**: A vendor historically billing $5,000/month suddenly submits
a $75,000 invoice → RSF = 15 → immediate escalation.

---

### 4. Duplicate Transaction Detection
**What it does**: Flags any set of transactions sharing identical date + amount + vendor.

**Why it works**: Duplicate invoices are one of the most common billing fraud schemes.
The ACFE estimates organizations lose ~5% of revenue to fraud annually, with billing
fraud as the #1 asset misappropriation scheme.

**Implementation**:
- Groupby on [date, vendor, amount]
- Flag all members of groups with count > 1
- Surface estimated total overpayment exposure

**Red flag example**: Invoice INV-1042 and INV-1178 both charge $12,450.00
to "Meridian IT" on 2024-03-15 — one is likely fraudulent.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  User Browser (Streamlit Frontend)                      │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Benford │  │    IF    │  │   RSF    │  │  Dupes  │ │
│  │ Analysis│  │ Outliers │  │ Analysis │  │  Check  │ │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       └────────────┴──────────────┴──────────────┘      │
│                    Composite Risk Score (0–100)          │
│                    ↓                                     │
│              Plotly Visualizations                       │
│              Annotated CSV Export                        │
└─────────────────────────────────────────────────────────┘
         ↑ CSV Upload (in-memory only, never stored)
```

## 🔒 Security & Privacy
- **No data storage**: All uploaded data is processed in Pandas DataFrames in RAM and
  discarded when the session ends. Nothing is written to disk.
- **No external API calls**: 100% offline processing.

## 📦 Tech Stack
| Component | Library |
|---|---|
| App framework | Streamlit |
| ML detection | scikit-learn (IsolationForest) |
| Data processing | Pandas, NumPy |
| Visualization | Plotly |

## 📝 LinkedIn Caption Template

> 🔍 Built a **Forensic Accounting Fraud Detection System** using Python & Streamlit!
>
> This tool applies 4 independent detection methods used by real forensic accountants:
> • 📊 **Benford's Law** — statistical first-digit analysis
> • 🤖 **Isolation Forest** — ML-based anomaly detection
> • 📐 **RSF Analysis** — vendor-normalized transaction sizing
> • 🔁 **Duplicate Check** — double-billing identification
>
> Zero cloud cost — runs free on Streamlit Community Cloud.
> No data is stored — everything processes in memory only.
>
> #ForensicAccounting #FraudDetection #Python #DataScience #Accounting #FinTech
