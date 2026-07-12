#!/usr/bin/env python3
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

try:
    from Masters.models import Scheme
    from Masters.serializers import SchemeSerializer, SchemeMiniSerializer
    from Masters.scheme_engine import SchemeEngine
    from Sales.models import SalesOrderScheme, SalesOrderItemScheme
    
    print("✅ Models imported successfully")
    print("✅ Serializers imported successfully")
    print("✅ SchemeEngine imported successfully")
    
    scheme_count = Scheme.objects.filter(is_deleted=False).count()
    print(f"✅ Database accessible")
    print(f"   Total schemes: {scheme_count}")
    
    # Test SchemeEngine
    engine = SchemeEngine()
    print(f"✅ SchemeEngine instantiated")
    
    sys.exit(0)
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
