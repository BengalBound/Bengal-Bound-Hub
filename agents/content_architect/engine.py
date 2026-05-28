import json
from agents.utils import agent_chat

SYSTEM_PROMPT = """You are Content Architect, BengalBound's AI Editorial Planner.

Your role is to build content strategies that drive real business outcomes — traffic, leads, brand authority. You plan at scale and produce publish-ready content.

Capabilities:
- Build full monthly content calendars aligned to business goals
- Generate publish-ready content for blog, email, social, video, and ad channels
- Optimise content for SEO, engagement, and conversion
- Maintain consistent brand voice across channels
- Write compelling headlines, hooks, and CTAs
- Adapt content for different audience segments

Principles:
- Every piece of content should have a clear goal: awareness, consideration, or conversion
- Channel-specific: LinkedIn posts ≠ blog posts ≠ emails — each needs its own format
- SEO-first for blog and website content: include target keywords naturally
- For social: hook in the first line, value in the body, CTA at the end
- Quality over quantity — 3 great posts beat 10 mediocre ones
- Always include measurable success metrics with content plans

Content channels: blog, email, social (LinkedIn/Facebook/Instagram/Twitter), video (script), ad (copy)"""


class ContentArchitectEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def generate_content(self, entry) -> str:
        channel_guides = {
            "blog": "Long-form, SEO-optimised, 800-1200 words, include H2 subheadings",
            "email": "Subject line + preview text + body, scannable, one primary CTA",
            "social": "Hook (first line), value (body), CTA. Platform-appropriate length",
            "video": "Script with intro hook, 3 main points, outro CTA. Mark scene changes",
            "ad": "Headline (max 30 chars) + description (max 90 chars) + CTA button text",
        }
        channel = entry.channel
        guide = channel_guides.get(channel, "Clear, engaging, on-brand content")

        prompt = f"""Generate {channel} content for this brief.

Title: {entry.title}
Brief: {entry.brief}
Channel: {channel}
Publish Date: {entry.publish_date}
Format guide: {guide}

Write complete, publish-ready content. Include all elements required for this channel."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return agent_chat(messages)

    def plan_calendar(self, calendar) -> list:
        prompt = f"""Build a detailed content calendar for this campaign.

Calendar: {calendar.name}
Goal: {calendar.goal}
Month: {calendar.month}

Create a 4-week content plan with:
- 2x blog posts per week
- 5x social posts per week (mix of platforms)
- 1x email newsletter per week

Return a JSON array of content entries:
{{
  "title": "content title",
  "channel": "blog|email|social|video|ad",
  "publish_date": "YYYY-MM-DD",
  "brief": "what this piece covers and why",
  "goal": "awareness|consideration|conversion"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def optimise_for_seo(self, content: str, target_keyword: str) -> dict:
        prompt = f"""Optimise this content for the target keyword: "{target_keyword}"

Content:
{content[:3000]}

Return JSON:
{{
  "optimised_content": "full optimised version",
  "keyword_density": float,
  "seo_score": integer 0-100,
  "meta_title": "60 char max",
  "meta_description": "160 char max",
  "internal_link_suggestions": ["topics to link to"],
  "improvements_made": ["list of changes"]
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"optimised_content": content, "seo_score": 50, "improvements_made": []}

    def repurpose_content(self, content: str, source_channel: str, target_channels: list) -> dict:
        prompt = f"""Repurpose this {source_channel} content for: {', '.join(target_channels)}

Original content:
{content[:2000]}

For each target channel, write a complete repurposed version. Return JSON:
{{"channel_name": "repurposed content"}} for each target channel."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {ch: raw for ch in target_channels}
