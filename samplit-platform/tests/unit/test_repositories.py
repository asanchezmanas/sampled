# tests/unit/test_repositories.py

import pytest
from data_access.repositories.variant_repository import VariantRepository
from data_access.repositories.experiment_repository import ExperimentRepository
from data_access.repositories.allocation_repository import AllocationRepository

class TestVariantRepository:
    """Test suite for VariantRepository"""
    
    @pytest.mark.asyncio
    async def test_create_variant_with_encryption(
        self, 
        db_manager, 
        test_experiment
    ):
        """Test creating variant with encrypted state"""
        repo = VariantRepository(db_manager.pool)
        
        variant_id = await repo.create_variant(
            experiment_id=test_experiment['id'],
            name='Test Variant',
            content={'text': 'Test content'},
            initial_algorithm_state={
                'success_count': 1,
                'failure_count': 1,
                'samples': 0,
                'algorithm_type': 'bayesian'
            }
        )
        
        assert variant_id is not None
        assert len(variant_id) > 0
    
    @pytest.mark.asyncio
    async def test_get_variant_with_decrypted_state(
        self,
        db_manager,
        test_experiment
    ):
        """Test retrieving variant with decrypted state"""
        repo = VariantRepository(db_manager.pool)
        
        # Use existing variant from fixture
        variant_id = test_experiment['variant_ids'][0]
        
        variant = await repo.get_variant_with_algorithm_state(variant_id)
        
        assert variant is not None
        assert 'algorithm_state_decrypted' in variant
        assert 'success_count' in variant['algorithm_state_decrypted']
        assert 'failure_count' in variant['algorithm_state_decrypted']
    
    @pytest.mark.asyncio
    async def test_update_algorithm_state(
        self,
        db_manager,
        test_experiment
    ):
        """Test updating encrypted algorithm state"""
        repo = VariantRepository(db_manager.pool)
        variant_id = test_experiment['variant_ids'][0]
        
        # Get initial state
        initial = await repo.get_variant_with_algorithm_state(variant_id)
        initial_success = initial['algorithm_state_decrypted']['success_count']
        
        # Update state
        new_state = initial['algorithm_state_decrypted'].copy()
        new_state['success_count'] += 1
        
        await repo.update_algorithm_state(variant_id, new_state)
        
        # Verify update
        updated = await repo.get_variant_with_algorithm_state(variant_id)
        assert updated['algorithm_state_decrypted']['success_count'] == initial_success + 1
    
    @pytest.mark.asyncio
    async def test_get_variants_for_optimization(
        self,
        db_manager,
        test_experiment
    ):
        """Test retrieving all variants for optimization"""
        repo = VariantRepository(db_manager.pool)
        
        variants = await repo.get_variants_for_optimization(
            test_experiment['id']
        )
        
        assert len(variants) == 3  # From fixture
        
        for variant in variants:
            assert 'algorithm_state' in variant
            assert 'success_count' in variant['algorithm_state']
            assert 'failure_count' in variant['algorithm_state']
    
    @pytest.mark.asyncio
    async def test_get_variant_public_data_no_state(
        self,
        db_manager,
        test_experiment
    ):
        """Test public data doesn't include algorithm state"""
        repo = VariantRepository(db_manager.pool)
        variant_id = test_experiment['variant_ids'][0]
        
        public_data = await repo.get_variant_public_data(variant_id)
        
        assert public_data is not None
        assert 'algorithm_state' not in public_data
        assert 'algorithm_state_decrypted' not in public_data

class TestExperimentRepository:
    """Test suite for ExperimentRepository"""
    
    @pytest.mark.asyncio
    async def test_create_experiment(self, db_manager, test_user):
        """Test creating experiment"""
        repo = ExperimentRepository(db_manager.pool)
        
        exp_id = await repo.create({
            'user_id': test_user['id'],
            'name': 'New Test Experiment',
            'description': 'Test',
            'optimization_strategy': 'adaptive',
            'config': {'test': 'value'},
            'status': 'draft'
        })
        
        assert exp_id is not None
    
    @pytest.mark.asyncio
    async def test_find_experiment_by_id(self, db_manager, test_experiment):
        """Test finding experiment"""
        repo = ExperimentRepository(db_manager.pool)
        
        experiment = await repo.find_by_id(test_experiment['id'])
        
        assert experiment is not None
        assert experiment['id'] == test_experiment['id']
        assert experiment['name'] == 'Test Experiment'

class TestAllocationRepository:
    """Test suite for AllocationRepository"""
    
    @pytest.mark.asyncio
    async def test_create_allocation(self, db_manager, test_experiment):
        """Test creating allocation"""
        repo = AllocationRepository(db_manager.pool)
        
        allocation_id = await repo.create_allocation(
            experiment_id=test_experiment['id'],
            variant_id=test_experiment['variant_ids'][0],
            user_identifier='test_user_123',
            context={'device': 'mobile'}
        )
        
        assert allocation_id is not None
    
    @pytest.mark.asyncio
    async def test_get_existing_allocation(self, db_manager, test_experiment):
        """Test retrieving existing allocation"""
        repo = AllocationRepository(db_manager.pool)
        
        # Create allocation
        await repo.create_allocation(
            experiment_id=test_experiment['id'],
            variant_id=test_experiment['variant_ids'][0],
            user_identifier='test_user_456'
        )
        
        # Retrieve it
        allocation = await repo.get_allocation(
            test_experiment['id'],
            'test_user_456'
        )
        
        assert allocation is not None
        assert allocation['user_identifier'] == 'test_user_456'
    
    @pytest.mark.asyncio
    async def test_record_conversion(self, db_manager, test_experiment):
        """Test recording conversion"""
        repo = AllocationRepository(db_manager.pool)
        
        # Create allocation
        allocation_id = await repo.create_allocation(
            experiment_id=test_experiment['id'],
            variant_id=test_experiment['variant_ids'][0],
            user_identifier='test_user_789'
        )
        
        # Record conversion
        await repo.record_conversion(allocation_id, 5.0)
        
        # Verify
        allocation = await repo.get_allocation(
            test_experiment['id'],
            'test_user_789'
        )
        
        assert allocation['converted_at'] is not None
        assert allocation['conversion_value'] == 5.0
