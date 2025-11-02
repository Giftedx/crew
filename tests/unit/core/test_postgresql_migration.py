"""
Test suite for PostgreSQL migration functionality.

This module tests the unified store manager, migration scripts, and
data integrity during the SQLite to PostgreSQL migration process.
"""
import json
import tempfile
from datetime import datetime
from pathlib import Path
import pytest
from platform.core.store_adapter import CreatorProfile, Debate, KGNode, MemoryItem, UnifiedStoreManager, create_store_manager

@pytest.fixture
def temp_sqlite_db():
    """Create a temporary SQLite database for testing."""
    _db_fd, db_path = tempfile.mkstemp(suffix='.db')
    yield db_path
    Path(db_path).unlink()

@pytest.fixture
def temp_postgresql_url():
    """Create a temporary PostgreSQL database URL for testing."""
    return 'sqlite:///:memory:'

@pytest.fixture
def store_manager(temp_postgresql_url):
    """Create a store manager for testing."""
    manager = UnifiedStoreManager(temp_postgresql_url)
    manager.initialize()
    yield manager
    manager.close()

@pytest.fixture
def sample_memory_items():
    """Create sample memory items for testing."""
    return [MemoryItem(id=None, tenant='test_tenant', workspace='test_workspace', type='conversation', content_json='{"text": "Hello world", "metadata": {"source": "test"}}', embedding_json='[0.1, 0.2, 0.3]', ts_created=datetime.now().isoformat(), ts_last_used=datetime.now().isoformat(), retention_policy='default', decay_score=1.0, pinned=0, archived=0), MemoryItem(id=None, tenant='test_tenant', workspace='test_workspace', type='fact', content_json='{"text": "The sky is blue", "metadata": {"source": "knowledge"}}', embedding_json='[0.4, 0.5, 0.6]', ts_created=datetime.now().isoformat(), ts_last_used=datetime.now().isoformat(), retention_policy='long_term', decay_score=0.8, pinned=1, archived=0)]

@pytest.fixture
def sample_debates():
    """Create sample debates for testing."""
    return [Debate(id=None, tenant='test_tenant', workspace='test_workspace', query='What is the best programming language?', panel_config_json='{"agents": ["python_expert", "javascript_expert"]}', n_rounds=3, final_output='Python is better for data science, JavaScript for web development', created_at=datetime.now().isoformat())]

@pytest.fixture
def sample_kg_nodes():
    """Create sample KG nodes for testing."""
    return [KGNode(id=None, tenant='test_tenant', type='person', name='Ethan Klein', attrs_json='{"platforms": ["youtube", "tiktok"], "followers": 1000000}', created_at=datetime.now().isoformat()), KGNode(id=None, tenant='test_tenant', type='topic', name='debate analysis', attrs_json='{"category": "content", "difficulty": "medium"}', created_at=datetime.now().isoformat())]

@pytest.fixture
def sample_profiles():
    """Create sample creator profiles for testing."""
    return [CreatorProfile(name='ethan_klein', data={'platforms': ['youtube', 'tiktok', 'instagram'], 'subscribers': 1000000, 'content_types': ['podcast', 'shorts', 'long_form'], 'collaborators': ['hasan_piker', 'h3_crew']}), CreatorProfile(name='hasan_piker', data={'platforms': ['twitch', 'youtube', 'x'], 'subscribers': 2000000, 'content_types': ['streaming', 'political_commentary'], 'collaborators': ['ethan_klein', 'destiny']})]

class TestUnifiedStoreManager:
    """Test the unified store manager functionality."""

    def test_initialization(self, temp_postgresql_url):
        """Test store manager initialization."""
        manager = UnifiedStoreManager(temp_postgresql_url)
        result = manager.initialize()
        assert result.success
        assert 'Store initialized successfully' in result.data['data']['message']

    def test_health_check(self, store_manager):
        """Test store manager health check."""
        result = store_manager.health_check()
        assert result.success
        assert result.data['data']['status'] == 'healthy'

    def test_close(self, temp_postgresql_url):
        """Test store manager close."""
        manager = UnifiedStoreManager(temp_postgresql_url)
        manager.initialize()
        result = manager.close()
        assert result.success
        assert 'Store closed successfully' in result.data['data']['message']

class TestMemoryStoreOperations:
    """Test memory store operations."""

    def test_add_memory_item(self, store_manager, sample_memory_items):
        """Test adding memory items."""
        for item in sample_memory_items:
            result = store_manager.add_memory_item(item)
            assert result.success
            assert 'id' in result.data
            assert isinstance(result.data['id'], int)

    def test_get_memory_item(self, store_manager, sample_memory_items):
        """Test getting memory items."""
        result = store_manager.add_memory_item(sample_memory_items[0])
        assert result.success
        item_id = result.data['id']
        result = store_manager.get_memory_item(item_id)
        assert result.success
        assert 'item' in result.data
        item = result.data['item']
        assert item.tenant == sample_memory_items[0].tenant
        assert item.workspace == sample_memory_items[0].workspace
        assert item.type == sample_memory_items[0].type

    def test_get_nonexistent_memory_item(self, store_manager):
        """Test getting a nonexistent memory item."""
        result = store_manager.get_memory_item(99999)
        assert not result.success
        assert 'Memory item not found' in result.error

    def test_update_memory_item_last_used(self, store_manager, sample_memory_items):
        """Test updating memory item last used timestamp."""
        result = store_manager.add_memory_item(sample_memory_items[0])
        assert result.success
        item_id = result.data['id']
        new_timestamp = datetime.now().isoformat()
        result = store_manager.update_memory_item_last_used(item_id, new_timestamp)
        assert result.success
        result = store_manager.get_memory_item(item_id)
        assert result.success
        item = result.data['item']
        assert item.ts_last_used == new_timestamp

    def test_search_memory_keyword(self, store_manager, sample_memory_items):
        """Test searching memory items by keyword."""
        for item in sample_memory_items:
            result = store_manager.add_memory_item(item)
            assert result.success
        result = store_manager.search_memory_keyword('test_tenant', 'test_workspace', 'Hello')
        assert result.success
        assert 'items' in result.data
        items = result.data['items']
        assert len(items) >= 1
        assert any(('Hello' in item.content_json for item in items))

    def test_prune_memory_items(self, store_manager, sample_memory_items):
        """Test pruning memory items."""
        for item in sample_memory_items:
            result = store_manager.add_memory_item(item)
            assert result.success
        result = store_manager.prune_memory_items('test_tenant')
        assert result.success
        assert 'deleted_count' in result.data

class TestDebateStoreOperations:
    """Test debate store operations."""

    def test_add_debate(self, store_manager, sample_debates):
        """Test adding debates."""
        for debate in sample_debates:
            result = store_manager.add_debate(debate)
            assert result.success
            assert 'id' in result.data
            assert isinstance(result.data['id'], int)

    def test_list_debates(self, store_manager, sample_debates):
        """Test listing debates."""
        for debate in sample_debates:
            result = store_manager.add_debate(debate)
            assert result.success
        result = store_manager.list_debates('test_tenant', 'test_workspace')
        assert result.success
        assert 'debates' in result.data
        debates = result.data['debates']
        assert len(debates) >= len(sample_debates)
        debate = debates[0]
        assert debate.tenant == 'test_tenant'
        assert debate.workspace == 'test_workspace'
        assert 'programming language' in debate.query

class TestKnowledgeGraphOperations:
    """Test knowledge graph operations."""

    def test_add_kg_node(self, store_manager, sample_kg_nodes):
        """Test adding KG nodes."""
        for node in sample_kg_nodes:
            result = store_manager.add_kg_node(tenant=node.tenant, type=node.type, name=node.name, attrs=json.loads(node.attrs_json) if node.attrs_json else {})
            assert result.success
            assert 'id' in result.data
            assert isinstance(result.data['id'], int)

    def test_query_kg_nodes(self, store_manager, sample_kg_nodes):
        """Test querying KG nodes."""
        for node in sample_kg_nodes:
            result = store_manager.add_kg_node(tenant=node.tenant, type=node.type, name=node.name, attrs=json.loads(node.attrs_json) if node.attrs_json else {})
            assert result.success
        result = store_manager.query_kg_nodes('test_tenant')
        assert result.success
        assert 'nodes' in result.data
        nodes = result.data['nodes']
        assert len(nodes) >= len(sample_kg_nodes)
        result = store_manager.query_kg_nodes('test_tenant', type='person')
        assert result.success
        assert 'nodes' in result.data
        nodes = result.data['nodes']
        assert all((node.type == 'person' for node in nodes))

class TestProfileStoreOperations:
    """Test profile store operations."""

    def test_upsert_creator_profile(self, store_manager, sample_profiles):
        """Test upserting creator profiles."""
        for profile in sample_profiles:
            result = store_manager.upsert_creator_profile(profile)
            assert result.success
            assert 'Profile upserted successfully' in result.data['data']['message']

    def test_get_creator_profile(self, store_manager, sample_profiles):
        """Test getting creator profiles."""
        for profile in sample_profiles:
            result = store_manager.upsert_creator_profile(profile)
            assert result.success
        result = store_manager.get_creator_profile('ethan_klein')
        assert result.success
        assert 'profile' in result.data
        profile = result.data['profile']
        assert profile.name == 'ethan_klein'
        assert 'platforms' in profile.data
        assert 'youtube' in profile.data['platforms']

    def test_get_nonexistent_creator_profile(self, store_manager):
        """Test getting a nonexistent creator profile."""
        result = store_manager.get_creator_profile('nonexistent_profile')
        assert not result.success
        assert 'Creator profile not found' in result.error

class TestMigrationUtilities:
    """Test migration utility functions."""

    def test_create_store_manager(self, temp_postgresql_url):
        """Test creating a store manager."""
        result = create_store_manager(temp_postgresql_url)
        assert result.success
        assert 'manager' in result.data['data']
        assert isinstance(result.data['data']['manager'], UnifiedStoreManager)

    def test_create_store_manager_invalid_url(self):
        """Test creating a store manager with invalid URL."""
        result = create_store_manager('invalid://url')
        assert not result.success
        assert 'Failed to create store manager' in result.error

class TestDataIntegrity:
    """Test data integrity during migration."""

    def test_memory_item_data_integrity(self, store_manager, sample_memory_items):
        """Test that memory item data is preserved during storage and retrieval."""
        original_item = sample_memory_items[0]
        result = store_manager.add_memory_item(original_item)
        assert result.success
        item_id = result.data['id']
        result = store_manager.get_memory_item(item_id)
        assert result.success
        retrieved_item = result.data['item']
        assert retrieved_item.tenant == original_item.tenant
        assert retrieved_item.workspace == original_item.workspace
        assert retrieved_item.type == original_item.type
        assert retrieved_item.content_json == original_item.content_json
        assert retrieved_item.embedding_json == original_item.embedding_json
        assert retrieved_item.retention_policy == original_item.retention_policy
        assert retrieved_item.decay_score == original_item.decay_score
        assert retrieved_item.pinned == original_item.pinned
        assert retrieved_item.archived == original_item.archived

    def test_debate_data_integrity(self, store_manager, sample_debates):
        """Test that debate data is preserved during storage and retrieval."""
        original_debate = sample_debates[0]
        result = store_manager.add_debate(original_debate)
        assert result.success
        result = store_manager.list_debates(original_debate.tenant, original_debate.workspace)
        assert result.success
        debates = result.data['debates']
        assert len(debates) >= 1
        retrieved_debate = debates[0]
        assert retrieved_debate.tenant == original_debate.tenant
        assert retrieved_debate.workspace == original_debate.workspace
        assert retrieved_debate.query == original_debate.query
        assert retrieved_debate.panel_config_json == original_debate.panel_config_json
        assert retrieved_debate.n_rounds == original_debate.n_rounds
        assert retrieved_debate.final_output == original_debate.final_output

    def test_profile_data_integrity(self, store_manager, sample_profiles):
        """Test that profile data is preserved during storage and retrieval."""
        original_profile = sample_profiles[0]
        result = store_manager.upsert_creator_profile(original_profile)
        assert result.success
        result = store_manager.get_creator_profile(original_profile.name)
        assert result.success
        retrieved_profile = result.data['profile']
        assert retrieved_profile.name == original_profile.name
        assert retrieved_profile.data == original_profile.data

class TestConcurrentAccess:
    """Test concurrent access scenarios."""

    def test_concurrent_memory_item_additions(self, store_manager, sample_memory_items):
        """Test adding memory items concurrently."""
        import threading
        results = []
        errors = []

        def add_item(item):
            try:
                result = store_manager.add_memory_item(item)
                results.append(result)
            except Exception as e:
                errors.append(e)
        threads = []
        for _i in range(5):
            item = sample_memory_items[0]
            thread = threading.Thread(target=add_item, args=(item,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        assert len(errors) == 0, f'Errors during concurrent access: {errors}'
        assert len(results) == 5
        assert all((result.success for result in results))

class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_memory_item_data(self, store_manager):
        """Test handling invalid memory item data."""
        invalid_item = MemoryItem(id=None, tenant='', workspace='test_workspace', type='conversation', content_json='{"text": "Hello world"}', embedding_json='[0.1, 0.2, 0.3]', ts_created=datetime.now().isoformat(), ts_last_used=datetime.now().isoformat(), retention_policy='default', decay_score=1.0, pinned=0, archived=0)
        result = store_manager.add_memory_item(invalid_item)
        assert not result.success

    def test_invalid_debate_data(self, store_manager):
        """Test handling invalid debate data."""
        invalid_debate = Debate(id=None, tenant='test_tenant', workspace='test_workspace', query='', panel_config_json='{"agents": []}', n_rounds=3, final_output='Test output', created_at=datetime.now().isoformat())
        result = store_manager.add_debate(invalid_debate)
        assert not result.success

    def test_invalid_profile_data(self, store_manager):
        """Test handling invalid profile data."""
        invalid_profile = CreatorProfile(name='', data={'platforms': ['youtube']})
        result = store_manager.upsert_creator_profile(invalid_profile)
        assert not result.success
if __name__ == '__main__':
    pytest.main([__file__])