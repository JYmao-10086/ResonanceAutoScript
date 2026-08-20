"""GUI 包。"""

__all__ = ["TradingAssistantApp"]


def __getattr__(name: str):
    if name == "TradingAssistantApp":
        from .app import TradingAssistantApp

        return TradingAssistantApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
