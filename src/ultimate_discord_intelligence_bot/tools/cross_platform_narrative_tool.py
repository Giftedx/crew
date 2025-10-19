from __future__ import annotations

import time
from typing import Any, TypedDict

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class NarrativeEvent(TypedDict, total=False):
    """Individual event in a narrative timeline."""

    event_id: str
    narrative_id: str
    creator_id: str
    platform: str
    content_id: str
    content_type: str  # "video", "audio", "image", "text", "stream"
    event_type: str  # "statement", "response", "reaction", "clarification", "escalation"
    timestamp: float
    content_summary: str
    sentiment: float
    engagement_metrics: dict[str, Any]
    related_events: list[str]
    narrative_position: int  # Position in the narrative timeline


class NarrativeTimeline(TypedDict, total=False):
    """Complete narrative timeline across platforms."""

    narrative_id: str
    title: str
    description: str
    involved_creators: list[str]
    primary_topic: str
    start_date: float
    last_update: float
    status: str  # "active", "resolved", "dormant"
    platforms: list[str]
    total_events: int
    events: list[NarrativeEvent]
    narrative_arc: dict[str, Any]
    cross_platform_analysis: dict[str, Any]
    viral_moments: list[str]
    resolution_status: str | None


class CrossPlatformNarrativeResult(TypedDict, total=False):
    """Result of cross-platform narrative tracking."""

    timestamp: float
    narrative_id: str
    timeline_found: bool
    narrative_timeline: NarrativeTimeline | None
    narrative_analysis: dict[str, Any]
    cross_platform_insights: dict[str, Any]
    viral_propagation_analysis: dict[str, Any]
    creator_impact_analysis: dict[str, Any]
    next_events_prediction: list[str]
    processing_time_seconds: float
    errors: list[str]


class CrossPlatformNarrativeTrackingTool(BaseTool[StepResult]):
    """Track stories and narratives across creators and time."""

    name: str = "Cross-Platform Narrative Tracking"
    description: str = (
        "Track narratives and stories across creators, platforms, and time. "
        "Build comprehensive timelines, analyze cross-platform propagation, "
        "and predict narrative developments"
    )

    def __init__(self) -> None:
        super().__init__()
        self._active_narratives: dict[str, NarrativeTimeline] = {}
        self._narrative_events: dict[str, list[NarrativeEvent]] = {}
        self._cross_platform_mappings: dict[str, list[str]] = {}

    def _run(self, narrative_query: str, analysis_depth: str, tenant: str, workspace: str) -> StepResult:
        """
        Track cross-platform narrative based on query.

        Args:
            narrative_query: Query to identify the narrative (e.g., "H3 vs Triller lawsuit", "Hasan political drama")
            analysis_depth: Depth of analysis ("basic", "comprehensive", "deep")
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with narrative tracking data
        """
        try:
            if not narrative_query or not analysis_depth:
                return StepResult.fail("Narrative query and analysis depth are required")

            if analysis_depth not in ["basic", "comprehensive", "deep"]:
                return StepResult.fail("Analysis depth must be 'basic', 'comprehensive', or 'deep'")

            start_time = time.time()

            # Identify or create narrative
            narrative_id = self._identify_narrative(narrative_query, tenant, workspace)

            # Build or update timeline
            narrative_timeline = self._build_narrative_timeline(
                narrative_id, narrative_query, analysis_depth, tenant, workspace
            )

            if not narrative_timeline:
                result = CrossPlatformNarrativeResult(
                    timestamp=time.time(),
                    narrative_id=narrative_id,
                    timeline_found=False,
                    narrative_timeline=None,
                    narrative_analysis={},
                    cross_platform_insights={},
                    viral_propagation_analysis={},
                    creator_impact_analysis={},
                    next_events_prediction=[],
                    processing_time_seconds=time.time() - start_time,
                    errors=["Could not build narrative timeline"],
                )
                return StepResult.ok(data=result)

            # Perform narrative analysis
            narrative_analysis = self._analyze_narrative_structure(
                narrative_timeline, analysis_depth, tenant, workspace
            )

            # Analyze cross-platform insights
            cross_platform_insights = self._analyze_cross_platform_patterns(
                narrative_timeline, analysis_depth, tenant, workspace
            )

            # Analyze viral propagation
            viral_propagation_analysis = self._analyze_viral_propagation(
                narrative_timeline, analysis_depth, tenant, workspace
            )

            # Analyze creator impact
            creator_impact_analysis = self._analyze_creator_impact(
                narrative_timeline, analysis_depth, tenant, workspace
            )

            # Predict next events
            next_events_prediction = self._predict_next_events(
                narrative_timeline, analysis_depth, tenant, workspace
            )

            result = CrossPlatformNarrativeResult(
                timestamp=time.time(),
                narrative_id=narrative_id,
                timeline_found=True,
                narrative_timeline=narrative_timeline,
                narrative_analysis=narrative_analysis,
                cross_platform_insights=cross_platform_insights,
                viral_propagation_analysis=viral_propagation_analysis,
                creator_impact_analysis=creator_impact_analysis,
                next_events_prediction=next_events_prediction,
                processing_time_seconds=time.time() - start_time,
                errors=[],
            )

            return StepResult.ok(data=result)

        except Exception as e:
            return StepResult.fail(f"Cross-platform narrative tracking failed: {str(e)}")

    def _identify_narrative(self, narrative_query: str, tenant: str, workspace: str) -> str:
        """Identify or create narrative ID from query."""
        try:
            # Simple hash-based ID generation
            import hashlib
            narrative_id = f"narrative_{hashlib.md5(narrative_query.encode()).hexdigest()[:12]}"

            # Check if narrative already exists
            if narrative_id in self._active_narratives:
                return narrative_id

            return narrative_id

        except Exception:
            return f"narrative_{int(time.time())}"

    def _build_narrative_timeline(
        self, narrative_id: str, narrative_query: str, analysis_depth: str, tenant: str, workspace: str
    ) -> NarrativeTimeline | None:
        """Build comprehensive narrative timeline."""
        try:
            # Check if timeline already exists
            if narrative_id in self._active_narratives:
                timeline = self._active_narratives[narrative_id]
                # Update with new events
                self._update_timeline_events(timeline, analysis_depth, tenant, workspace)
                return timeline

            # Create new timeline
            timeline = self._create_new_timeline(narrative_id, narrative_query, analysis_depth, tenant, workspace)

            if timeline:
                self._active_narratives[narrative_id] = timeline

            return timeline

        except Exception as e:
            print(f"Error building narrative timeline: {e}")
            return None

    def _create_new_timeline(
        self, narrative_id: str, narrative_query: str, analysis_depth: str, tenant: str, workspace: str
    ) -> NarrativeTimeline | None:
        """Create new narrative timeline."""
        try:
            # Mock implementation - in real system, would search content databases
            current_time = time.time()

            # Generate mock events based on query
            events = self._generate_mock_narrative_events(narrative_query, analysis_depth, tenant, workspace)

            if not events:
                return None

            # Create timeline
            timeline = NarrativeTimeline(
                narrative_id=narrative_id,
                title=f"Narrative: {narrative_query}",
                description=f"Timeline tracking the narrative: {narrative_query}",
                involved_creators=list(set(event["creator_id"] for event in events)),
                primary_topic=self._extract_primary_topic(narrative_query),
                start_date=min(event["timestamp"] for event in events),
                last_update=current_time,
                status="active",
                platforms=list(set(event["platform"] for event in events)),
                total_events=len(events),
                events=events,
                narrative_arc={},
                cross_platform_analysis={},
                viral_moments=[],
                resolution_status=None,
            )

            return timeline

        except Exception as e:
            print(f"Error creating new timeline: {e}")
            return None

    def _generate_mock_narrative_events(
        self, narrative_query: str, analysis_depth: str, tenant: str, workspace: str
    ) -> list[NarrativeEvent]:
        """Generate mock narrative events based on query."""
        try:
            events: list[NarrativeEvent] = []
            current_time = time.time()

            # Mock events based on query content
            if "h3" in narrative_query.lower() or "ethan" in narrative_query.lower():
                events = [
                    NarrativeEvent(
                        event_id="event_1",
                        narrative_id="narrative_1",
                        creator_id="ethan_klein",
                        platform="youtube",
                        content_id="h3_initial_statement",
                        content_type="video",
                        event_type="statement",
                        timestamp=current_time - (7 * 24 * 3600),  # 7 days ago
                        content_summary="Initial statement about the controversy",
                        sentiment=0.3,
                        engagement_metrics={"views": 500000, "likes": 25000, "comments": 1500},
                        related_events=[],
                        narrative_position=1,
                    ),
                    NarrativeEvent(
                        event_id="event_2",
                        narrative_id="narrative_1",
                        creator_id="hasan_piker",
                        platform="twitch",
                        content_id="hasan_response",
                        content_type="stream",
                        event_type="response",
                        timestamp=current_time - (6 * 24 * 3600),  # 6 days ago
                        content_summary="Response to Ethan's statement",
                        sentiment=-0.2,
                        engagement_metrics={"views": 200000, "likes": 12000, "comments": 800},
                        related_events=["event_1"],
                        narrative_position=2,
                    ),
                    NarrativeEvent(
                        event_id="event_3",
                        narrative_id="narrative_1",
                        creator_id="ethan_klein",
                        platform="youtube",
                        content_id="h3_clarification",
                        content_type="video",
                        event_type="clarification",
                        timestamp=current_time - (5 * 24 * 3600),  # 5 days ago
                        content_summary="Clarification and additional context",
                        sentiment=0.5,
                        engagement_metrics={"views": 300000, "likes": 18000, "comments": 1200},
                        related_events=["event_1", "event_2"],
                        narrative_position=3,
                    ),
                ]

            elif "hasan" in narrative_query.lower():
                events = [
                    NarrativeEvent(
                        event_id="event_4",
                        narrative_id="narrative_2",
                        creator_id="hasan_piker",
                        platform="twitch",
                        content_id="hasan_political_take",
                        content_type="stream",
                        event_type="statement",
                        timestamp=current_time - (3 * 24 * 3600),  # 3 days ago
                        content_summary="Political commentary on current events",
                        sentiment=0.1,
                        engagement_metrics={"views": 300000, "likes": 20000, "comments": 2000},
                        related_events=[],
                        narrative_position=1,
                    ),
                    NarrativeEvent(
                        event_id="event_5",
                        narrative_id="narrative_2",
                        creator_id="will_neff",
                        platform="youtube",
                        content_id="will_reaction",
                        content_type="video",
                        event_type="reaction",
                        timestamp=current_time - (2 * 24 * 3600),  # 2 days ago
                        content_summary="Reaction to Hasan's political take",
                        sentiment=0.4,
                        engagement_metrics={"views": 150000, "likes": 8000, "comments": 600},
                        related_events=["event_4"],
                        narrative_position=2,
                    ),
                ]

            else:
                # Generic narrative events
                events = [
                    NarrativeEvent(
                        event_id="event_generic_1",
                        narrative_id="narrative_generic",
                        creator_id="generic_creator",
                        platform="youtube",
                        content_id="generic_content_1",
                        content_type="video",
                        event_type="statement",
                        timestamp=current_time - (24 * 3600),  # 1 day ago
                        content_summary="Generic narrative event",
                        sentiment=0.0,
                        engagement_metrics={"views": 100000, "likes": 5000, "comments": 300},
                        related_events=[],
                        narrative_position=1,
                    ),
                ]

            return events

        except Exception as e:
            print(f"Error generating mock narrative events: {e}")
            return []

    def _extract_primary_topic(self, narrative_query: str) -> str:
        """Extract primary topic from narrative query."""
        try:
            # Simple topic extraction
            query_lower = narrative_query.lower()

            if any(word in query_lower for word in ["politics", "political", "election"]):
                return "Politics"
            elif any(word in query_lower for word in ["gaming", "game", "stream"]):
                return "Gaming"
            elif any(word in query_lower for word in ["drama", "controversy", "feud"]):
                return "Drama"
            elif any(word in query_lower for word in ["lawsuit", "legal", "court"]):
                return "Legal"
            else:
                return "General"

        except Exception:
            return "Unknown"

    def _update_timeline_events(
        self, timeline: NarrativeTimeline, analysis_depth: str, tenant: str, workspace: str
    ) -> None:
        """Update timeline with new events."""
        try:
            # Mock implementation - in real system, would search for new events
            current_time = time.time()

            # Check for new events (mock)
            new_events = self._search_for_new_events(
                timeline, analysis_depth, tenant, workspace
            )

            if new_events:
                timeline["events"].extend(new_events)
                timeline["total_events"] = len(timeline["events"])
                timeline["last_update"] = current_time

                # Update involved creators and platforms
                timeline["involved_creators"] = list(set(
                    event["creator_id"] for event in timeline["events"]
                ))
                timeline["platforms"] = list(set(
                    event["platform"] for event in timeline["events"]
                ))

        except Exception as e:
            print(f"Error updating timeline events: {e}")

    def _search_for_new_events(
        self, timeline: NarrativeTimeline, analysis_depth: str, tenant: str, workspace: str
    ) -> list[NarrativeEvent]:
        """Search for new events related to the narrative."""
        try:
            # Mock implementation - in real system, would search content databases
            new_events: list[NarrativeEvent] = []
            current_time = time.time()

            # Simulate finding new events occasionally
            import random
            if random.random() < 0.3:  # 30% chance of new event
                new_event = NarrativeEvent(
                    event_id=f"event_new_{int(current_time)}",
                    narrative_id=timeline["narrative_id"],
                    creator_id=random.choice(timeline["involved_creators"]),
                    platform=random.choice(timeline["platforms"]),
                    content_id=f"new_content_{int(current_time)}",
                    content_type="video",
                    event_type="update",
                    timestamp=current_time - (2 * 3600),  # 2 hours ago
                    content_summary="New development in the narrative",
                    sentiment=random.uniform(-0.5, 0.5),
                    engagement_metrics={
                        "views": random.randint(10000, 100000),
                        "likes": random.randint(500, 5000),
                        "comments": random.randint(50, 500),
                    },
                    related_events=[timeline["events"][-1]["event_id"]] if timeline["events"] else [],
                    narrative_position=timeline["total_events"] + 1,
                )
                new_events.append(new_event)

            return new_events

        except Exception as e:
            print(f"Error searching for new events: {e}")
            return []

    def _analyze_narrative_structure(
        self, timeline: NarrativeTimeline, analysis_depth: str, tenant: str, workspace: str
    ) -> dict[str, Any]:
        """Analyze narrative structure and arc."""
        try:
            analysis = {
                "narrative_length_days": (timeline["last_update"] - timeline["start_date"]) / (24 * 3600),
                "total_events": timeline["total_events"],
                "creators_involved": len(timeline["involved_creators"]),
                "platforms_used": len(timeline["platforms"]),
                "event_types": {},
                "sentiment_progression": [],
                "engagement_trends": [],
                "narrative_phases": [],
                "key_moments": [],
            }

            # Analyze event types
            for event in timeline["events"]:
                event_type = event["event_type"]
                analysis["event_types"][event_type] = analysis["event_types"].get(event_type, 0) + 1

            # Analyze sentiment progression
            for event in sorted(timeline["events"], key=lambda x: x["timestamp"]):
                analysis["sentiment_progression"].append({
                    "timestamp": event["timestamp"],
                    "sentiment": event["sentiment"],
                    "creator": event["creator_id"],
                })

            # Analyze engagement trends
            for event in sorted(timeline["events"], key=lambda x: x["timestamp"]):
                analysis["engagement_trends"].append({
                    "timestamp": event["timestamp"],
                    "engagement_rate": event["engagement_metrics"].get("engagement_rate", 0),
                    "views": event["engagement_metrics"].get("views", 0),
                })

            # Identify narrative phases
            analysis["narrative_phases"] = self._identify_narrative_phases(timeline["events"])

            # Identify key moments
            analysis["key_moments"] = self._identify_key_moments(timeline["events"])

            return analysis

        except Exception as e:
            print(f"Error analyzing narrative structure: {e}")
            return {}

    def _identify_narrative_phases(self, events: list[NarrativeEvent]) -> list[dict[str, Any]]:
        """Identify different phases in the narrative."""
        try:
            phases = []
            sorted_events = sorted(events, key=lambda x: x["timestamp"])

            if len(sorted_events) >= 3:
                # Initial phase
                phases.append({
                    "phase": "initial",
                    "start_event": sorted_events[0]["event_id"],
                    "end_event": sorted_events[1]["event_id"],
                    "description": "Initial statements and setup",
                })

                # Development phase
                if len(sorted_events) >= 4:
                    phases.append({
                        "phase": "development",
                        "start_event": sorted_events[2]["event_id"],
                        "end_event": sorted_events[-2]["event_id"],
                        "description": "Development and back-and-forth",
                    })

                # Resolution phase
                phases.append({
                    "phase": "resolution",
                    "start_event": sorted_events[-1]["event_id"],
                    "end_event": sorted_events[-1]["event_id"],
                    "description": "Resolution or current status",
                })

            return phases

        except Exception:
            return []

    def _identify_key_moments(self, events: list[NarrativeEvent]) -> list[dict[str, Any]]:
        """Identify key moments in the narrative."""
        try:
            key_moments = []

            # Find events with high engagement
            for event in events:
                views = event["engagement_metrics"].get("views", 0)
                if views > 200000:  # High view threshold
                    key_moments.append({
                        "event_id": event["event_id"],
                        "reason": "high_engagement",
                        "views": views,
                        "creator": event["creator_id"],
                        "platform": event["platform"],
                    })

            # Find events with extreme sentiment
            for event in events:
                sentiment = event["sentiment"]
                if abs(sentiment) > 0.6:  # High sentiment threshold
                    key_moments.append({
                        "event_id": event["event_id"],
                        "reason": "extreme_sentiment",
                        "sentiment": sentiment,
                        "creator": event["creator_id"],
                        "platform": event["platform"],
                    })

            return key_moments

        except Exception:
            return []

    def _analyze_cross_platform_patterns(
        self, timeline: NarrativeTimeline, analysis_depth: str, tenant: str, workspace: str
    ) -> dict[str, Any]:
        """Analyze cross-platform propagation patterns."""
        try:
            analysis = {
                "platform_sequence": [],
                "platform_engagement": {},
                "cross_platform_amplification": {},
                "platform_specific_patterns": {},
                "migration_patterns": [],
            }

            # Analyze platform sequence
            for event in sorted(timeline["events"], key=lambda x: x["timestamp"]):
                analysis["platform_sequence"].append({
                    "timestamp": event["timestamp"],
                    "platform": event["platform"],
                    "creator": event["creator_id"],
                    "event_type": event["event_type"],
                })

            # Analyze platform engagement
            for event in timeline["events"]:
                platform = event["platform"]
                if platform not in analysis["platform_engagement"]:
                    analysis["platform_engagement"][platform] = {
                        "total_events": 0,
                        "total_views": 0,
                        "total_engagement": 0,
                    }

                analysis["platform_engagement"][platform]["total_events"] += 1
                analysis["platform_engagement"][platform]["total_views"] += event["engagement_metrics"].get("views", 0)
                analysis["platform_engagement"][platform]["total_engagement"] += (
                    event["engagement_metrics"].get("likes", 0) +
                    event["engagement_metrics"].get("comments", 0) +
                    event["engagement_metrics"].get("shares", 0)
                )

            # Analyze cross-platform amplification
            for i, event in enumerate(timeline["events"]):
                if i > 0:
                    prev_event = timeline["events"][i - 1]
                    if event["platform"] != prev_event["platform"]:
                        # Cross-platform event
                        amplification = event["engagement_metrics"].get("views", 0) / max(
                            prev_event["engagement_metrics"].get("views", 1), 1
                        )
                        analysis["cross_platform_amplification"][event["event_id"]] = {
                            "from_platform": prev_event["platform"],
                            "to_platform": event["platform"],
                            "amplification_factor": amplification,
                        }

            return analysis

        except Exception as e:
            print(f"Error analyzing cross-platform patterns: {e}")
            return {}

    def _analyze_viral_propagation(
        self, timeline: NarrativeTimeline, analysis_depth: str, tenant: str, workspace: str
    ) -> dict[str, Any]:
        """Analyze viral propagation patterns."""
        try:
            analysis = {
                "viral_moments": [],
                "propagation_velocity": {},
                "reach_expansion": [],
                "viral_indicators": {},
            }

            # Identify viral moments
            for event in timeline["events"]:
                views = event["engagement_metrics"].get("views", 0)
                if views > 300000:  # Viral threshold
                    analysis["viral_moments"].append({
                        "event_id": event["event_id"],
                        "views": views,
                        "creator": event["creator_id"],
                        "platform": event["platform"],
                        "viral_score": min(views / 1000000, 1.0),
                    })

            # Analyze propagation velocity
            sorted_events = sorted(timeline["events"], key=lambda x: x["timestamp"])
            for i in range(1, len(sorted_events)):
                prev_event = sorted_events[i - 1]
                current_event = sorted_events[i]

                time_diff = current_event["timestamp"] - prev_event["timestamp"]
                views_diff = current_event["engagement_metrics"].get("views", 0) - prev_event["engagement_metrics"].get("views", 0)

                if time_diff > 0:
                    velocity = views_diff / (time_diff / 3600)  # Views per hour
                    analysis["propagation_velocity"][current_event["event_id"]] = velocity

            return analysis

        except Exception as e:
            print(f"Error analyzing viral propagation: {e}")
            return {}

    def _analyze_creator_impact(
        self, timeline: NarrativeTimeline, analysis_depth: str, tenant: str, workspace: str
    ) -> dict[str, Any]:
        """Analyze creator impact in the narrative."""
        try:
            analysis = {
                "creator_contributions": {},
                "creator_influence": {},
                "creator_sentiment_impact": {},
                "creator_engagement_impact": {},
            }

            # Analyze creator contributions
            for event in timeline["events"]:
                creator = event["creator_id"]
                if creator not in analysis["creator_contributions"]:
                    analysis["creator_contributions"][creator] = {
                        "total_events": 0,
                        "total_views": 0,
                        "event_types": {},
                    }

                analysis["creator_contributions"][creator]["total_events"] += 1
                analysis["creator_contributions"][creator]["total_views"] += event["engagement_metrics"].get("views", 0)

                event_type = event["event_type"]
                analysis["creator_contributions"][creator]["event_types"][event_type] = (
                    analysis["creator_contributions"][creator]["event_types"].get(event_type, 0) + 1
                )

            # Analyze creator influence
            for creator, contributions in analysis["creator_contributions"].items():
                total_views = contributions["total_views"]
                total_views_all = sum(
                    event["engagement_metrics"].get("views", 0) for event in timeline["events"]
                )

                influence_score = total_views / max(total_views_all, 1)
                analysis["creator_influence"][creator] = influence_score

            return analysis

        except Exception as e:
            print(f"Error analyzing creator impact: {e}")
            return {}

    def _predict_next_events(
        self, timeline: NarrativeTimeline, analysis_depth: str, tenant: str, workspace: str
    ) -> list[str]:
        """Predict likely next events in the narrative."""
        try:
            predictions = []

            # Simple prediction logic based on patterns
            last_event = timeline["events"][-1] if timeline["events"] else None

            if last_event:
                # Predict based on event type
                if last_event["event_type"] == "statement":
                    predictions.append("Likely response from other involved creators")
                    predictions.append("Potential escalation or clarification")

                elif last_event["event_type"] == "response":
                    predictions.append("Possible counter-response")
                    predictions.append("Potential de-escalation or resolution")

                elif last_event["event_type"] == "escalation":
                    predictions.append("High probability of continued conflict")
                    predictions.append("Potential for third-party involvement")

                # Predict based on sentiment
                if last_event["sentiment"] < -0.5:
                    predictions.append("Negative sentiment likely to continue")
                elif last_event["sentiment"] > 0.5:
                    predictions.append("Positive resolution may be possible")

                # Predict based on engagement
                high_engagement = last_event["engagement_metrics"].get("views", 0) > 200000
                if high_engagement:
                    predictions.append("High engagement suggests continued interest")
                    predictions.append("Potential for viral expansion")

            # General predictions
            predictions.extend([
                "Monitor for new content from involved creators",
                "Watch for cross-platform propagation",
                "Look for community reactions and responses",
            ])

            return predictions

        except Exception as e:
            print(f"Error predicting next events: {e}")
            return []

    def get_active_narratives(self) -> dict[str, NarrativeTimeline]:
        """Get all active narratives."""
        return self._active_narratives.copy()

    def get_narrative_events(self, narrative_id: str) -> list[NarrativeEvent]:
        """Get events for a specific narrative."""
        return self._narrative_events.get(narrative_id, [])

    def add_narrative_event(
        self, narrative_id: str, event: NarrativeEvent, tenant: str = "default", workspace: str = "default"
    ) -> StepResult:
        """Add a new event to a narrative."""
        try:
            if narrative_id not in self._active_narratives:
                return StepResult.fail(f"Narrative {narrative_id} not found")

            timeline = self._active_narratives[narrative_id]
            timeline["events"].append(event)
            timeline["total_events"] = len(timeline["events"])
            timeline["last_update"] = time.time()

            # Update involved creators and platforms
            timeline["involved_creators"] = list(set(
                event["creator_id"] for event in timeline["events"]
            ))
            timeline["platforms"] = list(set(
                event["platform"] for event in timeline["events"]
            ))

            return StepResult.ok(data={"event_added": event["event_id"]})

        except Exception as e:
            return StepResult.fail(f"Failed to add narrative event: {str(e)}")

    def get_tool_stats(self) -> dict[str, Any]:
        """Get tool statistics."""
        return {
            "active_narratives": len(self._active_narratives),
            "total_events": sum(len(timeline["events"]) for timeline in self._active_narratives.values()),
            "monitored_platforms": len(self._cross_platform_mappings),
        }
