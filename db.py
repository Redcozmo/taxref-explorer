"""
db.py — Connexion DuckDB (singleton, lecture seule)
"""
 
import os
import streamlit as st
import duckdb
 
DUCKDB_PATH = os.path.join(os.path.dirname(__file__), "data", "taxref.duckdb")
 
 
@st.cache_resource
def get_con() -> duckdb.DuckDBPyConnection:
    """Connexion DuckDB en lecture seule — une seule instance partagée."""
    if not os.path.exists(DUCKDB_PATH):
        st.error(
            f"Base DuckDB introuvable : `{DUCKDB_PATH}`\n\n"
            "Lance d'abord la conversion :\n"
            "```\npython convert.py --input input_data/TAXREF_v18.txt\n```"
        )
        st.stop()
    return duckdb.connect(DUCKDB_PATH, read_only=True)