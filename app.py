"""
app.py — TAXREF Explorer
Stack : Streamlit · DuckDB · Parquet

Lancement : streamlit run app.py
"""

import streamlit as st
import pandas as pd
import queries

# ---------------------------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="TAXREF Explorer",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar — infos générales
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🌿 TAXREF Explorer")
    st.caption("Exploration de la base nationale de référence des taxons")

    try:
        total = queries.total_count()
        st.metric("Total taxons", f"{total:,}")
    except Exception:
        st.warning("Base non chargée.")

    st.divider()
    st.markdown(
        "**Navigation**\n"
        "- 🔎 Filtrer\n"
        "- 🔍 Rechercher\n"
        "- 📋 Détail taxon\n"
        "- 📊 Statistiques"
    )

# ---------------------------------------------------------------------------
# Tabs principales
# ---------------------------------------------------------------------------
tab_filter, tab_search, tab_detail, tab_stats = st.tabs([
    "🔎 Filtrer",
    "🔍 Rechercher",
    "📋 Détail taxon",
    "📊 Statistiques",
])


# ── TAB 1 : FILTRER ────────────────────────────────────────────────────────
with tab_filter:
    st.subheader("Filtrer par attribut")
    st.caption("Sélectionne une ou plusieurs valeurs pour filtrer les taxons.")

    # Colonnes catégorielles proposées au filtrage
    FILTER_COLS = ["REGNE", "PHYLUM", "CLASSE", "ORDRE", "FAMILLE",
                   "GROUP1_INPN", "GROUP2_INPN"]
    available_cols = [c for c in FILTER_COLS if c in queries.get_columns()]

    cols = st.columns(3)
    filters = {}
    for i, col in enumerate(available_cols):
        with cols[i % 3]:
            options = ["(tous)"] + queries.get_distinct_values(col)
            choice = st.selectbox(col.capitalize(), options, key=f"filter_{col}")
            if choice != "(tous)":
                filters[col] = choice

    limit = st.slider("Nombre max de résultats", 50, 2000, 500, 50, key="filter_limit")

    if filters:
        with st.spinner("Requête en cours…"):
            df = queries.filter_taxons(filters, limit=limit)

        st.success(f"{len(df):,} taxon(s) trouvé(s)")
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=420,
        )
        st.download_button(
            "⬇️ Télécharger CSV",
            df.to_csv(index=False).encode("utf-8"),
            "taxref_filtre.csv",
            "text/csv",
        )
    else:
        st.info("Sélectionne au moins un filtre pour lancer la recherche.")


# ── TAB 2 : RECHERCHER ─────────────────────────────────────────────────────
with tab_search:
    st.subheader("Recherche dans un attribut")
    st.caption("Recherche partielle, insensible à la casse.")

    all_cols = queries.get_columns()

    col1, col2, col3 = st.columns([2, 4, 1])
    with col1:
        search_col = st.selectbox(
            "Attribut",
            all_cols,
            index=all_cols.index("LB_NOM") if "LB_NOM" in all_cols else 0,
            key="search_col",
        )
    with col2:
        search_val = st.text_input("Valeur recherchée", key="search_val",
                                   placeholder="ex : Canis, Quercus, Parus…")
    with col3:
        search_limit = st.number_input("Max", 10, 2000, 200, 10, key="search_limit")

    if search_val:
        with st.spinner("Recherche…"):
            df = queries.search_taxons(search_col, search_val, limit=search_limit)

        if df.empty:
            st.warning("Aucun résultat.")
        else:
            st.success(f"{len(df):,} résultat(s)")
            st.dataframe(df, use_container_width=True, hide_index=True, height=420)
            st.download_button(
                "⬇️ Télécharger CSV",
                df.to_csv(index=False).encode("utf-8"),
                "taxref_recherche.csv",
                "text/csv",
            )
    else:
        st.info("Saisis une valeur pour lancer la recherche.")


# ── TAB 3 : DÉTAIL TAXON ───────────────────────────────────────────────────
with tab_detail:
    st.subheader("Détail d'un taxon")
    st.caption("Affiche toutes les données d'un taxon à partir de son CD_NOM.")

    cd_nom = st.number_input("CD_NOM", min_value=1, step=1, key="detail_cd_nom")

    if st.button("Afficher le taxon", type="primary"):
        with st.spinner("Chargement…"):
            df = queries.get_taxon_by_cd_nom(int(cd_nom))

        if df.empty:
            st.error(f"Aucun taxon trouvé pour CD_NOM = {cd_nom}")
        else:
            row = df.iloc[0]

            # En-tête lisible
            nom_sci  = row.get("LB_NOM", "—")
            nom_vern = row.get("NOM_VERN", "")
            regne    = row.get("REGNE", "")

            st.markdown(f"### *{nom_sci}*")
            if nom_vern:
                st.markdown(f"**Nom vernaculaire :** {nom_vern}")
            if regne:
                st.markdown(f"**Règne :** {regne}")

            st.divider()

            # Affichage de toutes les colonnes en deux groupes
            non_null = {k: v for k, v in row.items() if pd.notna(v) and v != ""}
            null_cols = [k for k, v in row.items() if pd.isna(v) or v == ""]

            c1, c2 = st.columns(2)
            items = list(non_null.items())
            mid   = (len(items) + 1) // 2

            with c1:
                for k, v in items[:mid]:
                    st.markdown(f"**{k}** : {v}")
            with c2:
                for k, v in items[mid:]:
                    st.markdown(f"**{k}** : {v}")

            with st.expander(f"Colonnes vides ({len(null_cols)})"):
                st.write(", ".join(null_cols))


# ── TAB 4 : STATISTIQUES ───────────────────────────────────────────────────
with tab_stats:
    st.subheader("Statistiques")
    st.caption("Distribution des taxons par attribut.")

    STAT_COLS = ["REGNE", "GROUP1_INPN", "GROUP2_INPN", "CLASSE", "ORDRE", "FAMILLE"]
    available_stat_cols = [c for c in STAT_COLS if c in queries.get_columns()]

    stat_col = st.selectbox("Répartition par", available_stat_cols, key="stat_col")

    with st.spinner("Calcul…"):
        df_stat = queries.count_by_column(stat_col)

    st.dataframe(
        df_stat,
        use_container_width=True,
        hide_index=True,
        column_config={
            "valeur":    st.column_config.TextColumn(stat_col),
            "nb_taxons": st.column_config.ProgressColumn(
                "Nb taxons",
                min_value=0,
                max_value=int(df_stat["nb_taxons"].max()) if not df_stat.empty else 1,
            ),
        },
        height=500,
    )
