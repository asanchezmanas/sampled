# tests/conftest.py

import pytest
import asyncio
import asyncpg
import os
from typing import AsyncGenerator
from datetime import datetime, timezone

# Asegurar que el secret esté disponible para tests
os.environ['ALGORITHM_STATE_SECRET'] = 'test-secret-key-minimum-32-characters-for-testing-purposes'
os.environ['SUPABASE_DB_URL'] = os.environ.get('TEST_DATABASE_URL', 'postgresql://localhost/samplit_test')

from data_access.database import DatabaseManager
from engine.state.encryption import StateEncryption

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_manager() -> AsyncGenerator[DatabaseManager, None]:
    """
    Database manager for tests
    Uses separate test database
    """
    db = DatabaseManager()
    await db.initialize()
    
    # Ensure clean state
    await _clean_test_database(db)
    
    yield db
    
    # Cleanup after all tests
    await _clean_test_database(db)
    await db.close()

async def _clean_test_database(db: DatabaseManager):
    """Clean test database"""
    async with db.pool.acquire() as conn:
        # Delete in reverse order of dependencies
        await conn.execute("DELETE FROM element_interactions")
        await conn.execute("DELETE FROM micro_conversions")
        await conn.execute("DELETE FROM session_analytics")
        await conn.execute("DELETE FROM funnel_path_performance")
        await conn.execute("DELETE FROM allocations")
        await conn.execute("DELETE FROM variants")
        await conn.execute("DELETE FROM experiments")
        await conn.execute("DELETE FROM users")

@pytest.fixture
async def test_user(db_manager: DatabaseManager) -> dict:
    """Create test user"""
    from data_access.repositories.user_repository import UserRepository
    
    repo = UserRepository(db_manager.pool)
    user_id = await repo.create({
        'email': 'test@example.com',
        'name': 'Test User',
        'password_hash': 'fake_hash'
    })
    
    return {'id': user_id, 'email': 'test@example.com', 'name': 'Test User'}

@pytest.fixture
async def test_experiment(db_manager: DatabaseManager, test_user: dict) -> dict:
    """Create test experiment with variants"""
    from data_access.repositories.experiment_repository import ExperimentRepository
    from data_access.repositories.variant_repository import VariantRepository
    
    exp_repo = ExperimentRepository(db_manager.pool)
    var_repo = VariantRepository(db_manager.pool)
    
    # Create experiment
    exp_id = await exp_repo.create({
        'user_id': test_user['id'],
        'name': 'Test Experiment',
        'description': 'Test Description',
        'optimization_strategy': 'adaptive',
        'config': {},
        'status': 'active'
    })
    
    # Create variants
    variant_ids = []
    for i, name in enumerate(['Control', 'Variant A', 'Variant B']):
        var_id = await var_repo.create_variant(
            experiment_id=exp_id,
            name=name,
            content={'text': f'Content {i}'},
            initial_algorithm_state={
                'success_count': 1,
                'failure_count': 1,
                'samples': 0,
                'algorithm_type': 'bayesian'
            }
        )
        variant_ids.append(var_id)
    
    return {
        'id': exp_id,
        'user_id': test_user['id'],
        'variant_ids': variant_ids
    }

@pytest.fixture
def encryptor() -> StateEncryption:
    """Encryption instance for tests"""
    return StateEncryption()
