boutique_app/
├── .gitignore                    # Exclusion des fichiers temporaires, bases locales et clés
├── README.md                     # Documentation officielle du projet
├──pyproject.toml
│
│
├── supabase/                     # Backend Cloud & Webhook
│   └── functions/
│       └── paytech-webhook/
│           └── index.ts          # Edge Function de validation des paiements PayTech
│
└── src/                          # Code source principal (Python)
    ├── assets/                       # Ressources visuelles de l'application
    │   └── icon.png                  # Icône HD de l'application (Android / Fenêtre)
    ├── main.py                   # Point d'entrée de l'application Flet
    ├── requirements.txt          # Dépendances Python verrouillées
    │
    ├── database/                 # Couche de données
    │   ├── __init__.py
    │   ├── db_manager.py         # Gestionnaire SQLite local (Clients, Transactions, Cache)
    │   └── supabase_client.py    # Client Supabase Cloud
    │
    ├── ui/                       # Composants et Vues Flet
    │   ├── __init__.py
    │   ├── auth_view.py          # Écran de connexion / identification
    │   ├── components/           # Composants réutilisables
    │   │   ├── __init__.py
    │   │   ├── client_tile.py    # Carte déroulante client & historique
    │   │   ├── header.py         # En-tête avec totaux
    │   │   └── pin_view.py       # Interface de saisie du PIN
    │   └── dialogs/              # Boîtes de dialogue
    │       ├── __init__.py
    │       ├── ajout_client.py
    │       ├── dialogue_operation.py
    │       └── pin_settings.py
    │
    └── utils/                    # Services et Utilitaires
        ├── __init__.py
        ├── formatters.py         # Formatage des devises (FCFA) et dates
        ├── paytech_service.py    # Génération des liens de paiement PayTech
        ├── subscription_checker.py # Vérification d'abonnement + Cache local 3 jours
        └── updater.py            # Vérificateur de mises à jour GitHub Releases