# 🌿 TAXREF Explorer

Application Streamlit pour explorer la base TAXREF (référentiel national des taxons).

## Stack technique

- **Streamlit** — interface web
- **DuckDB** — moteur SQL embarqué, sans serveur
- **Parquet** — format de stockage compressé
- **Pandas** — manipulation des données

---

## Installation

### 1. Cloner / télécharger le projet

```bash
git clone https://github.com/Redcozmo/taxref-explorer.git
cd taxref-explorer
```

```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## Conversion de la base TAXREF

Télécharger le fichier TAXREF depuis [INPN](https://inpn.mnhn.fr/telechargement/referentielEspece/taxref) ou la page [temporaire](https://www.patrinat.fr/fr/page-temporaire-de-telechargement-des-referentiels-de-donnees-lies-linpn-7353) 

Puis lancer la conversion du fichier texte en parquet et duckdb :

```bash
python convert.py --input input_data/TAXREFv18.txt
```

Cela génère dans le dossier `data/` :
- `taxref.parquet` — fichier Parquet compressé (~10–20 Mo)
- `taxref.duckdb`  — base DuckDB avec index (~15–25 Mo)


---

## Lancement de l'application

```bash
streamlit run app.py
```

Tester l'application sur [http://localhost:8501](http://localhost:8501)

---

## Structure du projet

```
taxref_explorer/
├── app.py              # Application Streamlit (UI)
├── pages
│   ├── 1_TAXREF_Explorer.py
│   └── 2_Observations.py
├── input_data
│   └── TAXREFv18.txt
├── queries.py          # Toutes les requêtes SQL
├── data/               # Généré par convert.py
│   ├── taxref.parquet
│   └── taxref.duckdb
├── db.py               # Connexion DuckDB (singleton)
├── convert.py          # Script de conversion TSV → Parquet + DuckDB
├── requirements.txt    # Dépendances Python
└── README.md

```

---

## Fonctionnalités

| Onglet | Description |
|---|---|
| 👤 Profil | Sélectionner un profil à partir des règnes disponibles |
| 🔎 Filtrer | Filtres par la taxonomie linnéenne ou par les regroupements vernaculaires INPN |
| 🔍 Rechercher | Recherche dans certains attributs |
| 📋 Détail taxon | Affichage complet d'un taxon par son CD_NOM |
| 📊 Statistiques | Distribution des taxons |