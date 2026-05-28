import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Dox, BengalBound's AI Technical Writer.

Your role is to produce clear, accurate, maintainable documentation that developers and non-technical users can both use effectively. You write documentation that actually gets read.

Capabilities:
- Generate API documentation from endpoint descriptions and schemas
- Write user manuals, onboarding guides, and SOPs
- Create wiki articles and internal knowledge base entries
- Generate changelogs from code descriptions
- Review and improve existing documentation for clarity
- Produce code documentation and inline comments

Principles:
- Clarity over completeness — a short clear doc beats a long unclear one
- Documentation should answer: What is it? How do I use it? What can go wrong?
- Use concrete examples, not abstract descriptions
- For APIs: include request/response examples for every endpoint
- For user guides: step-by-step numbered instructions, screenshots described in text
- For SOPs: clear trigger, steps, expected outcome, troubleshooting

Doc types: api, user_manual, sop, wiki, changelog, code_docs"""


class DoxEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def generate_page(self, project, page, instance=None) -> str:
        type_instructions = {
            "api": "Include: endpoint, method, auth, request params, response schema, example request+response, error codes",
            "user_manual": "Include: overview, step-by-step instructions, screenshots (described), FAQs, troubleshooting",
            "sop": "Include: purpose, trigger, prerequisites, step-by-step procedure, expected outcomes, escalation path",
            "wiki": "Include: overview, key concepts, how it works, related topics, examples",
            "changelog": "Include: version, date, new features, bug fixes, breaking changes, migration guide",
            "code_docs": "Include: purpose, parameters with types, return value, example usage, edge cases",
        }
        instruction = type_instructions.get(project.doc_type, "Clear, structured documentation")

        prompt = f"""Write a documentation page for this project.

Project: {project.name} ({project.doc_type})
Project Description: {project.description}
Page Title: {page.title}
Section: {page.section}

Documentation requirements:
{instruction}

Write complete, production-ready documentation in Markdown format."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_page for {page.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if project.doc_type == "sop":
                raise PermissionRequired(
                    context=f"Standard Operating Procedure (SOP) drafted: {page.title}. Requires review.",
                    option_a="Approve and publish SOP",
                    option_b="Deny and flag for human revision"
                )
        return res

    def review_and_improve(self, content: str, doc_type: str, instance=None) -> dict:
        prompt = f"""Review and improve this {doc_type} documentation.

Current content:
{content[:3000]}

Return JSON:
{{
  "improved_content": "the improved version",
  "issues_found": ["list of issues in the original"],
  "improvements_made": ["list of improvements"],
  "clarity_score": integer 0-100,
  "completeness_score": integer 0-100
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"improved_content": content, "issues_found": [], "improvements_made": [], "clarity_score": 70, "completeness_score": 70}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="review_and_improve",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def generate_changelog(self, version: str, changes: list, instance=None) -> str:
        changes_text = "\n".join(f"- {c}" for c in changes)
        prompt = f"""Generate a user-facing changelog entry.

Version: {version}
Raw changes:
{changes_text}

Write a clear, structured changelog in Markdown with sections:
## What's New, ## Improvements, ## Bug Fixes, ## Breaking Changes (if any)

Use plain language — this is for end users, not developers."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_changelog {version}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def scan_for_outdated(self, page, days_old: int, instance=None) -> dict:
        prompt = f"""Assess if this documentation page is likely outdated.

Title: {page.title}
Section: {page.section}
Days since last update: {days_old}
Content preview:
{page.content[:1000]}

Return JSON:
{{
  "likely_outdated": boolean,
  "reasons": ["why it might be outdated"],
  "sections_to_review": ["specific sections that may need updating"],
  "update_priority": "low|medium|high"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"likely_outdated": days_old > 90, "reasons": [], "sections_to_review": [], "update_priority": "low"}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"scan_for_outdated {page.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
