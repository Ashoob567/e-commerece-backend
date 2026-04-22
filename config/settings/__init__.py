import os
import sys

# Determine which settings module to use
settings_module = os.getenv('DJANGO_SETTINGS_MODULE', 'config.settings.development')

if 'test' in sys.argv or 'pytest' in sys.modules:
    # Use development settings for tests
    from .development import *
elif 'production' in settings_module:
    from .production import *
else:
    from .development import *
