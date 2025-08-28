import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_portal.settings')
django.setup()

from django.core.files.storage import default_storage
from django.conf import settings

print("=== STORAGE CONFIGURATION ===")
print(f"Default storage: {default_storage.__class__.__name__}")
print(f"DEFAULT_FILE_STORAGE setting: {settings.DEFAULT_FILE_STORAGE}")

# Check if it's actually S3
if hasattr(default_storage, 'bucket_name'):
    print(f"S3 Bucket: {default_storage.bucket_name}")
    print("✅ Using S3 storage")
else:
    print("❌ Still using local storage")
    print("Check settings loading order")