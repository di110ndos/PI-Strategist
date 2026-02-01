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
        "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
        "default_buffer": 20,
        "default_cd_target": 30,
        "theme": "light",
    }


st.markdown("---")

# API Configuration
st.subheader("API Configuration")

st.markdown(
    """
    PI Strategist can use Claude AI for enhanced analysis. Configure your API key below.
    Your API key is stored only in your session and never transmitted except to Anthropic.
    """
)

col1, col2 = st.columns([3, 1])

with col1:
    api_key = st.text_input(
        "Anthropic API Key",
        value=st.session_state.settings["api_key"],
        type="password",
        placeholder="sk-ant-...",
        help="Enter your Anthropic API key for AI-powered features",
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if api_key:
        # Validate API key format
        if api_key.startswith("sk-ant-"):
            st.success("✓ Valid format")
        else:
            st.warning("⚠ Check format")

# Show API key status
if api_key:
    masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
    st.caption(f"Current key: {masked_key}")
else:
    st.caption("No API key configured")

st.info(
    "Get your API key from [console.anthropic.com](https://console.anthropic.com/). "
    "The API key enables AI-powered analysis features."
)

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

# Display Settings
st.subheader("Display Settings")

col1, col2 = st.columns(2)

with col1:
    theme = st.selectbox(
        "Color Theme",
        options=["Light", "Dark", "System"],
        index=["Light", "Dark", "System"].index(
            st.session_state.settings.get("theme", "Light").capitalize()
        ),
        help="Color theme for the application",
    )
    st.caption("Note: Theme changes require a page refresh to take effect.")

with col2:
    st.markdown("**Severity Colors:**")
    st.markdown(
        """
        <div style="display: flex; gap: 20px; margin-top: 10px;">
            <div style="display: flex; align-items: center;">
                <span style="background-color: #e74c3c; width: 20px; height: 20px;
                     border-radius: 4px; display: inline-block; margin-right: 8px;"></span>
                Critical
            </div>
            <div style="display: flex; align-items: center;">
                <span style="background-color: #f39c12; width: 20px; height: 20px;
                     border-radius: 4px; display: inline-block; margin-right: 8px;"></span>
                Moderate
            </div>
            <div style="display: flex; align-items: center;">
                <span style="background-color: #3498db; width: 20px; height: 20px;
                     border-radius: 4px; display: inline-block; margin-right: 8px;"></span>
                Low
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# Save settings
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("💾 Save Settings", type="primary", width="stretch"):
        st.session_state.settings = {
            "api_key": api_key,
            "default_buffer": default_buffer,
            "default_cd_target": default_cd_target,
            "theme": theme.lower(),
        }

        # Set environment variable for API key
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key

        st.success("Settings saved successfully!")

with col2:
    if st.button("🔄 Reset to Defaults", width="stretch"):
        st.session_state.settings = {
            "api_key": "",
            "default_buffer": 20,
            "default_cd_target": 30,
            "theme": "light",
        }
        st.rerun()

st.markdown("---")

# Current Configuration Display
st.subheader("Current Configuration")

config_display = {
    "API Key": "Configured" if st.session_state.settings["api_key"] else "Not configured",
    "Default Buffer": f"{st.session_state.settings['default_buffer']}%",
    "Default CD Target": f"{st.session_state.settings['default_cd_target']}%",
    "Theme": st.session_state.settings["theme"].capitalize(),
}

col1, col2 = st.columns(2)

with col1:
    for key, value in list(config_display.items())[:2]:
        st.markdown(f"**{key}:** {value}")

with col2:
    for key, value in list(config_display.items())[2:]:
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

        **Links:**
        - [Documentation](https://github.com/yourusername/pi-strategist)
        - [Report Issues](https://github.com/yourusername/pi-strategist/issues)
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
        ("anthropic", "anthropic"),
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
    st.page_link("pages/1_Analyze.py", label="Full Analysis", icon="📊")
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
