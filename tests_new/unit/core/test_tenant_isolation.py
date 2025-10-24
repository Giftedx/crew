"""Tests for tenant isolation across critical workflows."""

from unittest.mock import Mock, patch


class TestTenantIsolation:
    """Test tenant isolation in critical workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tenant1 = "tenant_1"
        self.tenant2 = "tenant_2"
        self.workspace1 = "workspace_1"
        self.workspace2 = "workspace_2"

    def test_memory_storage_tenant_isolation(self):
        """Test memory storage respects tenant boundaries."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool

        tool = MemoryStorageTool()

        with patch("ultimate_discord_intelligence_bot.tools.memory_storage_tool.get_qdrant_client") as mock_client:
            mock_client.return_value.upsert.return_value = Mock()

            # Store content for tenant 1
            result1 = tool._run("content for tenant 1", self.tenant1, self.workspace1)
            assert result1.success

            # Store content for tenant 2
            result2 = tool._run("content for tenant 2", self.tenant2, self.workspace2)
            assert result2.success

            # Verify different tenant contexts were used
            assert mock_client.return_value.upsert.call_count == 2
            calls = mock_client.return_value.upsert.call_args_list

            # Verify tenant isolation in storage calls
            tenant1_call = calls[0]
            tenant2_call = calls[1]

            assert self.tenant1 in str(tenant1_call)
            assert self.tenant2 in str(tenant2_call)
            assert tenant1_call != tenant2_call

    def test_memory_retrieval_tenant_isolation(self):
        """Test memory retrieval respects tenant boundaries."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool

        tool = MemoryStorageTool()

        with patch("ultimate_discord_intelligence_bot.tools.memory_storage_tool.get_qdrant_client") as mock_client:
            mock_client.return_value.search.return_value = Mock()

            # Search in tenant 1
            result1 = tool._run("query for tenant 1", self.tenant1, self.workspace1)
            assert result1.success

            # Search in tenant 2
            result2 = tool._run("query for tenant 2", self.tenant2, self.workspace2)
            assert result2.success

            # Verify different tenant contexts were used for search
            assert mock_client.return_value.search.call_count == 2
            calls = mock_client.return_value.search.call_args_list

            tenant1_call = calls[0]
            tenant2_call = calls[1]

            assert self.tenant1 in str(tenant1_call)
            assert self.tenant2 in str(tenant2_call)

    def test_fact_checking_tenant_isolation(self):
        """Test fact checking respects tenant boundaries."""
        from ultimate_discord_intelligence_bot.tools.fact_check_tool import FactCheckTool

        tool = FactCheckTool()

        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = {"results": []}

            # Fact check for tenant 1
            result1 = tool._run("claim for tenant 1", self.tenant1, self.workspace1)
            assert result1.success

            # Fact check for tenant 2
            result2 = tool._run("claim for tenant 2", self.tenant2, self.workspace2)
            assert result2.success

            # Both should succeed independently
            assert result1.success
            assert result2.success

    def test_workspace_isolation(self):
        """Test workspace isolation within same tenant."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool

        tool = MemoryStorageTool()

        with patch("ultimate_discord_intelligence_bot.tools.memory_storage_tool.get_qdrant_client") as mock_client:
            mock_client.return_value.upsert.return_value = Mock()

            # Store in workspace 1
            result1 = tool._run("content for workspace 1", self.tenant1, self.workspace1)
            assert result1.success

            # Store in workspace 2
            result2 = tool._run("content for workspace 2", self.tenant1, self.workspace2)
            assert result2.success

            # Verify different workspace contexts were used
            calls = mock_client.return_value.upsert.call_args_list
            workspace1_call = calls[0]
            workspace2_call = calls[1]

            assert self.workspace1 in str(workspace1_call)
            assert self.workspace2 in str(workspace2_call)

    def test_tenant_context_validation(self):
        """Test tenant context validation."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool

        tool = MemoryStorageTool()

        # Test with invalid tenant format
        result = tool._run("content", "invalid@tenant", self.workspace1)
        assert not result.success
        assert "Invalid tenant format" in result.error

    def test_workspace_context_validation(self):
        """Test workspace context validation."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool

        tool = MemoryStorageTool()

        # Test with invalid workspace format
        result = tool._run("content", self.tenant1, "invalid@workspace")
        assert not result.success
        assert "Invalid workspace format" in result.error

    def test_cross_tenant_data_leakage_prevention(self):
        """Test prevention of cross-tenant data leakage."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool

        tool = MemoryStorageTool()

        with patch("ultimate_discord_intelligence_bot.tools.memory_storage_tool.get_qdrant_client") as mock_client:
            mock_client.return_value.upsert.return_value = Mock()

            # Store data for tenant 1
            tool._run("sensitive data for tenant 1", self.tenant1, self.workspace1)

            # Attempt to access tenant 1 data from tenant 2 context
            result = tool._run("query", self.tenant2, self.workspace2)

            # Should not have access to tenant 1's data
            assert result.success
            # The search should be scoped to tenant 2 only
            search_call = mock_client.return_value.search.call_args
            assert self.tenant2 in str(search_call)
            assert self.tenant1 not in str(search_call)

    def test_tenant_namespace_generation(self):
        """Test proper tenant namespace generation."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool

        tool = MemoryStorageTool()

        with patch("ultimate_discord_intelligence_bot.tools.memory_storage_tool.get_qdrant_client") as mock_client:
            mock_client.return_value.upsert.return_value = Mock()

            result = tool._run("content", self.tenant1, self.workspace1)
            assert result.success

            # Verify namespace was properly constructed
            upsert_call = mock_client.return_value.upsert.call_args
            assert f"{self.tenant1}_{self.workspace1}" in str(upsert_call)

    def test_tenant_isolation_error_handling(self):
        """Test error handling maintains tenant isolation."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool

        tool = MemoryStorageTool()

        with patch("ultimate_discord_intelligence_bot.tools.memory_storage_tool.get_qdrant_client") as mock_client:
            mock_client.return_value.upsert.side_effect = Exception("Storage error")

            result = tool._run("content", self.tenant1, self.workspace1)
            assert not result.success

            # Error should be scoped to the specific tenant
            assert self.tenant1 in result.error or "tenant" in result.error.lower()

    def test_concurrent_tenant_operations(self):
        """Test concurrent operations across different tenants."""
        import threading

        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool

        tool = MemoryStorageTool()
        results = {}

        def store_for_tenant(tenant, workspace, content):
            with patch("ultimate_discord_intelligence_bot.tools.memory_storage_tool.get_qdrant_client") as mock_client:
                mock_client.return_value.upsert.return_value = Mock()
                result = tool._run(content, tenant, workspace)
                results[f"{tenant}_{workspace}"] = result

        # Simulate concurrent operations
        thread1 = threading.Thread(target=store_for_tenant, args=(self.tenant1, self.workspace1, "content1"))
        thread2 = threading.Thread(target=store_for_tenant, args=(self.tenant2, self.workspace2, "content2"))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Both operations should succeed independently
        assert results[f"{self.tenant1}_{self.workspace1}"].success
        assert results[f"{self.tenant2}_{self.workspace2}"].success
