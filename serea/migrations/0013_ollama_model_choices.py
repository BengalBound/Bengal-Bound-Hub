"""
Migration 0013: Update SereaAgent.ai_model to reflect actual Ollama models
on the NeuroLinkIt home server.

Changes:
  - ai_model: max_length 60 → 80 (longest ID is 56 chars, extra headroom)
  - ai_model: default 'neurolinkit/default' → 'neurolinkit/neural-chat:latest'
  - ai_model: choices updated to match real Ollama model IDs
  - Data: existing rows with the old placeholder default are migrated forward
"""
from django.db import migrations, models


def migrate_old_default(apps, schema_editor):
    """Point any agents still using the placeholder default to the real model."""
    SereaAgent = apps.get_model('serea', 'SereaAgent')
    SereaAgent.objects.filter(ai_model='neurolinkit/default').update(
        ai_model='neurolinkit/neural-chat:latest'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('serea', '0012_memory_community_cs_escalation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sereaagent',
            name='ai_model',
            field=models.CharField(
                choices=[
                    # NeuroLinkIt — Conversational
                    ('neurolinkit/neural-chat:latest',                  'Neural Chat (NeuroLinkIt) — best for chat'),
                    ('neurolinkit/unbound-neural-chat:latest',          'Neural Chat Unbound (NeuroLinkIt)'),
                    ('neurolinkit/dolphin-mistral:7b',                  'Dolphin Mistral 7B (NeuroLinkIt) — best for persona'),
                    ('neurolinkit/unbound-dolphin-mistral:7b',          'Dolphin Mistral 7B Unbound (NeuroLinkIt)'),
                    # NeuroLinkIt — Strong General
                    ('neurolinkit/glm4:9b',                             'GLM4 9B (NeuroLinkIt) — strong general'),
                    ('neurolinkit/unbound-glm4:latest',                 'GLM4 Unbound (NeuroLinkIt)'),
                    ('neurolinkit/qwen2.5-coder:14b',                   'Qwen 2.5 14B (NeuroLinkIt) — strong reasoning'),
                    ('neurolinkit/qwen2.5-coder:7b',                    'Qwen 2.5 7B (NeuroLinkIt)'),
                    ('neurolinkit/unbound-qwen-coder:latest',           'Qwen Coder Unbound (NeuroLinkIt)'),
                    ('neurolinkit/deepseek-coder-v2:16b',               'DeepSeek V2 16B (NeuroLinkIt) — most capable'),
                    ('neurolinkit/unbound-deepseek-coder:latest',       'DeepSeek Coder Unbound (NeuroLinkIt)'),
                    # NeuroLinkIt — Fast/Compact
                    ('neurolinkit/phi4-mini:latest',                    'Phi-4 Mini (NeuroLinkIt)'),
                    ('neurolinkit/unbound-phi4-mini:latest',            'Phi-4 Mini Unbound (NeuroLinkIt)'),
                    ('neurolinkit/phi3.5:latest',                       'Phi 3.5 (NeuroLinkIt)'),
                    ('neurolinkit/unbound-phi3.5:latest',               'Phi 3.5 Unbound (NeuroLinkIt)'),
                    ('neurolinkit/llama3.2:3b',                         'Llama 3.2 3B (NeuroLinkIt)'),
                    ('neurolinkit/unbound-llama3.2:3b',                 'Llama 3.2 3B Unbound (NeuroLinkIt)'),
                    ('neurolinkit/gemma3:1b',                           'Gemma 3 1B (NeuroLinkIt)'),
                    ('neurolinkit/unbound-gemma3:1b',                   'Gemma 3 1B Unbound (NeuroLinkIt)'),
                    ('neurolinkit/gemma2:2b',                           'Gemma 2 2B (NeuroLinkIt)'),
                    ('neurolinkit/unbound-gemma2:2b',                   'Gemma 2 2B Unbound (NeuroLinkIt)'),
                    ('neurolinkit/qwen3.5:0.8b',                        'Qwen 3.5 0.8B (NeuroLinkIt) — fastest'),
                    ('neurolinkit/unbound-qwen3.5:0.8b',                'Qwen 3.5 0.8B Unbound (NeuroLinkIt)'),
                    # NeuroLinkIt — Code-Specialized
                    ('neurolinkit/deepseek-coder-v2:16b-lite-instruct-q4_K_M', 'DeepSeek V2 16B Lite Q4 (NeuroLinkIt)'),
                    ('neurolinkit/codellama:7b-python',                 'Code Llama 7B Python (NeuroLinkIt)'),
                    ('neurolinkit/unbound-codellama-python:latest',     'Code Llama Python Unbound (NeuroLinkIt)'),
                    # Groq
                    ('llama3-70b-8192',                         'Llama 3 70B (Groq)'),
                    ('llama3-8b-8192',                          'Llama 3 8B (Groq)'),
                    ('llama-3.3-70b-versatile',                 'Llama 3.3 70B Versatile (Groq)'),
                    ('llama-3.1-8b-instant',                    'Llama 3.1 8B Instant (Groq)'),
                    ('mixtral-8x7b-32768',                      'Mixtral 8×7B (Groq)'),
                    ('gemma2-9b-it',                            'Gemma 2 9B (Groq)'),
                    # OpenRouter FREE
                    ('meta-llama/llama-3.3-70b-instruct:free',  'Llama 3.3 70B (OpenRouter FREE)'),
                    ('meta-llama/llama-3.1-8b-instruct:free',   'Llama 3.1 8B (OpenRouter FREE)'),
                    ('google/gemma-3-27b-it:free',              'Gemma 3 27B (OpenRouter FREE)'),
                    ('mistralai/mistral-7b-instruct:free',      'Mistral 7B (OpenRouter FREE)'),
                    ('deepseek/deepseek-r1:free',               'DeepSeek R1 (OpenRouter FREE)'),
                    ('microsoft/phi-4:free',                    'Phi-4 (OpenRouter FREE)'),
                    # OpenRouter Paid
                    ('meta-llama/llama-3.3-70b-instruct',       'Llama 3.3 70B (OpenRouter)'),
                    ('anthropic/claude-3.5-haiku',              'Claude 3.5 Haiku (OpenRouter)'),
                    ('google/gemini-flash-1.5',                 'Gemini Flash 1.5 (OpenRouter)'),
                    # OpenAI
                    ('gpt-4o',                                  'GPT-4o (OpenAI)'),
                    ('gpt-4o-mini',                             'GPT-4o Mini (OpenAI)'),
                    ('gpt-3.5-turbo',                           'GPT-3.5 Turbo (OpenAI)'),
                ],
                default='neurolinkit/neural-chat:latest',
                max_length=80,
                help_text=(
                    'The LLM model Serea will use. '
                    'NeuroLinkIt models run on your home server (configure NEUROLINKIT_BASE_URL). '
                    'Recommended for social media: Neural Chat, Dolphin Mistral, or GLM4.'
                ),
            ),
        ),
        migrations.RunPython(migrate_old_default, migrations.RunPython.noop),
    ]
