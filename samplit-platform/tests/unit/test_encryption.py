# tests/unit/test_encryption.py

import pytest
from engine.state.encryption import StateEncryption, get_encryptor

class TestStateEncryption:
    """Test suite for state encryption"""
    
    def test_encryption_singleton(self):
        """Test encryptor singleton pattern"""
        enc1 = get_encryptor()
        enc2 = get_encryptor()
        assert enc1 is enc2
    
    def test_encrypt_decrypt_state(self, encryptor: StateEncryption):
        """Test basic encryption/decryption"""
        original_state = {
            'alpha': 5.0,
            'beta': 3.0,
            'samples': 100,
            'algorithm_type': 'bayesian'
        }
        
        # Encrypt
        encrypted = encryptor.encrypt_state(original_state)
        assert isinstance(encrypted, bytes)
        assert len(encrypted) > 0
        
        # Decrypt
        decrypted = encryptor.decrypt_state(encrypted)
        assert decrypted == original_state
    
    def test_encrypt_complex_state(self, encryptor: StateEncryption):
        """Test encryption with complex nested data"""
        complex_state = {
            'success_count': 10,
            'failure_count': 5,
            'exploration_rate': 0.15,
            'metadata': {
                'last_updated': '2024-01-01',
                'version': 1
            },
            'nested': {
                'deep': {
                    'value': [1, 2, 3]
                }
            }
        }
        
        encrypted = encryptor.encrypt_state(complex_state)
        decrypted = encryptor.decrypt_state(encrypted)
        
        assert decrypted == complex_state
    
    def test_encrypt_path_data(self, encryptor: StateEncryption):
        """Test path encryption for funnels"""
        path = ['variant_1', 'variant_2', 'variant_3']
        
        encrypted = encryptor.encrypt_path_data(path)
        decrypted = encryptor.decrypt_path_data(encrypted)
        
        assert decrypted == path
    
    def test_encryption_deterministic(self, encryptor: StateEncryption):
        """Test that same data encrypts differently each time (IV)"""
        state = {'alpha': 1.0, 'beta': 1.0}
        
        encrypted1 = encryptor.encrypt_state(state)
        encrypted2 = encryptor.encrypt_state(state)
        
        # Should be different due to IV
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same value
        assert encryptor.decrypt_state(encrypted1) == state
        assert encryptor.decrypt_state(encrypted2) == state
    
    def test_decrypt_invalid_data(self, encryptor: StateEncryption):
        """Test decryption of invalid data raises error"""
        with pytest.raises(Exception):
            encryptor.decrypt_state(b'invalid_encrypted_data')
    
    def test_empty_state(self, encryptor: StateEncryption):
        """Test encryption of empty state"""
        empty_state = {}
        
        encrypted = encryptor.encrypt_state(empty_state)
        decrypted = encryptor.decrypt_state(encrypted)
        
        assert decrypted == empty_state
