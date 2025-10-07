# tests/integration/test_experiment_flow.py

import pytest
from orchestration.services.experiment_service import ExperimentService

class TestExperimentFlow:
    """Integration tests for complete experiment flow"""
    
    @pytest.mark.asyncio
    async def test_complete_experiment_lifecycle(self, db_manager, test_user):
        """Test full experiment lifecycle"""
        service = ExperimentService(db_manager)
        
        # 1. Create experiment
        result = await service.create_experiment(
            user_id=test_user['id'],
            name='Integration Test Experiment',
            variants_data=[
                {'name': 'Control', 'content': {'text': 'Control'}},
                {'name': 'Variant A', 'content': {'text': 'Variant A'}}
            ],
            config={'min_samples': 10}
        )
        
        experiment_id = result['experiment_id']
        assert len(result['variant_ids']) == 2
        
        # 2. Allocate users and simulate conversions
        conversions = {'Control': 0, 'Variant A': 0}
        allocations = {}
        
        for i in range(100):
            user_id = f'user_{i}'
            
            # Allocate
            allocation = await service.allocate_user_to_variant(
                experiment_id=experiment_id,
                user_identifier=user_id,
                context={'device': 'mobile' if i % 2 == 0 else 'desktop'}
            )
            
            allocations[user_id] = allocation['variant_id']
            
            # Simulate conversion (Variant A performs better)
            variant_name = next(
                v['name'] for v in await db_manager.pool.fetchrow(
                    "SELECT name FROM variants WHERE id = $1",
                    allocation['variant_id']
                )
            )
            
            should_convert = (
                (variant_name == 'Control' and i % 5 == 0) or  # 20%
                (variant_name == 'Variant A' and i % 3 == 0)   # 33%
            )
            
            if should_convert:
                await service.record_conversion(
                    experiment_id=experiment_id,
                    user_identifier=user_id,
                    value=1.0
                )
                conversions[variant_name] = conversions.get(variant_name, 0) + 1
        
        # 3. Verify Thompson Sampling learned
        # Variant A should get more traffic as experiment progresses
        recent_allocations = [
            allocations[f'user_{i}'] 
            for i in range(50, 100)  # Last 50 users
        ]
        
        variant_a_id = result['variant_ids'][1]
        variant_a_count = recent_allocations.count(variant_a_id)
        
        # Should allocate more to better performer
        assert variant_a_count > 25  # More than 50%
    
    @pytest.mark.asyncio
    async def test_experiment_state_persistence(self, db_manager, test_experiment):
        """Test that algorithm state persists correctly"""
        service = ExperimentService(db_manager)
        
        # Allocate and convert
        allocation1 = await service.allocate_user_to_variant(
            experiment_id=test_experiment['id'],
            user_identifier='persist_test_1'
        )
        
        await service.record_conversion(
            experiment_id=test_experiment['id'],
            user_identifier='persist_test_1',
            value=1.0
        )
        
        # Get variant state before
        from data_access.repositories.variant_repository import VariantRepository
        repo = VariantRepository(db_manager.pool)
        
        variant_before = await repo.get_variant_with_algorithm_state(
            allocation1['variant_id']
        )
        
        success_before = variant_before['algorithm_state_decrypted']['success_count']
        
        # Allocate another user to same variant and convert
        allocation2 = await service.allocate_user_to_variant(
            experiment_id=test_experiment['id'],
            user_identifier='persist_test_2'
        )
        
        # If same variant, convert and check persistence
        if allocation2['variant_id'] == allocation1['variant_id']:
            await service.record_conversion(
                experiment_id=test_experiment['id'],
                user_identifier='persist_test_2',
                value=1.0
            )
            
            variant_after = await repo.get_variant_with_algorithm_state(
                allocation1['variant_id']
            )
            
            success_after = variant_after['algorithm_state_decrypted']['success_count']
            assert success_after > success_before
