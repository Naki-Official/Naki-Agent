import json
from typing import Optional

try:
    from services import cryptocompare
except ImportError:
    raise ImportError("`cryptocompare` not installed. Please install using `pip install cryptocompare`.")

class CryptoCompareTools():
    def __init__(
        self,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the CryptoCompare Toolkit.

        Args:
            api_key Optional[str]: The api key for CryptoCompare API.
        """
        self.api_key = api_key


    def historical_ohlcv_minute(self, from_symbol: str = 'btc', to_symbol: str = 'usd', aggregate: int = 30, limit: int = 48) -> str:
        """
        Get historical OHLCV minute data.

        :param aggregate:
        :param from_symbol:
        :param to_symbol:
        :return:
        """
        historical = cryptocompare.get_historical_price_minute(coin=from_symbol, currency=to_symbol, aggregate=aggregate, limit=limit)
        print(historical)

        return historical
    
    def historical_ohlcv_hour(self, from_symbol: str = 'btc', to_symbol: str = 'usd', limit: int = 48, aggregate: int = 1) -> str:
        """
        Get historical OHLCV hour data.

        :param aggregate:
        :param from_symbol:
        :param to_symbol:
        :return:
        """
        historical = cryptocompare.get_historical_price_hour(coin=from_symbol, currency=to_symbol, limit=limit, aggregate=aggregate)
        return historical

    def historical_ohlcv_day(self, from_symbol: str = 'btc', to_symbol: str = 'usd', limit: int = 48) -> str:
        """
        Get historical OHLCV day data.

        :param from_symbol:
        :param to_symbol:
        :return:
        """
        historical = cryptocompare.get_historical_price_day(coin=from_symbol, currency=to_symbol, limit=limit)
        return historical
