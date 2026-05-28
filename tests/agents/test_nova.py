from django.test import TestCase


class NovaEngineTests(TestCase):
    # Unit tests for NovaEngine - Data Scientist

    def test_engine_import(self):
        from agents.nova.engine import NovaEngine
        engine = NovaEngine()
        self.assertIsNotNone(engine)

    def test_system_prompt_defined(self):
        from agents.nova.engine import NovaEngine
        self.assertGreater(len(NovaEngine.SYSTEM_PROMPT), 50)


class NovaModelTests(TestCase):
    # Model-level tests for Data Scientist agent
    pass  # TODO: add model creation and field validation tests


class NovaAPITests(TestCase):
    # Integration tests for Data Scientist REST API
    pass  # TODO: add endpoint tests
