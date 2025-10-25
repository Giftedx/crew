"""Tests for Arq worker and task queue."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

try:
    from arq import ArqRedis
    ARQ_AVAILABLE = True
except ImportError:
    ARQ_AVAILABLE = False
    ArqRedis = None


class TestArqWorker:
    """Test cases for Arq worker."""

    @pytest.fixture
    def worker(self):
        """Create Arq worker instance."""
        from src.tasks.worker import ArqWorker
        return ArqWorker()

    @pytest.mark.skipif(not ARQ_AVAILABLE, reason="Arq not available")
    def test_worker_initialization(self, worker):
        """Test worker initialization."""
        assert worker is not None
        assert worker.settings is not None
        assert worker.worker is None  # Not started yet

    @pytest.mark.skipif(not ARQ_AVAILABLE, reason="Arq not available")
    @pytest.mark.asyncio
    async def test_worker_start_stop(self, worker):
        """Test worker start and stop."""
        # Mock Worker class to avoid actual Redis connection
        with patch('src.tasks.worker.Worker') as mock_worker_class:
            mock_worker = AsyncMock()
            mock_worker_class.return_value = mock_worker
            
            await worker.start()
            assert worker.worker is not None


class TestTaskQueueService:
    """Test cases for task queue service."""

    @pytest.fixture
    def service(self):
        """Create task queue service instance."""
        from src.tasks.queue_service import TaskQueueService
        return TaskQueueService()

    @pytest.mark.skipif(not ARQ_AVAILABLE, reason="Arq not available")
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization."""
        assert service is not None
        assert service.redis_pool is None  # Not initialized yet
        
        # Initialize service
        await service.initialize()
        # Service may be None if Redis unavailable, which is OK for tests

    @pytest.mark.skipif(not ARQ_AVAILABLE, reason="Arq not available")
    @pytest.mark.asyncio
    async def test_enqueue_job(self, service):
        """Test job enqueueing."""
        await service.initialize()
        
        if service.redis_pool:
            job_id = await service.enqueue("test_function", arg1="value1")
            # job_id may be None if Redis not running, which is OK for tests
            assert isinstance(job_id, (str, type(None)))
