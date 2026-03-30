"""
db.py — Connexion DuckDB (singleton, lecture seule)
Si le fichier .duckdb n'existe pas, il est regénéré depuis le Parquet.
"""

import os
import streamlit as st
import duckdb

BASE_DIR    = os.path.dirname(__file__)
PARQUET_PATH = os.path.join(BASE_DIR, "data", "taxref.parquet")
DUCKDB_PATH  = os.path.join(BASE_DIR, "data", "taxref.duckdb")


def _build_duckdb_from_parquet() -> None:
    """Crée le fichier DuckDB depuis le Parquet avec les index nécessaires."""
    con = duckdb.connect(DUCKDB_PATH)
    con.execute(f"CREATE TABLE taxon AS SELECT * FROM read_parquet('{PARQUET_PATH}')")
    for col in ["CD_NOM", "CD_REF", "LB_NOM", "NOM_VERN", "FAMILLE", "ORDRE", "CLASSE", "REGNE"]:
        try:
            con.execute(f'CREATE INDEX idx_{col.lower()} ON taxon("{col}")')
        except Exception:
            pass
    con.close()


@st.cache_resource
def get_con() -> duckdb.DuckDBPyConnection:
    """Connexion DuckDB en lecture seule — une seule instance partagée.
    Génère le .duckdb depuis le Parquet si nécessaire."""

    if not os.path.exists(PARQUET_PATH):
        st.error(
            f"Fichier Parquet introuvable : `{PARQUET_PATH}`\n\n"
            "Lance d'abord la conversion :\n"
            "```\npython convert.py --input input_data/TAXREF_v18.txt\n```"
        )
        st.stop()

    if not os.path.exists(DUCKDB_PATH):
        with st.spinner("Première utilisation : génération de la base DuckDB depuis le Parquet…"):
            _build_duckdb_from_parquet()

    return duckdb.connect(DUCKDB_PATH, read_only=True)
