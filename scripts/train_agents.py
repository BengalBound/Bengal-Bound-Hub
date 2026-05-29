import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(BASE_DIR, 'agents')

OLD_DIRECTIVE_PATTERN = r'\n---[\s\S]*?UNIVERSAL ALIGNMENT DIRECTIVES[\s\S]*?---'

NEW_DIRECTIVE = """
[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.
"""

def train_agent(engine_path):
    with open(engine_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove the old verbose directive if it exists
    new_content = re.sub(OLD_DIRECTIVE_PATTERN, '', content)

    # If already trained with the new ultra-short directive, skip
    if "[STRICT SYSTEM RULES]" in new_content:
        return False

    # Try triple double quotes first
    pattern_double = r'(SYSTEM_PROMPT\s*=\s*\"\"\"[\s\S]*?)(\"\"\")'
    if re.search(pattern_double, new_content):
        new_content = re.sub(pattern_double, r'\1' + NEW_DIRECTIVE + r'\n\2', new_content, count=1)
    else:
        # Try triple single quotes
        pattern_single = r"(SYSTEM_PROMPT\s*=\s*\'\'\'[\s\S]*?)(\'\'\')"
        if re.search(pattern_single, new_content):
            new_content = re.sub(pattern_single, r'\1' + NEW_DIRECTIVE + r'\n\2', new_content, count=1)
        else:
            # Fallback for single quotes or double quotes on one line
            pattern_str = r'(SYSTEM_PROMPT\s*=\s*\"[\s\S]*?)(\")'
            if re.search(pattern_str, new_content):
                 new_content = re.sub(pattern_str, r'\1' + NEW_DIRECTIVE.replace('\n', ' ') + r'\2', new_content, count=1)
            else:
                 print(f"Could not find SYSTEM_PROMPT in {engine_path}")
                 return False

    with open(engine_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    trained_count = 0
    for agent_slug in os.listdir(AGENTS_DIR):
        agent_dir = os.path.join(AGENTS_DIR, agent_slug)
        if not os.path.isdir(agent_dir):
            continue
            
        engine_path = os.path.join(agent_dir, 'engine.py')
        if os.path.exists(engine_path):
            if train_agent(engine_path):
                trained_count += 1
                print(f"Token-optimized prompt injected for: {agent_slug}")

    print(f"\nTotal agents successfully optimized: {trained_count}")

if __name__ == "__main__":
    main()
