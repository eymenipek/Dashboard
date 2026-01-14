import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO
import requests

st.set_page_config(page_title="Data Viewer & Plotter", layout="wide")

st.title("📊 Data Viewer & Plotter")
st.markdown("Upload or import CSV, XLSX, or Parquet files from GitHub")

# Tabs for different input methods
tab1, tab2 = st.tabs(["Upload File", "GitHub Import"])

with tab1:
    st.subheader("Upload File")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx", "parquet"]
    )
    df = None
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.parquet'):
                df = pd.read_parquet(uploaded_file)
            st.success(f"✅ File '{uploaded_file.name}' loaded successfully!")
        except Exception as e:
            st.error(f"Error reading file: {e}")

with tab2:
    st.subheader("Import from GitHub")
    github_url = st.text_input(
        "Enter GitHub raw file URL",
        placeholder="https://raw.githubusercontent.com/username/repo/branch/path/file.csv"
    )
    
    if github_url:
        try:
            response = requests.get(github_url)
            response.raise_for_status()
            
            if github_url.endswith('.csv'):
                df = pd.read_csv(StringIO(response.text))
            elif github_url.endswith('.xlsx'):
                df = pd.read_excel(StringIO(response.content))
            elif github_url.endswith('.parquet'):
                df = pd.read_parquet(StringIO(response.content))
            st.success("✅ File loaded successfully from GitHub!")
        except Exception as e:
            st.error(f"Error loading from GitHub: {e}")

# Display data and create visualizations
if df is not None:
    st.markdown("---")
    
    # Display table
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📋 Data Preview")
        st.write(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    with col2:
        st.subheader("📈 Data Info")
        st.write(f"Columns: {', '.join(df.columns.tolist())}")
    
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    
    # Plotting section
    st.subheader("📊 Create Visualization")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        plot_type = st.selectbox(
            "Select plot type",
            ["Scatter", "Line", "Bar", "Histogram", "Box", "Violin"]
        )
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    all_cols = df.columns.tolist()
    
    with col2:
        if plot_type in ["Scatter", "Line", "Bar", "Box", "Violin"]:
            x_col = st.selectbox("X-axis", all_cols)
        else:
            x_col = st.selectbox("Column", numeric_cols if numeric_cols else all_cols)
    
    with col3:
        if plot_type in ["Scatter", "Line", "Bar"]:
            y_col = st.selectbox("Y-axis", numeric_cols if numeric_cols else all_cols)
        elif plot_type in ["Box", "Violin"]:
            y_col = st.selectbox("Y-axis", numeric_cols if numeric_cols else all_cols)
        else:
            y_col = None
    
    try:
        # Create plot based on selection
        if plot_type == "Scatter":
            fig = px.scatter(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}")
        elif plot_type == "Line":
            fig = px.line(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}")
        elif plot_type == "Bar":
            fig = px.bar(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}")
        elif plot_type == "Histogram":
            fig = px.histogram(df, x=x_col, title=f"Distribution of {x_col}")
        elif plot_type == "Box":
            fig = px.box(df, x=x_col, y=y_col, title=f"Box Plot: {x_col}")
        elif plot_type == "Violin":
            fig = px.violin(df, x=x_col, y=y_col, title=f"Violin Plot: {x_col}")
        
        fig.update_layout(height=500, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating plot: {e}")
    
    # Download options
    st.markdown("---")
    st.subheader("💾 Download Data")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            label="Download as CSV",
            data=df.to_csv(index=False),
            file_name="data.csv",
            mime="text/csv"
        )
    with col2:
        st.download_button(
            label="Download as Excel",
            data=df.to_excel(index=False),
            file_name="data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col3:
        st.download_button(
            label="Download as Parquet",
            data=df.to_parquet(index=False),
            file_name="data.parquet",
            mime="application/octet-stream"
        )
else:
    st.info("👆 Upload a file or import from GitHub to get started")
