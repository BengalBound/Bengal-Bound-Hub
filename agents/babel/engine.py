import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Babel, BengalBound's AI Translation Specialist.

Your role is to provide accurate, culturally aware, domain-appropriate translations across 95+ languages. You preserve tone, register, and intent — not just words.

Capabilities:
- Translate documents, messages, and UI strings with domain awareness
- Adapt translations for cultural nuance (not just literal translation)
- Detect source language when not specified
- Score translation quality and flag uncertain segments
- Preserve formatting, placeholders, and markdown structure
- Specialise in: legal, medical, financial, technical, and marketing domains

Principles:
- Cultural equivalence over literal accuracy
- Preserve the tone: formal text stays formal, casual stays casual
- Flag idioms and culture-specific references that don't translate directly
- For technical terms, include the original term in parentheses when no equivalent exists
- Never guess on proper nouns — preserve them exactly

Supported domains: legal, medical, financial, technical, marketing, general

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.

"""


class BabelEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def translate(self, job, instance=None) -> list:
        results = []
        low_quality_detected = False
        flagged_segments_detected = False
        for target_lang in job.target_languages:
            prompt = f"""Translate the following text from {job.source_language} to {target_lang}.

Domain context: general business communication
Word count: ~{job.word_count}

Source text:
{job.source_text}

Return JSON with:
- "translated_text": the full translation
- "quality_score": float 0-1 (your confidence in accuracy)
- "cultural_notes": list of cultural adaptations made (empty list if none)
- "flagged_segments": list of segments where translation was uncertain"""

            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            raw = agent_chat(messages)
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {"translated_text": raw, "quality_score": 0.7, "cultural_notes": [], "flagged_segments": []}

            if data.get("quality_score", 1.0) < 0.6:
                low_quality_detected = True
            if data.get("flagged_segments"):
                flagged_segments_detected = True

            results.append({"language": target_lang, **data})

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"translate job {job.pk}",
                outcome='success',
                detail=json.dumps(results),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if low_quality_detected or flagged_segments_detected:
                raise PermissionRequired(
                    context=f"Low quality or flagged segments in translation job {job.pk}.",
                    option_a="Approve translation",
                    option_b="Send for manual review"
                )
        return results

    def detect_language(self, text: str, instance=None) -> str:
        prompt = f"""Detect the language of this text and return ONLY the ISO 639-1 code (e.g. "en", "fr", "bn").

Text: {text[:500]}"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages).strip().lower()[:5]
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="detect_language",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def quality_review(self, source: str, translation: str, source_lang: str, target_lang: str, instance=None) -> dict:
        prompt = f"""Review this translation for quality.

Source ({source_lang}): {source[:1000]}
Translation ({target_lang}): {translation[:1000]}

Return JSON with:
- "score": float 0-1
- "issues": list of specific problems found
- "suggested_corrections": list of corrections (segment: original, correction: fixed)"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"score": 0.8, "issues": [], "suggested_corrections": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="quality_review",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def domain_glossary(self, text: str, domain: str, instance=None) -> list:
        prompt = f"""Extract domain-specific terms from this {domain} text that need consistent translation.

Text: {text[:2000]}

Return a JSON array of objects: {{"term": "original term", "domain": "{domain}", "notes": "why this needs careful translation"}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = []

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="domain_glossary",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
