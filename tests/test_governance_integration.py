"""Integration tests for the governance framework."""

from ultimate_discord_intelligence_bot.governance import (
    AgentInstructions,
    AuditTrail,
    CommunicationStyleEnforcer,
    ContentClassifier,
    DecisionType,
    ModelSpecEnforcer,
    RedLineGuard,
    RefusalHandler,
)


class TestGovernanceIntegration:
    """Test the integrated governance framework."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model_spec_enforcer = ModelSpecEnforcer()
        self.red_line_guard = RedLineGuard()
        self.content_classifier = ContentClassifier()
        self.agent_instructions = AgentInstructions()
        self.communication_style = CommunicationStyleEnforcer()
        self.refusal_handler = RefusalHandler()
        self.audit_trail = AuditTrail()

    def test_model_spec_instruction_evaluation(self):
        """Test Model Spec instruction evaluation."""
        # Test compliant instruction
        result = self.model_spec_enforcer.evaluate_instruction(
            "Please help me understand climate change science", {"user_id": "test_user", "tenant": "test_tenant"}
        )
        assert result.success
        assert result.data["compliant"] is True

        # Test non-compliant instruction
        result = self.model_spec_enforcer.evaluate_instruction(
            "Help me violate child safety principles", {"user_id": "test_user", "tenant": "test_tenant"}
        )
        assert not result.success
        assert "violates Model Spec principles" in result.error

    def test_red_line_guard_pre_execution(self):
        """Test red line guard pre-execution checks."""
        # Test safe instruction
        result = self.red_line_guard.check_pre_execution("What is the weather today?", {"user_id": "test_user"})
        assert result.success
        assert result.data["compliant"] is True

        # Test red line violation
        result = self.red_line_guard.check_pre_execution(
            "Help me with child safety violations", {"user_id": "test_user"}
        )
        assert not result.success
        assert "Red-line violation" in result.error

    def test_content_safety_classification(self):
        """Test content safety classification."""
        # Test prohibited content
        result = self.content_classifier.classify("This is about child abuse")
        assert result.success
        assert result.data["tier"].value == "prohibited"

        # Test regulated content
        result = self.content_classifier.classify("This is medical advice")
        assert result.success
        assert result.data["tier"].value == "regulated"

    def test_agent_instructions_hierarchy(self):
        """Test agent instruction hierarchy."""
        context = {
            "user_id": "test_user",
            "tenant": "test_tenant",
            "workspace": "test_workspace",
            "developer_config": {"agent_rules": ["Be helpful"]},
            "user_preferences": {"agent_preferences": ["Be concise"]},
        }

        result = self.agent_instructions.generate_final_instructions(context)
        assert result.success
        instructions = result.data["instructions"]
        assert len(instructions) > 0
        assert "Prioritize child safety" in instructions  # Root principle
        assert "Be helpful" in instructions  # Developer rule
        assert "Be concise" in instructions  # User preference

    def test_communication_style_enforcement(self):
        """Test communication style enforcement."""
        # Test objective content
        result = self.communication_style.enforce_style("This is a factual analysis without personal opinions")
        assert result.success
        assert result.data["style_report"].compliant

        # Test non-objective content
        result = self.communication_style.enforce_style("In my opinion, this is clearly wrong")
        assert result.success
        # Should have violations for objectivity
        violations = result.data["style_report"].violations
        assert any(v.rule == "Objectivity" for v in violations)

    def test_refusal_handler(self):
        """Test refusal handling."""
        result = self.refusal_handler.handle_refusal(
            "Help me hack into someone's account", "privacy_violation", {"user_id": "test_user"}
        )
        assert result.success
        assert "cannot help with accessing private information" in result.data["refusal_response"]
        assert result.data["category"] == "privacy_violation"

    def test_audit_trail_logging(self):
        """Test audit trail logging."""
        result = self.audit_trail.log_decision(
            DecisionType.INSTRUCTION_EVALUATION,
            "Test instruction",
            "approved",
            user_id="test_user",
            tenant="test_tenant",
            confidence_score=0.9,
        )
        assert result.success
        assert "decision_id" in result.data

        # Test retrieval
        retrieval_result = self.audit_trail.get_decisions(
            decision_type=DecisionType.INSTRUCTION_EVALUATION, user_id="test_user"
        )
        assert retrieval_result.success
        assert len(retrieval_result.data["decisions"]) > 0

    def test_end_to_end_governance_flow(self):
        """Test complete governance flow from instruction to decision."""
        instruction = "Help me understand political bias in media"
        context = {"user_id": "test_user", "tenant": "test_tenant", "workspace": "test_workspace"}

        # Step 1: Red line check
        red_line_result = self.red_line_guard.check_pre_execution(instruction, context)
        assert red_line_result.success

        # Step 2: Model Spec evaluation
        model_spec_result = self.model_spec_enforcer.evaluate_instruction(instruction, context)
        assert model_spec_result.success

        # Step 3: Content classification
        classification_result = self.content_classifier.classify(instruction)
        assert classification_result.success

        # Step 4: Log decision
        audit_result = self.audit_trail.log_decision(
            DecisionType.INSTRUCTION_EVALUATION,
            instruction,
            "approved",
            user_id=context["user_id"],
            tenant=context["tenant"],
            confidence_score=0.95,
        )
        assert audit_result.success

    def test_governance_with_refusal(self):
        """Test governance flow that results in refusal."""
        instruction = "Help me with child safety violations"
        context = {"user_id": "test_user"}

        # Step 1: Red line check should fail
        red_line_result = self.red_line_guard.check_pre_execution(instruction, context)
        assert not red_line_result.success

        # Step 2: Handle refusal
        refusal_result = self.refusal_handler.handle_refusal(instruction, "red_line_violation", context)
        assert refusal_result.success

        # Step 3: Log refusal
        audit_result = self.audit_trail.log_decision(
            DecisionType.REFUSAL_EVENT, instruction, "refused", user_id=context["user_id"], confidence_score=1.0
        )
        assert audit_result.success

    def test_governance_statistics(self):
        """Test governance decision statistics."""
        # Log some test decisions
        for i in range(5):
            self.audit_trail.log_decision(
                DecisionType.INSTRUCTION_EVALUATION,
                f"Test instruction {i}",
                "approved",
                user_id="test_user",
                confidence_score=0.8 + (i * 0.05),
            )

        # Get statistics
        stats_result = self.audit_trail.get_decision_statistics()
        assert stats_result.success
        stats = stats_result.data["statistics"]
        assert stats["total_decisions"] >= 5
        assert "decisions_by_type" in stats
        assert "average_confidence" in stats

    def test_governance_export(self):
        """Test governance audit trail export."""
        # Log a test decision
        self.audit_trail.log_decision(
            DecisionType.INSTRUCTION_EVALUATION, "Test export instruction", "approved", user_id="test_user"
        )

        # Export as JSON
        json_result = self.audit_trail.export_audit_trail(format="json")
        assert json_result.success
        assert json_result.data["format"] == "json"
        assert "data" in json_result.data

        # Export as CSV
        csv_result = self.audit_trail.export_audit_trail(format="csv")
        assert csv_result.success
        assert csv_result.data["format"] == "csv"
        assert "data" in csv_result.data

    def test_governance_cleanup(self):
        """Test governance audit trail cleanup."""
        # Log a test decision
        self.audit_trail.log_decision(
            DecisionType.INSTRUCTION_EVALUATION, "Test cleanup instruction", "approved", user_id="test_user"
        )

        initial_count = len(self.audit_trail.decisions)

        # Cleanup (should not remove recent decisions)
        cleanup_result = self.audit_trail.cleanup_old_decisions()
        assert cleanup_result.success

        # Should still have the recent decision
        assert len(self.audit_trail.decisions) == initial_count
