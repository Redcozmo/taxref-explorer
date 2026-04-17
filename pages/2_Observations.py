"""
pages/2_Observations.py — Visualisation cartographique des observations ponctuelles
Format source : GeoPackage (.gpkg)
"""

import os
import streamlit as st

st.set_page_config(
    page_title="Observations",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Vérification des dépendances optionnelles
try:
    import geopandas as gpd
    import folium
    from streamlit_folium import st_folium
    DEPS_OK = True
except ImportError:
    DEPS_OK = False

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📍 Observations")
    st.caption("Visualisation des données d'observation ponctuelles")
    st.divider()

    if st.button("← Retour à l'accueil", use_container_width=True):
        st.switch_page("app.py")

    st.divider()

    # Chargement du fichier
    st.markdown("**Source de données**")
    GPKG_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "data", "observations.gpkg")

    if os.path.exists(GPKG_DEFAULT):
        gpkg_path = GPKG_DEFAULT
        st.success(f"Fichier chargé : `observations.gpkg`")
    else:
        uploaded = st.file_uploader("Charger un fichier .gpkg", type=["gpkg"])
        gpkg_path = None
        if uploaded:
            tmp_path = os.path.join("/tmp", uploaded.name)
            with open(tmp_path, "wb") as f:
                f.write(uploaded.read())
            gpkg_path = tmp_path
            st.success(f"Fichier chargé : `{uploaded.name}`")

# ---------------------------------------------------------------------------
# Corps principal
# ---------------------------------------------------------------------------
if not DEPS_OK:
    st.error(
        "Dépendances manquantes. Lance :\n"
        "```\npip install geopandas folium streamlit-folium\n```"
    )
    st.stop()

if not gpkg_path:
    st.info(
        "Aucune donnée chargée.\n\n"
        "- Place ton fichier dans `data/observations.gpkg`\n"
        "- Ou utilise le bouton de chargement dans la sidebar."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Chargement des données
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_gpkg(path: str):
    gdf = gpd.read_file(path)
    # Reprojection en WGS84 si nécessaire
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y
    return gdf

with st.spinner("Chargement des observations…"):
    gdf = load_gpkg(gpkg_path)

# ---------------------------------------------------------------------------
# Sidebar — filtres
# ---------------------------------------------------------------------------
with st.sidebar:
    st.divider()
    st.markdown("**Filtres**")
    st.metric("Observations", f"{len(gdf):,}")

    # Filtre dynamique sur les colonnes non géométriques
    filter_cols = [c for c in gdf.columns if c not in ("geometry", "lat", "lon")]
    if filter_cols:
        filter_col = st.selectbox("Filtrer par", ["(aucun)"] + filter_cols)
        if filter_col != "(aucun)":
            vals = ["(tous)"] + sorted(gdf[filter_col].dropna().unique().tolist())
            filter_val = st.selectbox("Valeur", vals)
            if filter_val != "(tous)":
                gdf = gdf[gdf[filter_col] == filter_val]
                st.caption(f"{len(gdf):,} observation(s) filtrée(s)")

    # Couleur des points
    point_color = st.color_picker("Couleur des points", "#E8593C")
    point_radius = st.slider("Taille des points", 2, 15, 5)

# ---------------------------------------------------------------------------
# Initialisation des filtres avancés en session_state
# ---------------------------------------------------------------------------
if "advanced_filters" not in st.session_state:
    st.session_state.advanced_filters = {}

# ---------------------------------------------------------------------------
# Carte Folium avec filtres
# ---------------------------------------------------------------------------
st.subheader("Carte des observations")

if gdf.empty:
    st.warning("Aucune observation à afficher avec ce filtre.")
    st.stop()

# Disposition : carte (80%) + filtres (20%)
col_map, col_filters = st.columns([4, 1], gap="medium")

# ── COLONNE DROITE : FILTRES AVANCÉS ────────────────────────────────────
with col_filters:
    st.markdown("### 🔍 Filtres")
    
    # Colonnes disponibles pour le filtrage
    filter_cols = [c for c in gdf.columns if c not in ("geometry", "lat", "lon")]
    
    if filter_cols:
        # Sélection de l'attribut
        selected_attr = st.selectbox(
            "Attribut",
            filter_cols,
            key="filter_attribute",
        )
        
        # Obtenir les valeurs uniques de cet attribut
        unique_vals = sorted(gdf[selected_attr].dropna().unique().tolist())
        
        # Multi-select des valeurs
        selected_vals = st.multiselect(
            "Valeurs",
            unique_vals,
            key="filter_values",
        )
        
        # Mettre à jour la copie du GeoDataFrame
        gdf_filtered = gdf.copy()
        if selected_vals:
            gdf_filtered = gdf_filtered[gdf_filtered[selected_attr].isin(selected_vals)]
        
        st.metric("Résultats", f"{len(gdf_filtered):,} obs.")
    else:
        gdf_filtered = gdf.copy()

# ── COLONNE GAUCHE : CARTE ──────────────────────────────────────────────
with col_map:
    centre = [gdf_filtered["lat"].mean(), gdf_filtered["lon"].mean()]
    m = folium.Map(location=centre, zoom_start=8, tiles="CartoDB positron")

    # Colonnes à inclure dans le popup (hors géométrie)
    popup_cols = [c for c in gdf_filtered.columns if c not in ("geometry", "lat", "lon")]

    # Préparation du GeoJSON avec propriétés pour le popup
    geojson_data = gdf_filtered[popup_cols + ["geometry"]].to_json()

    # Popup dynamique généré côté JS — bien plus rapide que Python
    popup_fields = popup_cols[:8]  # limiter à 8 champs pour la lisibilité
    popup_aliases = [f"<b>{c}</b>" for c in popup_fields]

    folium.GeoJson(
        geojson_data,
        name="Observations",
        marker=folium.CircleMarker(
            radius=point_radius,
            color=point_color,
            fill=True,
            fill_color=point_color,
            fill_opacity=0.7,
            weight=1,
        ),
        popup=folium.GeoJsonPopup(
            fields=popup_fields,
            aliases=popup_aliases,
            localize=True,
            max_width=300,
        ),
        tooltip=folium.GeoJsonTooltip(
            fields=[popup_fields[0]] if popup_fields else [],
            aliases=[""],
            localize=True,
        ),
    ).add_to(m)

    st_folium(m, use_container_width=True, height=600)

# ---------------------------------------------------------------------------
# Tableau des données
# ---------------------------------------------------------------------------
with st.expander(f"📋 Données brutes ({len(gdf_filtered):,} observations)"):
    display_cols = [c for c in gdf_filtered.columns if c != "geometry"]
    st.dataframe(gdf_filtered[display_cols], use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Télécharger CSV",
        gdf_filtered[display_cols].to_csv(index=False).encode("utf-8"),
        "observations.csv",
        "text/csv",
    )
