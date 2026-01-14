import streamlit as st
import pandas as pd
from io import StringIO
import requests

try:
    import plotly.express as px
except ImportError:
    st.error("⚠️ Plotly is not installed. Please install it with: pip install plotly")
    st.stop()

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
    
    # Resampling section
    st.subheader("⏰ Time Series Resampling")
    
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    all_cols_for_time = df.columns.tolist()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        time_col = st.selectbox("Select time column", all_cols_for_time)
    
    with col2:
        freq_options = {
            "5S": "5 Seconds",
            "10S": "10 Seconds",
            "30S": "30 Seconds",
            "T": "Minute",
            "H": "Hourly",
            "D": "Daily",
            "W": "Weekly",
            "M": "Monthly",
            "Q": "Quarterly",
            "Y": "Yearly"
        }
        resample_freq = st.selectbox(
            "Resample frequency",
            list(freq_options.keys()),
            format_func=lambda x: freq_options.get(x, x)
        )
    
    with col3:
        agg_method = st.selectbox(
            "Aggregation method",
            ["mean", "sum", "min", "max", "std", "count", "first", "last"]
        )
    
    with col4:
        resample_button = st.button("🔄 Resample Data")
    
    df_resampled = None
    
    if resample_button:
        try:
            # Create a copy for resampling
            df_resample = df.copy()
            
            # Check if column is numeric (seconds since epoch)
            if pd.api.types.is_numeric_dtype(df_resample[time_col]):
                # Assume it's seconds, convert to datetime
                df_resample['time_dt'] = pd.to_datetime(df_resample[time_col], unit='s', errors='coerce')
                original_time_col = time_col
                time_col_dt = 'time_dt'
            else:
                # Try to parse as datetime string
                df_resample['time_dt'] = pd.to_datetime(df_resample[time_col], errors='coerce')
                original_time_col = time_col
                time_col_dt = 'time_dt'
            
            # Check if conversion was successful
            if df_resample[time_col_dt].isna().all():
                st.error(f"❌ Column '{original_time_col}' could not be converted to datetime format.")
            else:
                if df_resample[time_col_dt].isna().any():
                    st.warning(f"⚠️ Some values in '{original_time_col}' could not be converted and will be ignored.")
                    df_resample = df_resample.dropna(subset=[time_col_dt])
                
                df_resample = df_resample.set_index(time_col_dt)
                
                # Resample numeric columns
                numeric_cols_all = df_resample.select_dtypes(include=['number']).columns.tolist()
                # Remove the original time column if it's numeric
                numeric_cols_all = [col for col in numeric_cols_all if col != original_time_col]
                
                if len(numeric_cols_all) == 0:
                    st.error("❌ No numeric columns found to resample.")
                else:
                    df_resampled = df_resample[numeric_cols_all].resample(resample_freq).agg(agg_method)
                    df_resampled = df_resampled.reset_index()
                    
                    # Convert datetime index back to seconds (Unix timestamp)
                    df_resampled[original_time_col] = (df_resampled[time_col_dt].astype(int) / 1e9).astype(int)
                    df_resampled = df_resampled.drop(columns=[time_col_dt])
                    
                    # Reorder columns
                    cols = [original_time_col] + [col for col in df_resampled.columns if col != original_time_col]
                    df_resampled = df_resampled[cols]
                    
                    st.success(f"✅ Data resampled to {agg_method.upper()} by {resample_freq}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Original rows", df.shape[0])
                    with col2:
                        st.metric("Resampled rows", df_resampled.shape[0])
                    
                    st.dataframe(df_resampled, use_container_width=True)
        except Exception as e:
            st.error(f"❌ Error resampling data: {e}")
    
    st.markdown("---")
    
    # Plotting section
    st.subheader("📊 Create Visualization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        plot_type = st.selectbox(
            "Select plot type",
            ["Scatter", "Line", "Bar", "Histogram", "Box", "Violin"]
        )
    
    with col2:
        compare_resampled = st.checkbox(
            "Compare original vs resampled data",
            value=False,
            disabled=(df_resampled is None)
        )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        plot_type = st.selectbox(
            "Select plot type",
            ["Scatter", "Line", "Bar", "Histogram", "Box", "Violin"],
            key="plot_type_main"
        )
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    all_cols = df.columns.tolist()
    
    with col2:
        if plot_type in ["Scatter", "Line", "Bar", "Box", "Violin"]:
            x_col = st.selectbox("X-axis", all_cols, key="x_col_main")
        else:
            x_col = st.selectbox("Column", numeric_cols if numeric_cols else all_cols, key="x_col_hist")
    
    with col3:
        if plot_type in ["Scatter", "Line", "Bar"]:
            y_col = st.selectbox("Y-axis", numeric_cols if numeric_cols else all_cols, key="y_col_main")
        elif plot_type in ["Box", "Violin"]:
            y_col = st.selectbox("Y-axis", numeric_cols if numeric_cols else all_cols, key="y_col_bv")
        else:
            y_col = None
    
    try:
        if compare_resampled and df_resampled is not None:
            # Create overlapped comparison plot
            st.subheader("📈 Original vs Resampled Data (Overlapped)")
            
            # Only works for line and scatter plots
            if plot_type in ["Line", "Scatter"]:
                # Create figure with original data
                if plot_type == "Line":
                    fig = px.line(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col} - Original vs Resampled")
                else:
                    fig = px.scatter(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col} - Original vs Resampled")
                
                # Add resampled data as overlay
                if plot_type == "Line":
                    fig_resampled = px.line(df_resampled, x=x_col, y=y_col)
                else:
                    fig_resampled = px.scatter(df_resampled, x=x_col, y=y_col)
                
                # Add resampled traces to original figure
                for trace in fig_resampled.data:
                    trace.name = f"{trace.name} (Resampled)"
                    trace.line.width = 3
                    trace.line.dash = "dash"
                    fig.add_trace(trace)
                
                # Update layout with CMU Serif font
                fig.update_layout(
                    height=600,
                    hovermode="x unified",
                    font=dict(family="CMU Serif", size=12),
                    title=dict(font=dict(family="CMU Serif", size=16)),
                    xaxis=dict(title=dict(font=dict(family="CMU Serif", size=12))),
                    yaxis=dict(title=dict(font=dict(family="CMU Serif", size=12)))
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📌 Overlapped comparison is only available for Line and Scatter plots. Please select one of these plot types.")
                
                # Show single plot instead
                if plot_type == "Bar":
                    fig = px.bar(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}")
                elif plot_type == "Histogram":
                    fig = px.histogram(df, x=x_col, title=f"Distribution of {x_col}")
                elif plot_type == "Box":
                    fig = px.box(df, x=x_col, y=y_col, title=f"Box Plot: {x_col}")
                elif plot_type == "Violin":
                    fig = px.violin(df, x=x_col, y=y_col, title=f"Violin Plot: {x_col}")
                
                fig.update_layout(
                    height=500,
                    hovermode="x unified",
                    font=dict(family="CMU Serif", size=12),
                    title=dict(font=dict(family="CMU Serif", size=16)),
                    xaxis=dict(title=dict(font=dict(family="CMU Serif", size=12))),
                    yaxis=dict(title=dict(font=dict(family="CMU Serif", size=12)))
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            # Single plot
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
            
            fig.update_layout(
                height=500,
                hovermode="x unified",
                font=dict(family="CMU Serif", size=12),
                title=dict(font=dict(family="CMU Serif", size=16)),
                xaxis=dict(title=dict(font=dict(family="CMU Serif", size=12))),
                yaxis=dict(title=dict(font=dict(family="CMU Serif", size=12)))
            )
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
