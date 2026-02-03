"""Session status component for sidebar display."""

import streamlit as st


def render_session_status():
    """Render session status in sidebar.

    Shows whether files are loaded and provides quick navigation
    to upload files if needed.
    """
    with st.sidebar:
        st.markdown("### 📁 Session")

        excel = st.session_state.get("excel_file_data")
        ded = st.session_state.get("ded_file_data")

        if excel:
            # Truncate filename if too long
            name = excel.get("name", "Capacity file")
            display_name = name[:20] + "..." if len(name) > 20 else name
            st.success(f"✓ {display_name}")
        else:
            st.caption("No capacity file loaded")

        if ded:
            # Truncate filename if too long
            name = ded.get("name", "DED file")
            display_name = name[:20] + "..." if len(name) > 20 else name
            st.success(f"✓ {display_name}")
        else:
            st.caption("No DED loaded")

        if not excel and not ded:
            st.page_link("pages/1_Analyze.py", label="Upload Files", icon="📤")

        st.markdown("---")
