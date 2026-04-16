"""
app.py — Landing page de l'application
"""

import streamlit as st

st.set_page_config(
    page_title="Accueil",
    page_icon="🌍",
    layout="centered",
)

st.title("🌍 Accueil")
st.markdown("Choisissez une application pour continuer.")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🌿 TAXREF Explorer")
    st.caption("Exploration de la base nationale de référence des taxons.\nSource : TAXREF v18")
    if st.button("Ouvrir TAXREF Explorer", use_container_width=True, type="primary"):
        st.switch_page("pages/1_TAXREF_Explorer.py")

with col2:
    st.markdown("### 📍 Données d'observation")
    st.caption("Visualisation cartographique des données d'observation ponctuelles.\nSource : perso")
    if st.button("Ouvrir les observations", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Observations.py")
