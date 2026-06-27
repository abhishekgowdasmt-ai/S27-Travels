import streamlit as st
import tempfile
import os
from trip_sheet_generator import generate_trip_sheets

# 1. Page Configuration
st.set_page_config(
    page_title="S27 Travels | Trip Sheet Generator",
    page_icon="🚕",
    layout="centered"
)

# 2. Custom CSS Styling for Premium Appearance
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Global Typography & Font override */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* App background styling */
    [data-testid="stAppViewContainer"] {
        background-color: #f8fafc;
        background-image: 
            radial-gradient(at 0% 0%, hsla(210, 40%, 93%, 1) 0px, transparent 50%),
            radial-gradient(at 50% 0%, hsla(215, 60%, 95%, 1) 0px, transparent 50%),
            radial-gradient(at 100% 0%, hsla(45, 50%, 94%, 1) 0px, transparent 50%);
    }
    
    /* Customize the main title */
    h1 {
        font-weight: 800 !important;
        color: #0F2E51 !important;
        text-align: center;
        margin-bottom: 5px !important;
        letter-spacing: -0.5px;
    }
    
    /* Custom description subtitle */
    .app-subtitle {
        text-align: center;
        color: #64748b;
        font-size: 1.15rem;
        font-weight: 400;
        margin-bottom: 30px;
    }
    
    /* Styling for primary action buttons (Generate) */
    div.stButton > button {
        background: linear-gradient(135deg, #0F2E51 0%, #1e4b7a 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 15px rgba(15, 46, 81, 0.15) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100% !important;
        height: auto !important;
    }
    
    div.stButton > button:hover {
        background: linear-gradient(135deg, #1e4b7a 0%, #0F2E51 100%) !important;
        box-shadow: 0 6px 20px rgba(15, 46, 81, 0.25) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Styling for download buttons (Gold themed) */
    div[data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, #D4AF37 0%, #b89222 100%) !important;
        color: #0F2E51 !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.15) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100% !important;
        height: auto !important;
    }
    
    div[data-testid="stDownloadButton"] > button:hover {
        background: linear-gradient(135deg, #b89222 0%, #D4AF37 100%) !important;
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.25) !important;
        transform: translateY(-2px) !important;
        color: #0F2E51 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Header Section (Logo + Branding)
col1, col2, col3 = st.columns([2, 1.2, 2])
with col2:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=140)

st.markdown("<h1>S27 TRAVELS</h1>", unsafe_allow_html=True)
st.markdown("<p class='app-subtitle'>🚕 Premium Trip Sheet PDF Generator</p>", unsafe_allow_html=True)

# 4. Main App Container
with st.container(border=True):
    st.subheader("📤 Upload Sheet")
    excel_file = st.file_uploader(
        "Upload Excel File (.xlsx)",
        type=["xlsx"],
        label_visibility="collapsed"
    )
    
    if excel_file:
        file_size = len(excel_file.getvalue()) / 1024
        st.info(f"📂 **File Uploaded:** {excel_file.name} ({file_size:.2f} KB)")
        
        # Generator Setup
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(excel_file.read())
            excel_path = tmp.name

        watermark_image = "logo.jpg"
        output_pdf = "Trip_Sheets_Output.pdf"

        st.write("") # Spacing
        
        if st.button("✨ Generate Trip Sheets PDF"):
            with st.spinner("Processing Excel records and drawing PDFs..."):
                try:
                    generate_trip_sheets(
                        excel_path,
                        output_pdf,
                        watermark_image
                    )
                    
                    st.success("🎉 Trip Sheets PDF generated successfully!")
                    
                    # Clean download section inside a nested border
                    with st.container(border=True):
                        st.markdown("<h4 style='color:#0F2E51; margin-top:0;'>📥 Download Ready</h4>", unsafe_allow_html=True)
                        st.write("Click below to download the compiled PDF containing all generated trip sheets.")
                        
                        with open(output_pdf, "rb") as f:
                            st.download_button(
                                "⬇️ Download PDF Document",
                                f,
                                file_name="Trip_Sheets.pdf",
                                mime="application/pdf"
                            )
                except Exception as e:
                    st.error(f"Error during PDF generation: {e}")
                    
# 5. Format Instructions / Expected Structure
st.write("") # spacing
with st.expander("📋 View Expected Excel Format / Column Names"):
    st.markdown("""
    The uploaded Excel file (`.xlsx`) must contain the following case-sensitive column headers:
    * **`SL NO`**: Serial Number (Used to identify data rows)
    * **`DATE`**: Trip Date
    * **`EMP NAME`**: Guest Name
    * **`CAB TYPE`**: Type of Cab Booked
    * **`CAB REG NO`**: Cab Registration/Plate Number
    * **`NAME`**: Driver Name
    * **`MOBIL NO`**: Driver Mobile Number
    * **`PICKUP TIME`**: Reporting & Start Time
    * **`DUTY TYPE`**: Duty Type description
    * **`PLAND START`**: Start Location
    * **`END LOACTION`**: End Location *(Note spelling: `END LOACTION`)*
    * **`END TIME`**: Trip End Time
    * **`TOTAL HRS SMT`**: Total SMT Hours
    * **`START KM`**: Starting Kilometer Reading
    * **`END KM`**: Ending Kilometer Reading
    * **`SMT TOTAL KM`**: Total Kilometers
    * **`PARKING`**: Parking Fees (numeric)
    * **`TOLL`**: Toll Fees (numeric)
    """)
