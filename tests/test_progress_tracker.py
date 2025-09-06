from datetime import UTC, datetime, timedelta

from scripts.progress_tracker import calculate_velocity, estimate_completion_date


class TestVelocityCalculation:
    def test_calculate_velocity_no_tasks(self):
        """Test velocity calculation with no completed tasks."""
        assert calculate_velocity([]) == 0.0

    def test_calculate_velocity_recent_tasks(self):
        """Test velocity calculation with recent completed tasks."""
        now = datetime.now(UTC)
        completed_tasks = [
            {'completed_at': (now - timedelta(days=5)).isoformat(), 'id': 1},
            {'completed_at': (now - timedelta(days=10)).isoformat(), 'id': 2},
            {'completed_at': (now - timedelta(days=15)).isoformat(), 'id': 3},
        ]

        velocity = calculate_velocity(completed_tasks, time_window_days=30)
        assert velocity == 3 / 30  # 3 tasks in 30 days

    def test_calculate_velocity_old_tasks_excluded(self):
        """Test that old tasks outside the window are excluded."""
        now = datetime.now(UTC)
        completed_tasks = [
            {'completed_at': (now - timedelta(days=5)).isoformat(), 'id': 1},
            {'completed_at': (now - timedelta(days=45)).isoformat(), 'id': 2},  # Outside window
        ]

        velocity = calculate_velocity(completed_tasks, time_window_days=30)
        assert velocity == 1 / 30  # Only 1 task in window


class TestCompletionEstimation:
    def test_estimate_completion_date_valid(self):
        """Test completion date estimation with valid inputs."""
        velocity = 1.0  # 1 task per day
        remaining = 10

        estimated = estimate_completion_date(remaining, velocity, buffer_factor=1.0)
        assert estimated is not None

        expected = datetime.now(UTC) + timedelta(days=10)
        # Allow 1 minute tolerance for test execution time
        assert abs((estimated - expected).total_seconds()) < 60

    def test_estimate_completion_date_with_buffer(self):
        """Test that buffer factor increases estimated time."""
        velocity = 1.0
        remaining = 10

        estimated_no_buffer = estimate_completion_date(remaining, velocity, buffer_factor=1.0)
        estimated_with_buffer = estimate_completion_date(remaining, velocity, buffer_factor=2.0)

        assert estimated_with_buffer > estimated_no_buffer

    def test_estimate_completion_date_zero_velocity(self):
        """Test that zero velocity returns None."""
        assert estimate_completion_date(10, 0.0) is None

    def test_estimate_completion_date_no_remaining(self):
        """Test that no remaining tasks returns None."""
        assert estimate_completion_date(0, 1.0) is None
