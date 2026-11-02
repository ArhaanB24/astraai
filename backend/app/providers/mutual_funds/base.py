from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseMutualFundProvider(ABC):

    @abstractmethod
    def search_funds(self, query: str) -> List[Dict[str, Any]]:
        """Search mutual funds by name or code."""
        pass

    @abstractmethod
    def get_fund_details(self, scheme_code: str) -> Optional[Dict[str, Any]]:
        """Fetch mutual fund details including meta information."""
        pass

    @abstractmethod
    def get_latest_nav(self, scheme_code: str) -> Optional[Dict[str, Any]]:
        """Fetch latest NAV and NAV date for scheme."""
        pass

    @abstractmethod
    def get_nav_history(self, scheme_code: str, limit: int = 365) -> List[Dict[str, Any]]:
        """Fetch historical NAV records."""
        pass

    @abstractmethod
    def get_holdings(self, scheme_code: str) -> List[Dict[str, Any]]:
        """Fetch fund stock/sector holdings if available."""
        pass
