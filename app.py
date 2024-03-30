import pandas as pd
import altair as alt
import streamlit as st
from local_components import card_container

# Set Streamlit page configuration
st.set_page_config(
    page_title="Analisis Trending Start-up Gas Turbine",
    layout="wide"
)

# Adjust the spacing at the top and bottom of the page
st.markdown("""
    <style>
        div.block-container {padding-top:1rem;}
        div.block-container {padding-bottom:1rem;}
    </style>
""", unsafe_allow_html=True)

# Add title to the page
st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>Analisis Trending Start-up Gas Turbine</h1>", unsafe_allow_html=True)

# Function to fetch data with caching
@st.cache_data
def fetch_data(file, start, end):
    data = pd.read_csv(file)
    data = data.iloc[start:end + 1]
    data = data.reset_index(drop=True)
    return data

# Fetch successful data
df_berhasil = fetch_data("start berhasil.csv", 1164, 2463)

# Add a sidebar for uploading data
with st.sidebar:
    st.markdown("<h4>Unggah Data (CSV)</h4>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "label",
        accept_multiple_files=False,
        type=["CSV"],
        label_visibility="collapsed"
    )

# Check if a file is uploaded
if uploaded_file:
    # Read the uploaded data
    df_gagal = pd.read_csv(uploaded_file)
    # Find the earliest index where G1.L4 is equal to 1
    earliest_index = df_gagal[df_gagal["G1.L4"] == 1].index.min()
    # Filter the data from the mentioned earliest index onwards
    df_gagal = df_gagal.loc[earliest_index:]
    # Ensure that the length of the failure data matches the length of successful data
    df_gagal = df_gagal.head(len(df_berhasil))
    # Reset index for both dataframes
    df_gagal = df_gagal.reset_index(drop=True)

    # Add columns and tolerance level selectors
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("<h4>Kolom</h4>", unsafe_allow_html=True)
        # Allow user to select columns to compare
        col_choices = st.multiselect(
            "label",
            options=sorted([col for col in df_berhasil.columns if "Time" not in col]),
            max_selections=15,
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("<h4>Batas Toleransi (%)</h4>", unsafe_allow_html=True)
        # Allow user to set tolerance level
        tolerance = st.number_input(
            "label",
            min_value=0.00,
            max_value=100.00,
            value=5.00,
            step=0.01,
            label_visibility="collapsed"
        )

    # Proceed if columns are selected
    if col_choices:
        selected_df_berhasil = df_berhasil[col_choices]
        selected_df_gagal = df_gagal[col_choices]

        # Display comparison metrics
        st.markdown("<h4>Grafik Perbandingan Berhasil dan Gagal</h4>", unsafe_allow_html=True)

        # Compute and display metrics for each selected column
        # These metrics include minimum, maximum, and average differences between successful and failed data
        list_min, list_maxs, list_means = [], [], []
        for col_name in col_choices:
            diff = ((selected_df_gagal[col_name] - selected_df_berhasil[col_name]) / selected_df_berhasil[col_name] * 100).abs()
            list_min.append(diff.min())
            list_maxs.append(diff.max())
            list_means.append(diff.mean())

        # Initialize session state variables to keep track of displayed metrics
        if "count" not in st.session_state:
            st.session_state.count = 0

        st.session_state.cols = col_choices
        st.session_state.mins = list_min
        st.session_state.maxs = list_maxs
        st.session_state.means = list_means

        # Function to display a metric for the current count
        def display_metric():
            if st.session_state.count >= len(st.session_state.cols):
                st.session_state.count = len(st.session_state.cols) - 1 

            col = st.session_state.cols[st.session_state.count]
            diff_min = st.session_state.mins[st.session_state.count]
            diff_max = st.session_state.maxs[st.session_state.count]
            diff_mean = st.session_state.means[st.session_state.count]

            col1, col2, col3 = st.columns(3)
            with col1:
                with card_container(key="metric1"):
                    st.metric(f"Minimal ({col})", f"{diff_min:.2f}%")

            with col2:
                with card_container(key="metric2"):
                    st.metric(f"Maksimal ({col})", f"{diff_max:.2f}%")

            with col3:
                with card_container(key="metric3"):
                    st.metric(f"Rata-rata ({col})", f"{diff_mean:.2f}%")

            # Display data in an expander
            with st.expander("Lihat data"):
                diff_df = pd.concat([df_berhasil[[col]], df_gagal[[col]]], axis=1)
                diff_df.columns = [f"Berhasil ({col})", f"Gagal ({col})"]
                diff_df["Perbedaan"] = ((diff_df[f"Gagal ({col})"] - diff_df[f"Berhasil ({col})"]) / diff_df[f"Berhasil ({col})"]).abs()
                st.dataframe(
                    diff_df.sort_values("Perbedaan", ascending=False),
                    column_config={
                        "Perbedaan": st.column_config.ProgressColumn(
                            "Perbedaan",
                            help=f"Bar penuh menunjukkan perbedaan lebih besar atau sama dengan {tolerance:.2f}%",
                            min_value=0,
                            max_value=tolerance / 100
                        )
                    },
                    height=250,
                    hide_index=True,
                    use_container_width=True,
                )

        # Function to display the next metric
        def next_metric():
            if st.session_state.count + 1 >= len(st.session_state.means):
                st.session_state.count = 0
            else:
                st.session_state.count += 1

        # Function to display the previous metric
        def previous_metric():
            if st.session_state.count == 0:
                st.session_state.count = len(st.session_state.means) - 1
            else:
                st.session_state.count -= 1

        # Display the current metric
        display_metric()

        # Add buttons for navigating through metrics
        cols = st.columns(8)
        with cols[0]:
            if st.button("⏮️ Previous", type="primary", on_click=previous_metric, use_container_width=True):
                pass

        with cols[-1]:
            if st.button("Next ⏭️", type="primary", on_click=next_metric, use_container_width=True):
                pass

        # Prepare data for line chart
        melted_df_berhasil = selected_df_berhasil.reset_index().melt(id_vars="index", var_name="Kolom", value_name="Nilai")
        melted_df_gagal = selected_df_gagal.reset_index().melt(id_vars="index", var_name="Kolom", value_name="Nilai")
        melted_df_berhasil["Sumber"] = "Berhasil"
        melted_df_gagal["Sumber"] = "Gagal"
        melted_df = pd.concat([melted_df_berhasil, melted_df_gagal])

        # Define chart properties
        gap_percentage = 0.01
        y_min = min(melted_df["Nilai"]) * (1 - gap_percentage)
        y_max = max(melted_df["Nilai"]) * (1 + gap_percentage)

        chart = alt.Chart(melted_df).mark_line(
            strokeWidth=3
        ).encode(
            x="index",
            y=alt.Y("Nilai", scale=alt.Scale(domain=[y_min, y_max])),
            color="Kolom",
            strokeDash="Sumber",
            detail="Kolom",
            opacity=alt.condition(alt.datum.Sumber == "Berhasil", alt.value(1), alt.value(0.7)),
            tooltip=["Kolom", "Sumber", "Nilai"]
        ).configure_axisX(
            title=None,
            grid=False
        ).configure_axisY(
            grid=False
        )

        # Display chart
        with card_container(key="chart"):
            st.altair_chart(chart, use_container_width=True)

        # Check if differences exceed tolerance level
        exceed_tolerance = {}
        change_info = ""
        for col_name, mean in zip(col_choices, list_means):
            exceed_tolerance[col_name] = mean > tolerance

            if mean > tolerance:
                diff_info = f"Terdapat perbedaan lebih dari {tolerance:.2f}% pada kolom {col_name}."
            elif mean == 0:
                diff_info = f"Tidak terdapat perbedaan pada kolom {col_name}."
            else:
                diff_info = f"Terdapat perbedaan kurang dari {tolerance:.2f}% pada kolom {col_name}."

            change_info += f"\n- {diff_info}"

        # Display information about differences
        st.info(change_info)

    else:
        # Inform the user to select columns for comparison
        st.info("Silakan pilih satu atau lebih kolom untuk menampilkan grafik.", icon="ℹ️")

else:
    # Inform the user to upload data
    st.info("Silakan unggah data terlebih dahulu.", icon="ℹ️")