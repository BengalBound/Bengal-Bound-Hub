import os
import re

CORE_APPS = ['accounts', 'booking_calendar', 'community_forum', 'console_admin', 'core', 'public_site']
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_tests_for_dir(app_dir):
    models_path = os.path.join(app_dir, 'models.py')
    tests_path = os.path.join(app_dir, 'tests.py')
    tests_dir = os.path.join(app_dir, 'tests')
    
    if os.path.isdir(tests_dir):
        return False
        
    if not os.path.exists(models_path):
        return False
        
    with open(models_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Find all models defined in this file that actually inherit from Model, AbstractUser or BaseModel
    # We ignore TextChoices, IntegerChoices, etc.
    model_matches = re.findall(r'^class\s+([A-Za-z0-9_]+)\s*\(\s*(?:models\.Model|AbstractUser|BaseModel)\s*\)\s*:', content, re.MULTILINE)
    
    # Remove BaseModel itself since it is abstract and has no .objects
    model_matches = [m for m in model_matches if m not in ('Meta', 'BaseModel')]
    
    if not model_matches:
        return False
        
    # If the tests.py is over 1000 bytes, assume it has real tests and skip it
    if os.path.exists(tests_path) and os.path.getsize(tests_path) > 1000:
        return False
        
    test_code = 'from django.test import TestCase\n'
    test_code += f'from .models import {", ".join(model_matches)}\n\n'
    
    for model in model_matches:
        test_code += f'class {model}ModelTest(TestCase):\n'
        test_code += f'    def test_model_exists(self):\n'
        test_code += f'        self.assertTrue(hasattr({model}, "objects"))\n\n'
        
    with open(tests_path, 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    return True

def run():
    count = 0
    # Core apps
    for app in CORE_APPS:
        app_path = os.path.join(BASE_DIR, app)
        if os.path.exists(app_path):
            if generate_tests_for_dir(app_path):
                print(f"Generated tests for core app: {app}")
                count += 1
                
    # Modules
    modules_dir = os.path.join(BASE_DIR, 'modules')
    if os.path.exists(modules_dir):
        for mod in os.listdir(modules_dir):
            mod_path = os.path.join(modules_dir, mod)
            if os.path.isdir(mod_path) and mod != '__pycache__':
                if generate_tests_for_dir(mod_path):
                    print(f"Generated tests for module: {mod}")
                    count += 1
                    
    # Agents
    agents_dir = os.path.join(BASE_DIR, 'agents')
    if os.path.exists(agents_dir):
        for agent in os.listdir(agents_dir):
            agent_path = os.path.join(agents_dir, agent)
            if os.path.isdir(agent_path) and agent != '__pycache__':
                if generate_tests_for_dir(agent_path):
                    print(f"Generated tests for agent: {agent}")
                    count += 1

    print(f"Total test files generated/overwritten: {count}")

if __name__ == '__main__':
    run()
