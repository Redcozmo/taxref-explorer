# 🌿 TAXREF Explorer

Application Streamlit pour explorer la base TAXREF (référentiel national des taxons).

## Stack technique

- **Streamlit** — interface web
- **DuckDB** — moteur SQL embarqué, sans serveur
- **Parquet** — format de stockage compressé (source de vérité)
- **Pandas** — manipulation des données

---

## Installation

### 1. Cloner / télécharger le projet

```bash
cd taxref_explorer
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## Conversion de la base TAXREF

Télécharge le fichier TAXREF depuis [INPN](https://inpn.mnhn.fr/telechargement/referentielEspece/taxref)
puis lance la conversion :

```bash
python convert.py --input input_data/TAXREFv18.txt
```

Cela génère dans le dossier `data/` :
- `taxref.parquet` — fichier Parquet compressé (~10–20 Mo)
- `taxref.duckdb`  — base DuckDB avec index (~15–25 Mo)

> La conversion prend ~30 secondes pour ~300 000 taxons.

---

## Lancement de l'application

```bash
streamlit run app.py
```

L'application s'ouvre automatiquement sur [http://localhost:8501](http://localhost:8501)

---

## Structure du projet

```
taxref_explorer/
├── app.py              # Application Streamlit (UI)
├── db.py               # Connexion DuckDB (singleton)
├── queries.py          # Toutes les requêtes SQL
├── convert.py          # Script de conversion TSV → Parquet + DuckDB
├── requirements.txt    # Dépendances Python
├── README.md
└── data/               # Généré par convert.py
    ├── taxref.parquet
    └── taxref.duckdb
```

---

## Fonctionnalités

| Onglet | Description |
|---|---|
| 🔎 Filtrer | Filtres multi-colonnes par valeur exacte (règne, classe, ordre…) |
| 🔍 Rechercher | Recherche partielle ILIKE dans n'importe quel attribut |
| 📋 Détail taxon | Affichage complet d'un taxon par CD_NOM |
| 📊 Statistiques | Distribution des taxons par attribut avec barre de progression |

Chaque onglet propose un export CSV des résultats.
