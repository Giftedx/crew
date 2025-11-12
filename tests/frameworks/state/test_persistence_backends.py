"""Tests for state persistence backends."""

import sqlite3
import tempfile
from pathlib import Path

import pytest


# Skip these tests as framework modules are not yet implemented
pytest.skip("Framework modules not yet implemented", allow_module_level=True)

# from ai.frameworks.state.persistence import MemoryBackend, SQLiteBackend
# from ai.frameworks.state.unified_state import UnifiedWorkflowState


class TestMemoryBackend:
    """Tests for MemoryBackend."""

    @pytest.fixture
    def backend(self):
        """Create a fresh MemoryBackend for each test."""
        return MemoryBackend()

    @pytest.fixture
    def sample_state(self):
        """Create sample state dictionary."""
        state = UnifiedWorkflowState()
        state.add_message("user", "Hello")
        state.add_message("assistant", "Hi there!")
        state.update_context(step=1, user_name="Alice")
        return state.to_dict()

    @pytest.mark.asyncio
    async def test_save_and_load(self, backend, sample_state):
        """Test saving and loading state."""
        workflow_id = "test-workflow-1"

        # Save state
        await backend.save(workflow_id, sample_state)

        # Load state
        loaded = await backend.load(workflow_id)
        assert loaded is not None
        assert loaded["metadata"]["workflow_id"] == sample_state["metadata"]["workflow_id"]
        assert len(loaded["messages"]) == len(sample_state["messages"])
        assert loaded["context"] == sample_state["context"]

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, backend):
        """Test loading nonexistent state."""
        loaded = await backend.load("nonexistent-workflow")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete(self, backend, sample_state):
        """Test deleting state."""
        workflow_id = "test-workflow-2"

        # Save then delete
        await backend.save(workflow_id, sample_state)
        deleted = await backend.delete(workflow_id)
        assert deleted is True

        # Verify deleted
        loaded = await backend.load(workflow_id)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, backend):
        """Test deleting nonexistent state."""
        deleted = await backend.delete("nonexistent-workflow")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_list_workflows(self, backend, sample_state):
        """Test listing workflows."""
        # Initially empty
        workflows = await backend.list_workflows()
        assert len(workflows) == 0

        # Save multiple workflows
        await backend.save("workflow-1", sample_state)
        await backend.save("workflow-2", sample_state)
        await backend.save("workflow-3", sample_state)

        # List all
        workflows = await backend.list_workflows()
        assert len(workflows) == 3
        assert "workflow-1" in workflows
        assert "workflow-2" in workflows
        assert "workflow-3" in workflows

    @pytest.mark.asyncio
    async def test_state_isolation(self, backend):
        """Test that saved states are isolated (no reference sharing)."""
        workflow_id = "test-workflow-3"

        # Create fresh state for this test
        state = UnifiedWorkflowState()
        state.add_message("user", "Hello")
        state.update_context(step=1)
        sample_state = state.to_dict()

        # Save state
        await backend.save(workflow_id, sample_state)

        # Modify original state
        sample_state["context"]["step"] = 999

        # Load state and verify it wasn't affected
        loaded = await backend.load(workflow_id)
        assert loaded["context"]["step"] == 1  # Original value

    @pytest.mark.asyncio
    async def test_update_state(self, backend, sample_state):
        """Test updating existing state."""
        workflow_id = "test-workflow-4"

        # Save initial state
        await backend.save(workflow_id, sample_state)

        # Create updated state
        updated_state = sample_state.copy()
        updated_state["context"]["step"] = 2

        # Save updated state
        await backend.save(workflow_id, updated_state)

        # Load and verify update
        loaded = await backend.load(workflow_id)
        assert loaded["context"]["step"] == 2

    def test_clear(self, backend, sample_state):
        """Test clearing all state."""
        import asyncio

        # Save multiple workflows
        asyncio.run(backend.save("workflow-1", sample_state))
        asyncio.run(backend.save("workflow-2", sample_state))

        # Clear all
        backend.clear()

        # Verify empty
        workflows = asyncio.run(backend.list_workflows())
        assert len(workflows) == 0


class TestSQLiteBackend:
    """Tests for SQLiteBackend."""

    @pytest.fixture
    def backend(self):
        """Create a SQLiteBackend with temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        backend = SQLiteBackend(db_path)
        yield backend
        backend.close()

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def sample_state(self):
        """Create sample state dictionary."""
        state = UnifiedWorkflowState()
        state.add_message("user", "Hello")
        state.add_message("assistant", "Hi there!")
        state.update_context(step=1, user_name="Bob")
        return state.to_dict()

    @pytest.mark.asyncio
    async def test_save_and_load(self, backend, sample_state):
        """Test saving and loading state."""
        workflow_id = "test-workflow-1"

        # Save state
        await backend.save(workflow_id, sample_state)

        # Load state
        loaded = await backend.load(workflow_id)
        assert loaded is not None
        assert loaded["metadata"]["workflow_id"] == sample_state["metadata"]["workflow_id"]
        assert len(loaded["messages"]) == len(sample_state["messages"])
        assert loaded["context"] == sample_state["context"]

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, backend):
        """Test loading nonexistent state."""
        loaded = await backend.load("nonexistent-workflow")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete(self, backend, sample_state):
        """Test deleting state."""
        workflow_id = "test-workflow-2"

        # Save then delete
        await backend.save(workflow_id, sample_state)
        deleted = await backend.delete(workflow_id)
        assert deleted is True

        # Verify deleted
        loaded = await backend.load(workflow_id)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, backend):
        """Test deleting nonexistent state."""
        deleted = await backend.delete("nonexistent-workflow")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_list_workflows(self, backend, sample_state):
        """Test listing workflows."""
        # Initially empty
        workflows = await backend.list_workflows()
        assert len(workflows) == 0

        # Save multiple workflows
        await backend.save("workflow-1", sample_state)
        await backend.save("workflow-2", sample_state)
        await backend.save("workflow-3", sample_state)

        # List all
        workflows = await backend.list_workflows()
        assert len(workflows) == 3
        assert "workflow-1" in workflows
        assert "workflow-2" in workflows
        assert "workflow-3" in workflows

    @pytest.mark.asyncio
    async def test_update_state(self, backend, sample_state):
        """Test updating existing state."""
        workflow_id = "test-workflow-4"

        # Save initial state
        await backend.save(workflow_id, sample_state)

        # Create updated state
        updated_state = sample_state.copy()
        updated_state["context"]["step"] = 2

        # Save updated state
        await backend.save(workflow_id, updated_state)

        # Load and verify update
        loaded = await backend.load(workflow_id)
        assert loaded["context"]["step"] == 2

    @pytest.mark.asyncio
    async def test_persistence_across_instances(self, sample_state):
        """Test that state persists across backend instances."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        workflow_id = "test-workflow-5"

        try:
            # Save with first instance
            backend1 = SQLiteBackend(db_path)
            await backend1.save(workflow_id, sample_state)
            backend1.close()

            # Load with second instance
            backend2 = SQLiteBackend(db_path)
            loaded = await backend2.load(workflow_id)
            backend2.close()

            assert loaded is not None
            assert loaded["metadata"]["workflow_id"] == sample_state["metadata"]["workflow_id"]
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_table_creation(self):
        """Test that database table is created correctly."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            backend = SQLiteBackend(db_path)
            # Access connection to trigger table creation
            backend._get_connection()
            backend.close()

            # Verify table exists
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_states'")
            assert cursor.fetchone() is not None
            conn.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_large_state(self, backend):
        """Test saving and loading large state."""
        workflow_id = "test-workflow-large"

        # Create large state with many messages
        state = UnifiedWorkflowState()
        for i in range(100):
            state.add_message("user", f"Message {i}" * 100)  # Long messages
            state.add_message("assistant", f"Response {i}" * 100)

        state_dict = state.to_dict()

        # Save and load
        await backend.save(workflow_id, state_dict)
        loaded = await backend.load(workflow_id)

        assert loaded is not None
        assert len(loaded["messages"]) == 200
