import streamlit as st
import pandas as pd
import io

# Set page config
st.set_page_config(page_title="ISG Data Integrator", layout="wide")

# App title
st.markdown("<h1 style='text-align: center; color: navy;'>ISG Data Integrator</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Sidebar info
with st.sidebar:
    st.image("https://streamlit.io/images/brand/streamlit-logo-primary-colormark-darktext.png", width=200)
    st.header("Navigation")
    st.markdown("1. Upload ISG CSV\n2. Upload Master File\n3. Select Columns\n4. Download Updated CSV")
    st.markdown("---")
    st.info("Ensure all files include `ITGRC_App_ID` column for proper merging.")

# Step 1: Upload ISG CSV File
with st.expander("📁 Step 1: Upload ISG CSV File", expanded=True):
    isg_file = st.file_uploader("Upload ISG_file.csv", type="csv", key="isg")
    if isg_file:
        isg_df = pd.read_csv(isg_file)

        # Add columns if missing
        required_columns = ['UH', 'FH', 'VH', 'Category', 'Subcategory']
        for col in required_columns:
            if col not in isg_df.columns:
                isg_df[col] = ''

        st.success("✅ Added missing columns: UH, FH, VH, Category, Subcategory")
        st.dataframe(isg_df.head(), use_container_width=True)
    else:
        isg_df = None

# Step 2: Upload Master Excel File
if isg_df is not None:
    with st.expander("📘 Step 2: Upload Master Excel File", expanded=True):
        master_file = st.file_uploader("Upload Master_file.xlsx", type=["xlsx"], key="master")
        if master_file:
            all_sheets = pd.read_excel(master_file, sheet_name=None)
            sheet_names = list(all_sheets.keys())

            main_sheet = st.selectbox("Select Main Sheet", sheet_names, key="main_sheet")
            extra_sheet = st.selectbox("Select Additional Sheet", sheet_names, key="extra_sheet")

            master_df = all_sheets[main_sheet]
            extra_df = all_sheets[extra_sheet]

            common_key = 'ITGRC_App_ID'

            if common_key not in isg_df.columns or common_key not in master_df.columns or common_key not in extra_df.columns:
                st.error(f"❌ Missing '{common_key}' in one or more files.")
            else:
                # Step 3: Column Selection
                with st.expander("🧩 Step 3: Select Columns to Merge", expanded=True):
                    master_cols = [col for col in master_df.columns if col != common_key and col in isg_df.columns]
                    extra_cols = [col for col in extra_df.columns if col != common_key and col in isg_df.columns]

                    selected_master_cols = st.multiselect("Select columns from Main Sheet", master_cols)
                    selected_extra_cols = st.multiselect("Select columns from Additional Sheet", extra_cols)

                    updated_df = isg_df.copy()

                    # Merge and update with master
                    if selected_master_cols:
                        master_subset = master_df[[common_key] + selected_master_cols]
                        updated_df = updated_df.merge(master_subset, on=common_key, how='left', suffixes=('', '_new'))

                        for col in selected_master_cols:
                            updated_df[col] = updated_df[f"{col}_new"].combine_first(updated_df[col])
                            updated_df.drop(columns=[f"{col}_new"], inplace=True)

                    # Merge and update with extra
                    if selected_extra_cols:
                        extra_subset = extra_df[[common_key] + selected_extra_cols]
                        updated_df = updated_df.merge(extra_subset, on=common_key, how='left', suffixes=('', '_new'))

                        for col in selected_extra_cols:
                            updated_df[col] = updated_df[f"{col}_new"].combine_first(updated_df[col])
                            updated_df.drop(columns=[f"{col}_new"], inplace=True)

                    st.success("✅ Data successfully updated!")
                    st.dataframe(updated_df.head(), use_container_width=True)

                    # Step 4: Download final CSV
                    with st.expander("📥 Step 4: Download Updated CSV"):
                        csv_buffer = io.StringIO()
                        updated_df.to_csv(csv_buffer, index=False)
                        csv_data = csv_buffer.getvalue().encode('utf-8')

                        st.download_button(
                            label="⬇️ Download Final CSV",
                            data=csv_data,
                            file_name="updated_ISG_file.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
