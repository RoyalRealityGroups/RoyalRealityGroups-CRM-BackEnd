import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from Masters.models import PriceBookDocument, PriceBook

# Sync all documents
docs = PriceBookDocument.objects.filter(is_deleted=False)
total_synced = 0

for doc in docs:
    count = PriceBook.objects.filter(document=doc, is_deleted=False).update(
        effective_from=doc.effective_from,
        effective_to=doc.effective_to
    )
    print(f"Document {doc.id[:8]}...: synced {count} entries (effective_from={doc.effective_from})")
    total_synced += count
    
print(f"\n✓ Total: {total_synced} entries synced!")
