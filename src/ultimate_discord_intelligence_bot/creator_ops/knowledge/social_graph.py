"""
Social graph mapping for creators, guests, and collaborators.

This module provides social graph analysis including co-appearance detection,
collaboration recommendations, and audience overlap estimation.
"""
from __future__ import annotations
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING
import networkx as nx
from sqlalchemy import and_
from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.models import Account, Media, Person
from platform.core.step_result import StepResult
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
logger = logging.getLogger(__name__)

@dataclass
class CreatorNode:
    """Creator node in the social graph."""
    handle: str
    platform: str
    name: str | None = None
    follower_count: int | None = None
    content_count: int = 0
    collaboration_count: int = 0

@dataclass
class CollaborationEdge:
    """Edge representing collaboration between creators."""
    creator1: str
    creator2: str
    collaboration_count: int
    collaboration_types: list[str]
    first_collaboration: str | None = None
    last_collaboration: str | None = None
    audience_overlap: float | None = None

@dataclass
class NetworkAnalysis:
    """Social network analysis results."""
    creator_count: int
    collaboration_count: int
    average_degree: float
    clustering_coefficient: float
    connected_components: int
    top_collaborators: list[tuple[str, int]]
    isolated_creators: list[str]

@dataclass
class CollaborationRecommendation:
    """Collaboration recommendation for a creator."""
    recommended_creator: str
    platform: str
    recommendation_score: float
    reasons: list[str]
    audience_overlap: float | None = None
    mutual_connections: int = 0

class SocialGraphMapper:
    """
    Social graph mapping and analysis for creator ecosystems.

    Features:
    - Co-appearance detection across episodes
    - Collaboration network analysis
    - Audience overlap estimation
    - Collaboration recommendations
    - Network metrics and insights
    """

    def __init__(self, config: CreatorOpsConfig | None=None, db_session: Session | None=None) -> None:
        """Initialize social graph mapper."""
        self.config = config or CreatorOpsConfig()
        self.db_session = db_session
        self.graph = nx.Graph()

    def build_social_graph(self) -> StepResult:
        """
        Build the social graph from database data.

        Returns:
            StepResult with graph statistics
        """
        try:
            if not self.db_session:
                return StepResult.fail('Database session not available')
            self.graph.clear()
            accounts = self.db_session.query(Account).all()
            for account in accounts:
                creator_node = CreatorNode(handle=account.handle, platform=account.platform, name=account.display_name, follower_count=account.follower_count)
                self.graph.add_node(account.handle, **creator_node.__dict__)
            people = self.db_session.query(Person).all()
            media_people = defaultdict(list)
            for person in people:
                if person.media_id:
                    media_people[person.media_id].append(person)
            collaborations = defaultdict(lambda: defaultdict(int))
            collaboration_types = defaultdict(lambda: defaultdict(set))
            collaboration_dates = defaultdict(lambda: defaultdict(list))
            for media_id, people_list in media_people.items():
                media = self.db_session.query(Media).filter(Media.id == media_id).first()
                if not media:
                    continue
                creator_handles = set()
                for person in people_list:
                    account = self.db_session.query(Account).filter(and_(Account.handle == person.name, Account.platform == media.account.platform)).first()
                    if account:
                        creator_handles.add(account.handle)
                creator_handles.add(media.account.handle)
                creator_list = list(creator_handles)
                for i, creator1 in enumerate(creator_list):
                    for creator2 in creator_list[i + 1:]:
                        collaborations[creator1][creator2] += 1
                        collaborations[creator2][creator1] += 1
                        collaboration_types[creator1][creator2].add(media.type)
                        collaboration_types[creator2][creator1].add(media.type)
                        collaboration_dates[creator1][creator2].append(media.created_at)
                        collaboration_dates[creator2][creator1].append(media.created_at)
            for creator1, collaborators in collaborations.items():
                for creator2, count in collaborators.items():
                    if creator1 != creator2 and count > 0:
                        types = list(collaboration_types[creator1][creator2])
                        dates = collaboration_dates[creator1][creator2]
                        dates.sort()
                        audience_overlap = self._calculate_audience_overlap(creator1, creator2)
                        edge_data = CollaborationEdge(creator1=creator1, creator2=creator2, collaboration_count=count, collaboration_types=types, first_collaboration=dates[0].isoformat() if dates else None, last_collaboration=dates[-1].isoformat() if dates else None, audience_overlap=audience_overlap)
                        self.graph.add_edge(creator1, creator2, **edge_data.__dict__)
            for node in self.graph.nodes():
                creator_data = self.graph.nodes[node]
                creator_data['content_count'] = self._get_creator_content_count(node)
                creator_data['collaboration_count'] = self.graph.degree(node)
            stats = self._calculate_graph_statistics()
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f'Failed to build social graph: {e!s}')
            return StepResult.fail(f'Failed to build social graph: {e!s}')

    def analyze_creator_network(self, creator_handle: str) -> StepResult:
        """
        Analyze the network around a specific creator.

        Args:
            creator_handle: Creator's handle/username

        Returns:
            StepResult with network analysis
        """
        try:
            if creator_handle not in self.graph:
                return StepResult.fail(f'Creator not found in graph: {creator_handle}')
            collaborators = list(self.graph.neighbors(creator_handle))
            collaboration_details = []
            for collaborator in collaborators:
                edge_data = self.graph[creator_handle][collaborator]
                collaboration_details.append({'creator': collaborator, 'collaboration_count': edge_data['collaboration_count'], 'collaboration_types': edge_data['collaboration_types'], 'first_collaboration': edge_data['first_collaboration'], 'last_collaboration': edge_data['last_collaboration'], 'audience_overlap': edge_data['audience_overlap']})
            collaboration_details.sort(key=lambda x: x['collaboration_count'], reverse=True)
            degree = self.graph.degree(creator_handle)
            clustering = nx.clustering(self.graph, creator_handle)
            two_hop_network = set()
            for collaborator in collaborators:
                two_hop_network.update(self.graph.neighbors(collaborator))
            two_hop_network.discard(creator_handle)
            two_hop_network -= set(collaborators)
            analysis = {'creator': creator_handle, 'direct_collaborators': len(collaborators), 'collaboration_details': collaboration_details, 'network_degree': degree, 'clustering_coefficient': clustering, 'two_hop_network_size': len(two_hop_network), 'two_hop_network': list(two_hop_network)}
            return StepResult.ok(data=analysis)
        except Exception as e:
            logger.error(f'Failed to analyze creator network: {e!s}')
            return StepResult.fail(f'Failed to analyze creator network: {e!s}')

    def get_collaboration_recommendations(self, creator_handle: str, limit: int=10) -> StepResult:
        """
        Get collaboration recommendations for a creator.

        Args:
            creator_handle: Creator's handle/username
            limit: Maximum number of recommendations

        Returns:
            StepResult with collaboration recommendations
        """
        try:
            if creator_handle not in self.graph:
                return StepResult.fail(f'Creator not found in graph: {creator_handle}')
            current_collaborators = set(self.graph.neighbors(creator_handle))
            potential_collaborators = set()
            for collaborator in current_collaborators:
                potential_collaborators.update(self.graph.neighbors(collaborator))
            potential_collaborators -= current_collaborators
            potential_collaborators.discard(creator_handle)
            recommendations = []
            for potential in potential_collaborators:
                score = self._calculate_collaboration_score(creator_handle, potential)
                if score > 0:
                    mutual_connections = len(current_collaborators & set(self.graph.neighbors(potential)))
                    audience_overlap = self._calculate_audience_overlap(creator_handle, potential)
                    reasons = self._generate_recommendation_reasons(creator_handle, potential, mutual_connections, audience_overlap)
                    platform = self.graph.nodes[potential].get('platform', 'unknown')
                    recommendation = CollaborationRecommendation(recommended_creator=potential, platform=platform, recommendation_score=score, reasons=reasons, audience_overlap=audience_overlap, mutual_connections=mutual_connections)
                    recommendations.append(recommendation)
            recommendations.sort(key=lambda x: x.recommendation_score, reverse=True)
            recommendations = recommendations[:limit]
            return StepResult.ok(data=recommendations)
        except Exception as e:
            logger.error(f'Failed to get collaboration recommendations: {e!s}')
            return StepResult.fail(f'Failed to get collaboration recommendations: {e!s}')

    def get_audience_overlap_estimation(self, creator1: str, creator2: str) -> StepResult:
        """
        Estimate audience overlap between two creators.

        Args:
            creator1: First creator's handle
            creator2: Second creator's handle

        Returns:
            StepResult with audience overlap estimation
        """
        try:
            if creator1 not in self.graph or creator2 not in self.graph:
                return StepResult.fail('One or both creators not found in graph')
            overlap_score = self._calculate_audience_overlap(creator1, creator2)
            collaboration_count = 0
            if self.graph.has_edge(creator1, creator2):
                collaboration_count = self.graph[creator1][creator2]['collaboration_count']
            mutual_connections = len(set(self.graph.neighbors(creator1)) & set(self.graph.neighbors(creator2)))
            estimation = {'creator1': creator1, 'creator2': creator2, 'overlap_score': overlap_score, 'collaboration_count': collaboration_count, 'mutual_connections': mutual_connections, 'interpretation': self._interpret_overlap_score(overlap_score)}
            return StepResult.ok(data=estimation)
        except Exception as e:
            logger.error(f'Failed to estimate audience overlap: {e!s}')
            return StepResult.fail(f'Failed to estimate audience overlap: {e!s}')

    def _calculate_audience_overlap(self, creator1: str, creator2: str) -> float:
        """Calculate audience overlap between two creators."""
        try:
            creator1_data = self.graph.nodes[creator1]
            creator2_data = self.graph.nodes[creator2]
            follower1 = creator1_data.get('follower_count', 0) or 0
            follower2 = creator2_data.get('follower_count', 0) or 0
            if follower1 == 0 or follower2 == 0:
                return 0.0
            min_followers = min(follower1, follower2)
            max_followers = max(follower1, follower2)
            similarity_ratio = min_followers / max_followers if max_followers > 0 else 0
            collaboration_boost = 0
            if self.graph.has_edge(creator1, creator2):
                collaboration_count = self.graph[creator1][creator2]['collaboration_count']
                collaboration_boost = min(collaboration_count * 0.1, 0.3)
            overlap_score = similarity_ratio * 0.7 + collaboration_boost
            return min(overlap_score, 1.0)
        except Exception as e:
            logger.warning(f'Failed to calculate audience overlap: {e!s}')
            return 0.0

    def _calculate_collaboration_score(self, creator1: str, creator2: str) -> float:
        """Calculate collaboration recommendation score."""
        try:
            score = 0.0
            mutual_connections = len(set(self.graph.neighbors(creator1)) & set(self.graph.neighbors(creator2)))
            score += mutual_connections * 0.2
            audience_overlap = self._calculate_audience_overlap(creator1, creator2)
            score += audience_overlap * 0.3
            creator1_platform = self.graph.nodes[creator1].get('platform', '')
            creator2_platform = self.graph.nodes[creator2].get('platform', '')
            if creator1_platform == creator2_platform:
                score += 0.2
            score += 0.1
            return min(score, 1.0)
        except Exception as e:
            logger.warning(f'Failed to calculate collaboration score: {e!s}')
            return 0.0

    def _generate_recommendation_reasons(self, creator1: str, creator2: str, mutual_connections: int, audience_overlap: float) -> list[str]:
        """Generate reasons for collaboration recommendation."""
        reasons = []
        if mutual_connections > 0:
            reasons.append(f'Has {mutual_connections} mutual collaborators')
        if audience_overlap > 0.3:
            reasons.append('High audience overlap potential')
        elif audience_overlap > 0.1:
            reasons.append('Moderate audience overlap')
        creator1_platform = self.graph.nodes[creator1].get('platform', '')
        creator2_platform = self.graph.nodes[creator2].get('platform', '')
        if creator1_platform == creator2_platform:
            reasons.append(f'Same platform ({creator1_platform})')
        else:
            reasons.append(f'Cross-platform opportunity ({creator1_platform} ↔ {creator2_platform})')
        creator1_content = self.graph.nodes[creator1].get('content_count', 0)
        creator2_content = self.graph.nodes[creator2].get('content_count', 0)
        if creator1_content > 0 and creator2_content > 0:
            reasons.append('Both creators have active content')
        return reasons

    def _interpret_overlap_score(self, score: float) -> str:
        """Interpret audience overlap score."""
        if score >= 0.7:
            return 'Very high overlap - strong potential for collaboration'
        elif score >= 0.5:
            return 'High overlap - good collaboration potential'
        elif score >= 0.3:
            return 'Moderate overlap - some collaboration potential'
        elif score >= 0.1:
            return 'Low overlap - limited collaboration potential'
        else:
            return 'Very low overlap - minimal collaboration potential'

    def _get_creator_content_count(self, creator_handle: str) -> int:
        """Get content count for a creator."""
        try:
            if not self.db_session:
                return 0
            account = self.db_session.query(Account).filter(Account.handle == creator_handle).first()
            if not account:
                return 0
            count = self.db_session.query(Media).filter(Media.account_id == account.id).count()
            return count
        except Exception as e:
            logger.warning(f'Failed to get content count for {creator_handle}: {e!s}')
            return 0

    def _calculate_graph_statistics(self) -> NetworkAnalysis:
        """Calculate overall graph statistics."""
        try:
            if len(self.graph) == 0:
                return NetworkAnalysis(creator_count=0, collaboration_count=0, average_degree=0.0, clustering_coefficient=0.0, connected_components=0, top_collaborators=[], isolated_creators=[])
            creator_count = len(self.graph)
            collaboration_count = len(self.graph.edges())
            average_degree = sum(dict(self.graph.degree()).values()) / creator_count
            clustering_coefficient = nx.average_clustering(self.graph)
            connected_components = nx.number_connected_components(self.graph)
            degree_centrality = nx.degree_centrality(self.graph)
            top_collaborators = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            isolated_creators = list(nx.isolates(self.graph))
            return NetworkAnalysis(creator_count=creator_count, collaboration_count=collaboration_count, average_degree=average_degree, clustering_coefficient=clustering_coefficient, connected_components=connected_components, top_collaborators=top_collaborators, isolated_creators=isolated_creators)
        except Exception as e:
            logger.error(f'Failed to calculate graph statistics: {e!s}')
            return NetworkAnalysis(creator_count=0, collaboration_count=0, average_degree=0.0, clustering_coefficient=0.0, connected_components=0, top_collaborators=[], isolated_creators=[])