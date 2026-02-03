"""Settings page for PI Strategist configuration."""

import sys
from pathlib import Path

# Add src directory to path for Streamlit Cloud deployment
_src_dir = Path(__file__).parent.parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import streamlit as st
import os

from pi_strategist.web.components.session_status import render_session_status


# Page config
st.set_page_config(
    page_title="Settings - PI Strategist",
    page_icon="⚙️",
    layout="wide",
)

# Render session status in sidebar first
render_session_status()

st.title("⚙️ Settings")
st.markdown("Configure PI Strategist settings and preferences.")

# Initialize session state for settings
if "settings" not in st.session_state:
    st.session_state.settings = {
        "default_buffer": 20,
        "default_cd_target": 30,
    }


st.markdown("---")

# Default Analysis Settings
st.subheader("Default Analysis Settings")

col1, col2 = st.columns(2)

with col1:
    default_buffer = st.slider(
        "Default Buffer Percentage",
        min_value=0,
        max_value=50,
        value=st.session_state.settings["default_buffer"],
        step=5,
        help="Default buffer percentage for capacity analysis",
    )

    st.caption(
        "Buffer accounts for unexpected work, meetings, and interruptions. "
        "Typical values: 15-25%"
    )

with col2:
    default_cd_target = st.slider(
        "Default CD Target Percentage",
        min_value=10,
        max_value=50,
        value=st.session_state.settings["default_cd_target"],
        step=5,
        help="Target percentage of tasks for continuous delivery",
    )

    st.caption(
        "Recommended percentage of work that can be deployed independently. "
        "Typical values: 20-40%"
    )

st.markdown("---")

# Save settings
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        st.session_state.settings = {
            "default_buffer": default_buffer,
            "default_cd_target": default_cd_target,
        }
        st.success("Settings saved successfully!")

with col2:
    if st.button("🔄 Reset to Defaults", use_container_width=True):
        st.session_state.settings = {
            "default_buffer": 20,
            "default_cd_target": 30,
        }
        st.rerun()

st.markdown("---")

# Current Configuration Display
st.subheader("Current Configuration")

config_display = {
    "Default Buffer": f"{st.session_state.settings['default_buffer']}%",
    "Default CD Target": f"{st.session_state.settings['default_cd_target']}%",
}

col1, col2 = st.columns(2)

with col1:
    for key, value in config_display.items():
        st.markdown(f"**{key}:** {value}")

st.markdown("---")

# About section
st.subheader("About PI Strategist")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        **Version:** 1.0.0

        **Description:**
        PI Strategist is a planning analysis tool that helps development teams
        identify risks in acceptance criteria, validate sprint capacity, and
        plan for continuous delivery.

        **Features:**
        - Red flag detection in acceptance criteria
        - Sprint capacity validation
        - Deployment clustering and strategy recommendations
        - Multiple report formats (HTML, JSON, Text)
        """
    )

with col2:
    st.markdown(
        """
        **Supported File Formats:**

        *DED Documents:*
        - Microsoft Word (.docx)
        - Markdown (.md)
        - Plain text (.txt)
        - PDF (.pdf)

        *Capacity Planners:*
        - Microsoft Excel (.xlsx)
        """
    )

# Environment info
with st.expander("Environment Information"):
    st.markdown("**Python Environment:**")

    env_info = {
        "Python Version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "Streamlit Version": st.__version__,
        "Working Directory": os.getcwd(),
    }

    for key, value in env_info.items():
        st.text(f"{key}: {value}")

    # Check for optional dependencies
    st.markdown("**Dependency Status:**")

    dependencies = [
        ("python-docx", "docx"),
        ("openpyxl", "openpyxl"),
        ("pdfplumber", "pdfplumber"),
    ]

    for name, module in dependencies:
        try:
            __import__(module)
            st.text(f"✓ {name}: Installed")
        except ImportError:
            st.text(f"✗ {name}: Not installed")

# Sidebar
with st.sidebar:
    st.markdown("### Quick Links")
    st.page_link("app.py", label="Home", icon="🏠")
    st.page_link("pages/2_Quick_Check.py", label="Quick Check", icon="⚡")

    st.markdown("---")
    st.markdown("### Help")
    st.markdown(
        """
        **Need help?**
        - Check the documentation
        - Report issues on GitHub
        - Review the sample files in `examples/`
        """
    )
