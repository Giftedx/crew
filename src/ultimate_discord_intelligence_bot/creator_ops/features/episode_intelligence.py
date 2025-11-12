"""
Episode Intelligence Pack for generating structured show notes and analysis.
Provides comprehensive episode analysis including agenda, guests, claims, quotations, and risk assessment.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.features.intelligence_models import (
    AgendaItem,
    BrandSafetyAnalysis,
    ClaimStatus,
    DefamationRisk,
    EpisodeIntelligence,
    FactCheckableClaim,
    GuestInfo,
    IntelligenceConfig,
    IntelligenceResult,
    NotableQuotation,
    OutboundLink,
    RiskLevel,
    ThumbnailSuggestion,
)
from ultimate_discord_intelligence_bot.creator_ops.knowledge.api import KnowledgeAPI
from ultimate_discord_intelligence_bot.creator_ops.media import NLPPipeline, NLPResult
from ultimate_discord_intelligence_bot.creator_ops.media.alignment import AlignedSegment, AlignedTranscript
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class EpisodeIntelligencePack:
    """Main class for generating episode intelligence packs."""

    def __init__(self, config: CreatorOpsConfig, knowledge_api: KnowledgeAPI):
        self.config = config
        self.knowledge_api = knowledge_api
        self.nlp_pipeline = NLPPipeline(config)
        self.output_dir = Path("outputs/intelligence_packs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_intelligence_pack(
        self,
        episode_id: str,
        transcript: AlignedTranscript,
        nlp_result: NLPResult | None = None,
        intelligence_config: IntelligenceConfig | None = None,
    ) -> StepResult:
        """
        Generate a comprehensive intelligence pack for an episode.

        Args:
            episode_id: Unique identifier for the episode
            transcript: Aligned transcript with speaker diarization
            nlp_result: Optional pre-computed NLP analysis
            intelligence_config: Configuration for intelligence generation

        Returns:
            StepResult with intelligence pack details
        """
        try:
            if not intelligence_config:
                intelligence_config = IntelligenceConfig()
            start_time = datetime.now()
            logger.info(f"Starting intelligence pack generation for episode {episode_id}")
            intelligence = EpisodeIntelligence(
                episode_id=episode_id,
                episode_title=transcript.metadata.get("title", "Untitled Episode"),
                episode_duration=transcript.duration,
                created_at=start_time,
                updated_at=start_time,
                total_speakers=len({segment.speakers[0] for segment in transcript.segments if segment.speakers}),
                total_segments=len(transcript.segments),
            )
            if intelligence_config.include_agenda:
                agenda_result = await self._generate_agenda(transcript, intelligence_config)
                if agenda_result.success:
                    intelligence.agenda = agenda_result.data["agenda"]
            if intelligence_config.include_guests:
                guests_result = await self._generate_guest_info(transcript)
                if guests_result.success:
                    intelligence.guests = guests_result.data["guests"]
            if intelligence_config.include_claims:
                claims_result = await self._generate_claims(transcript, nlp_result, intelligence_config)
                if claims_result.success:
                    intelligence.claims = claims_result.data["claims"]
            if intelligence_config.include_quotations:
                quotations_result = await self._generate_quotations(transcript, intelligence_config)
                if quotations_result.success:
                    intelligence.quotations = quotations_result.data["quotations"]
            if intelligence_config.include_links:
                links_result = await self._generate_links(transcript)
                if links_result.success:
                    intelligence.links = links_result.data["links"]
            if intelligence_config.include_thumbnails:
                thumbnails_result = await self._generate_thumbnail_suggestions(transcript, intelligence_config)
                if thumbnails_result.success:
                    intelligence.thumbnail_suggestions = thumbnails_result.data["thumbnails"]
            if intelligence_config.include_brand_safety:
                brand_safety_result = await self._generate_brand_safety_analysis(transcript, nlp_result)
                if brand_safety_result.success:
                    intelligence.brand_safety = brand_safety_result.data["brand_safety"]
            if intelligence_config.include_defamation_risk:
                defamation_result = await self._generate_defamation_risk(
                    transcript, intelligence.claims, intelligence_config
                )
                if defamation_result.success:
                    intelligence.defamation_risk = defamation_result.data["defamation_risk"]
            insights_result = await self._generate_key_insights(intelligence)
            if insights_result.success:
                intelligence.key_insights = insights_result.data["insights"]
            intelligence.average_sentiment = self._calculate_average_sentiment(transcript)
            intelligence.top_topics = self._extract_top_topics(transcript)
            intelligence.updated_at = datetime.now()
            export_result = await self._export_intelligence_pack(intelligence, intelligence_config)
            if export_result.success:
                intelligence.export_formats = list(export_result.data["formats"])
                intelligence.file_paths = export_result.data["file_paths"]
            processing_time = (datetime.now() - start_time).total_seconds()
            result = IntelligenceResult(
                episode_id=episode_id,
                success=True,
                intelligence_pack=intelligence,
                processing_time=processing_time,
                metadata={
                    "agenda_items": len(intelligence.agenda),
                    "guests": len(intelligence.guests),
                    "claims": len(intelligence.claims),
                    "quotations": len(intelligence.quotations),
                    "links": len(intelligence.links),
                    "thumbnail_suggestions": len(intelligence.thumbnail_suggestions),
                    "export_formats": intelligence.export_formats,
                },
            )
            logger.info(f"Intelligence pack generation completed for episode {episode_id} in {processing_time:.2f}s")
            return StepResult.ok(data={"result": result})
        except Exception as e:
            logger.error(f"Intelligence pack generation failed: {e!s}")
            return StepResult.fail(f"Intelligence pack generation failed: {e!s}")

    async def _generate_agenda(self, transcript: AlignedTranscript, config: IntelligenceConfig) -> StepResult:
        """Generate agenda items from transcript segments."""
        try:
            agenda_items = []
            current_topic = None
            current_start_time = None
            current_speakers = set()
            current_topics = set()
            for segment in transcript.segments:
                segment_topics = segment.topics or []
                if not current_topic or not any(topic in current_topics for topic in segment_topics):
                    if current_topic and current_start_time is not None:
                        agenda_item = AgendaItem(
                            title=current_topic,
                            start_time=current_start_time,
                            end_time=segment.start_time,
                            duration=segment.start_time - current_start_time,
                            description=f"Discussion about {current_topic}",
                            speakers=list(current_speakers),
                            topics=list(current_topics),
                        )
                        agenda_items.append(agenda_item)
                    current_topic = segment_topics[0] if segment_topics else f"Segment {len(agenda_items) + 1}"
                    current_start_time = segment.start_time
                    current_speakers = set(segment.speakers)
                    current_topics = set(segment_topics)
                else:
                    current_speakers.update(segment.speakers)
                    current_topics.update(segment_topics)
            if current_topic and current_start_time is not None:
                final_segment = transcript.segments[-1] if transcript.segments else None
                end_time = final_segment.end_time if final_segment else transcript.duration
                agenda_item = AgendaItem(
                    title=current_topic,
                    start_time=current_start_time,
                    end_time=end_time,
                    duration=end_time - current_start_time,
                    description=f"Discussion about {current_topic}",
                    speakers=list(current_speakers),
                    topics=list(current_topics),
                )
                agenda_items.append(agenda_item)
            if len(agenda_items) > config.max_agenda_items:
                agenda_items = agenda_items[: config.max_agenda_items]
            return StepResult.ok(data={"agenda": agenda_items})
        except Exception as e:
            logger.error(f"Failed to generate agenda: {e!s}")
            return StepResult.fail(f"Failed to generate agenda: {e!s}")

    async def _generate_guest_info(self, transcript: AlignedTranscript) -> StepResult:
        """Generate guest information from transcript."""
        try:
            guests = []
            speaker_stats = {}
            for segment in transcript.segments:
                for speaker in segment.speakers:
                    if speaker not in speaker_stats:
                        speaker_stats[speaker] = {
                            "total_time": 0,
                            "segments": 0,
                            "first_mentioned": segment.start_time,
                            "contributions": [],
                        }
                    speaker_stats[speaker]["total_time"] += segment.end_time - segment.start_time
                    speaker_stats[speaker]["segments"] += 1
                    if len(segment.text) > 50:
                        speaker_stats[speaker]["contributions"].append(segment.text)
            for speaker, stats in speaker_stats.items():
                total_time = sum(s["total_time"] for s in speaker_stats.values())
                speaking_percentage = stats["total_time"] / total_time if total_time > 0 else 0
                if speaking_percentage > 0.4:
                    role = "Host"
                elif speaking_percentage > 0.2:
                    role = "Co-host"
                elif speaking_percentage > 0.1:
                    role = "Guest"
                else:
                    role = "Participant"
                guest = GuestInfo(
                    name=speaker,
                    role=role,
                    bio=f"{role} with {stats['segments']} speaking segments",
                    first_mentioned=stats["first_mentioned"],
                    total_speaking_time=stats["total_time"],
                    segments=stats["segments"],
                    key_contributions=stats["contributions"][:5],
                    expertise_areas=self._extract_expertise_areas(stats["contributions"]),
                )
                guests.append(guest)
            return StepResult.ok(data={"guests": guests})
        except Exception as e:
            logger.error(f"Failed to generate guest info: {e!s}")
            return StepResult.fail(f"Failed to generate guest info: {e!s}")

    async def _generate_claims(
        self, transcript: AlignedTranscript, nlp_result: NLPResult | None, config: IntelligenceConfig
    ) -> StepResult:
        """Generate fact-checkable claims from transcript."""
        try:
            claims = []
            claim_id = 0
            claim_indicators = [
                "according to",
                "studies show",
                "research indicates",
                "statistics show",
                "data reveals",
                "experts say",
                "scientists found",
                "it's been proven",
                "the truth is",
                "actually",
                "in fact",
                "the reality is",
            ]
            for segment in transcript.segments:
                text_lower = segment.text.lower()
                if any(indicator in text_lower for indicator in claim_indicators):
                    claim_type = self._determine_claim_type(segment.text)
                    confidence = self._calculate_claim_confidence(segment.text, claim_type)
                    if confidence >= config.min_claim_confidence:
                        claim = FactCheckableClaim(
                            claim_id=f"claim_{claim_id}",
                            text=segment.text,
                            speaker=segment.speakers[0] if segment.speakers else "Unknown",
                            timestamp=segment.start_time,
                            context=f"Segment at {segment.start_time:.1f}s",
                            claim_type=claim_type,
                            status=ClaimStatus.UNVERIFIED,
                            confidence=confidence,
                            sources_mentioned=self._extract_sources(segment.text),
                            verification_notes="Requires manual verification",
                        )
                        claims.append(claim)
                        claim_id += 1
            return StepResult.ok(data={"claims": claims})
        except Exception as e:
            logger.error(f"Failed to generate claims: {e!s}")
            return StepResult.fail(f"Failed to generate claims: {e!s}")

    async def _generate_quotations(self, transcript: AlignedTranscript, config: IntelligenceConfig) -> StepResult:
        """Generate notable quotations from transcript."""
        try:
            quotations = []
            quote_id = 0
            quotation_indicators = [
                "quote",
                "saying",
                "proverb",
                "wise words",
                "insight",
                "perspective",
                "opinion",
                "belief",
                "philosophy",
            ]
            for segment in transcript.segments:
                text = segment.text.strip()
                if len(text) >= config.min_quotation_length:
                    text_lower = text.lower()
                    has_indicators = any(indicator in text_lower for indicator in quotation_indicators)
                    significance = self._calculate_quotation_significance(text)
                    viral_potential = self._calculate_viral_potential(text)
                    if has_indicators or significance > 0.5 or viral_potential > 0.5:
                        quotation = NotableQuotation(
                            quote_id=f"quote_{quote_id}",
                            text=text,
                            speaker=segment.speakers[0] if segment.speakers else "Unknown",
                            timestamp=segment.start_time,
                            context=f"Segment at {segment.start_time:.1f}s",
                            significance=f"Significance score: {significance:.2f}",
                            topics=segment.topics or [],
                            sentiment=segment.sentiment_score or 0.0,
                            viral_potential=viral_potential,
                        )
                        quotations.append(quotation)
                        quote_id += 1
            return StepResult.ok(data={"quotations": quotations})
        except Exception as e:
            logger.error(f"Failed to generate quotations: {e!s}")
            return StepResult.fail(f"Failed to generate quotations: {e!s}")

    async def _generate_links(self, transcript: AlignedTranscript) -> StepResult:
        """Generate outbound links mentioned in transcript."""
        try:
            links = []
            url_pattern = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\\\(\\\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
            for segment in transcript.segments:
                urls = re.findall(url_pattern, segment.text)
                for url in urls:
                    link = OutboundLink(
                        url=url,
                        title=self._extract_link_title(url),
                        description=f"Link mentioned by {(segment.speakers[0] if segment.speakers else 'Unknown')}",
                        mentioned_by=segment.speakers[0] if segment.speakers else "Unknown",
                        timestamp=segment.start_time,
                        context=segment.text,
                        link_type=self._determine_link_type(url),
                        domain=self._extract_domain(url),
                        is_affiliate=self._is_affiliate_link(url),
                        is_sponsored=self._is_sponsored_link(url),
                    )
                    links.append(link)
            return StepResult.ok(data={"links": links})
        except Exception as e:
            logger.error(f"Failed to generate links: {e!s}")
            return StepResult.fail(f"Failed to generate links: {e!s}")

    async def _generate_thumbnail_suggestions(
        self, transcript: AlignedTranscript, config: IntelligenceConfig
    ) -> StepResult:
        """Generate thumbnail suggestions based on high-engagement moments."""
        try:
            thumbnails = []
            engagement_scores = []
            for segment in transcript.segments:
                score = self._calculate_engagement_score(segment)
                engagement_scores.append((segment.start_time, score))
            engagement_scores.sort(key=lambda x: x[1], reverse=True)
            for i, (timestamp, score) in enumerate(engagement_scores[: config.max_thumbnail_suggestions]):
                thumbnail = ThumbnailSuggestion(
                    timestamp=timestamp,
                    frame_url=f"frame_at_{timestamp:.1f}s.jpg",
                    description=f"High-engagement moment at {timestamp:.1f}s",
                    engagement_score=score,
                    visual_elements=["speaker", "text_overlay"],
                    text_overlay=self._generate_thumbnail_text(transcript, timestamp),
                    recommended=i == 0,
                )
                thumbnails.append(thumbnail)
            return StepResult.ok(data={"thumbnails": thumbnails})
        except Exception as e:
            logger.error(f"Failed to generate thumbnail suggestions: {e!s}")
            return StepResult.fail(f"Failed to generate thumbnail suggestions: {e!s}")

    async def _generate_brand_safety_analysis(
        self, transcript: AlignedTranscript, nlp_result: NLPResult | None
    ) -> StepResult:
        """Generate brand safety analysis."""
        try:
            toxicity_score = 0.0
            controversy_score = 0.0
            flagged_segments = []
            content_warnings = []
            brand_mentions = []
            for segment in transcript.segments:
                segment_toxicity = segment.sentiment_score or 0.0
                if segment_toxicity < -0.5:
                    toxicity_score += abs(segment_toxicity)
                    flagged_segments.append(
                        {
                            "timestamp": segment.start_time,
                            "text": segment.text,
                            "reason": "negative_sentiment",
                            "score": abs(segment_toxicity),
                        }
                    )
                if segment.topics:
                    for topic in segment.topics:
                        if self._is_controversial_topic(topic):
                            controversy_score += 0.3
                            content_warnings.append(f"Controversial topic: {topic}")
            total_segments = len(transcript.segments)
            if total_segments > 0:
                toxicity_score /= total_segments
                controversy_score /= total_segments
            overall_score = 5.0 - toxicity_score * 2 - controversy_score * 2
            overall_score = max(1.0, min(5.0, overall_score))
            if overall_score >= 4.0:
                advertiser_friendliness = "safe"
            elif overall_score >= 3.0:
                advertiser_friendliness = "caution"
            else:
                advertiser_friendliness = "unsafe"
            brand_safety = BrandSafetyAnalysis(
                overall_score=overall_score,
                toxicity_score=toxicity_score,
                controversy_score=controversy_score,
                advertiser_friendliness=advertiser_friendliness,
                flagged_segments=flagged_segments,
                content_warnings=content_warnings,
                brand_mentions=brand_mentions,
            )
            return StepResult.ok(data={"brand_safety": brand_safety})
        except Exception as e:
            logger.error(f"Failed to generate brand safety analysis: {e!s}")
            return StepResult.fail(f"Failed to generate brand safety analysis: {e!s}")

    async def _generate_defamation_risk(
        self, transcript: AlignedTranscript, claims: list[FactCheckableClaim], config: IntelligenceConfig
    ) -> StepResult:
        """Generate defamation risk assessment."""
        try:
            risk_score = 0.0
            flagged_statements = []
            individuals_mentioned = []
            organizations_mentioned = []
            unverified_claims = []
            recommendations = []
            for claim in claims:
                if claim.status == ClaimStatus.UNVERIFIED:
                    unverified_claims.append(claim)
                    if self._mentions_individual(claim.text):
                        risk_score += 0.3
                        individuals_mentioned.extend(self._extract_individuals(claim.text))
                        flagged_statements.append(
                            {
                                "timestamp": claim.timestamp,
                                "text": claim.text,
                                "reason": "unverified_claim_about_individual",
                                "risk": "medium",
                            }
                        )
                    if self._mentions_organization(claim.text):
                        risk_score += 0.2
                        organizations_mentioned.extend(self._extract_organizations(claim.text))
                        flagged_statements.append(
                            {
                                "timestamp": claim.timestamp,
                                "text": claim.text,
                                "reason": "unverified_claim_about_organization",
                                "risk": "medium",
                            }
                        )
            risk_score = min(1.0, risk_score)
            if risk_score >= config.defamation_threshold:
                risk_level = RiskLevel.HIGH
                recommendations.append("Review all unverified claims about individuals and organizations")
                recommendations.append("Consider adding disclaimers for controversial statements")
            elif risk_score >= 0.5:
                risk_level = RiskLevel.MEDIUM
                recommendations.append("Verify claims about individuals and organizations")
            else:
                risk_level = RiskLevel.LOW
                recommendations.append("Continue monitoring for defamation risks")
            defamation_risk = DefamationRisk(
                risk_level=risk_level,
                risk_score=risk_score,
                flagged_statements=flagged_statements,
                individuals_mentioned=list(set(individuals_mentioned)),
                organizations_mentioned=list(set(organizations_mentioned)),
                unverified_claims=unverified_claims,
                recommendations=recommendations,
            )
            return StepResult.ok(data={"defamation_risk": defamation_risk})
        except Exception as e:
            logger.error(f"Failed to generate defamation risk assessment: {e!s}")
            return StepResult.fail(f"Failed to generate defamation risk assessment: {e!s}")

    async def _generate_key_insights(self, intelligence: EpisodeIntelligence) -> StepResult:
        """Generate key insights from the intelligence pack."""
        try:
            insights = []
            if intelligence.episode_duration > 3600:
                insights.append("Long-form episode with extensive content coverage")
            elif intelligence.episode_duration > 1800:
                insights.append("Medium-length episode with good content depth")
            else:
                insights.append("Short-form episode with focused content")
            if len(intelligence.guests) > 3:
                insights.append("Multi-participant discussion with diverse perspectives")
            elif len(intelligence.guests) == 2:
                insights.append("Intimate conversation between two participants")
            else:
                insights.append("Solo presentation or monologue format")
            if len(intelligence.claims) > 10:
                insights.append("Fact-heavy episode with many verifiable claims")
            elif len(intelligence.claims) > 5:
                insights.append("Moderate number of fact-checkable claims")
            else:
                insights.append("Opinion-focused episode with few verifiable facts")
            if intelligence.brand_safety:
                if intelligence.brand_safety.overall_score >= 4.0:
                    insights.append("Advertiser-friendly content with high brand safety score")
                elif intelligence.brand_safety.overall_score >= 3.0:
                    insights.append("Moderate brand safety with some caution areas")
                else:
                    insights.append("Content may not be suitable for all advertisers")
            if intelligence.defamation_risk:
                if intelligence.defamation_risk.risk_level == RiskLevel.HIGH:
                    insights.append("High defamation risk - review unverified claims")
                elif intelligence.defamation_risk.risk_level == RiskLevel.MEDIUM:
                    insights.append("Moderate defamation risk - verify key claims")
                else:
                    insights.append("Low defamation risk - content appears safe")
            return StepResult.ok(data={"insights": insights})
        except Exception as e:
            logger.error(f"Failed to generate key insights: {e!s}")
            return StepResult.fail(f"Failed to generate key insights: {e!s}")

    def _calculate_average_sentiment(self, transcript: AlignedTranscript) -> float:
        """Calculate average sentiment across all segments."""
        sentiments = [segment.sentiment_score for segment in transcript.segments if segment.sentiment_score is not None]
        return sum(sentiments) / len(sentiments) if sentiments else 0.0

    def _extract_top_topics(self, transcript: AlignedTranscript) -> list[str]:
        """Extract top topics from transcript."""
        topic_counts = {}
        for segment in transcript.segments:
            if segment.topics:
                for topic in segment.topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:5]]

    async def _export_intelligence_pack(
        self, intelligence: EpisodeIntelligence, config: IntelligenceConfig
    ) -> StepResult:
        """Export intelligence pack to requested formats."""
        try:
            formats = []
            file_paths = {}
            if config.export_markdown:
                markdown_path = await self._export_to_markdown(intelligence)
                if markdown_path:
                    formats.append("markdown")
                    file_paths["markdown"] = str(markdown_path)
            if config.export_json:
                json_path = await self._export_to_json(intelligence)
                if json_path:
                    formats.append("json")
                    file_paths["json"] = str(json_path)
            if config.export_html:
                html_path = await self._export_to_html(intelligence)
                if html_path:
                    formats.append("html")
                    file_paths["html"] = str(html_path)
            return StepResult.ok(data={"formats": formats, "file_paths": file_paths})
        except Exception as e:
            logger.error(f"Failed to export intelligence pack: {e!s}")
            return StepResult.fail(f"Failed to export intelligence pack: {e!s}")

    async def _export_to_markdown(self, intelligence: EpisodeIntelligence) -> Path | None:
        """Export intelligence pack to Markdown format."""
        try:
            markdown_content = self._generate_markdown_content(intelligence)
            file_path = self.output_dir / f"{intelligence.episode_id}_intelligence.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            return file_path
        except Exception as e:
            logger.error(f"Failed to export to Markdown: {e!s}")
            return None

    async def _export_to_json(self, intelligence: EpisodeIntelligence) -> Path | None:
        """Export intelligence pack to JSON format."""
        try:
            intelligence_dict = self._intelligence_to_dict(intelligence)
            file_path = self.output_dir / f"{intelligence.episode_id}_intelligence.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(intelligence_dict, f, indent=2, ensure_ascii=False, default=str)
            return file_path
        except Exception as e:
            logger.error(f"Failed to export to JSON: {e!s}")
            return None

    async def _export_to_html(self, intelligence: EpisodeIntelligence) -> Path | None:
        """Export intelligence pack to HTML format."""
        try:
            html_content = self._generate_html_content(intelligence)
            file_path = self.output_dir / f"{intelligence.episode_id}_intelligence.html"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return file_path
        except Exception as e:
            logger.error(f"Failed to export to HTML: {e!s}")
            return None

    def _generate_markdown_content(self, intelligence: EpisodeIntelligence) -> str:
        """Generate Markdown content for intelligence pack."""
        content = f"# Episode Intelligence Pack: {intelligence.episode_title}\n\n**Episode ID:** {intelligence.episode_id}\n**Duration:** {intelligence.episode_duration:.1f} seconds\n**Generated:** {intelligence.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n## Agenda\n\n"
        for item in intelligence.agenda:
            content += f"### {item.title}\n"
            content += f"- **Time:** {item.start_time:.1f}s - {item.end_time:.1f}s ({item.duration:.1f}s)\n"
            content += f"- **Speakers:** {', '.join(item.speakers)}\n"
            content += f"- **Topics:** {', '.join(item.topics)}\n"
            content += f"- **Description:** {item.description}\n\n"
        content += "## Guests\n\n"
        for guest in intelligence.guests:
            content += f"### {guest.name}\n"
            content += f"- **Role:** {guest.role}\n"
            content += f"- **Bio:** {guest.bio}\n"
            content += f"- **Speaking Time:** {guest.total_speaking_time:.1f}s\n"
            content += f"- **Segments:** {guest.segments}\n"
            content += f"- **Expertise:** {', '.join(guest.expertise_areas)}\n\n"
        content += "## Key Claims\n\n"
        for claim in intelligence.claims:
            content += f"### {claim.claim_id}\n"
            content += f"- **Text:** {claim.text}\n"
            content += f"- **Speaker:** {claim.speaker}\n"
            content += f"- **Time:** {claim.timestamp:.1f}s\n"
            content += f"- **Type:** {claim.claim_type}\n"
            content += f"- **Status:** {claim.status.value}\n"
            content += f"- **Confidence:** {claim.confidence:.2f}\n\n"
        content += "## Notable Quotations\n\n"
        for quote in intelligence.quotations:
            content += f"### {quote.quote_id}\n"
            content += f"- **Text:** {quote.text}\n"
            content += f"- **Speaker:** {quote.speaker}\n"
            content += f"- **Time:** {quote.timestamp:.1f}s\n"
            content += f"- **Significance:** {quote.significance}\n\n"
        content += "## Outbound Links\n\n"
        for link in intelligence.links:
            content += f"- **URL:** {link.url}\n"
            content += f"- **Title:** {link.title}\n"
            content += f"- **Mentioned by:** {link.mentioned_by}\n"
            content += f"- **Time:** {link.timestamp:.1f}s\n\n"
        if intelligence.brand_safety:
            content += "## Brand Safety Analysis\n\n"
            content += f"- **Overall Score:** {intelligence.brand_safety.overall_score:.1f}/5.0\n"
            content += f"- **Toxicity Score:** {intelligence.brand_safety.toxicity_score:.2f}\n"
            content += f"- **Controversy Score:** {intelligence.brand_safety.controversy_score:.2f}\n"
            content += f"- **Advertiser Friendliness:** {intelligence.brand_safety.advertiser_friendliness}\n\n"
        if intelligence.defamation_risk:
            content += "## Defamation Risk Assessment\n\n"
            content += f"- **Risk Level:** {intelligence.defamation_risk.risk_level.value}\n"
            content += f"- **Risk Score:** {intelligence.defamation_risk.risk_score:.2f}\n"
            content += "- **Recommendations:**\n"
            for rec in intelligence.defamation_risk.recommendations:
                content += f"  - {rec}\n"
            content += "\n"
        content += "## Key Insights\n\n"
        for insight in intelligence.key_insights:
            content += f"- {insight}\n"
        return content

    def _generate_html_content(self, intelligence: EpisodeIntelligence) -> str:
        """Generate HTML content for intelligence pack."""
        html = f'<!DOCTYPE html>\n<html>\n<head>\n    <title>Episode Intelligence Pack: {intelligence.episode_title}</title>\n    <style>\n        body {{ font-family: Arial, sans-serif; margin: 40px; }}\n        h1 {{ color: #333; }}\n        h2 {{ color: #666; border-bottom: 1px solid #ccc; }}\n        .metadata {{ background: #f5f5f5; padding: 10px; border-radius: 5px; }}\n        .claim {{ background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 5px; }}\n        .quote {{ background: #d1ecf1; padding: 10px; margin: 10px 0; border-radius: 5px; }}\n        .risk-high {{ background: #f8d7da; }}\n        .risk-medium {{ background: #fff3cd; }}\n        .risk-low {{ background: #d4edda; }}\n    </style>\n</head>\n<body>\n    <h1>Episode Intelligence Pack: {intelligence.episode_title}</h1>\n\n    <div class="metadata">\n        <p><strong>Episode ID:</strong> {intelligence.episode_id}</p>\n        <p><strong>Duration:</strong> {intelligence.episode_duration:.1f} seconds</p>\n        <p><strong>Generated:</strong> {intelligence.created_at.strftime("%Y-%m-%d %H:%M:%S")}</p>\n    </div>\n\n    <h2>Agenda</h2>\n'
        for item in intelligence.agenda:
            html += f"\n    <div>\n        <h3>{item.title}</h3>\n        <p><strong>Time:</strong> {item.start_time:.1f}s - {item.end_time:.1f}s ({item.duration:.1f}s)</p>\n        <p><strong>Speakers:</strong> {', '.join(item.speakers)}</p>\n        <p><strong>Topics:</strong> {', '.join(item.topics)}</p>\n        <p><strong>Description:</strong> {item.description}</p>\n    </div>\n"
        html += "    <h2>Key Claims</h2>\n"
        for claim in intelligence.claims:
            html += f'\n    <div class="claim">\n        <h3>{claim.claim_id}</h3>\n        <p><strong>Text:</strong> {claim.text}</p>\n        <p><strong>Speaker:</strong> {claim.speaker}</p>\n        <p><strong>Time:</strong> {claim.timestamp:.1f}s</p>\n        <p><strong>Type:</strong> {claim.claim_type}</p>\n        <p><strong>Status:</strong> {claim.status.value}</p>\n        <p><strong>Confidence:</strong> {claim.confidence:.2f}</p>\n    </div>\n'
        html += "    <h2>Notable Quotations</h2>\n"
        for quote in intelligence.quotations:
            html += f'\n    <div class="quote">\n        <h3>{quote.quote_id}</h3>\n        <p><strong>Text:</strong> {quote.text}</p>\n        <p><strong>Speaker:</strong> {quote.speaker}</p>\n        <p><strong>Time:</strong> {quote.timestamp:.1f}s</p>\n        <p><strong>Significance:</strong> {quote.significance}</p>\n    </div>\n'
        if intelligence.defamation_risk:
            risk_class = f"risk-{intelligence.defamation_risk.risk_level.value}"
            html += f'\n    <h2>Defamation Risk Assessment</h2>\n    <div class="{risk_class}">\n        <p><strong>Risk Level:</strong> {intelligence.defamation_risk.risk_level.value}</p>\n        <p><strong>Risk Score:</strong> {intelligence.defamation_risk.risk_score:.2f}</p>\n        <p><strong>Recommendations:</strong></p>\n        <ul>\n'
            for rec in intelligence.defamation_risk.recommendations:
                html += f"            <li>{rec}</li>\n"
            html += "        </ul>\n    </div>\n"
        html += "\n</body>\n</html>"
        return html

    def _intelligence_to_dict(self, intelligence: EpisodeIntelligence) -> dict:
        """Convert intelligence pack to dictionary for JSON serialization."""
        return {
            "episode_id": intelligence.episode_id,
            "episode_title": intelligence.episode_title,
            "episode_duration": intelligence.episode_duration,
            "created_at": intelligence.created_at.isoformat(),
            "updated_at": intelligence.updated_at.isoformat(),
            "agenda": [
                {
                    "title": item.title,
                    "start_time": item.start_time,
                    "end_time": item.end_time,
                    "duration": item.duration,
                    "description": item.description,
                    "speakers": item.speakers,
                    "topics": item.topics,
                    "key_points": item.key_points,
                }
                for item in intelligence.agenda
            ],
            "guests": [
                {
                    "name": guest.name,
                    "role": guest.role,
                    "bio": guest.bio,
                    "first_mentioned": guest.first_mentioned,
                    "total_speaking_time": guest.total_speaking_time,
                    "segments": guest.segments,
                    "key_contributions": guest.key_contributions,
                    "social_links": guest.social_links,
                    "expertise_areas": guest.expertise_areas,
                }
                for guest in intelligence.guests
            ],
            "claims": [
                {
                    "claim_id": claim.claim_id,
                    "text": claim.text,
                    "speaker": claim.speaker,
                    "timestamp": claim.timestamp,
                    "context": claim.context,
                    "claim_type": claim.claim_type,
                    "status": claim.status.value,
                    "confidence": claim.confidence,
                    "sources_mentioned": claim.sources_mentioned,
                    "verification_notes": claim.verification_notes,
                    "risk_assessment": claim.risk_assessment.value,
                }
                for claim in intelligence.claims
            ],
            "quotations": [
                {
                    "quote_id": quote.quote_id,
                    "text": quote.text,
                    "speaker": quote.speaker,
                    "timestamp": quote.timestamp,
                    "context": quote.context,
                    "significance": quote.significance,
                    "topics": quote.topics,
                    "sentiment": quote.sentiment,
                    "viral_potential": quote.viral_potential,
                }
                for quote in intelligence.quotations
            ],
            "links": [
                {
                    "url": link.url,
                    "title": link.title,
                    "description": link.description,
                    "mentioned_by": link.mentioned_by,
                    "timestamp": link.timestamp,
                    "context": link.context,
                    "link_type": link.link_type,
                    "domain": link.domain,
                    "is_affiliate": link.is_affiliate,
                    "is_sponsored": link.is_sponsored,
                }
                for link in intelligence.links
            ],
            "brand_safety": {
                "overall_score": intelligence.brand_safety.overall_score,
                "toxicity_score": intelligence.brand_safety.toxicity_score,
                "controversy_score": intelligence.brand_safety.controversy_score,
                "advertiser_friendliness": intelligence.brand_safety.advertiser_friendliness,
                "flagged_segments": intelligence.brand_safety.flagged_segments,
                "content_warnings": intelligence.brand_safety.content_warnings,
                "brand_mentions": intelligence.brand_safety.brand_mentions,
            }
            if intelligence.brand_safety
            else None,
            "defamation_risk": {
                "risk_level": intelligence.defamation_risk.risk_level.value,
                "risk_score": intelligence.defamation_risk.risk_score,
                "flagged_statements": intelligence.defamation_risk.flagged_statements,
                "individuals_mentioned": intelligence.defamation_risk.individuals_mentioned,
                "organizations_mentioned": intelligence.defamation_risk.organizations_mentioned,
                "recommendations": intelligence.defamation_risk.recommendations,
            }
            if intelligence.defamation_risk
            else None,
            "total_speakers": intelligence.total_speakers,
            "total_segments": intelligence.total_segments,
            "average_sentiment": intelligence.average_sentiment,
            "top_topics": intelligence.top_topics,
            "key_insights": intelligence.key_insights,
            "export_formats": intelligence.export_formats,
            "file_paths": intelligence.file_paths,
        }

    def _determine_claim_type(self, text: str) -> str:
        """Determine the type of claim based on text content."""
        text_lower = text.lower()
        if any(word in text_lower for word in ["statistics", "data", "study", "research"]):
            return "statistical"
        elif any(word in text_lower for word in ["history", "historical", "past", "years ago"]):
            return "historical"
        elif any(word in text_lower for word in ["science", "scientific", "study", "experiment"]):
            return "scientific"
        elif any(word in text_lower for word in ["personal", "experience", "happened to me"]):
            return "personal"
        else:
            return "general"

    def _calculate_claim_confidence(self, text: str, claim_type: str) -> float:
        """Calculate confidence in a claim based on text content."""
        confidence = 0.5
        text_lower = text.lower()
        if "according to" in text_lower:
            confidence += 0.2
        if "studies show" in text_lower:
            confidence += 0.3
        if "research indicates" in text_lower:
            confidence += 0.3
        if "experts say" in text_lower:
            confidence += 0.2
        if claim_type == "statistical":
            confidence += 0.1
        elif claim_type == "scientific":
            confidence += 0.2
        elif claim_type == "personal":
            confidence -= 0.1
        return min(1.0, max(0.0, confidence))

    def _extract_sources(self, text: str) -> list[str]:
        """Extract mentioned sources from text."""
        sources = []
        text_lower = text.lower()
        source_patterns = ["according to ([^,\\.]+)", "([^,\\.]+) study", "([^,\\.]+) research", "([^,\\.]+) report"]
        import re

        for pattern in source_patterns:
            matches = re.findall(pattern, text_lower)
            sources.extend(matches)
        return list(set(sources))

    def _calculate_quotation_significance(self, text: str) -> float:
        """Calculate significance of a quotation."""
        significance = 0.0
        text_lower = text.lower()
        if "important" in text_lower:
            significance += 0.2
        if "key" in text_lower:
            significance += 0.2
        if "insight" in text_lower:
            significance += 0.3
        if "wisdom" in text_lower:
            significance += 0.3
        if "perspective" in text_lower:
            significance += 0.2
        if len(text) > 100:
            significance += 0.1
        if "?" in text:
            significance += 0.1
        return min(1.0, significance)

    def _calculate_viral_potential(self, text: str) -> float:
        """Calculate viral potential of content."""
        potential = 0.0
        text_lower = text.lower()
        viral_words = ["amazing", "incredible", "unbelievable", "shocking", "controversial"]
        for word in viral_words:
            if word in text_lower:
                potential += 0.2
        emotional_words = ["love", "hate", "angry", "excited", "shocked"]
        for word in emotional_words:
            if word in text_lower:
                potential += 0.1
        controversial_topics = ["politics", "religion", "money", "fame", "celebrity"]
        for topic in controversial_topics:
            if topic in text_lower:
                potential += 0.2
        return min(1.0, potential)

    def _extract_link_title(self, url: str) -> str:
        """Extract a title for a link."""
        domain = self._extract_domain(url)
        return f"Link to {domain}"

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        import re

        match = re.search("https?://([^/]+)", url)
        return match.group(1) if match else url

    def _determine_link_type(self, url: str) -> str:
        """Determine the type of link."""
        domain = self._extract_domain(url).lower()
        if any(social in domain for social in ["twitter", "facebook", "instagram", "tiktok", "youtube"]):
            return "social"
        elif any(ecommerce in domain for ecommerce in ["amazon", "shopify", "etsy", "ebay"]):
            return "product"
        elif any(news in domain for news in ["news", "cnn", "bbc", "reuters", "nytimes"]):
            return "article"
        else:
            return "website"

    def _is_affiliate_link(self, url: str) -> bool:
        """Check if link is an affiliate link."""
        affiliate_indicators = ["affiliate", "ref=", "partner", "commission"]
        return any(indicator in url.lower() for indicator in affiliate_indicators)

    def _is_sponsored_link(self, url: str) -> bool:
        """Check if link is a sponsored link."""
        sponsored_indicators = ["sponsored", "ad", "promo", "promotion"]
        return any(indicator in url.lower() for indicator in sponsored_indicators)

    def _calculate_engagement_score(self, segment: AlignedSegment) -> float:
        """Calculate engagement score for a segment."""
        score = 0.0
        if segment.sentiment_score:
            score += abs(segment.sentiment_score) * 0.3
        if len(segment.speakers) > 1:
            score += 0.2
        if "?" in segment.text:
            score += 0.1
        if "!" in segment.text:
            score += 0.1
        if segment.topics and len(segment.topics) > 0:
            score += 0.1
        return min(1.0, score)

    def _generate_thumbnail_text(self, transcript: AlignedTranscript, timestamp: float) -> str:
        """Generate text overlay for thumbnail."""
        for segment in transcript.segments:
            if segment.start_time <= timestamp <= segment.end_time:
                words = segment.text.split()
                if len(words) > 5:
                    return " ".join(words[:5]) + "..."
                else:
                    return segment.text
        return "Key Moment"

    def _is_controversial_topic(self, topic: str) -> bool:
        """Check if a topic is controversial."""
        controversial_topics = [
            "politics",
            "religion",
            "controversy",
            "scandal",
            "breaking news",
            "conspiracy",
            "conspiracy theory",
            "controversial",
            "debate",
        ]
        return any(controversial in topic.lower() for controversial in controversial_topics)

    def _mentions_individual(self, text: str) -> bool:
        """Check if text mentions an individual."""
        individual_indicators = ["mr.", "mrs.", "ms.", "dr.", "professor", "ceo", "president"]
        return any(indicator in text.lower() for indicator in individual_indicators)

    def _mentions_organization(self, text: str) -> bool:
        """Check if text mentions an organization."""
        org_indicators = ["company", "corporation", "inc.", "llc", "organization", "institution"]
        return any(indicator in text.lower() for indicator in org_indicators)

    def _extract_individuals(self, text: str) -> list[str]:
        """Extract individual names from text."""
        individuals = []
        return individuals

    def _extract_organizations(self, text: str) -> list[str]:
        """Extract organization names from text."""
        organizations = []
        return organizations

    def _extract_expertise_areas(self, contributions: list[str]) -> list[str]:
        """Extract expertise areas from contributions."""
        expertise_areas = []
        expertise_keywords = {
            "technology": ["tech", "software", "programming", "ai", "machine learning"],
            "business": ["business", "entrepreneur", "startup", "marketing", "sales"],
            "science": ["science", "research", "study", "experiment", "data"],
            "entertainment": ["entertainment", "music", "movie", "tv", "celebrity"],
            "politics": ["politics", "government", "policy", "election", "democracy"],
        }
        for contribution in contributions:
            contribution_lower = contribution.lower()
            for area, keywords in expertise_keywords.items():
                if any(keyword in contribution_lower for keyword in keywords) and area not in expertise_areas:
                    expertise_areas.append(area)
        return expertise_areas
