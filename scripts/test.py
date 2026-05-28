import os, sys
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bengalbound_core.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

for u in User.objects.all().order_by('date_joined')[:10]:
    print(f"  {u.email:40} role={getattr(u, 'role', 'N/A')!r}  is_staff={u.is_staff}  is_superuser={u.is_superuser}")

print("\nRole field choices (if any):")
try:
    from django.contrib.auth import get_user_model
    u = User()
    role_field = User._meta.get_field('role')
    print(f"  type={type(role_field).__name__}  choices={getattr(role_field, 'choices', None)}")
except Exception as e:
    print(f"  {e}")
