from __future__ import annotations


class AlphaRadarError(Exception):
    """Base exception for all AlphaRadar errors."""


class CrustdataAPIError(AlphaRadarError):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Crustdata API error {status_code}: {detail}")


class CrustdataRateLimitError(CrustdataAPIError):
    pass


class MarketDataError(AlphaRadarError):
    pass


class StorageError(AlphaRadarError):
    pass


class EmbeddingError(AlphaRadarError):
    pass


class LLMError(AlphaRadarError):
    pass


class SignalDetectionError(AlphaRadarError):
    pass


class AlertDeliveryError(AlphaRadarError):
    pass
