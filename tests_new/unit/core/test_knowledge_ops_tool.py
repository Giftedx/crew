from datetime import datetime

from src.ultimate_discord_intelligence_bot.tools.knowledge_ops_tool import (
    AuditLog,
    KnowledgeItem,
    KnowledgeOpsInput,
    KnowledgeOpsTool,
    SearchResult,
)


class TestKnowledgeOpsInput:
    """Test the KnowledgeOpsInput schema."""

    def test_valid_input(self):
        """Test valid input creation."""
        input_data = KnowledgeOpsInput(
            operation="search",
            query="Triller lawsuit",
            content_id="content_123",
            tags=["legal", "lawsuit"],
            annotations={"sentiment": "positive"},
            user_id="user_123",
            team_id="team_456",
            permissions=["read", "write"],
        )

        assert input_data.operation == "search"
        assert input_data.query == "Triller lawsuit"
        assert input_data.content_id == "content_123"
        assert input_data.tags == ["legal", "lawsuit"]
        assert input_data.annotations == {"sentiment": "positive"}
        assert input_data.user_id == "user_123"
        assert input_data.team_id == "team_456"
        assert input_data.permissions == ["read", "write"]

    def test_default_values(self):
        """Test default values."""
        input_data = KnowledgeOpsInput(operation="search", user_id="user_123")

        assert input_data.operation == "search"
        assert input_data.query == ""
        assert input_data.content_id == ""
        assert input_data.tags == []
        assert input_data.annotations == {}
        assert input_data.user_id == "user_123"
        assert input_data.team_id == ""
        assert input_data.permissions == ["read"]


class TestKnowledgeItem:
    """Test the KnowledgeItem dataclass."""

    def test_knowledge_item_creation(self):
        """Test creating a KnowledgeItem."""
        now = datetime.now()
        item = KnowledgeItem(
            item_id="item_001",
            content_type="episode",
            title="Test Episode",
            content="Test content",
            tags=["tag1", "tag2"],
            annotations={"key": "value"},
            created_by="user_123",
            created_at=now,
            modified_by="user_123",
            modified_at=now,
            team_id="team_456",
            permissions=["read", "write"],
            url="https://example.com",
            metadata={"duration": 3600},
        )

        assert item.item_id == "item_001"
        assert item.content_type == "episode"
        assert item.title == "Test Episode"
        assert item.content == "Test content"
        assert item.tags == ["tag1", "tag2"]
        assert item.annotations == {"key": "value"}
        assert item.created_by == "user_123"
        assert item.created_at == now
        assert item.modified_by == "user_123"
        assert item.modified_at == now
        assert item.team_id == "team_456"
        assert item.permissions == ["read", "write"]
        assert item.url == "https://example.com"
        assert item.metadata == {"duration": 3600}


class TestSearchResult:
    """Test the SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a SearchResult."""
        item = KnowledgeItem(
            item_id="item_001",
            content_type="episode",
            title="Test Episode",
            content="Test content",
            tags=[],
            annotations={},
            created_by="user_123",
            created_at=datetime.now(),
            modified_by="user_123",
            modified_at=datetime.now(),
            team_id="team_456",
            permissions=["read"],
        )

        result = SearchResult(
            item=item,
            relevance_score=0.85,
            matched_fields=["title", "content"],
            highlights={"title": "Test <mark>Episode</mark>"},
        )

        assert result.item == item
        assert result.relevance_score == 0.85
        assert result.matched_fields == ["title", "content"]
        assert result.highlights == {"title": "Test <mark>Episode</mark>"}


class TestAuditLog:
    """Test the AuditLog dataclass."""

    def test_audit_log_creation(self):
        """Test creating an AuditLog."""
        now = datetime.now()
        log = AuditLog(
            log_id="log_001",
            timestamp=now,
            user_id="user_123",
            team_id="team_456",
            operation="search",
            resource_id="resource_789",
            resource_type="knowledge_item",
            details={"query": "test query"},
            ip_address="127.0.0.1",
            user_agent="TestAgent/1.0",
        )

        assert log.log_id == "log_001"
        assert log.timestamp == now
        assert log.user_id == "user_123"
        assert log.team_id == "team_456"
        assert log.operation == "search"
        assert log.resource_id == "resource_789"
        assert log.resource_type == "knowledge_item"
        assert log.details == {"query": "test query"}
        assert log.ip_address == "127.0.0.1"
        assert log.user_agent == "TestAgent/1.0"


class TestKnowledgeOpsTool:
    """Test the KnowledgeOpsTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = KnowledgeOpsTool()
        self.tenant = "test_tenant"
        self.workspace = "test_workspace"
        self.user_id = "test_user"
        self.team_id = "test_team"

    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "knowledge_ops_tool"
        assert "Cross-team knowledge operations" in self.tool.description
        assert self.tool.args_schema == KnowledgeOpsInput
        assert isinstance(self.tool.audit_logs, list)
        assert isinstance(self.tool.user_permissions, dict)

    def test_check_permissions_admin(self):
        """Test permission checking for admin users."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["admin"])

        # Admin should have all permissions
        assert self.tool._check_permissions(self.user_id, self.team_id, ["read", "write", "delete"])
        assert self.tool._check_permissions(self.user_id, self.team_id, ["admin"])

    def test_check_permissions_regular_user(self):
        """Test permission checking for regular users."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["read", "write"])

        # Should have required permissions
        assert self.tool._check_permissions(self.user_id, self.team_id, ["read"])
        assert self.tool._check_permissions(self.user_id, self.team_id, ["read", "write"])

        # Should not have insufficient permissions
        assert not self.tool._check_permissions(self.user_id, self.team_id, ["delete"])
        assert not self.tool._check_permissions(self.user_id, self.team_id, ["admin"])

    def test_check_permissions_no_permissions(self):
        """Test permission checking for users with no permissions."""
        # User with no permissions should fail
        assert not self.tool._check_permissions("unknown_user", self.team_id, ["read"])

    def test_search_knowledge(self):
        """Test knowledge search functionality."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["read"])

        result = self.tool._search_knowledge("Triller lawsuit", self.team_id, self.user_id)

        assert result.success
        data = result.data["data"]
        assert data["operation"] == "search"
        assert data["query"] == "Triller lawsuit"
        assert "results" in data
        assert "total_results" in data
        assert "search_time_ms" in data
        assert len(data["results"]) >= 0

    def test_tag_content(self):
        """Test content tagging functionality."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["write"])

        result = self.tool._tag_content("content_123", ["legal", "lawsuit"], self.user_id, self.team_id)

        assert result.success
        data = result.data["data"]
        assert data["operation"] == "tag"
        assert data["content_id"] == "content_123"
        assert "legal" in data["tags_added"]
        assert "lawsuit" in data["tags_added"]
        assert data["user_id"] == self.user_id
        assert data["team_id"] == self.team_id

    def test_annotate_content(self):
        """Test content annotation functionality."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["write"])

        annotations = {"sentiment": "positive", "confidence": 0.85}
        result = self.tool._annotate_content("content_123", annotations, self.user_id, self.team_id)

        assert result.success
        data = result.data["data"]
        assert data["operation"] == "annotate"
        assert data["content_id"] == "content_123"
        assert data["annotations_added"] == annotations
        assert data["user_id"] == self.user_id
        assert data["team_id"] == self.team_id

    def test_share_content(self):
        """Test content sharing functionality."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["write"])

        result = self.tool._share_content("content_123", self.team_id, self.user_id)

        assert result.success
        data = result.data["data"]
        assert data["operation"] == "share"
        assert data["content_id"] == "content_123"
        assert data["team_id"] == self.team_id
        assert data["shared_by"] == self.user_id
        assert "shared_with" in data

    def test_get_audit_logs(self):
        """Test audit log retrieval."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["read"])

        result = self.tool._get_audit_logs(self.team_id, self.user_id)

        assert result.success
        data = result.data["data"]
        assert data["operation"] == "audit"
        assert data["team_id"] == self.team_id
        assert data["requested_by"] == self.user_id
        assert "logs" in data
        assert "total_logs" in data

    def test_run_search_operation(self):
        """Test running search operation."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["read"])

        result = self.tool._run(
            operation="search",
            user_id=self.user_id,
            query="Triller lawsuit",
            team_id=self.team_id,
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        data = result.data["data"]
        assert data["operation"] == "search"
        assert data["query"] == "Triller lawsuit"

    def test_run_tag_operation(self):
        """Test running tag operation."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["write"])

        result = self.tool._run(
            operation="tag",
            user_id=self.user_id,
            content_id="content_123",
            tags=["legal", "lawsuit"],
            team_id=self.team_id,
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        data = result.data["data"]
        assert data["operation"] == "tag"
        assert data["content_id"] == "content_123"

    def test_run_annotate_operation(self):
        """Test running annotate operation."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["write"])

        annotations = {"sentiment": "positive"}
        result = self.tool._run(
            operation="annotate",
            user_id=self.user_id,
            content_id="content_123",
            annotations=annotations,
            team_id=self.team_id,
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        data = result.data["data"]
        assert data["operation"] == "annotate"
        assert data["content_id"] == "content_123"

    def test_run_share_operation(self):
        """Test running share operation."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["write"])

        result = self.tool._run(
            operation="share",
            user_id=self.user_id,
            content_id="content_123",
            team_id=self.team_id,
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        data = result.data["data"]
        assert data["operation"] == "share"
        assert data["content_id"] == "content_123"

    def test_run_audit_operation(self):
        """Test running audit operation."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["read"])

        result = self.tool._run(
            operation="audit",
            user_id=self.user_id,
            team_id=self.team_id,
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        data = result.data["data"]
        assert data["operation"] == "audit"
        assert data["team_id"] == self.team_id

    def test_run_insufficient_permissions(self):
        """Test running operation with insufficient permissions."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["read"])  # Only read permission

        result = self.tool._run(
            operation="tag",  # Requires write permission
            user_id=self.user_id,
            content_id="content_123",
            tags=["legal"],
            team_id=self.team_id,
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert not result.success
        assert "Insufficient permissions" in result.error

    def test_run_unknown_operation(self):
        """Test running unknown operation."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["admin"])  # Give admin permissions

        result = self.tool._run(
            operation="unknown_operation",
            user_id=self.user_id,
            team_id=self.team_id,  # Add team_id parameter
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert not result.success
        assert "Unknown operation" in result.error

    def test_audit_logging(self):
        """Test that operations are logged for audit."""
        self.tool.set_user_permissions(self.user_id, self.team_id, ["read"])

        initial_log_count = len(self.tool.audit_logs)

        result = self.tool._run(
            operation="search",
            user_id=self.user_id,
            query="test query",
            team_id=self.team_id,
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        assert len(self.tool.audit_logs) == initial_log_count + 1

        # Check the log entry
        log_entry = self.tool.audit_logs[-1]
        assert log_entry.user_id == self.user_id
        assert log_entry.team_id == self.team_id
        assert log_entry.operation == "search"
        assert log_entry.resource_id == "test query"
        assert log_entry.details["success"] is True

    def test_serialize_search_result(self):
        """Test search result serialization."""
        item = KnowledgeItem(
            item_id="item_001",
            content_type="episode",
            title="Test Episode",
            content="Test content",
            tags=["tag1"],
            annotations={"key": "value"},
            created_by="user_123",
            created_at=datetime.now(),
            modified_by="user_123",
            modified_at=datetime.now(),
            team_id="team_456",
            permissions=["read"],
        )

        search_result = SearchResult(
            item=item,
            relevance_score=0.85,
            matched_fields=["title"],
            highlights={"title": "Test <mark>Episode</mark>"},
        )

        serialized = self.tool._serialize_search_result(search_result)

        assert serialized["relevance_score"] == 0.85
        assert serialized["matched_fields"] == ["title"]
        assert serialized["highlights"] == {"title": "Test <mark>Episode</mark>"}
        assert "item" in serialized
        assert serialized["item"]["item_id"] == "item_001"

    def test_serialize_audit_log(self):
        """Test audit log serialization."""
        now = datetime.now()
        log = AuditLog(
            log_id="log_001",
            timestamp=now,
            user_id="user_123",
            team_id="team_456",
            operation="search",
            resource_id="resource_789",
            resource_type="knowledge_item",
            details={"query": "test"},
        )

        serialized = self.tool._serialize_audit_log(log)

        assert serialized["log_id"] == "log_001"
        assert serialized["timestamp"] == now.isoformat()
        assert serialized["user_id"] == "user_123"
        assert serialized["team_id"] == "team_456"
        assert serialized["operation"] == "search"
        assert serialized["resource_id"] == "resource_789"
        assert serialized["resource_type"] == "knowledge_item"
        assert serialized["details"] == {"query": "test"}

    def test_set_user_permissions(self):
        """Test setting user permissions."""
        self.tool.set_user_permissions("user_123", "team_456", ["read", "write"])

        assert "user_123" in self.tool.user_permissions
        assert "team_456" in self.tool.user_permissions["user_123"]
        assert self.tool.user_permissions["user_123"]["team_456"] == ["read", "write"]
