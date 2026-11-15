"""The clock of the shop.

Algeria runs on UTC+1 all year round (no daylight saving), so the wall clock
is always ``+01:00``. The database stores that local time, which keeps the
stored rows readable and makes the day and month buckets line up with the
calendar the customers use.

Django's own ``timezone.now()`` follows the *operating system* clock when
``USE_TZ`` is off, and Windows has no ``time.tzset`` to move it. The helper
here always returns the Algerian wall clock, whatever the host is set to.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

#: The timezone of the shop.
ALGERIA = ZoneInfo("Africa/Algiers")

#: The offset of Algeria from UTC — it has no daylight saving.
ALGERIA_OFFSET = timedelta(hours=1)


def now() -> datetime:
    """The current Algerian wall clock, without a timezone.

    The value is naive on purpose: that is what the database stores.
    """
    return datetime.now(ALGERIA).replace(tzinfo=None)


def today() -> datetime:
    """Today at midnight, in the Algerian wall clock."""
    return now().replace(hour=0, minute=0, second=0, microsecond=0)


def as_aware(moment: datetime) -> datetime:
    """Read a stored timestamp as an aware Algerian datetime."""
    if timezone.is_naive(moment):
        return moment.replace(tzinfo=ALGERIA)
    return moment.astimezone(ALGERIA)


def isoformat(moment: datetime) -> str:
    """A stored timestamp with its offset, so clients never guess."""
    return as_aware(moment).isoformat()
