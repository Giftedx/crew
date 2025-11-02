"""Tests for memory coordination system."""
import time
from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
from ultimate_discord_intelligence_bot.features.memory_coordinator import MemoryAccessLevel, MemoryCoordinator, MemoryEntry, MemoryOperation

class TestMemoryCoordinator:
    """Test suite for MemoryCoordinator system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.feature_flags = FeatureFlags()
        self.feature_flags.ENABLE_MEMORY_COORDINATION = True
        self.coordinator = MemoryCoordinator(self.feature_flags)

    def test_initialization(self):
        """Test memory coordinator initialization."""
        assert self.coordinator.feature_flags == self.feature_flags
        assert self.coordinator.is_enabled() is True
        assert len(self.coordinator.memory_pool) == 0
        assert len(self.coordinator.access_log) == 0

    def test_disabled_coordination(self):
        """Test behavior when coordination is disabled."""
        self.feature_flags.ENABLE_MEMORY_COORDINATION = False
        coordinator = MemoryCoordinator(self.feature_flags)
        assert coordinator.is_enabled() is False

    def test_store_memory_private(self):
        """Test storing private memory."""
        result = self.coordinator.store_memory(key='test_key', value='test_value', agent_id='agent1', access_level=MemoryAccessLevel.PRIVATE)
        assert result.success
        assert 'test_key' in self.coordinator.memory_pool
        assert self.coordinator.memory_pool['test_key'].value == 'test_value'
        assert self.coordinator.memory_pool['test_key'].agent_id == 'agent1'
        assert self.coordinator.memory_pool['test_key'].access_level == MemoryAccessLevel.PRIVATE

    def test_store_memory_shared(self):
        """Test storing shared memory."""
        result = self.coordinator.store_memory(key='shared_key', value='shared_value', agent_id='agent1', access_level=MemoryAccessLevel.SHARED)
        assert result.success
        assert 'shared_key' in self.coordinator.memory_pool
        assert 'shared_key' in self.coordinator.shared_context
        assert self.coordinator.shared_context['shared_key'] == 'shared_value'

    def test_store_memory_global(self):
        """Test storing global memory."""
        result = self.coordinator.store_memory(key='global_key', value='global_value', agent_id='agent1', access_level=MemoryAccessLevel.GLOBAL)
        assert result.success
        assert 'global_key' in self.coordinator.memory_pool
        assert 'global_key' in self.coordinator.shared_context

    def test_store_memory_with_ttl(self):
        """Test storing memory with TTL."""
        result = self.coordinator.store_memory(key='ttl_key', value='ttl_value', agent_id='agent1', access_level=MemoryAccessLevel.PRIVATE, ttl=0.1)
        assert result.success
        assert 'ttl_key' in self.coordinator.memory_pool
        time.sleep(0.2)
        result = self.coordinator.retrieve_memory('ttl_key', 'agent1')
        assert not result.success
        assert 'expired' in result.error

    def test_store_memory_with_tags(self):
        """Test storing memory with tags."""
        result = self.coordinator.store_memory(key='tagged_key', value='tagged_value', agent_id='agent1', access_level=MemoryAccessLevel.PRIVATE, tags={'category1', 'category2'})
        assert result.success
        entry = self.coordinator.memory_pool['tagged_key']
        assert entry.tags == {'category1', 'category2'}

    def test_retrieve_memory_success(self):
        """Test successful memory retrieval."""
        self.coordinator.store_memory('test_key', 'test_value', 'agent1')
        result = self.coordinator.retrieve_memory('test_key', 'agent1')
        assert result.success
        assert result.data['value'] == 'test_value'
        assert result.data['agent_id'] == 'agent1'

    def test_retrieve_memory_not_found(self):
        """Test retrieving non-existent memory."""
        result = self.coordinator.retrieve_memory('nonexistent', 'agent1')
        assert not result.success
        assert 'not found' in result.error

    def test_retrieve_memory_access_denied(self):
        """Test access denied for private memory."""
        self.coordinator.store_memory('private_key', 'private_value', 'agent1')
        result = self.coordinator.retrieve_memory('private_key', 'agent2')
        assert not result.success
        assert 'Access denied' in result.error

    def test_retrieve_memory_shared_access(self):
        """Test accessing shared memory."""
        self.coordinator.store_memory('shared_key', 'shared_value', 'agent1', MemoryAccessLevel.SHARED)
        result = self.coordinator.retrieve_memory('shared_key', 'agent2')
        assert result.success
        assert result.data['value'] == 'shared_value'

    def test_search_memory(self):
        """Test memory search functionality."""
        self.coordinator.store_memory('key1', 'value with search term', 'agent1')
        self.coordinator.store_memory('key2', 'different value', 'agent1')
        self.coordinator.store_memory('search_key', 'another search term', 'agent1')
        result = self.coordinator.search_memory('search', 'agent1')
        assert result.success
        assert result.data['total_found'] == 2
        assert len(result.data['matches']) == 2

    def test_search_memory_with_tags(self):
        """Test memory search with tag filtering."""
        self.coordinator.store_memory('key1', 'value1', 'agent1', tags={'category1'})
        self.coordinator.store_memory('key2', 'value2', 'agent1', tags={'category2'})
        result = self.coordinator.search_memory('value', 'agent1', tags={'category1'})
        assert result.success
        assert result.data['total_found'] == 1
        assert result.data['matches'][0]['key'] == 'key1'

    def test_get_shared_context(self):
        """Test getting shared context."""
        self.coordinator.store_memory('shared_key', 'shared_value', 'agent1', MemoryAccessLevel.SHARED)
        self.coordinator.store_memory('private_key', 'private_value', 'agent1', MemoryAccessLevel.PRIVATE)
        result = self.coordinator.get_shared_context('agent2')
        assert result.success
        assert 'shared_key' in result.data['shared_context']
        assert 'private_key' not in result.data['shared_context']

    def test_update_memory(self):
        """Test updating existing memory."""
        self.coordinator.store_memory('update_key', 'old_value', 'agent1')
        result = self.coordinator.update_memory('update_key', 'new_value', 'agent1')
        assert result.success
        retrieve_result = self.coordinator.retrieve_memory('update_key', 'agent1')
        assert retrieve_result.success
        assert retrieve_result.data['value'] == 'new_value'

    def test_delete_memory(self):
        """Test deleting memory."""
        self.coordinator.store_memory('delete_key', 'delete_value', 'agent1')
        result = self.coordinator.delete_memory('delete_key', 'agent1')
        assert result.success
        assert 'delete_key' not in self.coordinator.memory_pool

    def test_delete_memory_not_found(self):
        """Test deleting non-existent memory."""
        result = self.coordinator.delete_memory('nonexistent', 'agent1')
        assert not result.success
        assert 'not found' in result.error

    def test_get_memory_stats(self):
        """Test getting memory statistics."""
        self.coordinator.store_memory('key1', 'value1', 'agent1')
        self.coordinator.store_memory('key2', 'value2', 'agent1')
        self.coordinator.store_memory('key3', 'value3', 'agent2')
        result = self.coordinator.get_memory_stats()
        assert result.success
        assert result.data['total_memories'] == 3
        assert result.data['agent_memories'] == 3
        result = self.coordinator.get_memory_stats('agent1')
        assert result.success
        assert result.data['agent_memories'] == 2

    def test_cleanup_expired_memories(self):
        """Test cleanup of expired memories."""
        self.coordinator.store_memory('expired_key', 'expired_value', 'agent1', ttl=0.1)
        time.sleep(0.2)
        cleaned_count = self.coordinator.cleanup_expired_memories()
        assert cleaned_count == 1
        assert 'expired_key' not in self.coordinator.memory_pool

    def test_access_logging(self):
        """Test that memory access is logged."""
        self.coordinator.store_memory('log_key', 'log_value', 'agent1')
        self.coordinator.retrieve_memory('log_key', 'agent1')
        assert len(self.coordinator.access_log) == 2
        store_access = self.coordinator.access_log[0]
        assert store_access.operation == MemoryOperation.WRITE
        assert store_access.agent_id == 'agent1'
        assert store_access.success is True
        retrieve_access = self.coordinator.access_log[1]
        assert retrieve_access.operation == MemoryOperation.READ
        assert retrieve_access.agent_id == 'agent1'
        assert retrieve_access.success is True

    def test_agent_quota_check(self):
        """Test agent quota checking."""
        self.coordinator.agent_memory_quotas['agent1'] = 2
        self.coordinator.store_memory('key1', 'value1', 'agent1')
        self.coordinator.store_memory('key2', 'value2', 'agent1')
        result = self.coordinator.store_memory('key3', 'value3', 'agent1')
        assert not result.success
        assert 'quota exceeded' in result.error

    def test_memory_entry_creation(self):
        """Test MemoryEntry creation and properties."""
        entry = MemoryEntry(key='test_key', value='test_value', agent_id='agent1', access_level=MemoryAccessLevel.PRIVATE, ttl=60.0, tags={'tag1', 'tag2'}, metadata={'meta': 'data'})
        assert entry.key == 'test_key'
        assert entry.value == 'test_value'
        assert entry.agent_id == 'agent1'
        assert entry.access_level == MemoryAccessLevel.PRIVATE
        assert entry.ttl == 60.0
        assert entry.tags == {'tag1', 'tag2'}
        assert entry.metadata == {'meta': 'data'}
        assert entry.created_at > 0
        assert entry.updated_at > 0

    def test_disabled_operations(self):
        """Test operations when coordination is disabled."""
        self.feature_flags.ENABLE_MEMORY_COORDINATION = False
        coordinator = MemoryCoordinator(self.feature_flags)
        store_result = coordinator.store_memory('key', 'value', 'agent1')
        assert not store_result.success
        retrieve_result = coordinator.retrieve_memory('key', 'agent1')
        assert not retrieve_result.success
        search_result = coordinator.search_memory('query', 'agent1')
        assert not search_result.success

    def test_concurrent_access(self):
        """Test concurrent memory access."""
        import threading
        results = []

        def store_memory(agent_id, key, value):
            result = self.coordinator.store_memory(key, value, agent_id)
            results.append(result)
        threads = []
        for i in range(5):
            thread = threading.Thread(target=store_memory, args=(f'agent{i}', f'key{i}', f'value{i}'))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        assert len(results) == 5
        assert all((result.success for result in results))
        assert len(self.coordinator.memory_pool) == 5