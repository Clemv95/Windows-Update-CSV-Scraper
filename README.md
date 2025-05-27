# Windows Release Info Scraper

Ce dépôt contient un script Python pour extraire les informations de versions et de mises à jour de Windows 10 et Windows 11 à partir de la documentation officielle de Microsoft.

## Fonctionnalités

- Scraping des numéros de build, dates de sortie, et KB associés.
- Génération de fichiers CSV (`win10_builds.csv` et `win11_builds.csv`).
- Exécution automatique quotidienne via GitHub Actions.
- Commit automatique des fichiers CSV mis à jour.

## Structure

```
.
├── script.py              # Script principal
├── requirements.txt       # Dépendances Python
├── win10_builds.csv       # Résultat du scraping Windows 10
├── win11_builds.csv       # Résultat du scraping Windows 11
└── .github/
    └── workflows/
        └── schedule.yml   # Workflow GitHub Actions
```

## Exécution manuelle

Tu peux aussi lancer le workflow manuellement depuis l’onglet **Actions** de GitHub.

## Dépendances

- `requests`
- `beautifulsoup4`

Installe-les localement si tu veux tester en local :

```bash
pip install -r requirements.txt
```

## Licence

Libre d’usage.