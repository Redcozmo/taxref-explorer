"""
queries.py — Requêtes DuckDB pour TAXREF Explorer
Le filtre de règne est passé explicitement dans chaque requête.
"""
 
import pandas as pd
import streamlit as st
from db import get_con
 
LIMIT_DEFAULT = None  # pas de limite par défaut
 
 
def _where_regne(regne: str = None) -> tuple[str, list]:
    """
    Retourne la clause WHERE et les paramètres pour filtrer par règne.
    Si règne est None, pas de filtre.
    """
    if regne:
        return '"REGNE" = ?', [regne]
    return "1=1", []
 
 
@st.cache_data(ttl=3600)
def get_regnes() -> list[str]:
    """Liste de tous les règnes disponibles dans la base complète."""
    df = get_con().execute(
        'SELECT DISTINCT "REGNE" FROM taxon WHERE "REGNE" IS NOT NULL ORDER BY "REGNE"'
    ).df()
    return df["REGNE"].tolist()
 
 
@st.cache_data(ttl=3600)
def get_columns() -> list[str]:
    """Retourne la liste de toutes les colonnes de la table taxon."""
    df = get_con().execute("DESCRIBE taxon").df()
    return df["column_name"].tolist()
 
 
@st.cache_data(ttl=3600)
def get_distinct_values(column: str, regne: str = None) -> list:
    """Valeurs distinctes non nulles d'une colonne, filtrées par règne."""
    where, params = _where_regne(regne)
    df = get_con().execute(
        f'SELECT DISTINCT "{column}" FROM taxon '
        f'WHERE "{column}" IS NOT NULL AND {where} '
        f'ORDER BY "{column}"',
        params
    ).df()
    return df[column].tolist()
 
 
@st.cache_data(ttl=600)
def filter_taxons(filters: dict, regne: str = None, limit: int = LIMIT_DEFAULT) -> pd.DataFrame:
    """Filtre les taxons sur plusieurs colonnes (égalité stricte)."""
    if not filters:
        return pd.DataFrame()
 
    where_regne, params_regne = _where_regne(regne)
    where_filters = " AND ".join(f'"{k}" = ?' for k in filters)
    params = params_regne + list(filters.values())
 
    sql = f"SELECT * FROM taxon WHERE {where_regne} AND {where_filters}"
    if limit is not None:
        sql += f" LIMIT {limit}"
    return get_con().execute(sql, params).df()
 
 
@st.cache_data(ttl=600)
def search_taxons(column: str, value: str, regne: str = None, limit: int = LIMIT_DEFAULT) -> pd.DataFrame:
    """Recherche partielle (ILIKE) dans une colonne textuelle."""
    where_regne, params = _where_regne(regne)
    params = params + [f"%{value}%"]
    sql = f'SELECT * FROM taxon WHERE {where_regne} AND "{column}" ILIKE ?'
    if limit is not None:
        sql += f" LIMIT {limit}"
    return get_con().execute(sql, params).df()
 
 
@st.cache_data(ttl=600)
def get_taxon_by_cd_nom(cd_nom: int) -> pd.DataFrame:
    """Retourne un taxon par son CD_NOM (identifiant unique TAXREF)."""
    return get_con().execute(
        'SELECT * FROM taxon WHERE "CD_NOM" = ?', [cd_nom]
    ).df()
 
 
@st.cache_data(ttl=3600)
def count_by_column(column: str, regne: str = None) -> pd.DataFrame:
    """Compte le nombre de taxons par valeur d'une colonne."""
    where, params = _where_regne(regne)
    sql = f"""
        SELECT "{column}" AS valeur, COUNT(*) AS nb_taxons
        FROM taxon
        WHERE "{column}" IS NOT NULL AND {where}
        GROUP BY "{column}"
        ORDER BY nb_taxons DESC
    """
    return get_con().execute(sql, params).df()
 
 
@st.cache_data(ttl=3600)
def total_count(regne: str = None) -> int:
    """Nombre de taxons (filtré par règne si fourni)."""
    where, params = _where_regne(regne)
    return get_con().execute(
        f"SELECT COUNT(*) FROM taxon WHERE {where}", params
    ).fetchone()[0]