import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

DB_URL = "postgresql://postgres:postgres@localhost:5432/job_market"

st.set_page_config(
    page_title="JobsAI — Find Your Next Role",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.hero {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    padding: 40px; border-radius: 16px; color: white; margin-bottom: 24px;
}
.hero h1 { font-size: 2.2rem; font-weight: 700; margin: 0 0 6px 0; }
.hero p  { font-size: 1rem; opacity: 0.85; margin: 0; }
.kpi-card {
    background: white; border-radius: 12px; padding: 20px;
    box-shadow: 0 1px 8px rgba(0,0,0,0.06); text-align: center;
    border-left: 4px solid #3b82f6;
}
.kpi-number { font-size: 1.8rem; font-weight: 700; color: #1e3a8a; }
.kpi-label  { font-size: 0.82rem; color: #64748b; margin-top: 4px; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    engine = create_engine(DB_URL)
    df = pd.read_sql("SELECT * FROM jobs_raw", engine)
    df["salary_avg"] = pd.to_numeric(df["salary_avg"], errors="coerce").fillna(0)
    df["redirect_url"] = df["redirect_url"].fillna("").astype(str)
    df["location"] = df["location"].fillna("Location not specified")
    df["company"] = df["company"].fillna("Unknown Company")
    df["title"] = df["title"].fillna("Untitled Role")
    df["seniority"] = df["seniority"].fillna("mid")
    df["search_term"] = df["search_term"].fillna("other")
    df["is_remote"] = df["is_remote"].fillna(False)
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    return df

df = load_data()

# ── Hero ──
st.markdown(f"""
<div class="hero">
    <h1>🔍 JobsAI</h1>
    <p>Explore {len(df)} live AI, Data & ML job postings — powered by real market data</p>
</div>
""", unsafe_allow_html=True)

# ── Filters ──
c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
with c1:
    search = st.text_input("Search", placeholder="🔍 Search title or company...", label_visibility="collapsed")
with c2:
    role_filter = st.selectbox("Role", ["All Roles"] + sorted(df["search_term"].unique().tolist()), label_visibility="collapsed")
with c3:
    sen_filter = st.selectbox("Seniority", ["All Levels", "junior", "mid", "senior", "management"], label_visibility="collapsed")
with c4:
    sal_filter = st.selectbox("Salary", ["Any Salary", "$50k+", "$100k+", "$150k+", "$200k+"], label_visibility="collapsed")
with c5:
    remote_only = st.checkbox("Remote")

# ── Apply filters ──
filtered = df.copy()
if search:
    filtered = filtered[
        filtered["title"].str.contains(search, case=False, na=False) |
        filtered["company"].str.contains(search, case=False, na=False)
    ]
if role_filter != "All Roles":
    filtered = filtered[filtered["search_term"] == role_filter]
if sen_filter != "All Levels":
    filtered = filtered[filtered["seniority"] == sen_filter]
if sal_filter != "Any Salary":
    min_sal = int(sal_filter.replace("$","").replace("k+","")) * 1000
    filtered = filtered[filtered["salary_avg"] >= min_sal]
if remote_only:
    filtered = filtered[filtered["is_remote"] == True]

# ── KPIs ──
st.markdown("<br>", unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
avg_sal = filtered[filtered["salary_avg"] > 0]["salary_avg"].mean()
avg_sal = avg_sal if not pd.isna(avg_sal) else 0
with k1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-number">{len(filtered)}</div><div class="kpi-label">Jobs Found</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-number">${avg_sal:,.0f}</div><div class="kpi-label">Avg Salary</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-number">{filtered["company"].nunique()}</div><div class="kpi-label">Companies Hiring</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-number">{int(filtered["is_remote"].sum())}</div><div class="kpi-label">Remote Roles</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──
tab1, tab2 = st.tabs(["💼 Job Listings", "📊 Market Insights"])

# ── Tab 1: Job Cards ──
with tab1:
    sort_opt = st.selectbox("Sort by", ["Most Recent", "Highest Salary", "Company A-Z"])
    if sort_opt == "Highest Salary":
        filtered = filtered.sort_values("salary_avg", ascending=False)
    elif sort_opt == "Company A-Z":
        filtered = filtered.sort_values("company")
    else:
        filtered = filtered.sort_values("created_date", ascending=False, na_position="last")

    st.markdown(f"**Showing {len(filtered)} positions**")
    st.markdown("---")

    SENIORITY_EMOJI = {"senior": "🟣", "mid": "🔵", "junior": "🟢", "management": "🟠"}

    for _, job in filtered.head(50).iterrows():
        col_left, col_right = st.columns([4, 1])

        with col_left:
            sen_emoji = SENIORITY_EMOJI.get(str(job["seniority"]), "⚪")
            remote_tag = " 🌐 Remote" if job["is_remote"] else ""
            salary_text = f"💰 ${float(job['salary_avg']):,.0f}/yr" if float(job["salary_avg"]) > 0 else "💰 Salary not listed"
            date_str = job["created_date"].strftime("%b %d, %Y") if pd.notna(job["created_date"]) else "Recently posted"

            st.markdown(f"#### {job['title']}")
            st.markdown(f"🏢 **{job['company']}** &nbsp;|&nbsp; 📍 {job['location']}{remote_tag}")
            st.markdown(f"{sen_emoji} `{str(job['seniority']).title()}` &nbsp; 🔎 `{str(job['search_term']).title()}` &nbsp; 📅 {date_str}")
            st.markdown(f"{salary_text}")

        with col_right:
            url = str(job["redirect_url"])
            if url and url != "nan" and url != "":
                st.link_button("Apply Now →", url, type="primary")
            else:
                st.button("Apply Now →", disabled=True, key=f"btn_{job['id']}")

        st.markdown("---")

# ── Tab 2: Insights ──
with tab2:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("💰 Avg Salary by Role")
        sal = filtered[filtered["salary_avg"] > 0].groupby("search_term")["salary_avg"].mean().reset_index()
        sal.columns = ["Role", "Avg Salary"]
        sal = sal.sort_values("Avg Salary", ascending=True)
        fig = px.bar(sal, x="Avg Salary", y="Role", orientation="h",
                     color="Avg Salary", color_continuous_scale="Blues",
                     text=sal["Avg Salary"].apply(lambda x: f"${x:,.0f}"))
        fig.update_traces(textposition="outside")
        fig.update_layout(height=350, showlegend=False, plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("🏢 Top Hiring Companies")
        top = filtered["company"].value_counts().head(10).reset_index()
        top.columns = ["Company", "Jobs"]
        fig = px.bar(top, x="Jobs", y="Company", orientation="h",
                     color="Jobs", color_continuous_scale="Teal")
        fig.update_layout(height=350, showlegend=False, plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("📈 Jobs Posted Over Time")
        timeline = filtered[filtered["created_date"].notna()].copy()
        timeline = timeline.groupby("created_date").size().reset_index(name="count")
        fig = px.area(timeline, x="created_date", y="count",
                      color_discrete_sequence=["#3b82f6"])
        fig.update_layout(height=300, plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.subheader("🎯 Seniority Breakdown")
        sen = filtered["seniority"].value_counts().reset_index()
        sen.columns = ["Seniority", "Count"]
        fig = px.pie(sen, values="Count", names="Seniority",
                     color_discrete_sequence=["#1e3a8a","#3b82f6","#93c5fd","#dbeafe"])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("💼 Salary Distribution by Role")
    sal_dist = filtered[filtered["salary_avg"] > 0]
    fig = px.box(sal_dist, x="search_term", y="salary_avg",
                 color="search_term",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(height=400, showlegend=False,
                      xaxis_title="Role", yaxis_title="Salary ($)",
                      plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)