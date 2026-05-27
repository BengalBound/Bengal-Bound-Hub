import os
import django
from django.conf import settings
from django.urls import get_resolver

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bengalbound_core.settings')
django.setup()

resolver = get_resolver()
print("Namespaces:", resolver.namespace_dict.keys())
