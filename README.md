boutique_app/
│
├── .gitignore                    # <-- À ajouter (Sécurité Git)
├── README.md[cite: 11]
│
├── supabase/                     # <-- À ajouter (Sauvegarde Edge Function)
│   └── functions/
│       └── paytech-webhook/
│           └── index.ts
│
└── src/
    ├── main.py
    ├── requirements.txt
    │
    ├── database/
    │   ├── __init__.py
    │   ├── db_manager.py
    │   └── supabase_client.py
    │
    ├── ui/
    │   ├── __init__.py
    │   ├── auth_view.py
    │   ├── components/
    │   │   ├── __init__.py
    │   │   ├── client_tile.py
    │   │   ├── header.py
    │   │   └── pin_view.py
    │   └── dialogs/
    │       ├── __init__.py
    │       ├── ajout_client.py
    │       ├── dialogue_operation.py   # <-- Nom corrigé avec le "e"[cite: 1, 11]
    │       └── pin_settings.py
    │
    └── utils/
        ├── __init__.py
        ├── formatters.py
        ├── paytech_service.py
        ├── subscription_checker.py
        └── updater.py