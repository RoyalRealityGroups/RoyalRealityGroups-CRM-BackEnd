import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from Core.System.models import Menuitem

print("Menuitem codes in database:")
print("-" * 60)
for m in Menuitem.objects.filter(is_deleted=False).order_by('code'):
    print(f"  {m.code}: {m.name} (link: {m.link})")
