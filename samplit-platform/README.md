

samplit-platform/
│
├── public-api/                           # 🌐 API Pública (expuesta)
│   ├── main.py
│   ├── routers/
│   │   ├── experiments.py
│   │   ├── analytics.py
│   │   └── webhooks.py
│   └── middleware/
│       └── auth.py
│
├── orchestration/                        # 🎼 Capa de Coordinación
│   ├── services/
│   │   ├── experiment_service.py
│   │   ├── email_optimizer.py
│   │   ├── notification_optimizer.py
│   │   └── funnel_optimizer.py         # Killer feature
│   │
│   ├── interfaces/
│   │   └── optimizer_interface.py       # Abstracción
│   │
│   └── factories/
│       └── optimizer_factory.py         # Oculta implementaciones
│
├── data-access/                          # 🗄️ CAPA DE DATOS (NUEVA)
│   ├── repositories/                     # Repository pattern
│   │   ├── base_repository.py
│   │   ├── experiment_repository.py
│   │   ├── variant_repository.py        
│   │   ├── performance_repository.py    
│   │   ├── funnel_repository.py
│   │   ├── email_campaign_repository.py
│   │   └── notification_repository.py
│   │
│   ├── models/                           # ORM Models (ofuscados)
│   │   ├── experiment.py
│   │   ├── variant.py                   
│   │   ├── allocation.py                
│   │   ├── performance_metric.py        
│   │   ├── funnel.py
│   │   └── optimization_state.py        # Estado del algoritmo (cifrado)
│   │
│   ├── migrations/                       # Alembic migrations
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   │
│   └── database.py                       # Connection manager
│
├── engine/                               # 🔒 MOTOR PRIVADO
│   ├── core/
│   │   ├── allocators/
│   │   │   ├── _bayesian.py            
│   │   │   ├── _explore.py             
│   │   │   ├── _sequential.py          
│   │   │   └── _registry.py
│   │   │
│   │   ├── strategies/
│   │   │   ├── adaptive.py
│   │   │   ├── fast_learning.py
│   │   │   └── multi_step.py
│   │   │
│   │   └── math/
│   │       ├── _distributions.py
│   │       └── _statistics.py
│   │
│   └── state/                            # 🔐 Estado del algoritmo
│       ├── state_manager.py             # Gestión de estado ofuscado
│       └── encryption.py                # Cifrado para DB
│
├── config/
│   ├── settings.py
│   ├── database_config.py               # Supabase config
│   └── security.py
│
└── scripts/
    ├── encrypt_algorithm_state.py       # Cifrar estado antes de DB
    └── setup_database.py
