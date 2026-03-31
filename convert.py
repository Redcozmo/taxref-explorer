"""
convert.py — Conversion du fichier TAXREF .txt (TSV) vers Parquet + CSV + DuckDB

Usage :
    python convert.py --input TAXREF_v17_0.txt

Le script génère :
    - data/taxref.parquet   (source de vérité compressée)
    - data/taxref.csv       (export CSV, encodage UTF-8)
    - data/taxref.duckdb    (base requêtable via SQL)
"""

import argparse
import os
import time

import duckdb
import pandas as pd


# Colonnes à typer en "category" (peu de valeurs distinctes, très répétées)
CATEGORICAL_COLS = [
    "REGNE", "SOUS_REGNE", "DIVISION", "PHYLUM", "SOUS_PHYLUM",
    "SUPER_CLASSE", "CLASSE", "SOUS_CLASSE", "SUPER_ORDRE", "ORDRE",
    "SOUS_ORDRE", "FAMILLE", "SOUS_FAMILLE", "TRIBU", "GROUP1_INPN", "GROUP2_INPN",
    "FR", "GF", "MAR", "GUA", "SM", "SB", "SPM", "MF", "PAP", "MAY",
    "REU", "SA", "TA", "TAAF", "PF", "NC", "WF", "CLI",
]


def convert(input_path: str, output_dir: str = "data") -> None:
    os.makedirs(output_dir, exist_ok=True)
    parquet_path = os.path.join(output_dir, "taxref.parquet")
    csv_path     = os.path.join(output_dir, "taxref.csv")
    duckdb_path  = os.path.join(output_dir, "taxref.duckdb")

    # --- 1. Lecture du TSV ---
    print(f"📂 Lecture de {input_path} ...")
    t0 = time.time()
    df = pd.read_csv(
        input_path,
        sep="\t",
        dtype=str,
        low_memory=False,
        encoding="utf-8",
        encoding_errors="replace",  # remplace les octets invalides par ?
    )
    print(f"   {len(df):,} lignes · {len(df.columns)} colonnes ({time.time()-t0:.1f}s)")

    # --- 2. Nettoyage minimal ---
    df.columns = [c.strip().upper() for c in df.columns]
    df = df.where(df != "", other=None)

    # Nettoyage des caractères invalides dans les colonnes textuelles
    print("🧹 Nettoyage des caractères invalides...")
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(
            lambda x: x.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
            if isinstance(x, str) else x
        )

    # --- 3. Typage optimisé ---
    print("🔧 Optimisation des types ...")
    existing_cats = [c for c in CATEGORICAL_COLS if c in df.columns]
    for col in existing_cats:
        df[col] = df[col].astype("category")

    # CD_NOM / CD_REF / CD_SUP → entiers si possible
    for col in ["CD_NOM", "CD_REF", "CD_SUP", "CD_TAXSUP"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # --- 4. Export Parquet (zstd, compression optimale) ---
    print(f"💾 Export Parquet → {parquet_path} ...")
    t1 = time.time()
    df.to_parquet(parquet_path, compression="zstd", index=False)
    size_mb = os.path.getsize(parquet_path) / 1_048_576
    print(f"   ✅ {size_mb:.1f} Mo ({time.time()-t1:.1f}s)")

    # --- 5. Export CSV (UTF-8, séparateur virgule) ---
    print(f"📄 Export CSV → {csv_path} ...")
    t2 = time.time()
    df.to_csv(csv_path, index=False, encoding="utf-8")
    size_mb_csv = os.path.getsize(csv_path) / 1_048_576
    print(f"   ✅ {size_mb_csv:.1f} Mo ({time.time()-t2:.1f}s)")

    # --- 6. Création DuckDB ---
    print(f"🦆 Création DuckDB → {duckdb_path} ...")
    t3 = time.time()
    if os.path.exists(duckdb_path):
        os.remove(duckdb_path)

    con = duckdb.connect(duckdb_path)
    con.execute(f"CREATE TABLE taxon AS SELECT * FROM read_parquet('{parquet_path}')")

    # Index utiles pour les recherches fréquentes
    for col in ["CD_NOM", "CD_REF", "LB_NOM", "NOM_VERN", "FAMILLE", "ORDRE", "CLASSE", "REGNE"]:
        if col in df.columns:
            con.execute(f'CREATE INDEX idx_{col.lower()} ON taxon("{col}")')

    row_count = con.execute("SELECT COUNT(*) FROM taxon").fetchone()[0]
    con.close()
    print(f"   ✅ {row_count:,} taxons indexés ({time.time()-t3:.1f}s)")

    print(f"\n✨ Conversion terminée en {time.time()-t0:.1f}s")
    print(f"   Parquet : {parquet_path}  ({os.path.getsize(parquet_path)/1_048_576:.1f} Mo)")
    print(f"   CSV     : {csv_path}  ({os.path.getsize(csv_path)/1_048_576:.1f} Mo)")
    print(f"   DuckDB  : {duckdb_path}  ({os.path.getsize(duckdb_path)/1_048_576:.1f} Mo)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convertit le TSV TAXREF en Parquet + DuckDB")
    parser.add_argument("--input",  required=True, help="Chemin vers le fichier TAXREF .txt")
    parser.add_argument("--output", default="data", help="Dossier de sortie (défaut : data/)")
    args = parser.parse_args()
    convert(args.input, args.output)
