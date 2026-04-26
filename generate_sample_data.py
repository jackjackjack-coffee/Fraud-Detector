"""
generate_sample_data.py
=======================
Generates a realistic dummy invoice dataset with INJECTED fraud patterns
for testing the ForensiQ Fraud Detection System.

Fraud patterns injected:
  1. Benford violation  — round-number invoice clustering (9x, 49x, 99x patterns)
  2. Outlier amounts    — 3 extremely large payments to a shell company
  3. RSF violations     — single vendor suddenly billed 10× their normal rate
  4. Duplicate invoices — exact same date/amount/vendor triplets
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ─── CONFIG ────────────────────────────────────
N_NORMAL    = 950    # clean transactions
N_FRAUD     = 50     # injected fraud transactions
OUTPUT_PATH = "sample_invoices.csv"

# ─── MASTER LISTS ──────────────────────────────
VENDORS_LEGIT = [
    "Apex Office Supplies",
    "Titan Logistics Co.",
    "Meridian IT Solutions",
    "Blue Ridge Consulting",
    "Summit Facilities Mgmt",
    "Coastal Marketing Group",
    "Inland Legal Services",
    "NovaTech Systems",
    "Riverfront Catering",
    "Greenway Staffing",
]

VENDORS_SHELL = [
    "Alpha Business Services LLC",   # shell company for large fraud
    "Delta Management Group",        # RSF fraud vendor
]

CATEGORIES = [
    "IT Services", "Consulting", "Office Supplies",
    "Facilities", "Marketing", "Legal", "Catering",
    "Staffing", "Logistics", "Software Licenses"
]

START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2024, 12, 31)


def random_date(start: datetime, end: datetime) -> str:
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).strftime("%Y-%m-%d")


def random_amount_normal() -> float:
    """Naturally distributed invoice amounts (will conform to Benford's Law)."""
    choice = random.random()
    if choice < 0.4:
        return round(np.random.lognormal(mean=7.5, sigma=0.9), 2)   # ~$1k–$10k range
    elif choice < 0.7:
        return round(np.random.lognormal(mean=9.0, sigma=0.7), 2)   # ~$5k–$50k
    else:
        return round(np.random.lognormal(mean=6.0, sigma=1.0), 2)   # small invoices


# ─── GENERATE CLEAN TRANSACTIONS ───────────────
records = []
for i in range(N_NORMAL):
    vendor = random.choice(VENDORS_LEGIT)
    amt    = random_amount_normal()
    records.append({
        "invoice_id":  f"INV-{10000 + i}",
        "date":        random_date(START_DATE, END_DATE),
        "vendor":      vendor,
        "category":    random.choice(CATEGORIES),
        "amount":      amt,
        "approved_by": random.choice(["J.Kim", "S.Park", "M.Lee", "C.Choi"]),
        "fraud_label": "CLEAN"       # ground truth (remove before production)
    })


# ─── FRAUD PATTERN 1: BENFORD VIOLATION ────────
# Invoice amounts clustered just under approval thresholds ($9,999 / $4,999 / $999)
for i in range(12):
    threshold = random.choice([9999, 4999, 999])
    amt = threshold - random.uniform(0.01, 15.00)
    records.append({
        "invoice_id":  f"INV-BLAW-{i:04d}",
        "date":        random_date(START_DATE, END_DATE),
        "vendor":      random.choice(VENDORS_LEGIT),
        "category":    "Consulting",
        "amount":      round(amt, 2),
        "approved_by": "J.Kim",
        "fraud_label": "BENFORD_VIOLATION"
    })


# ─── FRAUD PATTERN 2: OUTLIER (SHELL COMPANY) ──
# 3 exceptionally large payments to a shell company
for i in range(5):
    records.append({
        "invoice_id":  f"INV-SHELL-{i:04d}",
        "date":        random_date(START_DATE, END_DATE),
        "vendor":      "Alpha Business Services LLC",
        "category":    "Consulting",
        "amount":      round(random.uniform(450_000, 890_000), 2),
        "approved_by": "J.Kim",
        "fraud_label": "OUTLIER_SHELL"
    })


# ─── FRAUD PATTERN 3: RSF VIOLATION ───────────
# Delta Management Group normally bills ~$5k, suddenly billed 10-15× that
normal_delta_invoices = 15
for i in range(normal_delta_invoices):
    records.append({
        "invoice_id":  f"INV-DLT-N{i:04d}",
        "date":        random_date(START_DATE, END_DATE),
        "vendor":      "Delta Management Group",
        "category":    "Management",
        "amount":      round(random.uniform(4_000, 6_500), 2),
        "approved_by": "S.Park",
        "fraud_label": "CLEAN"
    })
for i in range(8):   # inflated invoices
    records.append({
        "invoice_id":  f"INV-DLT-F{i:04d}",
        "date":        random_date(datetime(2024, 9, 1), END_DATE),
        "vendor":      "Delta Management Group",
        "category":    "Management",
        "amount":      round(random.uniform(58_000, 95_000), 2),
        "approved_by": "S.Park",
        "fraud_label": "RSF_VIOLATION"
    })


# ─── FRAUD PATTERN 4: DUPLICATE INVOICES ───────
# Exact same date/amount/vendor — double billing scheme
dup_templates = [
    ("2024-03-15", "Meridian IT Solutions",   12_450.00),
    ("2024-06-22", "Titan Logistics Co.",     8_799.99),
    ("2024-09-10", "Apex Office Supplies",    2_350.50),
    ("2024-11-05", "NovaTech Systems",        34_200.00),
    ("2024-08-30", "Blue Ridge Consulting",   17_000.00),
]
dup_counter = 0
for date, vendor, amount in dup_templates:
    for copy_num in range(2):   # each appears twice
        records.append({
            "invoice_id":  f"INV-DUP-{dup_counter:04d}",
            "date":        date,
            "vendor":      vendor,
            "category":    "Various",
            "amount":      amount,
            "approved_by": "M.Lee",
            "fraud_label": "DUPLICATE"
        })
        dup_counter += 1


# ─── SHUFFLE & EXPORT ──────────────────────────
df = pd.DataFrame(records)
df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

# Remove ground-truth label for realistic test  
df_no_label = df.drop(columns=["fraud_label"])

df_no_label.to_csv(OUTPUT_PATH, index=False)
df.to_csv("sample_invoices_labeled.csv", index=False)  # labeled version for validation

# ─── SUMMARY ───────────────────────────────────
total = len(df)
fraud_counts = df["fraud_label"].value_counts()

print("=" * 55)
print("  ForensiQ — Sample Dataset Generated")
print("=" * 55)
print(f"  Output (unlabeled): {OUTPUT_PATH}")
print(f"  Output (labeled):   sample_invoices_labeled.csv")
print(f"  Total records:      {total:,}")
print()
print("  Injected Fraud Patterns:")
for label, count in fraud_counts.items():
    tag = "" if label == "CLEAN" else "⚠️ "
    print(f"    {tag}{label:<22} {count:>4} records")
print()
print("  Fraud rate:   ", f"{(1 - fraud_counts.get('CLEAN', 0)/total)*100:.1f}%")
print("=" * 55)
print("  Upload 'sample_invoices.csv' to ForensiQ to test.")
print("=" * 55)
