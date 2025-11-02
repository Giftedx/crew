"""
PostgreSQL Store Adapter Layer

This module provides a unified PostgreSQL-based store adapter that consolidates
all SQLite stores into a single, scalable database backend.

Migration Priority:
P0: Memory, Profiles, Ingest (critical for core functionality)
P1: KG, Analytics, Debate (important for advanced features)
P2: Marketplace, Archive (nice-to-have features)
"""
from __future__ import annotations
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, func, text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship, sessionmaker
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)
PostgreSQLBase = declarative_base()

class StoreAdapter(ABC):
    """Abstract base class for all store adapters."""

    @abstractmethod
    def initialize(self) -> StepResult:
        """Initialize the store and create tables if needed."""

    @abstractmethod
    def health_check(self) -> StepResult:
        """Perform a health check on the store."""

    @abstractmethod
    def close(self) -> StepResult:
        """Close the store connection."""

@dataclass
class MemoryItem:
    """Memory item data structure."""
    id: int | None
    tenant: str
    workspace: str
    type: str
    content_json: str
    embedding_json: str
    ts_created: str
    ts_last_used: str
    retention_policy: str
    decay_score: float
    pinned: int
    archived: int

@dataclass
class RetentionPolicy:
    """Retention policy data structure."""
    name: str
    tenant: str
    ttl_days: int

class MemoryItemModel(PostgreSQLBase):
    """PostgreSQL model for memory items."""
    __tablename__ = 'memory_items'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant: Mapped[str] = mapped_column(String(255), nullable=False)
    workspace: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_json: Mapped[str] = mapped_column(Text, nullable=False)
    ts_created: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ts_last_used: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    retention_policy: Mapped[str] = mapped_column(String(100), nullable=False)
    decay_score: Mapped[float] = mapped_column(Float, default=1.0)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint('tenant', 'workspace', 'type', 'content_json', name='uq_memory_item_content'),)

class RetentionPolicyModel(PostgreSQLBase):
    """PostgreSQL model for retention policies."""
    __tablename__ = 'retention_policies'
    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant: Mapped[str] = mapped_column(String(255), primary_key=True)
    ttl_days: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

@dataclass
class Debate:
    """Debate data structure."""
    id: int | None
    tenant: str
    workspace: str
    query: str
    panel_config_json: str
    n_rounds: int
    final_output: str
    created_at: str

@dataclass
class DebateAgent:
    """Debate agent data structure."""
    id: int | None
    debate_id: int
    role: str
    model: str
    output: str
    cost_usd: float
    latency_ms: float
    round: int
    confidence: float

class DebateModel(PostgreSQLBase):
    """PostgreSQL model for debates."""
    __tablename__ = 'debates'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant: Mapped[str] = mapped_column(String(255), nullable=False)
    workspace: Mapped[str] = mapped_column(String(255), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    panel_config_json: Mapped[str] = mapped_column(Text, nullable=False)
    n_rounds: Mapped[int] = mapped_column(Integer, nullable=False)
    final_output: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    agents: Mapped[list[DebateAgentModel]] = relationship('DebateAgentModel', back_populates='debate')
    __table_args__ = (UniqueConstraint('tenant', 'workspace', 'query', 'created_at', name='uq_debate_query_time'),)

class DebateAgentModel(PostgreSQLBase):
    """PostgreSQL model for debate agents."""
    __tablename__ = 'debate_agents'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    debate_id: Mapped[int] = mapped_column(ForeignKey('debates.id'), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    debate: Mapped[DebateModel] = relationship('DebateModel', back_populates='agents')

@dataclass
class KGNode:
    """Knowledge graph node data structure."""
    id: int | None
    tenant: str
    type: str
    name: str
    attrs_json: str
    created_at: str

@dataclass
class KGEdge:
    """Knowledge graph edge data structure."""
    id: int | None
    src_id: int
    dst_id: int
    type: str
    weight: float
    provenance_id: int | None
    created_at: str

class KGNodeModel(PostgreSQLBase):
    """PostgreSQL model for knowledge graph nodes."""
    __tablename__ = 'kg_nodes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    attrs_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    __table_args__ = (UniqueConstraint('tenant', 'type', 'name', name='uq_kg_node_tenant_type_name'),)

class KGEdgeModel(PostgreSQLBase):
    """PostgreSQL model for knowledge graph edges."""
    __tablename__ = 'kg_edges'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    src_id: Mapped[int] = mapped_column(ForeignKey('kg_nodes.id'), nullable=False)
    dst_id: Mapped[int] = mapped_column(ForeignKey('kg_nodes.id'), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    provenance_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    __table_args__ = (UniqueConstraint('src_id', 'dst_id', 'type', name='uq_kg_edge_src_dst_type'),)

@dataclass
class CreatorProfile:
    """Creator profile data structure."""
    name: str
    data: dict[str, Any]

@dataclass
class CrossProfileLink:
    """Cross profile link data structure."""
    source: str
    target: str
    count: int
    first_seen: str
    last_seen: str

class CreatorProfileModel(PostgreSQLBase):
    """PostgreSQL model for creator profiles."""
    __tablename__ = 'creator_profiles'
    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class CrossProfileLinkModel(PostgreSQLBase):
    """PostgreSQL model for cross profile links."""
    __tablename__ = 'cross_profile_links'
    source: Mapped[str] = mapped_column(String(255), primary_key=True)
    target: Mapped[str] = mapped_column(String(255), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class UnifiedStoreManager:
    """Unified PostgreSQL store manager that consolidates all SQLite stores."""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        engine_kwargs = {'echo': False, 'pool_pre_ping': True, 'pool_recycle': 3600}
        if not database_url.startswith('sqlite'):
            engine_kwargs.update({'pool_size': 10, 'max_overflow': 20})
        self.engine = create_engine(database_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._session = None

    def get_session(self):
        """Get database session."""
        if self._session is None:
            self._session = self.SessionLocal()
        return self._session

    def initialize(self) -> StepResult:
        """Initialize all tables."""
        try:
            PostgreSQLBase.metadata.create_all(self.engine)
            logger.info('PostgreSQL store tables created successfully')
            return StepResult.ok(data={'message': 'Store initialized successfully'})
        except Exception as e:
            logger.error(f'Failed to initialize store: {e}')
            return StepResult.fail(f'Failed to initialize store: {e!s}')

    def health_check(self) -> StepResult:
        """Perform health check."""
        try:
            session = self.get_session()
            session.execute(text('SELECT 1'))
            session.commit()
            return StepResult.ok(data={'status': 'healthy'})
        except Exception as e:
            logger.error(f'Health check failed: {e}')
            return StepResult.fail(f'Health check failed: {e!s}')

    def close(self) -> StepResult:
        """Close connections."""
        try:
            if self._session:
                self._session.close()
            self.engine.dispose()
            return StepResult.ok(data={'message': 'Store closed successfully'})
        except Exception as e:
            logger.error(f'Failed to close store: {e}')
            return StepResult.fail(f'Failed to close store: {e!s}')

    def add_memory_item(self, item: MemoryItem) -> StepResult:
        """Add a memory item."""
        try:
            session = self.get_session()
            db_item = MemoryItemModel(tenant=item.tenant, workspace=item.workspace, type=item.type, content_json=item.content_json, embedding_json=item.embedding_json, ts_created=datetime.fromisoformat(item.ts_created), ts_last_used=datetime.fromisoformat(item.ts_last_used), retention_policy=item.retention_policy, decay_score=item.decay_score, pinned=bool(item.pinned), archived=bool(item.archived))
            session.add(db_item)
            session.commit()
            session.refresh(db_item)
            return StepResult.ok(data={'id': db_item.id})
        except Exception as e:
            session.rollback()
            logger.error(f'Failed to add memory item: {e}')
            return StepResult.fail(f'Failed to add memory item: {e!s}')

    def get_memory_item(self, item_id: int) -> StepResult:
        """Get a memory item by ID."""
        try:
            session = self.get_session()
            db_item = session.query(MemoryItemModel).filter(MemoryItemModel.id == item_id).first()
            if not db_item:
                return StepResult.fail('Memory item not found')
            item = MemoryItem(id=db_item.id, tenant=db_item.tenant, workspace=db_item.workspace, type=db_item.type, content_json=db_item.content_json, embedding_json=db_item.embedding_json, ts_created=db_item.ts_created.isoformat(), ts_last_used=db_item.ts_last_used.isoformat(), retention_policy=db_item.retention_policy, decay_score=db_item.decay_score, pinned=int(db_item.pinned), archived=int(db_item.archived))
            return StepResult.ok(data={'item': item})
        except Exception as e:
            logger.error(f'Failed to get memory item: {e}')
            return StepResult.fail(f'Failed to get memory item: {e!s}')

    def update_memory_item_last_used(self, item_id: int, ts: str) -> StepResult:
        """Update memory item last used timestamp."""
        try:
            session = self.get_session()
            db_item = session.query(MemoryItemModel).filter(MemoryItemModel.id == item_id).first()
            if not db_item:
                return StepResult.fail('Memory item not found')
            db_item.ts_last_used = datetime.fromisoformat(ts)
            session.commit()
            return StepResult.ok(data={'message': 'Memory item updated successfully'})
        except Exception as e:
            session.rollback()
            logger.error(f'Failed to update memory item: {e}')
            return StepResult.fail(f'Failed to update memory item: {e!s}')

    def search_memory_keyword(self, tenant: str, workspace: str, text: str, limit: int=5) -> StepResult:
        """Search memory items by keyword."""
        try:
            session = self.get_session()
            like_pattern = f'%{text}%'
            db_items = session.query(MemoryItemModel).filter(MemoryItemModel.tenant == tenant, MemoryItemModel.workspace == workspace, MemoryItemModel.content_json.like(like_pattern)).order_by(MemoryItemModel.ts_last_used.desc()).limit(limit).all()
            items = []
            for db_item in db_items:
                item = MemoryItem(id=db_item.id, tenant=db_item.tenant, workspace=db_item.workspace, type=db_item.type, content_json=db_item.content_json, embedding_json=db_item.embedding_json, ts_created=db_item.ts_created.isoformat(), ts_last_used=db_item.ts_last_used.isoformat(), retention_policy=db_item.retention_policy, decay_score=db_item.decay_score, pinned=int(db_item.pinned), archived=int(db_item.archived))
                items.append(item)
            return StepResult.ok(data={'items': items})
        except Exception as e:
            logger.error(f'Failed to search memory items: {e}')
            return StepResult.fail(f'Failed to search memory items: {e!s}')

    def prune_memory_items(self, tenant: str, now: datetime | None=None) -> StepResult:
        """Prune expired memory items."""
        try:
            now = now or datetime.utcnow()
            session = self.get_session()
            policies = session.query(RetentionPolicyModel).filter(RetentionPolicyModel.tenant == tenant).all()
            deleted_total = 0
            for policy in policies:
                cutoff = now - timedelta(days=policy.ttl_days)
                deleted_count = session.query(MemoryItemModel).filter(MemoryItemModel.tenant == tenant, MemoryItemModel.retention_policy == policy.name, MemoryItemModel.pinned == False, MemoryItemModel.archived == False, MemoryItemModel.ts_last_used < cutoff).delete()
                deleted_total += deleted_count
            session.commit()
            return StepResult.ok(data={'deleted_count': deleted_total})
        except Exception as e:
            session.rollback()
            logger.error(f'Failed to prune memory items: {e}')
            return StepResult.fail(f'Failed to prune memory items: {e!s}')

    def add_debate(self, debate: Debate) -> StepResult:
        """Add a debate."""
        try:
            session = self.get_session()
            db_debate = DebateModel(tenant=debate.tenant, workspace=debate.workspace, query=debate.query, panel_config_json=debate.panel_config_json, n_rounds=debate.n_rounds, final_output=debate.final_output, created_at=datetime.fromisoformat(debate.created_at))
            session.add(db_debate)
            session.commit()
            session.refresh(db_debate)
            return StepResult.ok(data={'id': db_debate.id})
        except Exception as e:
            session.rollback()
            logger.error(f'Failed to add debate: {e}')
            return StepResult.fail(f'Failed to add debate: {e!s}')

    def list_debates(self, tenant: str, workspace: str) -> StepResult:
        """List debates for a tenant/workspace."""
        try:
            session = self.get_session()
            db_debates = session.query(DebateModel).filter(DebateModel.tenant == tenant, DebateModel.workspace == workspace).order_by(DebateModel.id.desc()).all()
            debates = []
            for db_debate in db_debates:
                debate = Debate(id=db_debate.id, tenant=db_debate.tenant, workspace=db_debate.workspace, query=db_debate.query, panel_config_json=db_debate.panel_config_json, n_rounds=db_debate.n_rounds, final_output=db_debate.final_output, created_at=db_debate.created_at.isoformat())
                debates.append(debate)
            return StepResult.ok(data={'debates': debates})
        except Exception as e:
            logger.error(f'Failed to list debates: {e}')
            return StepResult.fail(f'Failed to list debates: {e!s}')

    def add_kg_node(self, tenant: str, node_type: str, name: str, attrs: dict[str, Any] | None=None) -> StepResult:
        """Add a knowledge graph node."""
        try:
            session = self.get_session()
            db_node = KGNodeModel(tenant=tenant, type=node_type, name=name, attrs_json=json.dumps(attrs or {}))
            session.add(db_node)
            session.commit()
            session.refresh(db_node)
            return StepResult.ok(data={'id': db_node.id})
        except Exception as e:
            session.rollback()
            logger.error(f'Failed to add KG node: {e}')
            return StepResult.fail(f'Failed to add KG node: {e!s}')

    def query_kg_nodes(self, tenant: str, *, node_type: str | None=None, name: str | None=None) -> StepResult:
        """Query knowledge graph nodes."""
        try:
            session = self.get_session()
            query = session.query(KGNodeModel).filter(KGNodeModel.tenant == tenant)
            if node_type:
                query = query.filter(KGNodeModel.type == node_type)
            if name:
                query = query.filter(KGNodeModel.name == name)
            db_nodes = query.all()
            nodes = []
            for db_node in db_nodes:
                node = KGNode(id=db_node.id, tenant=db_node.tenant, type=db_node.type, name=db_node.name, attrs_json=db_node.attrs_json, created_at=db_node.created_at.isoformat())
                nodes.append(node)
            return StepResult.ok(data={'nodes': nodes})
        except Exception as e:
            logger.error(f'Failed to query KG nodes: {e}')
            return StepResult.fail(f'Failed to query KG nodes: {e!s}')

    def upsert_creator_profile(self, profile: CreatorProfile) -> StepResult:
        """Upsert a creator profile."""
        try:
            session = self.get_session()
            db_profile = session.query(CreatorProfileModel).filter(CreatorProfileModel.name == profile.name).first()
            if db_profile:
                db_profile.data = profile.data
            else:
                db_profile = CreatorProfileModel(name=profile.name, data=profile.data)
                session.add(db_profile)
            session.commit()
            return StepResult.ok(data={'message': 'Profile upserted successfully'})
        except Exception as e:
            session.rollback()
            logger.error(f'Failed to upsert creator profile: {e}')
            return StepResult.fail(f'Failed to upsert creator profile: {e!s}')

    def get_creator_profile(self, name: str) -> StepResult:
        """Get a creator profile by name."""
        try:
            session = self.get_session()
            db_profile = session.query(CreatorProfileModel).filter(CreatorProfileModel.name == name).first()
            if not db_profile:
                return StepResult.fail('Creator profile not found')
            profile = CreatorProfile(name=db_profile.name, data=db_profile.data)
            return StepResult.ok(data={'profile': profile})
        except Exception as e:
            logger.error(f'Failed to get creator profile: {e}')
            return StepResult.fail(f'Failed to get creator profile: {e!s}')

def create_store_manager(database_url: str) -> StepResult:
    """Create a unified store manager."""
    try:
        manager = UnifiedStoreManager(database_url)
        return StepResult.ok(data={'manager': manager})
    except Exception as e:
        logger.error(f'Failed to create store manager: {e}')
        return StepResult.fail(f'Failed to create store manager: {e!s}')

def migrate_sqlite_to_postgresql(sqlite_path: str, postgresql_url: str, store_type: str) -> StepResult:
    """Migrate data from SQLite to PostgreSQL."""
    try:
        try:
            parsed = urlparse(postgresql_url)
            host = parsed.hostname or 'unknown'
            port = f':{parsed.port}' if parsed.port else ''
            safe_target = f'{parsed.scheme or 'postgresql'}://{host}{port}'
        except Exception:
            safe_target = 'postgresql://<unparsed>'
        logger.info('Migration from %s to %s for %s would be implemented here', sqlite_path, safe_target, store_type)
        return StepResult.ok(data={'message': f'Migration placeholder for {store_type}'})
    except Exception as e:
        logger.error(f'Failed to migrate {store_type}: {e}')
        return StepResult.fail(f'Failed to migrate {store_type}: {e!s}')
__all__ = ['CreatorProfile', 'CrossProfileLink', 'Debate', 'DebateAgent', 'KGEdge', 'KGNode', 'MemoryItem', 'RetentionPolicy', 'StoreAdapter', 'UnifiedStoreManager', 'create_store_manager', 'migrate_sqlite_to_postgresql']