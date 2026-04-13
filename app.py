import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from io import StringIO
from datetime import datetime

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="JPSI | Fertilizer Transportation Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── JPSI Brand Colors ─────────────────────────────────────────────────────────
DARK    = "#32373c"
BLUE    = "#0693e3"
WHITE   = "#ffffff"
LGRAY   = "#f4f5f7"
MGRAY   = "#e1e4e8"

CHART_COLORS = [
    "#0693e3", "#ff6900", "#32373c", "#9b51e0",
    "#cf2e2e", "#00b894", "#fdcb6e", "#636e72",
    "#a29bfe", "#fd79a8", "#00cec9", "#e17055",
]

MONTH_ABBR = {
    1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
    7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec",
}

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  /* ── Global ── */
  #MainMenu, footer, header {{visibility: hidden;}}
  .stApp {{background-color: {LGRAY};}}

  /* ── Top header bar ── */
  .jpsi-header {{
    background: {DARK};
    color: {WHITE};
    padding: 0.85rem 2rem;
    margin: -4rem -4rem 1.5rem -4rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 3px solid {BLUE};
  }}
  .jpsi-header h1 {{
    color: {WHITE};
    font-size: 1.4rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: 0.02em;
  }}
  .jpsi-header h1 span {{color: {BLUE};}}
  .jpsi-tagline {{
    font-size: 0.78rem;
    color: rgba(255,255,255,0.55);
    margin-top: 0.2rem;
  }}
  .jpsi-updated {{
    font-size: 0.78rem;
    color: rgba(255,255,255,0.45);
    text-align: right;
  }}

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {{
    background: {DARK};
    border-radius: 6px 6px 0 0;
    padding: 0 0.5rem;
    gap: 0;
  }}
  .stTabs [data-baseweb="tab"] {{
    color: rgba(255,255,255,0.6);
    font-weight: 500;
    font-size: 0.95rem;
    padding: 0.7rem 1.4rem;
    border-radius: 0;
    border-bottom: 3px solid transparent;
  }}
  .stTabs [aria-selected="true"] {{
    color: {WHITE} !important;
    border-bottom: 3px solid {BLUE} !important;
    background: transparent !important;
  }}

  /* ── Section headers ── */
  .sec-hdr {{
    color: {DARK};
    font-size: 1rem;
    font-weight: 600;
    border-left: 4px solid {BLUE};
    padding: 0.2rem 0 0.2rem 0.7rem;
    margin: 1.25rem 0 0.6rem 0;
  }}

  /* ── Filter row card ── */
  .filter-card {{
    background: {WHITE};
    border: 1px solid {MGRAY};
    border-radius: 6px;
    padding: 0.85rem 1rem 0.4rem 1rem;
    margin-bottom: 0.8rem;
  }}

  /* ── Info note ── */
  .info-note {{
    background: #e8f4fd;
    border-left: 4px solid {BLUE};
    padding: 0.6rem 1rem;
    border-radius: 0 4px 4px 0;
    font-size: 0.88rem;
    margin-bottom: 1rem;
    color: {DARK};
  }}

  /* ── YTD button ── */
  div[data-testid="stButton"] > button {{
    background: {BLUE};
    color: {WHITE};
    border: none;
    border-radius: 4px;
    font-weight: 600;
    padding: 0.45rem 1.1rem;
    font-size: 0.88rem;
  }}
  div[data-testid="stButton"] > button:hover {{
    background: #0578c5;
    color: {WHITE};
  }}

  /* ── Chart wrapper ── */
  .chart-wrap {{
    background: {WHITE};
    border: 1px solid {MGRAY};
    border-radius: 6px;
    padding: 0.5rem;
    margin-bottom: 1rem;
  }}

  /* ── Footer ── */
  .jpsi-footer {{
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    color: #999;
    font-size: 0.78rem;
    border-top: 1px solid {MGRAY};
    margin-top: 2rem;
  }}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
now = datetime.now()
st.markdown(f"""
<div class="jpsi-header">
  <div>
    <h1>🌾 JPSI | Fertilizer <span>Transportation</span> Dashboard</h1>
    <div class="jpsi-tagline">Live data · U.S. Department of Agriculture Agricultural Transport Platform</div>
  </div>
  <div class="jpsi-updated">
    Last loaded: {now.strftime("%B %d, %Y %I:%M %p")}<br>
    Imports: monthly &nbsp;·&nbsp; Barge: monthly &nbsp;·&nbsp; Rail: weekly
  </div>
</div>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
BASE = "https://agtransport.usda.gov/api/views"

@st.cache_data(ttl=86_400, show_spinner=False)
def load_imports():
    """rusv-mgid – U.S. Fertilizer Imports by Commodity by Month (Census Bureau)"""
    r = requests.get(f"{BASE}/rusv-mgid/rows.csv", params={"$limit": 50_000}, timeout=30)
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text), thousands=",")

@st.cache_data(ttl=86_400, show_spinner=False)
def load_barge():
    """4pdq-r8e8 – Monthly Fertilizer Barge Movements (Army Corps of Engineers)"""
    r = requests.get(f"{BASE}/4pdq-r8e8/rows.csv", params={"$limit": 50_000}, timeout=30)
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text), thousands=",")

@st.cache_data(ttl=3_600, show_spinner=False)
def load_rail():
    """tb7q-kn5i – Weekly Rail Carloadings (Surface Transportation Board)"""
    r = requests.get(f"{BASE}/tb7q-kn5i/rows.csv", params={"$limit": 250_000}, timeout=90)
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text), thousands=",")

@st.cache_data(ttl=86_400, show_spinner=False)
def load_rail_tonnage():
    """xve5-xb56 – Public Use Carload Waybill Sample: monthly fertilizer rail tonnage (STB)"""
    # STCC codes for fertilizer: 28198 ammonia, 28125 potassium, 28181 misc,
    # 28712 superphosphate/N solution, 28713 ammoniating/N solution, 28193 sulfuric acid
    # Socrata SOQL requires quoted strings for text fields
    fert_stcc = "('28125','28181','28193','28198','28712','28713')"
    r = requests.get(
        f"{BASE}/xve5-xb56/rows.csv",
        params={"$limit": 100_000, "$where": f"stcc5 in{fert_stcc}"},
        timeout=60,
    )
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text), thousands=",")

with st.spinner("Loading live USDA data…"):
    try:
        raw_imports    = load_imports()
        raw_barge      = load_barge()
        raw_rail       = load_rail()
        raw_rail_tons  = load_rail_tonnage()
        load_err       = None
    except Exception as exc:
        load_err = str(exc)

if load_err:
    st.error(f"Error loading data from USDA: {load_err}")
    st.stop()

# ── Clean: Barge ─────────────────────────────────────────────────────────────
df_barge = raw_barge.copy()
df_barge["Year"]  = pd.to_numeric(df_barge["Year"],  errors="coerce").astype("Int64")
df_barge["Month"] = pd.to_numeric(df_barge["Month"], errors="coerce").astype("Int64")
df_barge["Tons"]  = pd.to_numeric(df_barge["Tons"].astype(str).str.replace(",",""), errors="coerce").fillna(0)
df_barge = df_barge.dropna(subset=["Year","Month"])

# ── Clean: Rail ──────────────────────────────────────────────────────────────
df_rail = raw_rail.copy()
df_rail["Year"]     = pd.to_numeric(df_rail["Year"],     errors="coerce").astype("Int64")
df_rail["Month"]    = pd.to_numeric(df_rail["Month"],    errors="coerce").astype("Int64")
df_rail["Week"]     = pd.to_numeric(df_rail["Week"],     errors="coerce").astype("Int64")
df_rail["Carloads"] = pd.to_numeric(df_rail["Carloads"].astype(str).str.replace(",",""), errors="coerce").fillna(0)
df_rail = df_rail.dropna(subset=["Year","Month","Week"])

# ── Clean: Imports (dynamic column detection) ─────────────────────────────────
df_imp = raw_imports.copy()
cols_lower = {c: c.lower() for c in df_imp.columns}

year_col  = next((c for c in df_imp.columns if "year" in c.lower()), None)
month_col = next((c for c in df_imp.columns if "month" in c.lower()), None)
comm_col  = next((c for c in df_imp.columns if "commodity" in c.lower()), None)
qty_col   = next((c for c in df_imp.columns
                  if any(k in c.lower() for k in ["ton","quantity","metric","short","amount"])), None)

if year_col:
    df_imp[year_col] = pd.to_numeric(df_imp[year_col], errors="coerce").astype("Int64")
if month_col:
    df_imp[month_col] = pd.to_numeric(df_imp[month_col], errors="coerce").astype("Int64")
if qty_col:
    df_imp[qty_col] = pd.to_numeric(
        df_imp[qty_col].astype(str).str.replace(",",""), errors="coerce"
    ).fillna(0)

# ── Clean: Rail Tonnage (monthly waybill sample) ─────────────────────────────
df_rail_tons = raw_rail_tons.copy()
# Normalize column names to lowercase for safe access
df_rail_tons.columns = [c.strip() for c in df_rail_tons.columns]
rt_cols = {c.lower(): c for c in df_rail_tons.columns}

# Map expected fields
rt_year_col  = rt_cols.get("data year") or rt_cols.get("year") or next((v for k,v in rt_cols.items() if "year" in k), None)
rt_month_col = next((v for k,v in rt_cols.items() if "month" in k), None)
rt_stcc_col  = rt_cols.get("stcc5 description") or rt_cols.get("stcc5description") or next((v for k,v in rt_cols.items() if "description" in k), None)
rt_tons_col  = next((v for k,v in rt_cols.items() if "ton" in k and "billed" in k), None) or \
               next((v for k,v in rt_cols.items() if "ton" in k), None)

# Derive Month from Waybill Date if no dedicated month column
if rt_month_col is None:
    wbd_col = next((v for k,v in rt_cols.items() if "waybill" in k), None)
    if wbd_col:
        df_rail_tons[wbd_col] = pd.to_datetime(df_rail_tons[wbd_col], errors="coerce")
        df_rail_tons["_month"] = df_rail_tons[wbd_col].dt.month
        df_rail_tons["_year"]  = df_rail_tons[wbd_col].dt.year
        rt_month_col = "_month"
        rt_year_col  = "_year"

if rt_year_col:
    df_rail_tons[rt_year_col]  = pd.to_numeric(df_rail_tons[rt_year_col],  errors="coerce").astype("Int64")
if rt_month_col:
    df_rail_tons[rt_month_col] = pd.to_numeric(df_rail_tons[rt_month_col], errors="coerce").astype("Int64")
if rt_tons_col:
    df_rail_tons[rt_tons_col]  = pd.to_numeric(
        df_rail_tons[rt_tons_col].astype(str).str.replace(",",""), errors="coerce"
    ).fillna(0)

rail_tons_ok = all([rt_year_col, rt_month_col, rt_stcc_col, rt_tons_col])

# ── Helpers ───────────────────────────────────────────────────────────────────
def chart_layout(title, xlab, ylab, height=420):
    return dict(
        title=dict(text=title, font=dict(size=14, color=DARK), x=0.01),
        xaxis=dict(title=xlab, gridcolor=MGRAY, tickfont=dict(color=DARK)),
        yaxis=dict(title=ylab, gridcolor=MGRAY, tickfont=dict(color=DARK), tickformat=","),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color=DARK)),
        barmode="stack",
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        font=dict(color=DARK),
        height=height,
        hovermode="x unified",
        margin=dict(l=60, r=20, t=60, b=50),
    )

def sec(label):
    st.markdown(f'<div class="sec-hdr">{label}</div>', unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_imp, tab_barge, tab_rail = st.tabs([
    "📦  Fertilizer Imports",
    "🚢  Barge Movements",
    "🚂  Rail Shipments",
])

TODAY        = datetime.now()
CUR_YEAR     = TODAY.year
CUR_MONTH    = TODAY.month

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – FERTILIZER IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_imp:
    if not all([year_col, month_col, comm_col, qty_col]):
        st.warning(
            f"Could not auto-detect all required columns in the imports dataset.\n\n"
            f"Columns found: `{list(raw_imports.columns)}`\n\n"
            "Please report the column names so they can be mapped correctly."
        )
    else:
        all_imp_years = sorted(df_imp[year_col].dropna().unique().tolist())
        all_imp_comms = sorted(df_imp[comm_col].dropna().unique().tolist())

        # ── Filters ───────────────────────────────────────────────────────────
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        fc1, fc2, fc3, fc4 = st.columns([2, 2.5, 2, 1])

        with fc1:
            imp_year_sel = st.selectbox(
                "Calendar Year (Monthly Chart)",
                options=sorted(all_imp_years, reverse=True),
                index=0,
                key="imp_yr",
            )
        with fc2:
            imp_comm_sel = st.multiselect(
                "Commodity",
                options=all_imp_comms,
                default=all_imp_comms,
                key="imp_comm",
            )
        with fc3:
            imp_month_sel = st.multiselect(
                "Month",
                options=list(range(1, 13)),
                format_func=lambda m: MONTH_ABBR[m],
                default=list(range(1, 13)),
                key="imp_months",
            )
        with fc4:
            st.markdown("<br>", unsafe_allow_html=True)
            ytd_clicked = st.button("YTD", key="ytd", help="Year-to-Date: Jan → current month")

        st.markdown("</div>", unsafe_allow_html=True)

        active_months = list(range(1, CUR_MONTH + 1)) if ytd_clicked else imp_month_sel

        # ── Monthly Stacked Bar ───────────────────────────────────────────────
        sec("Monthly Imports by Commodity")
        df_m = df_imp[
            (df_imp[year_col] == imp_year_sel) &
            (df_imp[comm_col].isin(imp_comm_sel)) &
            (df_imp[month_col].isin(active_months))
        ].groupby([month_col, comm_col])[qty_col].sum().reset_index()

        fig_m = go.Figure()
        for i, comm in enumerate(imp_comm_sel):
            d = df_m[df_m[comm_col] == comm].sort_values(month_col)
            fig_m.add_trace(go.Bar(
                name=comm,
                x=[MONTH_ABBR[int(m)] for m in d[month_col]],
                y=d[qty_col],
                marker_color=CHART_COLORS[i % len(CHART_COLORS)],
                hovertemplate="%{y:,.0f} tons<extra>%{fullData.name}</extra>",
            ))
        title_suffix = " (YTD)" if ytd_clicked else ""
        fig_m.update_layout(**chart_layout(
            f"Monthly Fertilizer Imports — {imp_year_sel}{title_suffix}",
            "Month", "Short Tons",
        ))
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(fig_m, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Annual Stacked Bar ────────────────────────────────────────────────
        sec("Annual Imports by Commodity")
        df_a = df_imp[
            df_imp[comm_col].isin(imp_comm_sel)
        ].groupby([year_col, comm_col])[qty_col].sum().reset_index()

        fig_a = go.Figure()
        for i, comm in enumerate(imp_comm_sel):
            d = df_a[df_a[comm_col] == comm].sort_values(year_col)
            fig_a.add_trace(go.Bar(
                name=comm,
                x=d[year_col].astype(str),
                y=d[qty_col],
                marker_color=CHART_COLORS[i % len(CHART_COLORS)],
                hovertemplate="%{y:,.0f} tons<extra>%{fullData.name}</extra>",
            ))
        layout_a = chart_layout("Annual Fertilizer Imports by Commodity", "Year", "Short Tons")
        layout_a["hovermode"] = "x unified"
        fig_a.update_layout(**layout_a)
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(fig_a, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – BARGE MOVEMENTS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_barge:
    st.markdown("""
    <div class="info-note">
      <strong>Data note:</strong> USDA fertilizer barge data (U.S. Army Corps of Engineers)
      is published on a <strong>monthly</strong> basis — no weekly barge dataset is publicly
      available. Charts use monthly reporting periods. Click legend items to show/hide commodities.
    </div>
    """, unsafe_allow_html=True)

    barge_comms  = sorted(df_barge["Commodity"].dropna().unique().tolist())
    barge_years  = sorted(df_barge["Year"].dropna().unique().tolist())

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    bc1, bc2 = st.columns(2)
    with bc1:
        barge_comm_sel = st.multiselect(
            "Commodity", barge_comms, default=barge_comms, key="bg_comm"
        )
    with bc2:
        barge_year_sel = st.multiselect(
            "Calendar Year (add / remove years)",
            barge_years,
            default=[y for y in barge_years if y >= CUR_YEAR - 4],
            key="bg_years",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    df_bg = df_barge[
        df_barge["Commodity"].isin(barge_comm_sel) &
        df_barge["Year"].isin(barge_year_sel)
    ]

    # ── Line Chart: monthly totals, one line per year ─────────────────────────
    sec("Monthly Barge Movements — One Line per Calendar Year")
    df_bg_line = (
        df_bg.groupby(["Year", "Month"])["Tons"].sum()
        .reset_index()
        .sort_values(["Year", "Month"])
    )

    fig_bg_line = go.Figure()
    for i, yr in enumerate(sorted(barge_year_sel)):
        d = df_bg_line[df_bg_line["Year"] == yr]
        fig_bg_line.add_trace(go.Scatter(
            name=str(yr),
            x=[MONTH_ABBR[int(m)] for m in d["Month"]],
            y=d["Tons"],
            mode="lines+markers",
            line=dict(color=CHART_COLORS[i % len(CHART_COLORS)], width=2.5),
            marker=dict(size=6),
            hovertemplate="%{y:,.0f} tons<extra>%{fullData.name}</extra>",
        ))
    layout_bg_line = chart_layout(
        "Monthly Fertilizer Barge Movements (Short Tons)", "Month", "Short Tons"
    )
    layout_bg_line.pop("barmode", None)
    fig_bg_line.update_layout(**layout_bg_line)
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig_bg_line, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Stacked Bar: monthly by commodity ────────────────────────────────────
    sec("Monthly Summary by Commodity — Stacked")
    bg_bar_yr = st.selectbox(
        "Select Year for Monthly Commodity Breakdown",
        sorted(barge_year_sel, reverse=True),
        key="bg_bar_yr",
    )

    df_bg_bar = (
        df_barge[
            (df_barge["Commodity"].isin(barge_comm_sel)) &
            (df_barge["Year"] == bg_bar_yr)
        ]
        .groupby(["Month", "Commodity"])["Tons"].sum()
        .reset_index()
        .sort_values("Month")
    )

    fig_bg_bar = go.Figure()
    for i, comm in enumerate(barge_comm_sel):
        d = df_bg_bar[df_bg_bar["Commodity"] == comm]
        fig_bg_bar.add_trace(go.Bar(
            name=comm,
            x=[MONTH_ABBR[int(m)] for m in d["Month"]],
            y=d["Tons"],
            marker_color=CHART_COLORS[i % len(CHART_COLORS)],
            hovertemplate="%{y:,.0f} tons<extra>%{fullData.name}</extra>",
        ))
    fig_bg_bar.update_layout(**chart_layout(
        f"Monthly Barge Movements by Commodity — {bg_bar_yr}", "Month", "Short Tons"
    ))
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig_bg_bar, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – RAIL SHIPMENTS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_rail:
    st.markdown("""
    <div class="info-note">
      <strong>Units:</strong> The weekly line chart uses <strong>carloads</strong> (railcar count)
      — the only publicly available weekly rail granularity from the STB.
      The monthly summary bar chart below uses <strong>short tons</strong> from the STB
      Public Use Carload Waybill Sample, broken out by fertilizer STCC commodity code.
      Click legend items to show/hide any year or commodity.
    </div>
    """, unsafe_allow_html=True)

    rail_comms = sorted(df_rail["Commodity"].dropna().unique().tolist())
    rail_years = sorted(df_rail["Year"].dropna().unique().tolist())
    rail_types = sorted(df_rail["Type"].dropna().unique().tolist())

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        rail_comm_sel = st.multiselect(
            "Commodity",
            rail_comms,
            default=["Fertilizer"] if "Fertilizer" in rail_comms else rail_comms[:1],
            key="rl_comm",
        )
    with rc2:
        rail_year_sel = st.multiselect(
            "Calendar Year (add / remove years)",
            rail_years,
            default=[y for y in rail_years if y >= CUR_YEAR - 4],
            key="rl_years",
        )
    with rc3:
        rail_type_sel = st.multiselect(
            "Type (Originated / Received)",
            rail_types,
            default=list(rail_types),
            key="rl_type",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    df_rl = df_rail[
        df_rail["Commodity"].isin(rail_comm_sel) &
        df_rail["Year"].isin(rail_year_sel) &
        df_rail["Type"].isin(rail_type_sel)
    ]

    # ── Line Chart: weekly totals, one line per year ──────────────────────────
    sec("Weekly Rail Movements — One Line per Calendar Year")
    df_rl_line = (
        df_rl.groupby(["Year", "Week"])["Carloads"].sum()
        .reset_index()
        .sort_values(["Year", "Week"])
    )

    fig_rl_line = go.Figure()
    for i, yr in enumerate(sorted(rail_year_sel)):
        d = df_rl_line[df_rl_line["Year"] == yr]
        fig_rl_line.add_trace(go.Scatter(
            name=str(yr),
            x=d["Week"],
            y=d["Carloads"],
            mode="lines",
            line=dict(color=CHART_COLORS[i % len(CHART_COLORS)], width=2.5),
            hovertemplate="Week %{x} — %{y:,.0f} carloads<extra>%{fullData.name}</extra>",
        ))
    layout_rl_line = chart_layout(
        "Weekly Fertilizer Rail Carloadings", "Week Number", "Carloads"
    )
    layout_rl_line.pop("barmode", None)
    fig_rl_line.update_layout(**layout_rl_line)
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig_rl_line, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Stacked Bar: monthly by commodity in TONS (waybill dataset) ──────────
    sec("Monthly Summary by Fertilizer Type — Short Tons (Waybill Sample)")
    rl_bar_yr = st.selectbox(
        "Select Year for Monthly Tonnage Breakdown",
        sorted(rail_year_sel, reverse=True),
        key="rl_bar_yr",
    )

    if rail_tons_ok:
        rt_comms = sorted(df_rail_tons[rt_stcc_col].dropna().unique().tolist())
        rl_tons_comm_sel = st.multiselect(
            "Fertilizer Type (STCC)", rt_comms, default=rt_comms, key="rl_tons_comm"
        )

        df_rl_bar = (
            df_rail_tons[
                (df_rail_tons[rt_stcc_col].isin(rl_tons_comm_sel)) &
                (df_rail_tons[rt_year_col] == rl_bar_yr)
            ]
            .groupby([rt_month_col, rt_stcc_col])[rt_tons_col].sum()
            .reset_index()
            .sort_values(rt_month_col)
        )

        fig_rl_bar = go.Figure()
        for i, comm in enumerate(rl_tons_comm_sel):
            d = df_rl_bar[df_rl_bar[rt_stcc_col] == comm]
            fig_rl_bar.add_trace(go.Bar(
                name=comm,
                x=[MONTH_ABBR[int(m)] for m in d[rt_month_col]],
                y=d[rt_tons_col],
                marker_color=CHART_COLORS[i % len(CHART_COLORS)],
                hovertemplate="%{y:,.0f} short tons<extra>%{fullData.name}</extra>",
            ))
        fig_rl_bar.update_layout(**chart_layout(
            f"Monthly Fertilizer Rail Tonnage by Type — {rl_bar_yr}", "Month", "Short Tons"
        ))
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(fig_rl_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info(
            "Monthly rail tonnage (waybill dataset) columns could not be mapped. "
            f"Columns found: {list(raw_rail_tons.columns)}"
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="jpsi-footer">
  Data sources: U.S. Census Bureau (Fertilizer Imports) &nbsp;·&nbsp;
  U.S. Army Corps of Engineers (Barge) &nbsp;·&nbsp;
  Surface Transportation Board (Rail)<br>
  Delivered via USDA Agricultural Transport Platform (agtransport.usda.gov) &nbsp;·&nbsp;
  Built with Streamlit &amp; Plotly
</div>
""", unsafe_allow_html=True)
