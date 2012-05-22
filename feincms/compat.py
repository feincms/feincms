try:
    from django.utils.timezone import now as compatible_now
except ImportError:
    # Django < 1.4 comes without timezone support
    from datetime import datetime
    compatible_now = datetime.now
