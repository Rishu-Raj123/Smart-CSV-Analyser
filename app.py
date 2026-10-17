import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from csv_utils import (
    build_column_profile,
    clean_dataframe,
    dataframe_to_csv_bytes,
    get_numeric_summary,
    get_overview,
    read_uploaded_csv,
)

st.set_page_config(
    page_title="CSV Analyser",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 CSV Analyser")
st.caption("Explore CSV files, check data quality, create charts, and export a cleaned copy.")

with st.sidebar:
    st.header("Upload")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    st.divider()
    st.header("Cleaning options")
    drop_duplicates = st.checkbox("Remove duplicate rows", value=True)
    fill_missing = st.checkbox("Fill missing values", value=False)
    fill_strategy = st.selectbox(
        "Missing-value strategy",
        [
            "Median for numeric / mode for text",
            "Zero for numeric / empty text",
        ],
        disabled=not fill_missing,
    )
    trim_text = st.checkbox("Trim whitespace in text columns", value=True)
    st.caption("These options affect the export preview, not the original uploaded file.")

if uploaded_file is None:
    st.subheader("Welcome")
    st.markdown(
        """
        Upload a CSV file to get started.

        **Features**
        - Dataset overview and data preview
        - Missing-value and duplicate-row checks
        - Numeric summaries and categorical value counts
        - Interactive Plotly charts
        - Optional data cleaning and CSV download

        **Tip:** Files with column headers are easiest to explore.
        """
    )
    st.stop()

try:
    df = read_uploaded_csv(uploaded_file)
except Exception as exc:
    st.error(f"Could not read this CSV file: {exc}")
    st.info("Try exporting the file as CSV (UTF-8) and upload it again.")
    st.stop()

if len(df.columns) == 0:
    st.warning("This file has no readable columns. Please upload a non-empty CSV.")
    st.stop()

overview = get_overview(df)
profile = build_column_profile(df)

st.subheader("Dataset overview")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Rows", f"{overview['rows']:,}")
m2.metric("Columns", f"{overview['columns']:,}")
m3.metric("Missing cells", f"{overview['missing_cells']:,}")
m4.metric("Duplicate rows", f"{overview['duplicate_rows']:,}")

tab_preview, tab_quality, tab_stats, tab_charts, tab_clean = st.tabs(
    ["Preview", "Data quality", "Statistics", "Visualize", "Clean & export"]
)

with tab_preview:
    st.markdown("#### Data preview")
    st.dataframe(df.head(100), use_container_width=True, height=360)
    st.caption(f"Showing up to 100 of {len(df):,} rows.")
    with st.expander("Column names and data types"):
        type_df = pd.DataFrame({
            "Column": [str(c) for c in df.columns],
            "Data type": [str(dtype) for dtype in df.dtypes],
        })
        st.dataframe(type_df, use_container_width=True, hide_index=True)

with tab_quality:
    st.markdown("#### Column quality profile")
    
    st.dataframe(profile, use_container_width=True, hide_index=True)
    left, right = st.columns(2)
    with left:
        missing_df = profile.loc[profile["Missing"] > 0, ["Column", "Missing", "Missing %"]]
        if missing_df.empty:
            st.success("No missing values detected.")
        else:
            fig = px.bar(missing_df, x="Column", y="Missing", title="Missing values by column")
            fig.update_layout(xaxis_tickangle=-35)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with right:
        st.metric("Completely empty columns", int(df.isna().all().sum()))
        st.metric("Completely empty rows", int(df.isna().all(axis=1).sum()))

with tab_stats:
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    if numeric_cols:
        st.markdown("#### Numeric summary")
        st.dataframe(get_numeric_summary(df), use_container_width=True)
        selected_numeric = st.selectbox("Inspect a numeric column", numeric_cols)
        values = pd.to_numeric(df[selected_numeric], errors="coerce").dropna()
        if not values.empty:
            a, b, c = st.columns(3)
            a.metric("Mean", f"{values.mean():,.3g}")
            b.metric("Median", f"{values.median():,.3g}")
            c.metric(
                "Standard deviation",
                f"{values.std():,.3g}" if len(values) > 1 else "N/A",
            )
    else:
        st.info("No numeric columns were detected.")

    categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    if categorical_cols:
        st.markdown("#### Categorical value counts")
        selected_cat = st.selectbox("Inspect a categorical column", categorical_cols)
        counts = df[selected_cat].fillna("(missing)").astype(str).value_counts().head(20)
        counts_df = counts.rename_axis("Value").reset_index(name="Count")
        st.dataframe(counts_df, use_container_width=True, hide_index=True)

with tab_charts:
    st.markdown("#### Create an interactive chart")
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    all_cols = [str(c) for c in df.columns]
    chart_type = st.selectbox("Chart type", ["Histogram", "Bar chart", "Scatter plot", "Box plot"])

    if chart_type == "Histogram":
        if not numeric_cols:
            st.info("A histogram requires at least one numeric column.")
        else:
            col = st.selectbox("Numeric column", numeric_cols, key="hist_col")
            fig = px.histogram(df, x=col, title=f"Distribution of {col}", marginal="box")
            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Bar chart":
        col = st.selectbox("Column to count", all_cols, key="bar_col")
        top_n = st.slider("Categories to display", min_value=5, max_value=30, value=10)
        counts = df[col].fillna("(missing)").astype(str).value_counts().head(top_n)
        chart_df = counts.rename_axis("Value").reset_index(name="Count")
        fig = px.bar(chart_df, x="Value", y="Count", title=f"Top values in {col}")
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Scatter plot":
        if len(numeric_cols) < 2:
            st.info("A scatter plot requires at least two numeric columns.")
        else:
            x_col = st.selectbox("X-axis", numeric_cols, key="scatter_x")
            y_options = [c for c in numeric_cols if c != x_col]
            y_col = st.selectbox("Y-axis", y_options, key="scatter_y")
            color_col = st.selectbox("Optional color grouping", ["None"] + all_cols)
            kwargs = {} if color_col == "None" else {"color": color_col}
            fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}", **kwargs)
            st.plotly_chart(fig, use_container_width=True)

    else:
        if not numeric_cols:
            st.info("A box plot requires at least one numeric column.")
        else:
            col = st.selectbox("Numeric column", numeric_cols, key="box_col")
            fig = px.box(df, y=col, title=f"Box plot of {col}")
            st.plotly_chart(fig, use_container_width=True)

with tab_clean:
    st.markdown("#### Clean and export")
    cleaned = clean_dataframe(
        df,
        drop_duplicates=drop_duplicates,
        fill_missing=fill_missing,
        fill_strategy=fill_strategy,
        trim_text=trim_text,
    )
    before_rows, after_rows = len(df), len(cleaned)
    a, b, c = st.columns(3)
    a.metric("Original rows", f"{before_rows:,}")
    b.metric("Export rows", f"{after_rows:,}")
    b_delta = before_rows - after_rows
    c.metric("Rows removed", f"{b_delta:,}")
    st.dataframe(cleaned.head(100), use_container_width=True, height=300)
    st.download_button(
        "Download cleaned CSV",
        data=dataframe_to_csv_bytes(cleaned),
        file_name="cleaned_data.csv",
        mime="text/csv",
        use_container_width=True,
    )
st.divider()