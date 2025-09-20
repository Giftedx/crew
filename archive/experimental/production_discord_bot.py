"""
Production Discord Bot Integration - Advanced Contextual Bandits

This module provides production-ready integration between the Advanced Contextual Bandits system
and Discord bot infrastructure, enabling real-world AI routing with live traffic handling,
comprehensive performance benchmarking, and seamless fallback mechanisms.

Features:
- Real Discord bot integration with message handling
- Live traffic routing through advanced bandits system
- Production API integration with external AI services
- Comprehensive performance benchmarking and comparison
- Graceful fallback mechanisms for reliability
- Real-time metrics collection and monitoring
- A/B testing with actual user interactions
- Cost optimization and budget management
"""

import asyncio
import json
import logging
import os
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import aiohttp
import discord
from discord.ext import commands, tasks

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class APIEndpoint:
    """Configuration for AI API endpoints"""

    name: str
    base_url: str
    api_key: str
    model_name: str
    cost_per_1k_tokens: float
    max_tokens: int = 4096
    timeout_seconds: int = 30
    rate_limit_rpm: int = 60
    quality_score: float = 0.85
    avg_latency_ms: float = 2000


@dataclass
class RoutingDecision:
    """Record of a routing decision and its outcome"""

    user_id: str
    channel_id: str
    message_content: str
    selected_model: str
    algorithm: str
    confidence: float
    context_features: dict[str, float]
    timestamp: datetime
    response_time_ms: float
    response_length: int
    user_feedback: float | None = None
    cost_estimate: float = 0.0
    actual_cost: float = 0.0
    error: str | None = None


@dataclass
class PerformanceBenchmark:
    """Performance comparison between different routing strategies"""

    strategy_name: str
    total_requests: int
    avg_response_time: float
    avg_user_satisfaction: float
    total_cost: float
    success_rate: float
    avg_response_quality: float
    timestamp: datetime


class ProductionDiscordBot(commands.Bot):
    """Production Discord bot with advanced contextual bandits integration"""

    def __init__(self, config: dict[str, Any]):
        # Initialize Discord bot
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(command_prefix=config.get("command_prefix", "!"), intents=intents, help_command=None)

        self.config = config
        self.orchestrator = None
        self.autonomous_optimizer = None

        # API endpoints configuration
        self.api_endpoints = self._initialize_api_endpoints()

        # Performance tracking
        self.routing_decisions: list[RoutingDecision] = []
        self.performance_benchmarks: list[PerformanceBenchmark] = []

        # Rate limiting and cost tracking
        self.api_usage_tracker = {}
        self.cost_tracker = {"daily_cost": 0.0, "monthly_cost": 0.0}
        self.daily_budget_limit = config.get("daily_budget_limit", 100.0)

        # Fallback system
        self.fallback_enabled = True
        self.fallback_model = config.get("fallback_model", "simple_response")

        # A/B testing
        self.ab_testing_enabled = config.get("enable_ab_testing", True)
        self.baseline_strategy = config.get("baseline_strategy", "round_robin")

        logger.info("Production Discord Bot initialized")

    def _initialize_api_endpoints(self) -> dict[str, APIEndpoint]:
        """Initialize API endpoint configurations"""
        endpoints = {}

        # OpenAI GPT-4
        if self.config.get("openai_api_key"):
            endpoints["gpt-4-turbo"] = APIEndpoint(
                name="gpt-4-turbo",
                base_url="https://api.openai.com/v1",
                api_key=self.config["openai_api_key"],
                model_name="gpt-4-turbo",
                cost_per_1k_tokens=0.03,
                avg_latency_ms=2000,
                quality_score=0.95,
            )

        # Anthropic Claude
        if self.config.get("anthropic_api_key"):
            endpoints["claude-3.5-sonnet"] = APIEndpoint(
                name="claude-3.5-sonnet",
                base_url="https://api.anthropic.com",
                api_key=self.config["anthropic_api_key"],
                model_name="claude-3-5-sonnet-20241022",
                cost_per_1k_tokens=0.015,
                avg_latency_ms=1500,
                quality_score=0.92,
            )

        # Google Gemini
        if self.config.get("google_api_key"):
            endpoints["gemini-pro"] = APIEndpoint(
                name="gemini-pro",
                base_url="https://generativelanguage.googleapis.com/v1beta",
                api_key=self.config["google_api_key"],
                model_name="gemini-pro",
                cost_per_1k_tokens=0.0025,
                max_tokens=2048,
                avg_latency_ms=1000,
                quality_score=0.88,
            )

        # OpenRouter (for Llama and other models)
        if self.config.get("openrouter_api_key"):
            endpoints["llama-3.1-70b"] = APIEndpoint(
                name="llama-3.1-70b",
                base_url="https://openrouter.ai/api/v1",
                api_key=self.config["openrouter_api_key"],
                model_name="meta-llama/llama-3.1-70b-instruct",
                cost_per_1k_tokens=0.008,
                avg_latency_ms=3000,
                quality_score=0.85,
            )

        logger.info(f"Initialized {len(endpoints)} API endpoints")
        return endpoints

    async def setup_hook(self):
        """Initialize advanced bandits system when bot starts"""
        try:
            # Initialize advanced contextual bandits
            from src.ai import initialize_advanced_bandits

            self.orchestrator = await initialize_advanced_bandits(
                {"context_dimension": 8, "num_actions": len(self.api_endpoints), "default_algorithm": "doubly_robust"}
            )

            # Initialize autonomous optimizer
            from autonomous_performance_optimizer import create_autonomous_optimizer

            self.autonomous_optimizer = await create_autonomous_optimizer(
                self.orchestrator, self.config.get("optimization_config", {})
            )

            # Start background tasks
            self.performance_monitoring.start()
            self.cost_tracking.start()
            self.autonomous_optimization_cycle.start()

            logger.info("Advanced Contextual Bandits system initialized")

        except Exception as e:
            logger.error(f"Failed to initialize bandits system: {e}")
            self.fallback_enabled = True

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"{self.user} is connected to Discord!")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        logger.info(f"Advanced bandits enabled: {self.orchestrator is not None}")
        logger.info(f"Fallback enabled: {self.fallback_enabled}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle incoming messages with advanced routing"""
        # Ignore bot messages and commands
        if message.author.bot or message.content.startswith(self.command_prefix):
            return

        # Process with advanced bandits routing
        await self.process_intelligent_message(message)

    async def process_intelligent_message(self, message):
        """Process message using advanced contextual bandits routing"""
        start_time = time.time()

        try:
            # Extract context features
            context_features = await self.extract_context_features(message)

            # Decide routing strategy (A/B testing vs always advanced)
            use_advanced_routing = await self.should_use_advanced_routing(message)

            if use_advanced_routing and self.orchestrator:
                # Use advanced contextual bandits routing
                response, routing_info = await self.route_with_advanced_bandits(message, context_features)
            else:
                # Use baseline routing strategy
                response, routing_info = await self.route_with_baseline_strategy(message, context_features)

            # Send response
            if response:
                await message.channel.send(response[:2000])  # Discord message limit

            # Record routing decision
            response_time_ms = (time.time() - start_time) * 1000
            await self.record_routing_decision(message, routing_info, response, response_time_ms)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Fallback to simple response
            if self.fallback_enabled:
                fallback_response = await self.generate_fallback_response(message)
                await message.channel.send(fallback_response)

    async def extract_context_features(self, message) -> dict[str, float]:
        """Extract contextual features from Discord message"""
        # Message characteristics
        message_length = len(message.content)
        word_count = len(message.content.split())

        # Complexity heuristics
        question_marks = message.content.count("?")
        complex_words = sum(1 for word in message.content.split() if len(word) > 7)
        complexity = min(
            0.9,
            max(
                0.1,
                (message_length / 500) + (question_marks / 5) + (complex_words / word_count if word_count > 0 else 0),
            ),
        )

        # User characteristics
        user_id_hash = hash(str(message.author.id)) % 1000 / 1000.0

        # Channel characteristics
        channel_type_score = 0.5
        if hasattr(message.channel, "type"):
            if message.channel.type == discord.ChannelType.text:
                channel_type_score = 0.7
            elif message.channel.type == discord.ChannelType.private:
                channel_type_score = 0.9

        # Time-based features
        hour_of_day = datetime.now().hour / 24.0

        # Priority based on user roles/status
        priority = 0.5
        if hasattr(message.author, "premium_since") and message.author.premium_since:
            priority = 0.8
        elif hasattr(message.author, "roles"):
            for role in message.author.roles:
                if "admin" in role.name.lower() or "mod" in role.name.lower():
                    priority = 0.9
                    break

        return {
            "complexity": complexity,
            "priority": priority,
            "user_representation": user_id_hash,
            "channel_type": channel_type_score,
            "message_length_norm": min(1.0, message_length / 1000),
            "time_of_day": hour_of_day,
            "word_count_norm": min(1.0, word_count / 100),
            "question_indicator": min(1.0, question_marks / 3),
        }

    async def should_use_advanced_routing(self, message) -> bool:
        """Determine if advanced routing should be used (A/B testing)"""
        if not self.ab_testing_enabled:
            return True

        # Simple A/B split based on user ID
        user_hash = hash(str(message.author.id)) % 100
        return user_hash < 50  # 50% get advanced routing

    async def route_with_advanced_bandits(self, message, context_features) -> tuple[str, dict]:
        """Route message using advanced contextual bandits"""
        try:
            # Create bandit context
            from src.ai import create_bandit_context

            context = await create_bandit_context(
                user_id=str(message.author.id),
                domain="model_routing",
                complexity=context_features["complexity"],
                priority=context_features["priority"],
                **{k: v for k, v in context_features.items() if k not in ["complexity", "priority"]},
            )

            # Get routing decision
            action = await self.orchestrator.make_decision(context)

            # Map action to model
            model_mapping = {str(i): name for i, name in enumerate(self.api_endpoints.keys())}
            selected_model = model_mapping.get(action.action_id, list(self.api_endpoints.keys())[0])

            # Generate response using selected model
            response = await self.generate_ai_response(message.content, selected_model, context_features)

            routing_info = {
                "strategy": "advanced_bandits",
                "selected_model": selected_model,
                "algorithm": action.algorithm,
                "confidence": action.confidence,
                "action_id": action.action_id,
                "context": context,
                "action": action,
            }

            return response, routing_info

        except Exception as e:
            logger.error(f"Advanced routing failed: {e}")
            # Fallback to baseline
            return await self.route_with_baseline_strategy(message, context_features)

    async def route_with_baseline_strategy(self, message, context_features) -> tuple[str, dict]:
        """Route message using baseline strategy (round-robin or simple rules)"""
        try:
            if self.baseline_strategy == "round_robin":
                # Simple round-robin selection
                model_names = list(self.api_endpoints.keys())
                selected_model = model_names[len(self.routing_decisions) % len(model_names)]

            elif self.baseline_strategy == "complexity_based":
                # Simple rule-based routing
                complexity = context_features["complexity"]
                if complexity > 0.7:
                    selected_model = "gpt-4-turbo"  # High complexity -> best model
                elif complexity > 0.4:
                    selected_model = "claude-3.5-sonnet"  # Medium complexity
                else:
                    selected_model = "gemini-pro"  # Low complexity -> fastest/cheapest

            else:
                # Default to first available model
                selected_model = list(self.api_endpoints.keys())[0]

            # Generate response
            response = await self.generate_ai_response(message.content, selected_model, context_features)

            routing_info = {
                "strategy": f"baseline_{self.baseline_strategy}",
                "selected_model": selected_model,
                "algorithm": "baseline",
                "confidence": 0.5,
                "action_id": "baseline",
            }

            return response, routing_info

        except Exception as e:
            logger.error(f"Baseline routing failed: {e}")
            return await self.generate_fallback_response(message), {
                "strategy": "fallback",
                "selected_model": "fallback",
            }

    async def generate_ai_response(self, user_message: str, model_name: str, context_features: dict) -> str:
        """Generate AI response using specified model"""
        endpoint = self.api_endpoints.get(model_name)
        if not endpoint:
            raise ValueError(f"Unknown model: {model_name}")

        # Check rate limits and budget
        if not await self.check_rate_limits(model_name):
            raise Exception(f"Rate limit exceeded for {model_name}")

        if not await self.check_budget_limits(endpoint):
            raise Exception(f"Budget limit exceeded for {model_name}")

        # Generate response based on API type
        if endpoint.name.startswith("gpt"):
            return await self.call_openai_api(user_message, endpoint)
        elif endpoint.name.startswith("claude"):
            return await self.call_anthropic_api(user_message, endpoint)
        elif endpoint.name.startswith("gemini"):
            return await self.call_google_api(user_message, endpoint)
        elif endpoint.name.startswith("llama"):
            return await self.call_openrouter_api(user_message, endpoint)
        else:
            raise ValueError(f"Unsupported model type: {endpoint.name}")

    async def call_openai_api(self, message: str, endpoint: APIEndpoint) -> str:
        """Call OpenAI API"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {endpoint.api_key}", "Content-Type": "application/json"}

            payload = {
                "model": endpoint.model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant integrated with Discord."},
                    {"role": "user", "content": message},
                ],
                "max_tokens": min(endpoint.max_tokens, 500),  # Limit for Discord
                "temperature": 0.7,
            }

            async with session.post(
                f"{endpoint.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=endpoint.timeout_seconds),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]

                    # Track usage and cost
                    usage = data.get("usage", {})
                    await self.track_api_usage(endpoint.name, usage)

                    return content.strip()
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")

    async def call_anthropic_api(self, message: str, endpoint: APIEndpoint) -> str:
        """Call Anthropic Claude API"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": endpoint.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            }

            payload = {
                "model": endpoint.model_name,
                "max_tokens": min(endpoint.max_tokens, 500),
                "messages": [{"role": "user", "content": message}],
            }

            async with session.post(
                f"{endpoint.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=endpoint.timeout_seconds),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["content"][0]["text"]

                    # Track usage
                    usage = data.get("usage", {})
                    await self.track_api_usage(endpoint.name, usage)

                    return content.strip()
                else:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error {response.status}: {error_text}")

    async def call_google_api(self, message: str, endpoint: APIEndpoint) -> str:
        """Call Google Gemini API"""
        async with aiohttp.ClientSession() as session:
            url = f"{endpoint.base_url}/models/{endpoint.model_name}:generateContent"
            params = {"key": endpoint.api_key}

            payload = {
                "contents": [{"parts": [{"text": message}]}],
                "generationConfig": {"maxOutputTokens": min(endpoint.max_tokens, 500), "temperature": 0.7},
            }

            async with session.post(
                url, params=params, json=payload, timeout=aiohttp.ClientTimeout(total=endpoint.timeout_seconds)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]

                    # Track usage (simplified for Gemini)
                    await self.track_api_usage(endpoint.name, {"total_tokens": len(content.split())})

                    return content.strip()
                else:
                    error_text = await response.text()
                    raise Exception(f"Google API error {response.status}: {error_text}")

    async def call_openrouter_api(self, message: str, endpoint: APIEndpoint) -> str:
        """Call OpenRouter API (for Llama and others)"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {endpoint.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://discord-bot.example.com",
                "X-Title": "Discord Bot with Advanced Bandits",
            }

            payload = {
                "model": endpoint.model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": message},
                ],
                "max_tokens": min(endpoint.max_tokens, 500),
                "temperature": 0.7,
            }

            async with session.post(
                f"{endpoint.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=endpoint.timeout_seconds),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]

                    # Track usage
                    usage = data.get("usage", {})
                    await self.track_api_usage(endpoint.name, usage)

                    return content.strip()
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error {response.status}: {error_text}")

    async def generate_fallback_response(self, message) -> str:
        """Generate simple fallback response"""
        fallback_responses = [
            "I'm currently experiencing some technical difficulties. Please try again later.",
            "Sorry, I'm having trouble processing your request right now.",
            "I'm temporarily unable to provide a detailed response. Please try again in a moment.",
            "My advanced systems are currently offline. I'll be back to full capacity soon!",
            "I'm having some connectivity issues. Please bear with me!",
        ]

        # Simple hash-based selection for consistency
        response_index = hash(str(message.author.id) + message.content) % len(fallback_responses)
        return fallback_responses[response_index]

    async def check_rate_limits(self, model_name: str) -> bool:
        """Check if model is within rate limits"""
        current_time = time.time()
        minute_window = 60  # 1 minute

        if model_name not in self.api_usage_tracker:
            self.api_usage_tracker[model_name] = []

        # Remove old entries
        usage_times = self.api_usage_tracker[model_name]
        usage_times[:] = [t for t in usage_times if current_time - t < minute_window]

        # Check rate limit
        endpoint = self.api_endpoints[model_name]
        if len(usage_times) >= endpoint.rate_limit_rpm:
            logger.warning(f"Rate limit exceeded for {model_name}")
            return False

        # Record this usage
        usage_times.append(current_time)
        return True

    async def check_budget_limits(self, endpoint: APIEndpoint) -> bool:
        """Check if within budget limits"""
        if self.cost_tracker["daily_cost"] >= self.daily_budget_limit:
            logger.warning("Daily budget limit exceeded")
            return False
        return True

    async def track_api_usage(self, model_name: str, usage: dict):
        """Track API usage and costs"""
        endpoint = self.api_endpoints[model_name]

        # Calculate cost
        total_tokens = usage.get("total_tokens", usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0))
        cost = (total_tokens / 1000) * endpoint.cost_per_1k_tokens

        # Update cost tracking
        self.cost_tracker["daily_cost"] += cost
        self.cost_tracker["monthly_cost"] += cost

        logger.debug(f"API usage: {model_name}, tokens: {total_tokens}, cost: ${cost:.4f}")

    async def record_routing_decision(self, message, routing_info: dict, response: str, response_time_ms: float):
        """Record routing decision for analysis"""
        decision = RoutingDecision(
            user_id=str(message.author.id),
            channel_id=str(message.channel.id),
            message_content=message.content[:500],  # Truncate for storage
            selected_model=routing_info["selected_model"],
            algorithm=routing_info["algorithm"],
            confidence=routing_info.get("confidence", 0.0),
            context_features=routing_info.get("context_features", {}),
            timestamp=datetime.now(),
            response_time_ms=response_time_ms,
            response_length=len(response) if response else 0,
            cost_estimate=self.estimate_cost(routing_info["selected_model"], len(response)),
        )

        self.routing_decisions.append(decision)

        # Provide feedback to bandits system
        if (
            self.orchestrator
            and routing_info["strategy"] == "advanced_bandits"
            and "context" in routing_info
            and "action" in routing_info
        ):
            # Simple satisfaction estimate based on response characteristics
            satisfaction = self.estimate_user_satisfaction(message.content, response, response_time_ms)

            from src.ai import BanditFeedback

            feedback = BanditFeedback(
                context=routing_info["context"], action=routing_info["action"], reward=satisfaction
            )

            await self.orchestrator.provide_feedback(feedback)

    def estimate_cost(self, model_name: str, response_length: int) -> float:
        """Estimate cost for response"""
        endpoint = self.api_endpoints.get(model_name)
        if not endpoint:
            return 0.0

        # Rough token estimation (4 chars per token average)
        estimated_tokens = response_length / 4
        return (estimated_tokens / 1000) * endpoint.cost_per_1k_tokens

    def estimate_user_satisfaction(self, user_message: str, response: str, response_time_ms: float) -> float:
        """Estimate user satisfaction based on response characteristics"""
        base_satisfaction = 0.7

        # Response time penalty
        if response_time_ms > 5000:  # 5 seconds
            base_satisfaction -= 0.2
        elif response_time_ms > 2000:  # 2 seconds
            base_satisfaction -= 0.1

        # Response length consideration
        if len(response) < 10:
            base_satisfaction -= 0.2
        elif len(response) > 1000:
            base_satisfaction += 0.1

        # Question answering heuristic
        if "?" in user_message and len(response.split(".")) > 1:
            base_satisfaction += 0.1

        return max(0.1, min(1.0, base_satisfaction))

    @tasks.loop(minutes=5)
    async def performance_monitoring(self):
        """Monitor performance and generate benchmarks"""
        if len(self.routing_decisions) < 10:
            return

        try:
            # Generate performance benchmarks
            await self.generate_performance_benchmarks()

            # Clean old data
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.routing_decisions = [d for d in self.routing_decisions if d.timestamp > cutoff_time]

        except Exception as e:
            logger.error(f"Performance monitoring error: {e}")

    @tasks.loop(hours=1)
    async def cost_tracking(self):
        """Track and reset cost counters"""
        try:
            # Log current costs
            logger.info(
                f"Current costs: Daily: ${self.cost_tracker['daily_cost']:.2f}, "
                f"Monthly: ${self.cost_tracker['monthly_cost']:.2f}"
            )

            # Reset daily costs at midnight
            if datetime.now().hour == 0:
                self.cost_tracker["daily_cost"] = 0.0

            # Reset monthly costs on first day of month
            if datetime.now().day == 1 and datetime.now().hour == 0:
                self.cost_tracker["monthly_cost"] = 0.0

        except Exception as e:
            logger.error(f"Cost tracking error: {e}")

    @tasks.loop(minutes=30)
    async def autonomous_optimization_cycle(self):
        """Run autonomous optimization cycle"""
        if self.autonomous_optimizer and len(self.routing_decisions) > 50:
            try:
                await self.autonomous_optimizer._optimization_cycle()
                logger.info("Autonomous optimization cycle completed")
            except Exception as e:
                logger.error(f"Autonomous optimization error: {e}")

    async def generate_performance_benchmarks(self):
        """Generate performance benchmarks comparing strategies"""
        recent_decisions = [d for d in self.routing_decisions if d.timestamp > datetime.now() - timedelta(hours=1)]

        if len(recent_decisions) < 5:
            return

        # Group by strategy
        strategies = {}
        for decision in recent_decisions:
            strategy = "advanced_bandits" if decision.algorithm != "baseline" else "baseline"
            if strategy not in strategies:
                strategies[strategy] = []
            strategies[strategy].append(decision)

        # Generate benchmarks for each strategy
        for strategy_name, decisions in strategies.items():
            if len(decisions) < 3:
                continue

            benchmark = PerformanceBenchmark(
                strategy_name=strategy_name,
                total_requests=len(decisions),
                avg_response_time=statistics.mean(d.response_time_ms for d in decisions),
                avg_user_satisfaction=statistics.mean(
                    d.user_feedback or self.estimate_user_satisfaction(d.message_content, "", d.response_time_ms)
                    for d in decisions
                ),
                total_cost=sum(d.cost_estimate for d in decisions),
                success_rate=sum(1 for d in decisions if not d.error) / len(decisions),
                avg_response_quality=statistics.mean(min(1.0, d.response_length / 100) for d in decisions),
                timestamp=datetime.now(),
            )

            self.performance_benchmarks.append(benchmark)

    @commands.command(name="stats")
    async def show_stats(self, ctx):
        """Show bot performance statistics"""
        if not self.routing_decisions:
            await ctx.send("No routing decisions recorded yet.")
            return

        recent_decisions = [d for d in self.routing_decisions if d.timestamp > datetime.now() - timedelta(hours=24)]

        if not recent_decisions:
            await ctx.send("No recent routing decisions found.")
            return

        # Calculate statistics
        total_requests = len(recent_decisions)
        avg_response_time = statistics.mean(d.response_time_ms for d in recent_decisions)
        total_cost = sum(d.cost_estimate for d in recent_decisions)

        # Model usage
        model_usage = {}
        for decision in recent_decisions:
            model_usage[decision.selected_model] = model_usage.get(decision.selected_model, 0) + 1

        # Advanced vs baseline
        advanced_count = sum(1 for d in recent_decisions if d.algorithm != "baseline")
        baseline_count = total_requests - advanced_count

        stats_text = f"""📊 **Bot Performance Stats (Last 24h)**

🎯 **Requests**: {total_requests}
⚡ **Avg Response Time**: {avg_response_time:.1f}ms
💰 **Total Cost**: ${total_cost:.3f}

🤖 **Routing Strategy**:
• Advanced Bandits: {advanced_count} ({advanced_count / total_requests * 100:.1f}%)
• Baseline: {baseline_count} ({baseline_count / total_requests * 100:.1f}%)

🧠 **Model Usage**:
"""

        for model, count in sorted(model_usage.items(), key=lambda x: x[1], reverse=True):
            percentage = count / total_requests * 100
            stats_text += f"• {model}: {count} ({percentage:.1f}%)\n"

        await ctx.send(stats_text)

    @commands.command(name="benchmark")
    async def show_benchmark(self, ctx):
        """Show performance benchmark comparison"""
        if not self.performance_benchmarks:
            await ctx.send("No performance benchmarks available yet.")
            return

        recent_benchmarks = [
            b for b in self.performance_benchmarks if b.timestamp > datetime.now() - timedelta(hours=6)
        ]

        if not recent_benchmarks:
            await ctx.send("No recent benchmarks found.")
            return

        # Group by strategy
        strategy_benchmarks = {}
        for benchmark in recent_benchmarks:
            if benchmark.strategy_name not in strategy_benchmarks:
                strategy_benchmarks[benchmark.strategy_name] = []
            strategy_benchmarks[benchmark.strategy_name].append(benchmark)

        benchmark_text = "📈 **Performance Benchmark (Last 6h)**\n\n"

        for strategy, benchmarks in strategy_benchmarks.items():
            if not benchmarks:
                continue

            avg_satisfaction = statistics.mean(b.avg_user_satisfaction for b in benchmarks)
            avg_response_time = statistics.mean(b.avg_response_time for b in benchmarks)
            avg_cost = statistics.mean(b.total_cost for b in benchmarks)
            success_rate = statistics.mean(b.success_rate for b in benchmarks)

            benchmark_text += f"🎯 **{strategy.title()}**:\n"
            benchmark_text += f"• Satisfaction: {avg_satisfaction:.3f}\n"
            benchmark_text += f"• Response Time: {avg_response_time:.1f}ms\n"
            benchmark_text += f"• Cost: ${avg_cost:.4f}\n"
            benchmark_text += f"• Success Rate: {success_rate:.3f}\n\n"

        await ctx.send(benchmark_text)


async def create_production_bot(config_path: str = "production_bot_config.json") -> ProductionDiscordBot:
    """Create and configure production Discord bot"""
    # Load configuration
    try:
        with open(config_path) as f:
            config = json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found, using environment variables")
        config = {
            "discord_token": os.getenv("DISCORD_BOT_TOKEN"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
            "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
            "command_prefix": "!",
            "daily_budget_limit": 50.0,
            "enable_ab_testing": True,
            "baseline_strategy": "complexity_based",
        }

    # Create bot instance
    bot = ProductionDiscordBot(config)

    logger.info("Production Discord bot created and configured")
    return bot


async def main():
    """Main function to run the production bot"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("production_bot.log"), logging.StreamHandler()],
    )

    try:
        # Create bot
        bot = await create_production_bot()

        # Get Discord token
        discord_token = bot.config.get("discord_token")
        if not discord_token:
            logger.error("Discord token not found in config or environment")
            return

        # Run bot
        logger.info("Starting production Discord bot...")
        await bot.start(discord_token)

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
