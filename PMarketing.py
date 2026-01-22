import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- NEW IMPORTS FOR DRIVE UPLOAD ---
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- NEW IMPORTS FOR EMAIL ---
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# --- CONFIGURATION ---
COMPANY_LIST = ["Pick Company Here","ATI", "Brewdog", "Cadogan Tate", "Corepower"
,"Crumbl","Dude Wipes","Eos Fitness","Hempz","Legacy.com",
"Mavis Discount Tire","Phlur","Powerstop"
,"Pura Vida","Radiance","Revolut","Rough Country"
,"Summer Fridays","Superstar Car Wash","Thrive",
"Tukios","Wrench"
]

st.set_page_config(page_title="TSG Portfolio Marketing Data Entry", page_icon="📈", layout="wide")

# --- AUTHENTICATION LOGIC ---
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input("Please enter the access password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    return False
    
# --- EMAIL FUNCTION ---
def send_email_with_attachment(uploaded_file, user_note):
    """Sends the uploaded file to the admin email via SMTP."""
    
    # Load secrets
    sender_email = st.secrets["email"]["sender_email"]
    sender_password = st.secrets["email"]["sender_password"]
    receiver_email = st.secrets["email"]["receiver_email"]

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"📎 New File Upload: {uploaded_file.name}"

    body = f"A new file was uploaded via the Marketing App.\n\nNote: {user_note}"
    msg.attach(MIMEText(body, 'plain'))

    # Process attachment
    # We read the uploaded file bytes directly from Streamlit
    part = MIMEBase('application', "octet-stream")
    part.set_payload(uploaded_file.getvalue())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{uploaded_file.name}"')
    msg.attach(part)

    # Send via Gmail SMTP
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email Error: {e}")
        return False

# --- DRIVE UPLOAD FUNCTION ---
def save_file_to_drive(uploaded_file):
    """Uploads a file to the specific Google Drive folder defined in secrets."""
    # Load credentials from the same secrets we use for Sheets
    # We convert the Streamlit Secrets object to a standard Python dict for the Drive API
    secrets_dict = dict(st.secrets["connections"]["gsheets"])
    
    # Authenticate
    creds = service_account.Credentials.from_service_account_info(
        secrets_dict,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build('drive', 'v3', credentials=creds)

    # File Metadata (Name + Parent Folder)
    file_metadata = {
        'name': uploaded_file.name,
        'parents': [st.secrets["connections"]["gsheets"]["drive_folder_id"]]
    }
    
    # Upload Logic
    media = MediaIoBaseUpload(uploaded_file, mimetype=uploaded_file.type)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    return file.get('id')

# --- MAIN APP EXECUTION ---
if check_password():
    
    # --- SIDEBAR (Uploads + Definitions) ---
    with st.sidebar:
        # 1. File Uploader Section
        st.header("📂 File Upload")
        st.markdown("Submit historical data via upload.")
        
        uploaded_file = st.file_uploader("Choose a file", accept_multiple_files=False)
        
        # Add a text input for the note (so you have something to pass to the function)
        email_note = st.text_input("Short note for submitting (optional)")
        
        if uploaded_file is not None:
            # Change button text to be clear
            if st.button("Submit File 📨", type="primary"):
                with st.spinner("Sending file..."):
                    # --- THE FIX IS HERE ---
                    # We call the EMAIL function, not the DRIVE function
                    success = send_email_with_attachment(uploaded_file, email_note)
                    
                    if success:
                        st.success("✅ File sent successfully!")
        
        st.divider()

        # 2. Definitions Section (Keep the rest the same)
        st.header("📝 Metric Definitions")
        st.info("Hover over the (?) icon next to form fields for quick tips.")
        
        with st.expander("💰 Financials", expanded=False):
            st.markdown("""
            **Total Digital Spend:** Working Media spend only (FB, Google, TikTok, Affiliate, etc.). 
            * *Includes:* Retargeting & Brand Search.
            * *Excludes:* Agency fees, production, headcount.
            
            **Gross Profit:** Total gross profit dollars.
            """)

        with st.expander("👥 Customers & Orders", expanded=False):
            st.markdown("""
            **New Customers:** Unique users transacting for the first time.
            **Repeat Customers:** Returning users who transacted.
            """)

    # --- MAIN PAGE CONTENT ---
    st.title("📈 TSG Portfolio Monthly Performance Entry")

    # 1. Establish Connection
    conn = st.connection("gsheets", type=GSheetsConnection)

    # 2. Fetch existing data (with error handling for empty sheets)
    try:
        existing_data = conn.read(worksheet="Sheet1", ttl=5)
    except:
        st.warning("No existing data found. Starting fresh.")
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
        
        st.subheader("2. Financials")
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            digital_spend = st.number_input(
                "Total Digital Spend ($)", 
                min_value=0.0, format="%.2f",
                help="Total Working Media (FB, Google, TikTok, Affiliate). Excludes agency fees/production. Includes Retargeting."
            )
        with f_col2:
            total_revenue = st.number_input(
                "Total Revenue ($)", 
                min_value=0.0, format="%.2f",
                help="Total corporate revenue."
            )
        with f_col3:
            gross_profit = st.number_input(
                "Gross Profit ($)", 
                min_value=0.0, format="%.2f",
                help="Total gross profit dollars."
            )

        st.divider()

        st.subheader("3. Orders & Customers")
        c_col1, c_col2, c_col3 = st.columns(3)
        with c_col1:
            total_orders = st.number_input(
                "Total Orders", 
                min_value=0, step=1,
                help="Total number of orders."
            )
        with c_col2:
            new_customers = st.number_input(
                "New Customers", 
                min_value=0, step=1,
                help="A unique user who transacts for the first time."
            )
        with c_col3:
            repeat_customers = st.number_input(
                "Repeat/Existing Customers", 
                min_value=0, step=1,
                help="Returning customers who transacted."
            )

        st.divider()

        st.subheader("4. Retention Analysis")
        st.caption("Revenue breakdown for the specific customers active this month.")
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            rev_existing_curr = st.number_input(
                "Revenue From Existing Customers (This Month) ($)", 
                min_value=0.0, format="%.2f",
                help="Total dollar spend by existing customers *in the current month*."
            )
        with r_col2:
            rev_same_prev = st.number_input(
                "Revenue From Same Customers (Last Month) ($)", 
                min_value=0.0, format="%.2f",
                help="Total amount spent *last month* by the specific group of existing customers active this month."
            )

        st.divider()
        notes = st.text_area("Notes / Anomalies")

        submitted = st.form_submit_button("Submit Entry", type="primary")

        if submitted:
            if not entered_by:
                st.error("Please fill in the 'Entered By' field.")
            else:
                # Construct the new row
                entry_data = {
                    "Entry Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Report Month": report_date.strftime("%Y-%m-%d"),
                    "Company": company,
                    "Entered By": entered_by,
                    "Total Digital Spend": digital_spend,
                    "Total Revenue": total_revenue,
                    "Gross Profit": gross_profit,
                    "Total Orders": total_orders,
                    "New Customers": new_customers,
                    "Repeat Customers": repeat_customers,
                    "Rev Existing (Current Month)": rev_existing_curr,
                    "Rev Same Custs (Last Month)": rev_same_prev,
                    "Notes": notes
                }
                
                new_row = pd.DataFrame([entry_data])
                
                # Append to existing data and update sheet
                updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.success(f"Success! Data for **{company}** submitted.")
                st.cache_data.clear()