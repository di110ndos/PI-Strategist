"""Main Streamlit entry point for PI Strategist."""

import streamlit as st
from pathlib import Path


def main():
    """Run the Streamlit web application."""
    import subprocess
    import sys

    # Get the path to this file's directory
    app_dir = Path(__file__).parent

    # Run streamlit with the correct working directory
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_dir / "app.py")],
        cwd=str(app_dir.parent.parent.parent),
    )


# Page configuration
st.set_page_config(
    page_title="PI Strategist",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Landing page content
st.title("📊 PI Strategist")
st.markdown("Select a page from the sidebar to get started.")

st.markdown("---")

# Show quick status if files are loaded
if st.session_state.get("excel_file_data"):
    st.success("✓ Data loaded - ready to analyze")
    st.page_link("pages/1_Analyze.py", label="Go to Analysis", icon="📊")
else:
    st.info("Upload files on the Analyze page to begin")
    st.page_link("pages/1_Analyze.py", label="Upload Files", icon="📤")

st.markdown("---")

# Feature overview
st.markdown("### Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        **📊 Analyze**
        - Upload capacity planner and DED files
        - View capacity metrics and red flags
        - Generate comprehensive reports

        **⚡ Quick Check**
        - Instant text analysis
        - No file upload needed
        - Paste acceptance criteria for red flag detection
        """
    )

with col2:
    st.markdown(
        """
        **🔮 Scenarios**
        - What-if scenario planning
        - Compare resource allocation options
        - Simulate cost and utilization changes

        **⚙️ Settings**
        - Configure API keys
        - Set default analysis parameters
        - Customize display options
        """
    )

# Sidebar
with st.sidebar:
    st.markdown("### 📁 Session")

    excel = st.session_state.get("excel_file_data")
    ded = st.session_state.get("ded_file_data")

    if excel:
        name = excel.get("name", "Capacity file")
        display_name = name[:20] + "..." if len(name) > 20 else name
        st.success(f"✓ {display_name}")
    else:
        st.caption("No capacity file loaded")

    if ded:
        name = ded.get("name", "DED file")
        display_name = name[:20] + "..." if len(name) > 20 else name
        st.success(f"✓ {display_name}")
    else:
        st.caption("No DED loaded")

    if not excel and not ded:
        st.page_link("pages/1_Analyze.py", label="Upload Files", icon="📤")

    st.markdown("---")

    st.markdown("### Quick Links")
    st.page_link("pages/1_Analyze.py", label="Full Analysis", icon="📊")
    st.page_link("pages/2_Quick_Check.py", label="Quick Check", icon="⚡")
    st.page_link("pages/4_Scenarios.py", label="Scenarios", icon="🔮")
    st.page_link("pages/3_Settings.py", label="Settings", icon="⚙️")


if __name__ == "__main__":
    # When run directly, this file serves as the Streamlit app
    pass
