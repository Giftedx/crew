"""Social graph analysis tool for creator networks."""

from __future__ import annotations
import time
from typing import Any, TypedDict
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class SocialGraphAnalysisResult(TypedDict, total=False):
    """Result of social graph analysis."""

    creator_id: str
    analysis_type: str
    centrality_scores: dict[str, float]
    influence_metrics: dict[str, float]
    community_clusters: dict[str, list[str]]
    collaboration_strength: dict[str, float]
    network_position: dict[str, Any]
    recommendations: list[str]
    timestamp: float


class SocialGraphAnalysisTool(BaseTool[StepResult]):
    """Analyze social graphs and creator networks."""

    name: str = "Social Graph Analysis"
    description: str = "Analyze social graph metrics including centrality scores, influence propagation, community detection, and collaboration strength for creator networks"

    def _run(self, creator_id: str, analysis_type: str, tenant: str, workspace: str) -> StepResult:
        """
        Analyze social graph metrics for a creator.

        Args:
            creator_id: ID of the creator to analyze
            analysis_type: Type of analysis ("centrality", "influence", "clusters", "communities", "comprehensive")
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with social graph analysis data
        """
        try:
            if not creator_id or not analysis_type:
                return StepResult.fail("Creator ID and analysis type are required")
            analysis_result = self._perform_analysis(creator_id, analysis_type, tenant, workspace)
            return StepResult.ok(data=analysis_result)
        except Exception as e:
            return StepResult.fail(f"Social graph analysis failed: {e!s}")

    def _perform_analysis(
        self, creator_id: str, analysis_type: str, tenant: str, workspace: str
    ) -> SocialGraphAnalysisResult:
        """Perform the actual social graph analysis."""
        mock_network_data = self._get_mock_network_data()
        if analysis_type == "centrality":
            return self._analyze_centrality(creator_id, mock_network_data)
        elif analysis_type == "influence":
            return self._analyze_influence(creator_id, mock_network_data)
        elif analysis_type == "clusters":
            return self._analyze_clusters(creator_id, mock_network_data)
        elif analysis_type == "communities":
            return self._analyze_communities(creator_id, mock_network_data)
        elif analysis_type == "comprehensive":
            return self._comprehensive_analysis(creator_id, mock_network_data)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")

    def _get_mock_network_data(self) -> dict[str, Any]:
        """Get mock network data for analysis."""
        return {
            "nodes": {
                "h3_podcast": {"type": "show", "followers": 1000000, "platforms": ["youtube", "tiktok"]},
                "ethan_klein": {"type": "person", "followers": 500000, "platforms": ["youtube", "twitter"]},
                "hila_klein": {"type": "person", "followers": 300000, "platforms": ["youtube", "instagram"]},
                "hasan_piker": {"type": "person", "followers": 800000, "platforms": ["twitch", "youtube"]},
                "dan": {"type": "person", "followers": 50000, "platforms": ["youtube", "twitter"]},
                "ab": {"type": "person", "followers": 30000, "platforms": ["youtube", "twitter"]},
                "will_neff": {"type": "person", "followers": 200000, "platforms": ["twitch", "youtube"]},
                "qt_cinderella": {"type": "person", "followers": 150000, "platforms": ["twitch", "instagram"]},
            },
            "edges": {
                "h3_podcast": ["ethan_klein", "hila_klein", "dan", "ab"],
                "ethan_klein": ["h3_podcast", "hila_klein", "dan", "ab"],
                "hila_klein": ["h3_podcast", "ethan_klein"],
                "hasan_piker": ["will_neff", "qt_cinderella"],
                "dan": ["h3_podcast", "ethan_klein"],
                "ab": ["h3_podcast", "ethan_klein"],
                "will_neff": ["hasan_piker", "qt_cinderella"],
                "qt_cinderella": ["hasan_piker", "will_neff"],
            },
            "collaborations": {
                ("h3_podcast", "hasan_piker"): {"count": 3, "last_date": "2024-01-15"},
                ("ethan_klein", "hasan_piker"): {"count": 2, "last_date": "2024-01-10"},
                ("hasan_piker", "will_neff"): {"count": 10, "last_date": "2024-01-20"},
                ("hasan_piker", "qt_cinderella"): {"count": 5, "last_date": "2024-01-18"},
            },
        }

    def _analyze_centrality(self, creator_id: str, network_data: dict[str, Any]) -> SocialGraphAnalysisResult:
        """Analyze centrality metrics for a creator."""
        nodes = network_data["nodes"]
        edges = network_data["edges"]
        degree_centrality = len(edges.get(creator_id, []))
        max_degree = max((len(connections) for connections in edges.values())) if edges else 1
        normalized_degree = degree_centrality / max_degree if max_degree > 0 else 0
        betweenness = self._calculate_betweenness_centrality(creator_id, edges)
        closeness = self._calculate_closeness_centrality(creator_id, edges)
        eigenvector = self._calculate_eigenvector_centrality(creator_id, edges)
        return SocialGraphAnalysisResult(
            creator_id=creator_id,
            analysis_type="centrality",
            centrality_scores={
                "degree": normalized_degree,
                "betweenness": betweenness,
                "closeness": closeness,
                "eigenvector": eigenvector,
            },
            influence_metrics={},
            community_clusters={},
            collaboration_strength={},
            network_position={
                "total_connections": degree_centrality,
                "network_size": len(nodes),
                "connection_ratio": degree_centrality / len(nodes) if nodes else 0,
            },
            recommendations=self._generate_centrality_recommendations(normalized_degree, betweenness),
            timestamp=time.time(),
        )

    def _analyze_influence(self, creator_id: str, network_data: dict[str, Any]) -> SocialGraphAnalysisResult:
        """Analyze influence metrics for a creator."""
        nodes = network_data["nodes"]
        edges = network_data["edges"]
        collaborations = network_data["collaborations"]
        creator_data = nodes.get(creator_id, {})
        follower_count = creator_data.get("followers", 0)
        reachable_nodes = self._get_reachable_nodes(creator_id, edges, max_depth=2)
        influence_reach = len(reachable_nodes)
        collaboration_influence = 0
        for (source, target), data in collaborations.items():
            if source == creator_id:
                target_followers = nodes.get(target, {}).get("followers", 0)
                collaboration_influence += target_followers * data["count"]
        max_followers = max((node.get("followers", 0) for node in nodes.values())) if nodes else 1
        influence_score = (follower_count + collaboration_influence / 1000) / max_followers
        return SocialGraphAnalysisResult(
            creator_id=creator_id,
            analysis_type="influence",
            centrality_scores={},
            influence_metrics={
                "follower_count": follower_count,
                "influence_reach": influence_reach,
                "collaboration_influence": collaboration_influence,
                "influence_score": min(influence_score, 1.0),
                "network_penetration": influence_reach / len(nodes) if nodes else 0,
            },
            community_clusters={},
            collaboration_strength={},
            network_position={
                "reachable_creators": reachable_nodes,
                "collaboration_count": len([c for c in collaborations if creator_id in c]),
            },
            recommendations=self._generate_influence_recommendations(influence_score, influence_reach),
            timestamp=time.time(),
        )

    def _analyze_clusters(self, creator_id: str, network_data: dict[str, Any]) -> SocialGraphAnalysisResult:
        """Analyze community clusters for a creator."""
        edges = network_data["edges"]
        clusters = self._detect_communities(edges)
        creator_cluster = None
        for cluster_id, cluster_members in clusters.items():
            if creator_id in cluster_members:
                creator_cluster = cluster_id
                break
        return SocialGraphAnalysisResult(
            creator_id=creator_id,
            analysis_type="clusters",
            centrality_scores={},
            influence_metrics={},
            community_clusters={
                "creator_cluster": creator_cluster,
                "cluster_members": clusters.get(creator_cluster or "", []),
                "total_clusters": len(clusters),
                "cluster_size": len(clusters.get(creator_cluster or "", [])),
            },
            collaboration_strength={},
            network_position={
                "cluster_diversity": len(clusters),
                "intra_cluster_connections": len(edges.get(creator_id, [])),
            },
            recommendations=self._generate_cluster_recommendations(clusters, creator_cluster),
            timestamp=time.time(),
        )

    def _analyze_communities(self, creator_id: str, network_data: dict[str, Any]) -> SocialGraphAnalysisResult:
        """Analyze community structure and dynamics."""
        edges = network_data["edges"]
        network_data["collaborations"]
        communities = {
            "h3_network": ["h3_podcast", "ethan_klein", "hila_klein", "dan", "ab"],
            "hasan_network": ["hasan_piker", "will_neff", "qt_cinderella"],
            "cross_platform": ["h3_podcast", "hasan_piker"],
        }
        creator_communities = []
        for community_name, members in communities.items():
            if creator_id in members:
                creator_communities.append(community_name)
        bridge_score = self._calculate_bridge_score(creator_id, communities, edges)
        return SocialGraphAnalysisResult(
            creator_id=creator_id,
            analysis_type="communities",
            centrality_scores={},
            influence_metrics={},
            community_clusters={
                "communities": creator_communities,
                "bridge_score": bridge_score,
                "community_diversity": len(creator_communities),
            },
            collaboration_strength={},
            network_position={
                "total_communities": len(communities),
                "cross_community_connections": len(
                    [
                        target
                        for target in edges.get(creator_id, [])
                        if any((target in comm for comm in communities.values()))
                    ]
                ),
            },
            recommendations=self._generate_community_recommendations(creator_communities, bridge_score),
            timestamp=time.time(),
        )

    def _comprehensive_analysis(self, creator_id: str, network_data: dict[str, Any]) -> SocialGraphAnalysisResult:
        """Perform comprehensive social graph analysis."""
        centrality_result = self._analyze_centrality(creator_id, network_data)
        influence_result = self._analyze_influence(creator_id, network_data)
        cluster_result = self._analyze_clusters(creator_id, network_data)
        community_result = self._analyze_communities(creator_id, network_data)
        overall_score = (
            centrality_result["centrality_scores"].get("eigenvector", 0) * 0.3
            + influence_result["influence_metrics"].get("influence_score", 0) * 0.4
            + cluster_result["community_clusters"].get("cluster_size", 0) / 10 * 0.2
            + community_result["community_clusters"].get("bridge_score", 0) * 0.1
        )
        return SocialGraphAnalysisResult(
            creator_id=creator_id,
            analysis_type="comprehensive",
            centrality_scores=centrality_result["centrality_scores"],
            influence_metrics=influence_result["influence_metrics"],
            community_clusters={**cluster_result["community_clusters"], **community_result["community_clusters"]},
            collaboration_strength={},
            network_position={
                "overall_score": overall_score,
                "network_tier": self._determine_network_tier(overall_score),
                "influence_level": self._determine_influence_level(
                    influence_result["influence_metrics"].get("influence_score", 0)
                ),
            },
            recommendations=self._generate_comprehensive_recommendations(
                centrality_result, influence_result, cluster_result, community_result
            ),
            timestamp=time.time(),
        )

    def _calculate_betweenness_centrality(self, creator_id: str, edges: dict[str, list[str]]) -> float:
        """Calculate betweenness centrality for a creator."""
        total_paths = 0
        paths_through_creator = 0
        all_nodes = set(edges.keys()) | {node for connections in edges.values() for node in connections}
        for source in all_nodes:
            for target in all_nodes:
                if source != target:
                    path = self._find_shortest_path(source, target, edges)
                    if path:
                        total_paths += 1
                        if creator_id in path[1:-1]:
                            paths_through_creator += 1
        return paths_through_creator / total_paths if total_paths > 0 else 0

    def _calculate_closeness_centrality(self, creator_id: str, edges: dict[str, list[str]]) -> float:
        """Calculate closeness centrality for a creator."""
        distances = self._calculate_distances(creator_id, edges)
        total_distance = sum(distances.values())
        return (len(distances) - 1) / total_distance if total_distance > 0 else 0

    def _calculate_eigenvector_centrality(self, creator_id: str, edges: dict[str, list[str]]) -> float:
        """Calculate eigenvector centrality for a creator."""
        nodes = list(set(edges.keys()) | {node for connections in edges.values() for node in connections})
        n = len(nodes)
        if n == 0:
            return 0
        centrality = dict.fromkeys(nodes, 1.0)
        for _ in range(10):
            new_centrality = {}
            for node in nodes:
                score = sum((centrality[neighbor] for neighbor in edges.get(node, [])))
                new_centrality[node] = score
            total = sum(new_centrality.values())
            if total > 0:
                centrality = {node: score / total for node, score in new_centrality.items()}
        return centrality.get(creator_id, 0)

    def _get_reachable_nodes(self, creator_id: str, edges: dict[str, list[str]], max_depth: int = 2) -> set[str]:
        """Get all nodes reachable within max_depth from creator."""
        visited = set()
        queue = [(creator_id, 0)]
        while queue:
            node, depth = queue.pop(0)
            if node in visited or depth > max_depth:
                continue
            visited.add(node)
            for neighbor in edges.get(node, []):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))
        return visited - {creator_id}

    def _detect_communities(self, edges: dict[str, list[str]]) -> dict[str, list[str]]:
        """Detect communities using connected components."""
        visited = set()
        communities = {}
        community_id = 0
        for node in edges:
            if node not in visited:
                community = []
                stack = [node]
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        community.append(current)
                        stack.extend(edges.get(current, []))
                if community:
                    communities[f"community_{community_id}"] = community
                    community_id += 1
        return communities

    def _calculate_bridge_score(
        self, creator_id: str, communities: dict[str, list[str]], edges: dict[str, list[str]]
    ) -> float:
        """Calculate how much a creator bridges different communities."""
        creator_communities = set()
        for comm_name, members in communities.items():
            if creator_id in members:
                creator_communities.add(comm_name)
        if len(creator_communities) <= 1:
            return 0
        cross_community_connections = 0
        for neighbor in edges.get(creator_id, []):
            neighbor_communities = set()
            for comm_name, members in communities.items():
                if neighbor in members:
                    neighbor_communities.add(comm_name)
            if neighbor_communities != creator_communities:
                cross_community_connections += 1
        return cross_community_connections / len(edges.get(creator_id, [])) if edges.get(creator_id) else 0

    def _find_shortest_path(self, source: str, target: str, edges: dict[str, list[str]]) -> list[str] | None:
        """Find shortest path between two nodes using BFS."""
        if source == target:
            return [source]
        queue = [(source, [source])]
        visited = {source}
        while queue:
            node, path = queue.pop(0)
            for neighbor in edges.get(node, []):
                if neighbor == target:
                    return [*path, neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, [*path, neighbor]))
        return None

    def _calculate_distances(self, creator_id: str, edges: dict[str, list[str]]) -> dict[str, int]:
        """Calculate distances from creator to all other nodes."""
        distances = {creator_id: 0}
        queue = [creator_id]
        while queue:
            current = queue.pop(0)
            for neighbor in edges.get(current, []):
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
        return distances

    def _determine_network_tier(self, overall_score: float) -> int:
        """Determine network tier based on overall score."""
        if overall_score >= 0.8:
            return 1
        elif overall_score >= 0.6:
            return 2
        elif overall_score >= 0.4:
            return 3
        else:
            return 4

    def _determine_influence_level(self, influence_score: float) -> str:
        """Determine influence level based on score."""
        if influence_score >= 0.8:
            return "high"
        elif influence_score >= 0.5:
            return "medium"
        elif influence_score >= 0.2:
            return "low"
        else:
            return "minimal"

    def _generate_centrality_recommendations(self, degree: float, betweenness: float) -> list[str]:
        """Generate recommendations based on centrality analysis."""
        recommendations = []
        if degree < 0.3:
            recommendations.append("Consider collaborating with more creators to increase network connections")
        if betweenness > 0.5:
            recommendations.append("You're a key connector in the network - leverage this position for influence")
        if degree > 0.7:
            recommendations.append("High connectivity detected - focus on quality over quantity of connections")
        return recommendations

    def _generate_influence_recommendations(self, influence_score: float, reach: int) -> list[str]:
        """Generate recommendations based on influence analysis."""
        recommendations = []
        if influence_score < 0.3:
            recommendations.append("Focus on building audience and increasing follower engagement")
        if reach < 5:
            recommendations.append("Expand network connections to increase influence reach")
        if influence_score > 0.7:
            recommendations.append("High influence detected - consider mentoring other creators")
        return recommendations

    def _generate_cluster_recommendations(
        self, clusters: dict[str, list[str]], creator_cluster: str | None
    ) -> list[str]:
        """Generate recommendations based on cluster analysis."""
        recommendations = []
        if creator_cluster:
            cluster_size = len(clusters.get(creator_cluster, []))
            if cluster_size < 3:
                recommendations.append("Small cluster detected - consider expanding within-cluster connections")
            elif cluster_size > 10:
                recommendations.append("Large cluster detected - consider creating sub-communities")
        if len(clusters) < 3:
            recommendations.append("Limited community diversity - explore connections outside current clusters")
        return recommendations

    def _generate_community_recommendations(self, communities: list[str], bridge_score: float) -> list[str]:
        """Generate recommendations based on community analysis."""
        recommendations = []
        if len(communities) == 1:
            recommendations.append("Single community membership - consider bridging to other communities")
        if bridge_score > 0.5:
            recommendations.append("High bridge score - leverage cross-community connections for influence")
        if bridge_score < 0.2 and len(communities) > 1:
            recommendations.append("Multiple communities but low bridging - increase cross-community interactions")
        return recommendations

    def _generate_comprehensive_recommendations(
        self,
        centrality_result: SocialGraphAnalysisResult,
        influence_result: SocialGraphAnalysisResult,
        cluster_result: SocialGraphAnalysisResult,
        community_result: SocialGraphAnalysisResult,
    ) -> list[str]:
        """Generate comprehensive recommendations combining all analyses."""
        recommendations = []
        recommendations.extend(centrality_result.get("recommendations", []))
        recommendations.extend(influence_result.get("recommendations", []))
        recommendations.extend(cluster_result.get("recommendations", []))
        recommendations.extend(community_result.get("recommendations", []))
        overall_score = centrality_result.get("network_position", {}).get("overall_score", 0)
        if overall_score > 0.8:
            recommendations.append("Excellent network position - consider strategic partnerships and mentorship")
        elif overall_score < 0.3:
            recommendations.append("Focus on building foundational network connections and content quality")
        return list(set(recommendations))

    def analyze_temporal_evolution(self, creator_id: str, time_window: str, tenant: str, workspace: str) -> StepResult:
        """
        Analyze the temporal evolution of a creator's social network.

        Args:
            creator_id: ID of the creator to analyze.
            time_window: The time window for the analysis (e.g., "30d", "90d", "1y").
            tenant: Tenant identifier.
            workspace: Workspace identifier.

        Returns:
            StepResult with temporal analysis data.
        """
        try:
            if not creator_id or not time_window:
                return StepResult.fail("Creator ID and time window are required")
            historical_data = self._get_mock_historical_data(time_window)
            evolution_analysis = self._perform_temporal_analysis(creator_id, historical_data)
            return StepResult.ok(data=evolution_analysis)
        except Exception as e:
            return StepResult.fail(f"Temporal evolution analysis failed: {e!s}")

    def _get_mock_historical_data(self, time_window: str) -> list[dict[str, Any]]:
        """Get mock historical network data for temporal analysis."""
        snapshots = [
            {"date": "2023-01-01", "followers": 100000, "connections": 5, "influence_score": 0.4},
            {"date": "2023-04-01", "followers": 200000, "connections": 10, "influence_score": 0.5},
            {"date": "2023-07-01", "followers": 500000, "connections": 15, "influence_score": 0.7},
            {"date": "2023-10-01", "followers": 800000, "connections": 20, "influence_score": 0.8},
            {"date": "2024-01-01", "followers": 1000000, "connections": 25, "influence_score": 0.85},
        ]
        return snapshots

    def _perform_temporal_analysis(self, creator_id: str, historical_data: list[dict[str, Any]]) -> dict:
        """Analyzes trends and changes in the creator's network over time."""
        if not historical_data:
            return {}
        start_data = historical_data[0]
        end_data = historical_data[-1]
        follower_growth = end_data["followers"] - start_data["followers"]
        connection_growth = end_data["connections"] - start_data["connections"]
        influence_growth = end_data["influence_score"] - start_data["influence_score"]
        return {
            "creator_id": creator_id,
            "analysis_type": "temporal_evolution",
            "time_window": f"{start_data['date']} to {end_data['date']}",
            "follower_growth": follower_growth,
            "connection_growth": connection_growth,
            "influence_growth": influence_growth,
            "trend": "positive" if influence_growth > 0 else "stable",
            "recommendations": [
                f"Follower growth of {follower_growth} is strong.",
                "Continue to expand network connections.",
            ],
        }
