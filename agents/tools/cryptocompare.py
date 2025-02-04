import os
import json
from typing import Optional


from agno.tools import Toolkit
from agno.utils.log import logger

try:
    from services import cryptocompare
except ImportError:
    raise ImportError("`cryptocompare` not installed. Please install using `pip install cryptocompare`.")

class CryptoCompareTools(Toolkit):
    def __init__(
        self,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the CryptoCompare Toolkit.

        Args:
            api_key Optional[str]: The api key for CryptoCompare API.
        """
        super().__init__(name="cryptocompare")

        self.api_key = api_key

        cryptocompare._set_api_key_parameter(api_key)
        self.register(self.historical_ohlcv_minute)


    def historical_ohlcv_minute(self, from_symbol: str = 'btc', to_symbol: str = 'usd', aggregate: int = 30) -> str:
        """
        Get historical OHLCV minute data.

        :param aggregate:
        :param from_symbol:
        :param to_symbol:
        :return:
        """
        historical = cryptocompare.get_historical_price_minute(coin=from_symbol, currency=to_symbol, aggregate=aggregate, limit=48)
        print(historical)

        return json.dumps(historical, indent=2)

