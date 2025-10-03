
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Smart Home — Live Dashboard (Pro)", page_icon="🏠", layout="wide")

def load_default_excel():
    try:
        return pd.ExcelFile("LT09 smart_home_devices_data.xlsx")
    except Exception:
        return None

def coerce_month(col):
    try:
        return pd.to_datetime(col, format="%b-%Y")
    except Exception:
        try:
            return pd.to_datetime(col)
        except Exception:
            return col

def add_helpers(df):
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    if "Month" in df.columns:
        df["Month"] = coerce_month(df["Month"])
    # Calculated fields
    if "Monthly Revenue (USD)" in df.columns and "Marketing Spend (USD)" in df.columns:
        den = df["Marketing Spend (USD)"].replace(0, np.nan)
        df["Revenue per Marketing $"] = df["Monthly Revenue (USD)"] / den
    if "Active Users" in df.columns and "Monthly Revenue (USD)" in df.columns:
        den2 = df["Active Users"].replace(0, np.nan)
        df["Revenue per Active User"] = df["Monthly Revenue (USD)"] / den2
    return df



def load_sheets(xls):
    sheet_names = xls.sheet_names
    dfs = {name: pd.read_excel(xls, sheet_name=name) for name in sheet_names}
    return dfs, sheet_names

st.markdown("<h2 style='margin-bottom:0'>🏠 Smart Home — Live Dashboard</h2><p style='color:#6b7280;margin-top:4px'>Interactive KPIs, trends & relationships (designed for your GEN AI project)</p>", unsafe_allow_html=True)

uploaded = st.file_uploader("Upload Excel (.xlsx) with MAIN DATA (optional)", type=["xlsx"])

xls = pd.ExcelFile(uploaded) if uploaded is not None else load_default_excel()
if xls is None:
    st.warning("No Excel found. Upload your file to begin.")
    st.stop()

dfs, sheet_names = load_sheets(xls)
base_sheet = "MAIN DATA" if "MAIN DATA" in sheet_names else sheet_names[0]
df = add_helpers(dfs[base_sheet])

with st.sidebar:
    st.header("Filters")
    if "Product" in df.columns:
        products = sorted(df["Product"].dropna().unique().tolist())
        selected_products = st.multiselect("Product(s)", products, default=products if products else None)
    else:
        selected_products = None

    if "Month" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Month"]):
        min_m, max_m = df["Month"].min(), df["Month"].max()
        start, end = st.slider(
            "Month range",
            min_value=min_m.to_pydatetime(),
            max_value=max_m.to_pydatetime(),
            value=(min_m.to_pydatetime(), max_m.to_pydatetime()),
            format="MMM %Y"
        )
    else:
        start, end = None, None

    st.header("Targets")
    tgt_cvr = st.number_input("Target Conversion Rate (%)", value=8.0, step=0.5)
    tgt_ret = st.number_input("Target Retention Rate (%)", value=75.0, step=1.0)

    st.header("Presets")
    preset = st.radio("View", ["Efficiency", "Growth", "Customer Experience"], index=0)
    # --- PRESET behavior (defaults for charts) ---
if preset == "Efficiency":
    ts_default = "Revenue per Marketing $"
    x_default, y_default = "Marketing Spend (USD)", "Monthly Revenue (USD)"
elif preset == "Growth":
    ts_default = "Monthly Revenue (USD)"
    x_default, y_default = "Active Users", "Conversion Rate (%)"
else:  # Customer Experience
    ts_default = "Customer Satisfaction (1-5)"
    x_default, y_default = "Customer Satisfaction (1-5)", "Retention Rate (%)"


f = df.copy()
if selected_products:
    f = f[f["Product"].isin(selected_products)]
if start and end and "Month" in f.columns and pd.api.types.is_datetime64_any_dtype(f["Month"]):
    f = f[(f["Month"] >= pd.Timestamp(start)) & (f["Month"] <= pd.Timestamp(end))]

k1, k2, k3, k4, k5 = st.columns(5)
rev = float(f["Monthly Revenue (USD)"].sum()) if "Monthly Revenue (USD)" in f.columns else float("nan")
mkt = float(f["Marketing Spend (USD)"].sum()) if "Marketing Spend (USD)" in f.columns else float("nan")
romi = float(f["Revenue per Marketing $"].mean()) if "Revenue per Marketing $" in f.columns else float("nan")
cvr = float(f["Conversion Rate (%)"].mean()) if "Conversion Rate (%)" in f.columns else float("nan")
ret = float(f["Retention Rate (%)"].mean()) if "Retention Rate (%)" in f.columns else float("nan")

def compact(n):
    if pd.isna(n): return "—"
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return f"{n:.0f}"

k1.metric("Total Revenue", compact(rev))
k2.metric("Marketing Spend", compact(mkt))
k3.metric("Avg Rev / Marketing $", "—" if pd.isna(romi) else f"{romi:.2f}")
k4.metric("Avg CVR", "—" if pd.isna(cvr) else f"{cvr:.2f}%",
          delta=None if pd.isna(cvr) else f"{cvr - tgt_cvr:+.2f} vs target")
k5.metric("Avg Retention", "—" if pd.isna(ret) else f"{ret:.2f}%",
          delta=None if pd.isna(ret) else f"{ret - tgt_ret:+.1f} vs target")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "🧮 Relationships", "💡 Insights", "📚 Data"])

with tab1:
    ts_metrics = [c for c in [
        "Monthly Revenue (USD)","Marketing Spend (USD)","Active Users",
        "Conversion Rate (%)","Customer Satisfaction (1-5)","Retention Rate (%)",
        "Revenue per Marketing $","Revenue per Active User"
    ] if c in f.columns]
    if ts_metrics and "Month" in f.columns:
       default_ts_idx = ts_metrics.index(ts_default) if ts_default in ts_metrics else 0
m = st.selectbox("Metric", ts_metrics, index=default_ts_idx, key="ts_metric")

        color = "Product" if ("Product" in f.columns and (selected_products is None or len(selected_products)!=1)) else None
        fig = px.line(f.sort_values("Month"), x="Month", y=m, color=color, markers=True)
        if m == "Conversion Rate (%)":
            fig.add_hline(y=tgt_cvr, line_dash="dot", annotation_text=f"Target CVR {tgt_cvr}%")
        if m == "Retention Rate (%)":
            fig.add_hline(y=tgt_ret, line_dash="dot", annotation_text=f"Target Ret {tgt_ret}%")
        fig.update_layout(height=420, margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    num_cols = [c for c in [
        "Active Users","Conversion Rate (%)","Marketing Spend (USD)",
        "Monthly Revenue (USD)","Customer Satisfaction (1-5)","Retention Rate (%)",
        "Revenue per Marketing $","Revenue per Active User"
    ] if c in f.columns]
    c1, c2 = st.columns(2)
    with c1:
        x_idx = num_cols.index(x_default) if x_default in num_cols else 0
x = st.selectbox("X", num_cols, index=x_idx)
    with c2:
        y_idx = num_cols.index(y_default) if y_default in num_cols else 0
y = st.selectbox("Y", num_cols, index=y_idx)
    color = "Product" if ("Product" in f.columns and (selected_products is None or len(selected_products)!=1)) else None
    fig2 = px.scatter(f, x=x, y=y, color=color, trendline="ols")
    fig2.update_layout(height=420, margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    bullets = []
    if "Revenue per Marketing $" in f.columns and f["Revenue per Marketing $"].notna().any():
        bullets.append(f"Average Revenue per Marketing $ ≈ **{f['Revenue per Marketing $'].mean():.2f}**; top month ≈ **{f['Revenue per Marketing $'].max():.2f}**.")
    if "Conversion Rate (%)" in f.columns:
        bullets.append(f"CVR spans **{f['Conversion Rate (%)'].min():.2f}%–{f['Conversion Rate (%)'].max():.2f}%**; vs target **{tgt_cvr}%**.")
    if "Retention Rate (%)" in f.columns:
        bullets.append(f"Retention averages **{f['Retention Rate (%)'].mean():.1f}%** (target **{tgt_ret}%**).")
    if "Marketing Spend (USD)" in f.columns and "Monthly Revenue (USD)" in f.columns:
        corr = f[["Marketing Spend (USD)","Monthly Revenue (USD)"]].corr().iloc[0,1]
        bullets.append(f"Spend↔Revenue correlation ≈ **{corr:.2f}** (interpret with caution, small n).")
    if "Customer Satisfaction (1-5)" in f.columns:
        bullets.append(f"CSAT mean ≈ **{f['Customer Satisfaction (1-5)'].mean():.2f}/5**; consider linking CSAT↔Retention in analysis.")

    st.markdown("### Auto-insights")
    for b in bullets:
        st.markdown(f"- {b}")
    st.caption("Deterministic rules for transparency (no external API).")

with tab4:
    st.dataframe(f.reset_index(drop=True), use_container_width=True)
    st.download_button("Download filtered data (CSV)", f.to_csv(index=False).encode("utf-8"),
                       file_name="filtered_smart_home_data.csv", mime="text/csv")
