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
    ├── main.py[cite: 11]
    ├── requirements.txt[cite: 11]
    │
    ├── database/[cite: 11]
    │   ├── __init__.py[cite: 11]
    │   ├── db_manager.py[cite: 11]
    │   └── supabase_client.py[cite: 11]
    │
    ├── ui/[cite: 11]
    │   ├── __init__.py[cite: 11]
    │   ├── auth_view.py[cite: 11]
    │   ├── components/[cite: 11]
    │   │   ├── __init__.py[cite: 11]
    │   │   ├── client_tile.py[cite: 11]
    │   │   ├── header.py[cite: 11]
    │   │   └── pin_view.py[cite: 11]
    │   └── dialogs/[cite: 11]
    │       ├── __init__.py[cite: 11]
    │       ├── ajout_client.py[cite: 11]
    │       ├── dialogue_operation.py   # <-- Nom corrigé avec le "e"[cite: 1, 11]
    │       └── pin_settings.py[cite: 11]
    │
    └── utils/[cite: 11]
        ├── __init__.py[cite: 11]
        ├── formatters.py[cite: 11]
        ├── paytech_service.py[cite: 11]
        ├── subscription_checker.py[cite: 11]
        └── updater.py[cite: 11]