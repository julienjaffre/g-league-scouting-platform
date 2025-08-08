import streamlit as st

# Gamma presentation
st.subheader("📽️ Presentation – G-League Scouting Platform")

# Add full-page button
if st.button("🔍 View in Full Page", type="primary"):
    st.components.v1.html(
        """
        <script>
            window.open('https://gamma.app/docs/G-League-Scouting-Platform-c2heegpofqnf1pw?mode=present#card-m2q5ep05v9rqrbl', '_blank');
        </script>
        """,
        height=0
    )

st.markdown("You can also [open the presentation in full screen](https://gamma.app/docs/G-League-Scouting-Platform-c2heegpofqnf1pw?mode=present#card-bh4txxhpoz62olk)")

st.components.v1.html(
    """
    <iframe
        src="https://gamma.app/embed/c2heegpofqnf1pw"
        style="width: 100%; height: 800px; border: none;"
        allow="fullscreen"
        title="G-League Scouting Platform">
    </iframe>
    """,
    height=800
)
