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
# Initialisation du session_state
# ---------------------------------------------------------------------------
if "regne_actif" not in st.session_state:
    st.session_state.regne_actif = None

# ---------------------------------------------------------------------------
# Sidebar — infos générales + règne actif
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🌿 TAXREF Explorer")
    st.caption("Exploration de la base nationale de référence des taxons")

    try:
        total = queries.total_count(st.session_state.regne_actif)
        st.metric(
            "Taxons" if not st.session_state.regne_actif else f"Taxons ({st.session_state.regne_actif})",
            f"{total:,}"
        )
    except Exception:
        st.warning("Base non chargée.")

    # Affichage du règne actif
    if st.session_state.regne_actif:
        st.success(f"🔬 Profil actif : **{st.session_state.regne_actif}**")
        if st.button("✖ Réinitialiser le profil", use_container_width=True):
            st.session_state.regne_actif = None
            st.cache_data.clear()
            st.rerun()
    else:
        st.info("Aucun profil sélectionné\n\nToute la base est accessible.")

    st.divider()
    st.markdown(
        "**Navigation**\n"
        "- 👤 Profil\n"
        "- 🔎 Filtrer\n"
        "- 🔍 Rechercher\n"
        "- 📋 Détail taxon\n"
        "- 📊 Statistiques"
    )

# ---------------------------------------------------------------------------
# Tabs principales
# ---------------------------------------------------------------------------
tab_profil, tab_filter, tab_search, tab_detail, tab_stats = st.tabs([
    "👤 Profil",
    "🔎 Filtrer",
    "🔍 Rechercher",
    "📋 Détail taxon",
    "📊 Statistiques",
])


# ── TAB 0 : PROFIL ─────────────────────────────────────────────────────────
with tab_profil:
    st.subheader("Sélection du profil taxonomique")
    st.caption(
        "Le profil filtre l'ensemble de l'application sur un règne. "
        "Tous les onglets (Filtrer, Rechercher, Statistiques…) travailleront "
        "uniquement sur les taxons de ce règne."
    )

    try:
        regnes = queries.get_regnes()
    except Exception:
        regnes = []
        st.error("Impossible de charger les règnes.")

    if regnes:
        # Grille de boutons — un par règne
        EMOJIS = {
            "Animalia": "🐾",
            "Plantae": "🌿",
            "Fungi": "🍄",
            "Chromista": "🔬",
            "Bacteria": "🦠",
            "Archaea": "🧬",
            "Protozoa": "🔬",
            "Orthornavirae": "🧫",
        }

        st.markdown("#### Choisir un règne")
        cols = st.columns(4)
        for i, regne in enumerate(regnes):
            emoji = EMOJIS.get(regne, "🌐")
            with cols[i % 4]:
                actif = st.session_state.regne_actif == regne
                label = f"{emoji} **{regne}**" if actif else f"{emoji} {regne}"
                if st.button(
                    label,
                    key=f"profil_{regne}",
                    use_container_width=True,
                    type="primary" if actif else "secondary",
                ):
                    if actif:
                        # Désactiver le profil si on reclique dessus
                        st.session_state.regne_actif = None
                    else:
                        st.session_state.regne_actif = regne
                    st.cache_data.clear()
                    st.rerun()

        st.divider()

        # Résumé du profil actif
        if st.session_state.regne_actif:
            r = st.session_state.regne_actif
            total_r = queries.total_count(r)
            st.success(
                f"✅ Profil **{r}** actif — "
                f"**{total_r:,}** taxons disponibles dans les autres onglets."
            )
        else:
            total_all = queries.total_count()
            st.info(
                f"Aucun profil sélectionné — "
                f"**{total_all:,}** taxons accessibles (base complète)."
            )


# ── TAB 1 : FILTRER ────────────────────────────────────────────────────────
with tab_filter:
    st.subheader("Filtrer par attribut")
    st.caption("Sélectionne une ou plusieurs valeurs pour filtrer les taxons.")

    if st.session_state.regne_actif:
        st.info(f"🔬 Profil actif : **{st.session_state.regne_actif}**")

    # REGNE exclu des filtres si un profil est actif (déjà filtré)
    FILTER_COLS = ["REGNE", "PHYLUM", "CLASSE", "ORDRE", "FAMILLE", "GROUP1_INPN", "GROUP2_INPN"]
    if st.session_state.regne_actif:
        FILTER_COLS = [c for c in FILTER_COLS if c != "REGNE"]

    available_cols = [c for c in FILTER_COLS if c in queries.get_columns()]

    cols = st.columns(3)
    filters = {}
    for i, col in enumerate(available_cols):
        with cols[i % 3]:
            options = ["(tous)"] + queries.get_distinct_values(col, st.session_state.regne_actif)
            choice = st.selectbox(col.capitalize(), options, key=f"filter_{col}")
            if choice != "(tous)":
                filters[col] = choice

    if "filter_no_limit" not in st.session_state:
        st.session_state.filter_no_limit = False

    col_slider, col_btn = st.columns([4, 1])
    with col_slider:
        limit = st.slider(
            "Nombre max de résultats", 50, 2000, 500, 50,
            key="filter_limit",
            disabled=st.session_state.filter_no_limit,
        )
    with col_btn:
        st.write("")
        btn_label = "Remettre la limite" if st.session_state.filter_no_limit else "Supprimer la limite"
        if st.button(btn_label, use_container_width=True, key="filter_toggle_limit"):
            st.session_state.filter_no_limit = not st.session_state.filter_no_limit
            st.rerun()

    active_limit = None if st.session_state.filter_no_limit else limit

    if filters:
        with st.spinner("Requête en cours…"):
            df = queries.filter_taxons(filters, st.session_state.regne_actif, limit=active_limit)

        if st.session_state.filter_no_limit:
            st.success(f"{len(df):,} taxon(s) trouvé(s) — sans limite")
        else:
            st.success(f"{len(df):,} taxon(s) trouvé(s) — limité à {limit}")

        st.dataframe(df, use_container_width=True, hide_index=True, height=420)
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

    if st.session_state.regne_actif:
        st.info(f"🔬 Profil actif : **{st.session_state.regne_actif}**")

    SEARCH_COLS = ["FAMILLE", "LB_NOM", "NOM_VERN", "NOM_VERN_ENG", "LB_AUTEUR"]
    if st.session_state.regne_actif:
        SEARCH_COLS = [c for c in SEARCH_COLS if c != "REGNE"]

    available_cols = [c for c in SEARCH_COLS if c in queries.get_columns()]

    col1, col2 = st.columns([1, 3])
    with col1:
        search_col = st.selectbox(
            "Attribut",
            available_cols,
            index=available_cols.index("LB_NOM") if "LB_NOM" in available_cols else 0,
            key="search_col",
        )
    with col2:
        distinct_values = queries.get_distinct_values(search_col, st.session_state.regne_actif)
        search_val = st.selectbox(
            "Valeur",
            options=[None] + distinct_values,
            format_func=lambda x: "" if x is None else str(x),
            key="search_val",
        )

    if search_val:
        with st.spinner("Recherche…"):
            df = queries.search_taxons(search_col, str(search_val), st.session_state.regne_actif)

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
        st.info("Sélectionne une valeur pour lancer la recherche.")


# ── TAB 3 : DÉTAIL TAXON ───────────────────────────────────────────────────
with tab_detail:
    st.subheader("Détail d'un taxon")
    st.caption("Affiche toutes les données d'un taxon à partir de son CD_NOM.")

    sample_cd_noms = queries.get_sample_values("CD_NOM", st.session_state.regne_actif, n=5)
    placeholder = "ex : " + ", ".join(str(int(v)) for v in sample_cd_noms) if sample_cd_noms else "ex : 1234"

    cd_nom_saisi = st.text_input("CD_NOM", placeholder=placeholder, key="detail_cd_nom")

    if cd_nom_saisi:
        try:
            cd_nom_actif = int(cd_nom_saisi)
        except ValueError:
            st.error("Veuillez saisir un nombre entier.")
            cd_nom_actif = None

        if cd_nom_actif:
            with st.spinner("Chargement…"):
                df = queries.get_taxon_by_cd_nom(cd_nom_actif)

            if df.empty:
                st.error(f"Aucun taxon trouvé pour CD_NOM = {cd_nom_actif}")
            else:
                row = df.iloc[0]

                nom_sci  = row.get("LB_NOM", "—")
                nom_vern = row.get("NOM_VERN", "")
                regne    = row.get("REGNE", "")

                st.markdown(f"### *{nom_sci}*")
                if nom_vern:
                    st.markdown(f"**Nom vernaculaire :** {nom_vern}")
                if regne:
                    st.markdown(f"**Règne :** {regne}")

                st.divider()

                non_null  = {k: v for k, v in row.items() if pd.notna(v) and v != ""}
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

    if st.session_state.regne_actif:
        st.info(f"🔬 Profil actif : **{st.session_state.regne_actif}**")

    STAT_COLS = ["REGNE", "GROUP1_INPN", "GROUP2_INPN", "CLASSE", "ORDRE", "FAMILLE"]
    if st.session_state.regne_actif:
        STAT_COLS = [c for c in STAT_COLS if c != "REGNE"]
    available_stat_cols = [c for c in STAT_COLS if c in queries.get_columns()]

    stat_col = st.selectbox("Répartition par", available_stat_cols, key="stat_col")

    with st.spinner("Calcul…"):
        df_stat = queries.count_by_column(stat_col, st.session_state.regne_actif)

    if not df_stat.empty:
        total_stat = df_stat["nb_taxons"].sum()
        df_stat["pourcentage"] = (df_stat["nb_taxons"] / total_stat * 100).round(2)

    st.dataframe(
        df_stat,
        use_container_width=True,
        hide_index=True,
        column_config={
            "valeur":      st.column_config.TextColumn(stat_col),
            "nb_taxons":   st.column_config.ProgressColumn(
                "Nombre de taxons par groupe",
                format="%d",
                min_value=0,
                max_value=int(df_stat["nb_taxons"].max()) if not df_stat.empty else 1,
            ),
            "pourcentage": st.column_config.NumberColumn(
                "Répartition par groupe (en %)",
                format="%.2f %%",
                min_value=0,
                max_value=100,
            ),
        },
        height=500,
    )
