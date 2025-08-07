import streamlit as st

# Gamma presentation
st.subheader("📽️ Presentation – G-League Scouting Platform")
st.markdown("You can also [open the presentation in full screen](https://gamma.app/docs/G-League-Scouting-Platform-c2heegpofqnf1pw?mode=doc)")

st.components.v1.html(
    """
    <iframe
        src="https://gamma.app/embed/c2heegpofqnf1pw"
        style="width: 100%; height: 600px; border: none;"
        allow="fullscreen"
        title="G-League Scouting Platform">
    </iframe>
    """,
    height=600
)
