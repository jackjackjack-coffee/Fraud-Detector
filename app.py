"""
Forensic Accounting Fraud Detection System
==========================================
A Streamlit application for detecting financial fraud using:
- Benford's Law Analysis
- Isolation Forest (Outlier Detection)
- Relative Size Factor (RSF) Analysis
- Duplicate Transaction Detection
"""

import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ForensiQ · Fraud Detection",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
#  CUSTOM CSS  (dark forensic theme)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

:root {
    --bg:        #0a0c0f;
    --surface:   #111418;
    --border:    #1e2530;
    --accent:    #00e5ff;
    --danger:    #ff3b5c;
    --warn:      #ffb800;
    --ok:        #00e676;
    --text:      #cdd6e0;
    --text-dim:  #5a6a7a;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}

/* Metrics */
[data-testid="metric-container"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
}
[data-testid="metric-container"] label { color: var(--text-dim) !important; font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; letter-spacing: 0.12em; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: var(--accent) !important; font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 1px solid var(--border); background: transparent; }
.stTabs [data-baseweb="tab"] { background: transparent; color: var(--text-dim); border: none; border-bottom: 2px solid transparent; padding: 10px 24px; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; letter-spacing: 0.08em; }
.stTabs [aria-selected="true"] { color: var(--accent) !important; border-bottom-color: var(--accent) !important; background: transparent !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 8px; }

/* Buttons */
.stButton > button {
    background: transparent;
    border: 1px solid var(--accent);
    color: var(--accent);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    transition: all 0.2s;
}
.stButton > button:hover { background: var(--accent); color: var(--bg); }

/* Alerts */
.alert-danger { background: rgba(255,59,92,0.08); border-left: 3px solid var(--danger); padding: 12px 16px; border-radius: 4px; margin: 8px 0; font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; }
.alert-warn   { background: rgba(255,184,0,0.08);  border-left: 3px solid var(--warn);   padding: 12px 16px; border-radius: 4px; margin: 8px 0; font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; }
.alert-ok     { background: rgba(0,230,118,0.08);  border-left: 3px solid var(--ok);     padding: 12px 16px; border-radius: 4px; margin: 8px 0; font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; }

/* Score badge */
.score-badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 3.5rem;
    font-weight: 600;
    padding: 12px 28px;
    border-radius: 12px;
    border: 2px solid;
    margin: 8px 0;
}

/* Section headers */
h2, h3 { font-family: 'IBM Plex Mono', monospace !important; letter-spacing: -0.02em; }

/* Upload area */
[data-testid="stFileUploader"] {
    border: 1px dashed var(--border);
    border-radius: 8px;
    padding: 8px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  BENFORD'S LAW
# ─────────────────────────────────────────────
BENFORD_EXPECTED = {
    d: np.log10(1 + 1/d) * 100 for d in range(1, 10)
}

def get_first_digit(value):
    """Extract the first significant digit from a number."""
    try:
        s = str(abs(float(value))).replace('.', '').lstrip('0')
        return int(s[0]) if s else None
    except:
        return None

def benford_analysis(amounts: pd.Series) -> dict:
    """
    Compare first-digit distribution against Benford's Law.
    Returns observed %, expected %, chi-square stat, and MAD score.
    
    회계적 의미: 자연발생적 숫자(매출, 비용 등)는 벤포드 법칙을 따름.
    인위적으로 조작된 금액(특히 특정 승인 한도 아래로 의도적으로 설정한 금액)은
    특정 첫 자릿수(예: 9)에서 비정상적으로 높은 빈도를 보임.
    """
    digits = amounts.apply(get_first_digit).dropna()
    observed_counts = digits.value_counts().reindex(range(1, 10), fill_value=0)
    total = observed_counts.sum()
    
    observed_pct = (observed_counts / total * 100).to_dict()
    
    # Chi-square test
    chi2 = 0
    for d in range(1, 10):
        obs = observed_pct[d]
        exp = BENFORD_EXPECTED[d]
        chi2 += ((obs - exp) ** 2) / exp if exp > 0 else 0
    
    # Mean Absolute Deviation
    mad = np.mean([abs(observed_pct[d] - BENFORD_EXPECTED[d]) for d in range(1, 10)])
    
    # Conformity assessment
    if mad < 6:
        conformity = "ACCEPTABLE"
    elif mad < 10:
        conformity = "MARGINAL"
    else:
        conformity = "NON-CONFORMING"
    
    return {
        "observed": observed_pct,
        "expected": BENFORD_EXPECTED,
        "chi2": chi2,
        "mad": mad,
        "conformity": conformity,
        "total_records": total
    }


# ─────────────────────────────────────────────
#  ISOLATION FOREST  (Outlier Detection)
# ─────────────────────────────────────────────
def isolation_forest_analysis(df: pd.DataFrame, amount_col: str, 
                               contamination: float = 0.05) -> pd.DataFrame:
    """
    Use Isolation Forest to flag statistically anomalous transactions.
    
    회계적 의미: 정상 거래는 비슷한 금액대에 군집하지만,
    부정 거래는 비정상적으로 크거나 작은 금액을 가짐.
    Isolation Forest는 '고립하기 쉬운' 데이터 포인트를 이상치로 판단.
    """
    df = df.copy()
    amounts = df[[amount_col]].copy()
    
    # Add log-transform for better separation on skewed financial data
    amounts['log_amount'] = np.log1p(amounts[amount_col].abs())
    
    scaler = StandardScaler()
    X = scaler.fit_transform(amounts[['log_amount']])
    
    clf = IsolationForest(contamination=contamination, random_state=42, n_estimators=200)
    df['anomaly_score'] = clf.decision_function(X)
    df['is_outlier'] = clf.predict(X) == -1
    
    # Normalize score to 0-100 risk scale (higher = more suspicious)
    s = df['anomaly_score']
    df['risk_score'] = ((s.min() - s) / (s.min() - s.max()) * 100).clip(0, 100)
    
    return df


# ─────────────────────────────────────────────
#  RELATIVE SIZE FACTOR  (RSF)
# ─────────────────────────────────────────────
def rsf_analysis(df: pd.DataFrame, amount_col: str, vendor_col: str) -> pd.DataFrame:
    """
    RSF = Transaction Amount / Median Amount for that Vendor.
    RSF > 3 is typically flagged for review.
    
    회계적 의미: 특정 거래처와의 거래 평균 대비 비정상적으로 큰 금액을 찾아냄.
    예) 평소 100만원을 거래하는 업체에 갑자기 1,000만원 지급 → RSF=10 (고위험)
    """
    df = df.copy()
    vendor_median = df.groupby(vendor_col)[amount_col].transform('median')
    vendor_std    = df.groupby(vendor_col)[amount_col].transform('std').fillna(1)
    
    df['rsf'] = df[amount_col] / vendor_median.replace(0, np.nan)
    df['rsf_flag'] = df['rsf'] > 3.0
    df['rsf_zscore'] = (df[amount_col] - df.groupby(vendor_col)[amount_col].transform('mean')) / vendor_std
    
    return df


# ─────────────────────────────────────────────
#  DUPLICATE CHECK
# ─────────────────────────────────────────────
def duplicate_check(df: pd.DataFrame, 
                     date_col: str, amount_col: str, vendor_col: str) -> pd.DataFrame:
    """
    Flag records sharing the same date + amount + vendor.
    
    회계적 의미: 동일 날짜·금액·거래처의 중복 지급은 
    이중 청구(Double Billing) 또는 유령 거래처(Ghost Vendor) 사기의 주요 지표.
    """
    df = df.copy()
    dupe_key = [date_col, amount_col, vendor_col]
    df['dup_count'] = df.groupby(dupe_key)[date_col].transform('count')
    df['is_duplicate'] = df['dup_count'] > 1
    return df


# ─────────────────────────────────────────────
#  COMPOSITE RISK SCORE
# ─────────────────────────────────────────────
def compute_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    """Combine all signals into one 0-100 risk score per transaction."""
    df = df.copy()
    
    score = pd.Series(0.0, index=df.index)
    
    if 'risk_score' in df.columns:
        score += df['risk_score'] * 0.4          # 40% weight — IF outlier
    if 'rsf_flag' in df.columns:
        score += df['rsf_flag'].astype(float) * 30  # 30% weight — RSF flag
    if 'rsf_zscore' in df.columns:
        score += df['rsf_zscore'].clip(0, 5) / 5 * 15  # 15% — z-score magnitude
    if 'is_duplicate' in df.columns:
        score += df['is_duplicate'].astype(float) * 15  # 15% — duplicate flag
    
    df['composite_risk'] = score.clip(0, 100)
    df['risk_tier'] = pd.cut(df['composite_risk'], 
                              bins=[-1, 30, 60, 80, 101],
                              labels=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
    return df


# ─────────────────────────────────────────────
#  CHART HELPERS  (Plotly, dark theme)
# ─────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='IBM Plex Mono', color='#cdd6e0', size=11),
    margin=dict(l=40, r=20, t=50, b=40),
    xaxis=dict(gridcolor='#1e2530', linecolor='#1e2530'),
    yaxis=dict(gridcolor='#1e2530', linecolor='#1e2530'),
)

def chart_benford(result: dict) -> go.Figure:
    digits = list(range(1, 10))
    obs = [result['observed'].get(d, 0) for d in digits]
    exp = [result['expected'][d] for d in digits]
    
    fig = go.Figure()
    fig.add_bar(x=digits, y=exp, name='Expected (Benford)',
                marker_color='rgba(0,229,255,0.25)',
                marker_line_color='#00e5ff', marker_line_width=1.5)
    fig.add_bar(x=digits, y=obs, name='Observed',
                marker_color='rgba(255,59,92,0.6)',
                marker_line_color='#ff3b5c', marker_line_width=1.5)
    fig.add_scatter(x=digits, y=exp, mode='lines+markers',
                    line=dict(color='#00e5ff', width=2, dash='dot'),
                    marker=dict(size=6), name='Benford Curve', showlegend=False)
    
    fig.update_layout(**PLOT_LAYOUT,
        title=dict(text="Benford's Law — First Digit Distribution", font_size=13),
        barmode='overlay', bargap=0.25,
        xaxis_title="First Digit", yaxis_title="Frequency (%)",
        legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='#1e2530')
    )
    return fig


def chart_outliers(df: pd.DataFrame, amount_col: str) -> go.Figure:
    normal  = df[~df['is_outlier']]
    outlier = df[df['is_outlier']]
    
    fig = go.Figure()
    fig.add_scatter(x=normal.index, y=normal[amount_col], mode='markers',
                    name='Normal', marker=dict(color='#00e5ff', size=5, opacity=0.6))
    fig.add_scatter(x=outlier.index, y=outlier[amount_col], mode='markers',
                    name='Anomaly', marker=dict(color='#ff3b5c', size=9,
                    symbol='x', line=dict(width=2)))
    fig.update_layout(**PLOT_LAYOUT,
        title=dict(text="Isolation Forest — Transaction Anomaly Map", font_size=13),
        xaxis_title="Transaction Index", yaxis_title="Amount",
        legend=dict(bgcolor='rgba(0,0,0,0)')
    )
    return fig


def chart_rsf_vendors(df: pd.DataFrame, amount_col: str, vendor_col: str) -> go.Figure:
    top_vendors = (df.groupby(vendor_col)[amount_col]
                     .sum().nlargest(15).index.tolist())
    sub = df[df[vendor_col].isin(top_vendors)]
    
    colors = sub['rsf_flag'].map({True: '#ff3b5c', False: '#00e5ff'})
    
    fig = go.Figure()
    fig.add_box(x=sub[vendor_col], y=sub[amount_col],
                boxpoints='all', jitter=0.4,
                marker=dict(color=colors.tolist(), size=5, opacity=0.7),
                line_color='#2a3444', fillcolor='rgba(0,229,255,0.06)',
                name='Transactions')
    fig.update_layout(**PLOT_LAYOUT,
        title=dict(text="RSF Analysis — Amount Distribution by Vendor (Top 15)", font_size=13),
        xaxis_tickangle=-35, xaxis_title="Vendor", yaxis_title="Amount",
        showlegend=False
    )
    return fig


def chart_risk_distribution(df: pd.DataFrame) -> go.Figure:
    tier_colors = {'LOW': '#00e676', 'MEDIUM': '#ffb800', 
                   'HIGH': '#ff7043', 'CRITICAL': '#ff3b5c'}
    counts = df['risk_tier'].value_counts()
    
    fig = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.62,
        marker_colors=[tier_colors.get(t, '#888') for t in counts.index],
        textfont=dict(family='IBM Plex Mono', size=11),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
    ))
    fig.update_layout(**PLOT_LAYOUT,
        title=dict(text="Risk Tier Distribution", font_size=13),
        showlegend=True,
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(family='IBM Plex Mono'))
    )
    return fig


# ─────────────────────────────────────────────
#  FULL ANALYSIS PIPELINE
# ─────────────────────────────────────────────
def run_analysis(df: pd.DataFrame, amount_col: str, 
                  date_col: str, vendor_col: str,
                  contamination: float) -> dict:
    """Run all four detectors and return a results bundle."""
    
    # 1. Benford
    benford = benford_analysis(df[amount_col])
    
    # 2. Isolation Forest
    df = isolation_forest_analysis(df, amount_col, contamination)
    
    # 3. RSF
    df = rsf_analysis(df, amount_col, vendor_col)
    
    # 4. Duplicate
    df = duplicate_check(df, date_col, amount_col, vendor_col)
    
    # 5. Composite
    df = compute_composite_score(df)
    
    return {"df": df, "benford": benford}


# ─────────────────────────────────────────────
#  OVERALL RISK SCORE  (portfolio-level)
# ─────────────────────────────────────────────
def portfolio_risk_score(df: pd.DataFrame, benford: dict) -> float:
    outlier_rate  = df['is_outlier'].mean() * 100
    rsf_rate      = df['rsf_flag'].mean() * 100
    dup_rate      = df['is_duplicate'].mean() * 100
    benford_mad   = benford['mad']
    
    score = (
        min(outlier_rate * 2, 30) +   # max 30
        min(rsf_rate * 1.5, 25) +     # max 25
        min(dup_rate * 3, 25) +        # max 25
        min(benford_mad * 2, 20)       # max 20
    )
    return min(score, 100)


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 8px 0 24px; border-bottom: 1px solid #1e2530; margin-bottom: 20px;'>
        <span style='font-family: IBM Plex Mono; font-size: 1.2rem; color: #00e5ff; letter-spacing: -0.02em;'>
            🔍 ForensiQ
        </span><br>
        <span style='font-family: IBM Plex Mono; font-size: 0.65rem; color: #5a6a7a; letter-spacing: 0.15em;'>
            FORENSIC ACCOUNTING ENGINE v1.0
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**① Upload CSV**")
    uploaded = st.file_uploader("Invoice / Ledger Data", type=["csv"],
                                 label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("**② Column Mapping**")
    amount_col = st.text_input("Amount Column", value="amount")
    date_col   = st.text_input("Date Column",   value="date")
    vendor_col = st.text_input("Vendor Column", value="vendor")
    
    st.markdown("---")
    st.markdown("**③ Parameters**")
    contamination = st.slider("IF Contamination Rate", 0.01, 0.20, 0.05, 0.01,
                               help="Expected fraction of anomalies in dataset")
    
    st.markdown("---")
    st.markdown("""
    <div style='font-family: IBM Plex Mono; font-size: 0.65rem; color: #5a6a7a; line-height: 1.8;'>
    🔒 NO DATA STORAGE<br>
    All processing is in-memory.<br>
    Data is never saved to disk.<br><br>
    Built with Streamlit · sklearn<br>
    Plotly · Pandas · NumPy
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MAIN LAYOUT
# ─────────────────────────────────────────────
st.markdown("""
<div style='padding: 20px 0 32px;'>
    <span style='font-family: IBM Plex Mono; font-size: 0.7rem; color: #5a6a7a; letter-spacing: 0.18em;'>
        FORENSIC ACCOUNTING INTELLIGENCE PLATFORM
    </span><br>
    <h1 style='font-family: IBM Plex Mono; font-size: 2.1rem; color: #f0f4f8; margin: 6px 0 4px; letter-spacing: -0.03em;'>
        Fraud Detection System
    </h1>
    <p style='color: #5a6a7a; font-size: 0.88rem; margin: 0;'>
        Benford's Law · Isolation Forest · RSF Analysis · Duplicate Check
    </p>
</div>
""", unsafe_allow_html=True)

# ── LANDING (no file) ─────────────────────────
if uploaded is None:
    st.markdown("""
    <div style='border: 1px solid #1e2530; border-radius: 12px; padding: 40px; text-align: center; margin: 20px 0;'>
        <div style='font-size: 3rem; margin-bottom: 16px;'>📂</div>
        <p style='font-family: IBM Plex Mono; color: #5a6a7a; font-size: 0.85rem; margin: 0;'>
            Upload a CSV file via the sidebar to begin forensic analysis.<br>
            No data is stored — everything runs in memory.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📋 Expected CSV Format"):
        sample = pd.DataFrame({
            'date':   ['2024-01-15', '2024-01-15', '2024-01-16'],
            'vendor': ['ACME Corp', 'Beta LLC',    'ACME Corp'],
            'amount': [12500.00,     9999.99,       12500.00],
            'description': ['Office Supplies', 'Consulting', 'Office Supplies'],
            'invoice_id': ['INV-001', 'INV-002', 'INV-003']
        })
        st.dataframe(sample, use_container_width=True)
        
    st.info("💡 Don't have data? Generate a sample dataset using `generate_sample_data.py` included in this repo.")
    st.stop()


# ── DATA LOADING ──────────────────────────────
try:
    df_raw = pd.read_csv(uploaded)
    st.success(f"✅ Loaded {len(df_raw):,} transactions · {len(df_raw.columns)} columns")
except Exception as e:
    st.error(f"Failed to read CSV: {e}")
    st.stop()

# Column validation
missing = [c for c in [amount_col, date_col, vendor_col] if c not in df_raw.columns]
if missing:
    st.error(f"Missing columns: {missing}. Available: {list(df_raw.columns)}")
    st.stop()

# Clean
df_raw[amount_col] = pd.to_numeric(df_raw[amount_col], errors='coerce')
df_raw = df_raw.dropna(subset=[amount_col])
df_raw = df_raw[df_raw[amount_col] > 0]


# ── RUN ANALYSIS ──────────────────────────────
with st.spinner("Running forensic analysis…"):
    results = run_analysis(df_raw, amount_col, date_col, vendor_col, contamination)

df       = results["df"]
benford  = results["benford"]
port_risk = portfolio_risk_score(df, benford)

# Risk tier colour
if port_risk >= 80:
    risk_color, risk_label = "#ff3b5c", "CRITICAL RISK"
elif port_risk >= 60:
    risk_color, risk_label = "#ff7043", "HIGH RISK"
elif port_risk >= 30:
    risk_color, risk_label = "#ffb800", "MEDIUM RISK"
else:
    risk_color, risk_label = "#00e676", "LOW RISK"


# ── KPI ROW ───────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Portfolio Risk Score", f"{port_risk:.0f}/100")
c2.metric("Total Transactions",  f"{len(df):,}")
c3.metric("Anomalies (IF)",       f"{df['is_outlier'].sum():,}",
           f"{df['is_outlier'].mean()*100:.1f}%")
c4.metric("RSF Flags",            f"{df['rsf_flag'].sum():,}",
           f"{df['rsf_flag'].mean()*100:.1f}%")
c5.metric("Duplicates",           f"{df['is_duplicate'].sum():,}",
           f"{df['is_duplicate'].mean()*100:.1f}%")

st.markdown(f"""
<div style='display:flex; align-items:center; gap:20px; margin: 20px 0 8px;'>
    <div class='score-badge' style='color:{risk_color}; border-color:{risk_color};'>
        {port_risk:.0f}
    </div>
    <div>
        <div style='font-family:IBM Plex Mono; font-size:1.2rem; color:{risk_color};'>
            {risk_label}
        </div>
        <div style='font-family:IBM Plex Mono; font-size:0.72rem; color:#5a6a7a; margin-top:4px;'>
            Composite score based on 4 forensic detectors
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# ── TABS ──────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 BENFORD'S LAW",
    "🤖 ISOLATION FOREST",
    "📐 RSF ANALYSIS",
    "🔁 DUPLICATES",
    "🎯 RISK REPORT"
])


# ── TAB 1: BENFORD ────────────────────────────
with tab1:
    st.plotly_chart(chart_benford(benford), use_container_width=True)
    
    b1, b2, b3 = st.columns(3)
    b1.metric("Mean Absolute Deviation", f"{benford['mad']:.2f}%")
    b2.metric("Chi-Square Statistic",    f"{benford['chi2']:.2f}")
    b3.metric("Conformity Assessment",    benford['conformity'])
    
    if benford['conformity'] == 'NON-CONFORMING':
        st.markdown('<div class="alert-danger">⚠️ Dataset shows significant deviation from Benford\'s Law. Possible data manipulation or fraud.</div>', unsafe_allow_html=True)
    elif benford['conformity'] == 'MARGINAL':
        st.markdown('<div class="alert-warn">⚠️ Marginal conformity detected. Further investigation recommended.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-ok">✅ Dataset conforms to Benford\'s Law. No statistical red flags.</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ How Benford's Law Works"):
        st.markdown("""
        **Benford's Law** states that in naturally occurring financial data, the leading digit
        is "1" about 30.1% of the time, "2" about 17.6%, and so on logarithmically.
        
        Fraudsters who fabricate numbers tend to choose amounts that *feel* random — 
        resulting in a more uniform distribution that **deviates** from Benford's expected curve.
        
        - **MAD < 6%** → Acceptable conformity
        - **MAD 6–10%** → Marginal — warrants attention  
        - **MAD > 10%** → Non-conforming — high fraud signal
        """)


# ── TAB 2: ISOLATION FOREST ───────────────────
with tab2:
    st.plotly_chart(chart_outliers(df, amount_col), use_container_width=True)
    
    f1, f2 = st.columns([1, 2])
    with f1:
        st.metric("Anomalies Detected", df['is_outlier'].sum())
        st.metric("Anomaly Rate", f"{df['is_outlier'].mean()*100:.1f}%")
        st.metric("Avg Risk Score (Anomalies)",
                   f"{df.loc[df['is_outlier'], 'risk_score'].mean():.1f}")
    with f2:
        top_outliers = (df[df['is_outlier']]
                         .nlargest(10, 'risk_score')
                         [[vendor_col, amount_col, 'risk_score']]
                         .reset_index(drop=True))
        st.markdown("**Top 10 Highest-Risk Transactions**")
        st.dataframe(top_outliers, use_container_width=True)
    
    with st.expander("ℹ️ How Isolation Forest Works"):
        st.markdown("""
        **Isolation Forest** works by randomly partitioning data. Anomalies are isolated 
        in **fewer splits** than normal points — they're structurally different.
        
        Applied to invoice amounts (log-transformed for skew), this surfaces:
        - Unusually large payments (potential kickback, embezzlement)
        - Unusually small payments (structuring / smurfing to avoid approval limits)
        """)


# ── TAB 3: RSF ANALYSIS ───────────────────────
with tab3:
    st.plotly_chart(chart_rsf_vendors(df, amount_col, vendor_col), use_container_width=True)
    
    r1, r2, r3 = st.columns(3)
    r1.metric("RSF Flags",       df['rsf_flag'].sum())
    r2.metric("RSF Flag Rate",   f"{df['rsf_flag'].mean()*100:.1f}%")
    r3.metric("Max RSF Value",   f"{df['rsf'].max():.1f}x")
    
    rsf_flagged = (df[df['rsf_flag']]
                    .nlargest(10, 'rsf')
                    [[vendor_col, amount_col, 'rsf', 'rsf_zscore']]
                    .rename(columns={'rsf': 'RSF Ratio', 'rsf_zscore': 'Z-Score'})
                    .reset_index(drop=True))
    
    if len(rsf_flagged):
        st.markdown("**Flagged Transactions (RSF > 3.0)**")
        st.dataframe(rsf_flagged, use_container_width=True)
    
    with st.expander("ℹ️ What is RSF?"):
        st.markdown("""
        **Relative Size Factor** = Transaction Amount ÷ Median Amount for that Vendor.
        
        An RSF of **3.0** means the transaction is 3× the typical amount for that vendor.
        This is a classic test from ACFE (Association of Certified Fraud Examiners) methodology.
        
        Common fraud patterns detected:
        - One-time large payments to a shell company
        - Year-end bloated invoices to a collusive vendor
        - Inflated expense reimbursements
        """)


# ── TAB 4: DUPLICATES ─────────────────────────
with tab4:
    dupes = df[df['is_duplicate']].sort_values([date_col, vendor_col, amount_col])
    
    d1, d2 = st.columns(2)
    d1.metric("Duplicate Transactions", dupes.shape[0])
    d2.metric("Estimated Overpayment Risk",
               f"${dupes[amount_col].sum():,.0f}")
    
    if len(dupes) > 0:
        st.markdown('<div class="alert-danger">⚠️ Potential duplicate invoices detected. Review immediately for double-payment risk.</div>', unsafe_allow_html=True)
        st.markdown("**Duplicate Transaction Groups**")
        st.dataframe(
            dupes[[date_col, vendor_col, amount_col, 'dup_count']].reset_index(drop=True),
            use_container_width=True
        )
    else:
        st.markdown('<div class="alert-ok">✅ No duplicate transactions detected.</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ Why Duplicates Matter"):
        st.markdown("""
        Duplicate payments are one of the most common and costly fraud schemes.
        The ACFE 2024 Report on Occupational Fraud identifies billing fraud as
        the most frequent asset misappropriation scheme.
        
        **Detection key**: Same date + same amount + same vendor within the ledger.
        Even small duplicates aggregate to material misstatement.
        """)


# ── TAB 5: RISK REPORT ────────────────────────
with tab5:
    rc1, rc2 = st.columns([1, 1])
    with rc1:
        st.plotly_chart(chart_risk_distribution(df), use_container_width=True)
    with rc2:
        tier_summary = df['risk_tier'].value_counts().reset_index()
        tier_summary.columns = ['Risk Tier', 'Count']
        tier_summary['% of Portfolio'] = (tier_summary['Count'] / len(df) * 100).round(1)
        tier_summary['Amount Exposure'] = tier_summary['Risk Tier'].apply(
            lambda t: f"${df.loc[df['risk_tier']==t, amount_col].sum():,.0f}"
        )
        st.dataframe(tier_summary, use_container_width=True, hide_index=True)
    
    st.markdown("### 🔴 Critical & High Risk Transactions")
    high_risk = (df[df['risk_tier'].isin(['CRITICAL', 'HIGH'])]
                  .nlargest(20, 'composite_risk')
                  [[date_col, vendor_col, amount_col, 'composite_risk', 
                    'risk_tier', 'is_outlier', 'rsf_flag', 'is_duplicate']]
                  .reset_index(drop=True))
    st.dataframe(high_risk, use_container_width=True)
    
    # CSV Export
    st.markdown("### 📥 Export Full Results")
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        label="⬇ Download Annotated CSV",
        data=csv_buf.getvalue(),
        file_name=f"forensiq_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )
    
    with st.expander("📑 Methodology Summary (for Auditors)"):
        st.markdown(f"""
        **Analysis completed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
        **Records analyzed**: {len(df):,}  
        **Contamination parameter**: {contamination:.0%}
        
        | Detector | Algorithm | Threshold | Flags |
        |---|---|---|---|
        | Benford's Law | First-digit chi-square | MAD > 6% = marginal | {benford['conformity']} |
        | Isolation Forest | sklearn IsolationForest | contamination={contamination} | {df['is_outlier'].sum()} records |
        | RSF Analysis | Vendor-normalized ratio | RSF > 3.0 | {df['rsf_flag'].sum()} records |
        | Duplicate Check | Exact-match groupby | count > 1 | {df['is_duplicate'].sum()} records |
        
        *This tool is designed as a decision-support aid. All flagged items require
        professional judgment and further audit procedures before conclusions can be drawn.*
        """)
