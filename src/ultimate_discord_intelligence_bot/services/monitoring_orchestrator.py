from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, TypedDict

from ultimate_discord_intelligence_bot.profiles.creator_network_schema import (
    ALL_CREATOR_NETWORKS,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


class MonitoringSchedule(TypedDict, total=False):
    """Configuration for platform monitoring schedules."""

    platform: str
    interval_minutes: int
    priority: int  # 1=highest, 5=lowest
    enabled: bool
    last_run: float
    next_run: float
    creators: list[str]


class MonitoringResult(TypedDict, total=False):
    """Result of monitoring operation."""

    platform: str
    timestamp: float
    creators_checked: int
    new_content_found: int
    content_processed: int
    errors: list[str]
    processing_time_seconds: float
    next_check: float


class RealTimeMonitoringOrchestrator:
    """Orchestrates real-time monitoring across all platforms with intelligent scheduling."""

    def __init__(self) -> None:
        self._schedules: dict[str, MonitoringSchedule] = {}
        self._monitoring_tasks: dict[str, asyncio.Task] = {}
        self._running = False
        self._monitoring_stats: dict[str, Any] = {}

        # Initialize platform schedules
        self._initialize_platform_schedules()

    def _initialize_platform_schedules(self) -> None:
        """Initialize monitoring schedules for all platforms."""
        current_time = time.time()

        # Platform-specific intervals based on content velocity and importance
        platform_configs = {
            "youtube": {
                "interval_minutes": 5,
                "priority": 1,
            },  # High priority, frequent checks
            "twitch": {
                "interval_minutes": 2,
                "priority": 1,
            },  # Live content, very frequent
            "tiktok": {
                "interval_minutes": 10,
                "priority": 2,
            },  # High velocity, frequent
            "instagram": {
                "interval_minutes": 15,
                "priority": 2,
            },  # Stories expire, regular checks
            "twitter": {
                "interval_minutes": 5,
                "priority": 1,
            },  # High velocity, frequent
            "reddit": {
                "interval_minutes": 30,
                "priority": 3,
            },  # Lower velocity, less frequent
            "discord": {
                "interval_minutes": 2,
                "priority": 1,
            },  # Real-time chat, very frequent
        }

        for platform, config in platform_configs.items():
            self._schedules[platform] = MonitoringSchedule(
                platform=platform,
                interval_minutes=config["interval_minutes"],
                priority=config["priority"],
                enabled=True,
                last_run=0,
                next_run=current_time + (config["interval_minutes"] * 60),
                creators=self._get_creators_for_platform(platform),
            )

    def _get_creators_for_platform(self, platform: str) -> List[str]:
        """Get list of creators to monitor for a specific platform."""
        creators = []

        for creator_id, config in ALL_CREATOR_NETWORKS.items():
            platforms = config.get("platforms", [])
            if platform in platforms:
                creators.append(creator_id)

        return creators

    async def start_monitoring(
        self, tenant: str = "default", workspace: str = "default"
    ) -> StepResult:
        """Start the real-time monitoring orchestrator."""
        try:
            if self._running:
                return StepResult.fail("Monitoring orchestrator is already running")

            self._running = True
            self._monitoring_stats = {
                "start_time": time.time(),
                "total_checks": 0,
                "total_content_found": 0,
                "total_errors": 0,
                "platform_stats": {},
            }

            # Start monitoring tasks for each platform
            for platform, schedule in self._schedules.items():
                if schedule["enabled"]:
                    task = asyncio.create_task(
                        self._monitor_platform(platform, schedule, tenant, workspace)
                    )
                    self._monitoring_tasks[platform] = task

            return StepResult.ok(
                data={
                    "status": "monitoring_started",
                    "platforms": list(self._schedules.keys()),
                    "total_creators": sum(
                        len(s["creators"]) for s in self._schedules.values()
                    ),
                }
            )

        except Exception as e:
            return StepResult.fail(f"Failed to start monitoring: {str(e)}")

    async def stop_monitoring(self) -> StepResult:
        """Stop the real-time monitoring orchestrator."""
        try:
            if not self._running:
                return StepResult.fail("Monitoring orchestrator is not running")

            self._running = False

            # Cancel all monitoring tasks
            for task in self._monitoring_tasks.values():
                task.cancel()

            # Wait for tasks to complete
            await asyncio.gather(
                *self._monitoring_tasks.values(), return_exceptions=True
            )

            self._monitoring_tasks.clear()

            return StepResult.ok(data={"status": "monitoring_stopped"})

        except Exception as e:
            return StepResult.fail(f"Failed to stop monitoring: {str(e)}")

    async def _monitor_platform(
        self, platform: str, schedule: MonitoringSchedule, tenant: str, workspace: str
    ) -> None:
        """Monitor a specific platform according to its schedule."""
        try:
            while self._running:
                current_time = time.time()

                # Check if it's time to run
                if current_time >= schedule["next_run"]:
                    # Update schedule
                    schedule["last_run"] = current_time
                    schedule["next_run"] = current_time + (
                        schedule["interval_minutes"] * 60
                    )

                    # Perform monitoring
                    result = await self._check_platform_content(
                        platform, schedule, tenant, workspace
                    )

                    # Update statistics
                    self._update_monitoring_stats(platform, result)

                    # Update schedule
                    self._schedules[platform] = schedule

                # Wait before next check (minimum 10 seconds)
                await asyncio.sleep(10)

        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
        except Exception as e:
            print(f"Error monitoring {platform}: {e}")

    async def _check_platform_content(
        self, platform: str, schedule: MonitoringSchedule, tenant: str, workspace: str
    ) -> MonitoringResult:
        """Check for new content on a specific platform."""
        start_time = time.time()
        errors: list[str] = []
        new_content_found = 0
        content_processed = 0

        try:
            # Mock implementation - in real system, would use platform-specific tools
            for creator_id in schedule["creators"]:
                try:
                    # Simulate content check
                    content_count = await self._check_creator_content(
                        creator_id, platform, tenant, workspace
                    )
                    new_content_found += content_count

                    if content_count > 0:
                        # Process new content
                        processed = await self._process_new_content(
                            creator_id, platform, content_count, tenant, workspace
                        )
                        content_processed += processed

                except Exception as e:
                    errors.append(
                        f"Error checking {creator_id} on {platform}: {str(e)}"
                    )

        except Exception as e:
            errors.append(f"Platform monitoring error: {str(e)}")

        return MonitoringResult(
            platform=platform,
            timestamp=time.time(),
            creators_checked=len(schedule["creators"]),
            new_content_found=new_content_found,
            content_processed=content_processed,
            errors=errors,
            processing_time_seconds=time.time() - start_time,
            next_check=schedule["next_run"],
        )

    async def _check_creator_content(
        self, creator_id: str, platform: str, tenant: str, workspace: str
    ) -> int:
        """Check for new content from a specific creator on a platform."""
        try:
            # Mock implementation - in real system, would use platform-specific APIs
            import random

            # Simulate finding new content (0-3 pieces per check)
            content_count = random.randint(0, 3)
            return content_count

        except Exception:
            return 0

    async def _process_new_content(
        self,
        creator_id: str,
        platform: str,
        content_count: int,
        tenant: str,
        workspace: str,
    ) -> int:
        """Process newly found content."""
        try:
            # Mock implementation - in real system, would:
            # 1. Download content using platform-specific tools
            # 2. Analyze content using multimodal tools
            # 3. Store in memory system
            # 4. Trigger relevant agents for analysis

            processed_count = 0
            for i in range(content_count):
                # Simulate processing
                await asyncio.sleep(0.1)  # Simulate processing time
                processed_count += 1

            return processed_count

        except Exception:
            return 0

    def _update_monitoring_stats(self, platform: str, result: MonitoringResult) -> None:
        """Update monitoring statistics."""
        if platform not in self._monitoring_stats["platform_stats"]:
            self._monitoring_stats["platform_stats"][platform] = {
                "total_checks": 0,
                "total_content_found": 0,
                "total_errors": 0,
                "last_check": 0,
            }

        stats = self._monitoring_stats["platform_stats"][platform]
        stats["total_checks"] += 1
        stats["total_content_found"] += result["new_content_found"]
        stats["total_errors"] += len(result["errors"])
        stats["last_check"] = result["timestamp"]

        # Update global stats
        self._monitoring_stats["total_checks"] += 1
        self._monitoring_stats["total_content_found"] += result["new_content_found"]
        self._monitoring_stats["total_errors"] += len(result["errors"])

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status and statistics."""
        return {
            "running": self._running,
            "start_time": self._monitoring_stats.get("start_time", 0),
            "uptime_seconds": time.time()
            - self._monitoring_stats.get("start_time", time.time()),
            "total_checks": self._monitoring_stats.get("total_checks", 0),
            "total_content_found": self._monitoring_stats.get("total_content_found", 0),
            "total_errors": self._monitoring_stats.get("total_errors", 0),
            "platform_schedules": {
                platform: {
                    "enabled": schedule["enabled"],
                    "interval_minutes": schedule["interval_minutes"],
                    "priority": schedule["priority"],
                    "next_run": schedule["next_run"],
                    "creators_count": len(schedule["creators"]),
                }
                for platform, schedule in self._schedules.items()
            },
            "platform_stats": self._monitoring_stats.get("platform_stats", {}),
        }

    def update_schedule(
        self,
        platform: str,
        interval_minutes: int | None = None,
        enabled: bool | None = None,
    ) -> StepResult:
        """Update monitoring schedule for a platform."""
        try:
            if platform not in self._schedules:
                return StepResult.fail(f"Platform {platform} not found")

            schedule = self._schedules[platform]

            if interval_minutes is not None:
                schedule["interval_minutes"] = interval_minutes
                # Recalculate next run time
                schedule["next_run"] = schedule["last_run"] + (interval_minutes * 60)

            if enabled is not None:
                schedule["enabled"] = enabled

            self._schedules[platform] = schedule

            return StepResult.ok(
                data={"platform": platform, "updated_schedule": schedule}
            )

        except Exception as e:
            return StepResult.fail(f"Failed to update schedule: {str(e)}")

    def add_creator_to_platform(self, platform: str, creator_id: str) -> StepResult:
        """Add a creator to a platform's monitoring list."""
        try:
            if platform not in self._schedules:
                return StepResult.fail(f"Platform {platform} not found")

            schedule = self._schedules[platform]
            if creator_id not in schedule["creators"]:
                schedule["creators"].append(creator_id)
                self._schedules[platform] = schedule

            return StepResult.ok(
                data={"platform": platform, "creator_added": creator_id}
            )

        except Exception as e:
            return StepResult.fail(f"Failed to add creator: {str(e)}")

    def remove_creator_from_platform(
        self, platform: str, creator_id: str
    ) -> StepResult:
        """Remove a creator from a platform's monitoring list."""
        try:
            if platform not in self._schedules:
                return StepResult.fail(f"Platform {platform} not found")

            schedule = self._schedules[platform]
            if creator_id in schedule["creators"]:
                schedule["creators"].remove(creator_id)
                self._schedules[platform] = schedule

            return StepResult.ok(
                data={"platform": platform, "creator_removed": creator_id}
            )

        except Exception as e:
            return StepResult.fail(f"Failed to remove creator: {str(e)}")

    def get_next_checks(self) -> List[Dict[str, Any]]:
        """Get list of upcoming monitoring checks."""
        upcoming = []
        current_time = time.time()

        for platform, schedule in self._schedules.items():
            if schedule["enabled"]:
                time_until_next = schedule["next_run"] - current_time
                upcoming.append(
                    {
                        "platform": platform,
                        "next_run": schedule["next_run"],
                        "time_until_seconds": max(0, time_until_next),
                        "interval_minutes": schedule["interval_minutes"],
                        "creators_count": len(schedule["creators"]),
                    }
                )

        # Sort by next run time
        upcoming.sort(key=lambda x: x["next_run"])
        return upcoming
