import json
from agents.utils import agent_chat

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

Supported domains: legal, medical, financial, technical, marketing, general"""


class BabelEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def translate(self, job) -> list:
        results = []
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

            results.append({"language": target_lang, **data})
        return results

    def detect_language(self, text: str) -> str:
        prompt = f"""Detect the language of this text and return ONLY the ISO 639-1 code (e.g. "en", "fr", "bn").

Text: {text[:500]}"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return agent_chat(messages).strip().lower()[:5]

    def quality_review(self, source: str, translation: str, source_lang: str, target_lang: str) -> dict:
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
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"score": 0.8, "issues": [], "suggested_corrections": []}

    def domain_glossary(self, text: str, domain: str) -> list:
        prompt = f"""Extract domain-specific terms from this {domain} text that need consistent translation.

Text: {text[:2000]}

Return a JSON array of objects: {{"term": "original term", "domain": "{domain}", "notes": "why this needs careful translation"}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []
