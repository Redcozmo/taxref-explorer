"""
queries.py — Requêtes DuckDB pour TAXREF Explorer
"""

import pandas as pd
import streamlit as st
from db import get_con

LIMIT_DEFAULT = 500


@st.cache_data(ttl=3600)
def get_columns() -> list[str]:
    """Retourne la liste de toutes les colonnes de la table taxon."""
    df = get_con().execute("DESCRIBE taxon").df()
    return df["column_name"].tolist()


@st.cache_data(ttl=3600)
def get_distinct_values(column: str) -> list:
    """Valeurs distinctes non nulles d'une colonne (pour les selectbox)."""
    df = get_con().execute(
        f'SELECT DISTINCT "{column}" FROM taxon WHERE "{column}" IS NOT NULL ORDER BY "{column}"'
    ).df()
    return df[column].tolist()


@st.cache_data(ttl=600)
def filter_taxons(filters: dict, limit: int = LIMIT_DEFAULT) -> pd.DataFrame:
    """
    Filtre les taxons sur plusieurs colonnes (égalité stricte).
    filters = {"REGNE": "Animalia", "CLASSE": "Mammalia"}
    """
    if not filters:
        return pd.DataFrame()

    conditions = " AND ".join(f'"{k}" = $${k}$$' for k in filters)
    # DuckDB supporte les paramètres nommés via execute()
    params = list(filters.values())
    where  = " AND ".join(f'"{k}" = ?' for k in filters)
    sql = f"SELECT * FROM taxon WHERE {where} LIMIT {limit}"
    return get_con().execute(sql, params).df()


@st.cache_data(ttl=600)
def search_taxons(column: str, value: str, limit: int = LIMIT_DEFAULT) -> pd.DataFrame:
    """Recherche partielle (ILIKE) dans une colonne textuelle."""
    sql = f'SELECT * FROM taxon WHERE "{column}" ILIKE ? LIMIT {limit}'
    return get_con().execute(sql, [f"%{value}%"]).df()


@st.cache_data(ttl=600)
def get_taxon_by_cd_nom(cd_nom: int) -> pd.DataFrame:
    """Retourne un taxon par son CD_NOM (identifiant unique TAXREF)."""
    return get_con().execute('SELECT * FROM taxon WHERE "CD_NOM" = ?', [cd_nom]).df()


@st.cache_data(ttl=3600)
def count_by_column(column: str) -> pd.DataFrame:
    """Compte le nombre de taxons par valeur d'une colonne (pour les stats)."""
    sql = f"""
        SELECT "{column}" AS valeur, COUNT(*) AS nb_taxons
        FROM taxon
        WHERE "{column}" IS NOT NULL
        GROUP BY "{column}"
        ORDER BY nb_taxons DESC
    """
    return get_con().execute(sql).df()


@st.cache_data(ttl=3600)
def total_count() -> int:
    """Nombre total de taxons dans la base."""
    return get_con().execute("SELECT COUNT(*) FROM taxon").fetchone()[0]
