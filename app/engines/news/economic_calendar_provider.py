from abc import (
    ABC,
    abstractmethod,
)


class EconomicCalendarProvider(
    ABC
):

    @abstractmethod
    async def fetch_events(
        self,
        start,
        end,
    ):
        """
        Return normalized economic events.

        Each event must use:

        {
            "external_id": str | None,
            "title": str,
            "title_fa": str | None,
            "country": str | None,
            "currency": str | None,
            "category": str | None,
            "importance": "low|medium|high",
            "previous": str | None,
            "forecast": str | None,
            "actual": str | None,
            "event_time": datetime,
            "source": str,
            "source_url": str | None,
        }

        event_time must be UTC.
        """
        raise NotImplementedError