import os
import sys
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bengalbound_core.settings')
import django
django.setup()

from django.test import Client
from hub.models import Business

biz = Business.objects.filter(slug='company-one-1').first()
if biz and biz.owner:
    client = Client(SERVER_NAME='127.0.0.1')
    try:
        client.force_login(biz.owner)
        response = client.get('/hub/company-one-1/modules/')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
            print("ERROR 500 DETECTED!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("EXCEPTION RAISED!")
else:
    print("No business found")
