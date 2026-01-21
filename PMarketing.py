import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
COMPANY_LIST = ["Pick Name Here", "Summer Fridays", "Thrive", "Trinity Solar", "ATI", "Rough Country"]

st.set_page_config(page_title="TSG Performance Marketing Data Entry", page_icon="📈")

# --- AUTHENTICATION LOGIC ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    # Return True if the user has already verified their password
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    st.text_input(
        "Please enter the access password", type="password", on_change=password_entered, key="password"
    )
    
    # If incorrect, show error
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
        
    return False

# --- MAIN APP EXECUTION ---
if check_password():
    # EVERYTHING ELSE GOES HERE (Indented)
    
    st.title("📈 TSG Performance Marketing Entry")

    # 1. Establish Connection
    conn = st.connection("gsheets", type=GSheetsConnection)

    # 2. Fetch existing data
    try:
        existing_data = conn.read(worksheet="Sheet1", ttl=5)
    except:
        st.warning("Please Enter Data Below")
        existing_data = pd.DataFrame()

    # 3. The Entry Form
    with st.form("marketing_entry_form"):
        st.subheader("1. General Info")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            company = st.selectbox("Company Name", options=COMPANY_LIST)
        with col_b:
            entered_by = st.text_input("Entered By (Your Name)")
        with col_c:
            report_date = st.date_input("Report Month", value=datetime.today())

        st.divider()
        
        st.subheader("2. Performance Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Spend & Reach**")
            marketing_spend = st.number_input("Total Spend ($)", min_value=0.0, format="%.2f")
            impressions = st.number_input("Impressions", min_value=0, step=100)
            clicks = st.number_input("Clicks", min_value=0, step=10)
        
        with col2:
            st.markdown("**Conversion Data**")
            conversions = st.number_input("Total Conversions", min_value=0, step=1)
            qualified_leads = st.number_input("Qualified Leads (MQL/SQL)", min_value=0, step=1)
        
        with col3:
            st.markdown("**Revenue (Optional)**")
            revenue = st.number_input("Attributed Revenue ($)", min_value=0.0, format="%.2f")

        st.divider()
        notes = st.text_area("Campaign Notes / Anomalies")

        submitted = st.form_submit_button("Submit Entry", type="primary")

        if submitted:
            if not entered_by:
                st.error("Please fill in all fields.")
            else:
                entry_data = {
                    "Entry Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Report Month": report_date.strftime("%Y-%m-%d"),
                    "Company": company,
                    "Entered By": entered_by,
                    "Spend": marketing_spend,
                    "Impressions": impressions,
                    "Clicks": clicks,
                    "Conversions": conversions,
                    "Qualified Leads": qualified_leads,
                    "Revenue": revenue,
                    "Notes": notes
                }
                
                new_row = pd.DataFrame([entry_data])
                updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.success(f"Success! Data for **{company}** saved.")
                st.cache_data.clear()