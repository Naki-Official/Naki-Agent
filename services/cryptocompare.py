"""
CryptoCompare API wrapper
"""
import requests
import time
import datetime
import typing
import os
import logging
from typing import Union, Optional, List, Dict

Timestamp = Union[datetime.datetime, datetime.date, int, float]

# API
_API_KEY_PARAMETER = "7705cc210988866ded02a57eee0dbab0dae5cf2b7087800871e47b4bacc3635d"
_URL_COIN_LIST = "https://www.cryptocompare.com/api/data/coinlist?"
_URL_PRICE = "https://min-api.cryptocompare.com/data/pricemulti?fsyms={}&tsyms={}"
_URL_PRICE_MULTI = "https://min-api.cryptocompare.com/data/pricemulti?fsyms={}&tsyms={}"
_URL_PRICE_MULTI_FULL = (
    "https://min-api.cryptocompare.com/data/pricemultifull?fsyms={}&tsyms={}"
)
_URL_HIST_PRICE = (
    "https://min-api.cryptocompare.com/data/pricehistorical?fsym={}&tsyms={}&ts={}&e={}"
)
_URL_HIST_PRICE_DAY = "https://min-api.cryptocompare.com/data/v2/histoday?fsym={}&tsym={}&limit={}&e={}&toTs={}&aggregate={}"
_URL_HIST_PRICE_HOUR = "https://min-api.cryptocompare.com/data/v2/histohour?fsym={}&tsym={}&limit={}&e={}&toTs={}&aggregate={}"
_URL_HIST_PRICE_MINUTE = "https://min-api.cryptocompare.com/data/v2/histominute?fsym={}&tsym={}&limit={}&e={}&toTs={}&aggregate={}"
_URL_AVG = "https://min-api.cryptocompare.com/data/generateAvg?fsym={}&tsym={}&e={}"
_URL_EXCHANGES = "https://min-api.cryptocompare.com/data/top/exchanges?fsym={}&tsym={}"
_URL_PAIRS = "https://min-api.cryptocompare.com/data/pair/mapping/exchange?e={}"

_MAX_LIMIT_HISTO_API = 2000

# DEFAULTS
CURRENCY = "EUR"
LIMIT = 1440
###############################################################################

def _filter_fields(json_response: Dict, fields: List[str]) -> Optional[Dict]:
    """
    Filter JSON response keeping only specified fields.

    :param json_response: the JSON response
    :param fields: list of fields to keep
    :returns: filtered JSON response or None if the response is empty
    """
    if not json_response:
        return None

    filtered_response = {}
    for field in fields:
        if field in json_response:
            filtered_response[field] = json_response[field]

    return filtered_response if filtered_response else None

def _query_cryptocompare(url: str, errorCheck: bool = True, api_key: str = None, fields: Optional[List[str]] = None) -> Optional[Dict]:
    """
    Query the url and return the result or None on failure.

    :param url: the url
    :param errorCheck: run extra error checks (default: True)
    :param api_key: optional, if you want to add an API Key
    :returns: response, or nothing if errorCheck=True
    """
    api_key_parameter = _set_api_key_parameter(api_key)
    try:
        response = requests.get(url + api_key_parameter)
        if errorCheck:
            response.raise_for_status()  # Raise HTTPError for bad status codes
        response_data = response.json()  # Convert response to JSON
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting coin information: {e}")
        return None

    return response_data

def _format_parameter(parameter: object) -> str:
    """
    Format the parameter depending on its type and return
    the string representation accepted by the API.

    :param parameter: parameter to format
    """
    if isinstance(parameter, list):
        return ",".join(parameter)

    else:
        return str(parameter)


def _format_timestamp(timestamp: Timestamp) -> int:
    """
    Format the timestamp depending on its type and return
    the integer representation accepted by the API.

    :param timestamp: timestamp to format
    """
    if isinstance(timestamp, datetime.datetime) or isinstance(timestamp, datetime.date):
        return int(time.mktime(timestamp.timetuple()))
    return int(timestamp)


def _set_api_key_parameter(api_key: str = None) -> str:
    if api_key is None:
        api_key = os.getenv("CRYPTOCOMPARE_API_KEY")
    if api_key is not None:
        _API_KEY = f"&api_key={api_key}"
        return _API_KEY
    return ""


###############################################################################


def get_coin_list(format: bool = False, fields: Optional[List[str]] = None) -> Union[Dict, List, None]:
    """
    Get a list of coins (all available coins).

    :param format: format as Python list (default: False)
    :returns: dictionary or list of available coins
    """
    response = _query_cryptocompare(_URL_COIN_LIST, False, fields=fields)
    if response:
        response = typing.cast(Dict, response["Data"])
        return list(response.keys()) if format else response
    return None

def get_price(
    coin: str, currency: str = CURRENCY, full: bool = False, fields: Optional[List[str]] = None
) -> Optional[Dict]:
    """
    Get the currencyent price of a coin in a given currency.

    :param coin: symbolic name of the coin (e.g. BTC)
    :param currency: short hand description of the currency (e.g. EUR)
    :param full: full response or just the price (default: False)
    :returns: dict of coin and currency price pairs
    """
    if full:
        return _query_cryptocompare(
            _URL_PRICE_MULTI_FULL.format(
                _format_parameter(coin), _format_parameter(currency)
            ),
            fields=fields
        )
    if isinstance(coin, list):
        return _query_cryptocompare(
            _URL_PRICE_MULTI.format(
                _format_parameter(coin), _format_parameter(currency)
            ),
            fields=fields
        )
    return _query_cryptocompare(_URL_PRICE.format(coin, _format_parameter(currency)), fields=fields)


def get_historical_price(
    coin: str,
    currency: str = CURRENCY,
    timestamp: Timestamp = time.time(),
    exchange: str = "CCCAGG",
    fields: Optional[List[str]] = None
) -> Optional[Dict]:
    """
    Get the price of a coin in a given currency during a specific time.

    :param coin: symbolic name of the coin (e.g. BTC)
    :param currency: short hand description of the currency (e.g. EUR)
    :param timestamp: point in time
    :param exchange: the exchange to use
    :returns: dict of coin and currency price pairs
    """
    return _query_cryptocompare(
        _URL_HIST_PRICE.format(
            coin,
            _format_parameter(currency),
            _format_timestamp(timestamp),
            _format_parameter(exchange),
        ),
        fields=fields
    )


def get_historical_price_day(
    coin: str,
    currency: str = CURRENCY,
    limit: int = LIMIT,
    toTs: Timestamp = time.time(),
    fields: Optional[List[str]] = None
) -> Optional[List[Dict]]:
    """
    Get historical price (day).

    :param coin: symbolic name of the coin (e.g. BTC)
    :param currency: short hand description of the currency (e.g. EUR)
    :param limit: number of data points (max. 2000)
    :param toTs: return data before this timestamp. (Unix epoch time or datetime object)
    :returns: dict of coin and currency price pairs
    """
    exchange = get_exchange(coin, currency)
    response = _query_cryptocompare(
        _URL_HIST_PRICE_DAY.format(
            coin, _format_parameter(currency), limit, exchange, _format_timestamp(toTs)
        ),
        fields=fields
    )
    if response:
        return response["Data"]["Data"]
    return None


def get_historical_price_day_from(
    coin: str,
    currency: str = CURRENCY,
    exchange: str = "CCCAGG",
    toTs: Timestamp = time.time(),
    fromTs: Timestamp = 0,
    delay: float = 0.2,
    fields: Optional[List[str]] = None
) -> Optional[List[Dict]]:
    """
    Get historical price (day).

    :param coin: symbolic name of the coin (e.g. BTC)
    :param currency: short hand description of the currency (e.g. EUR)
    :param exchange: exchange to use (default: 'CCCAGG')
    :param toTs: return data before this timestamp. (Unix epoch time or datetime object)
    :param fromTs: return data after this timestamp. (Unix epoch time or datetime object)
    :param delay: time delay for API rate limit (default: 300 calls / 1 minute)
    :returns: dict of coin and currency price pairs
    """
    allHist: List[Dict] = []
    toTs_i = _format_timestamp(toTs)
    fromTs_i = _format_timestamp(fromTs)

    while fromTs_i <= toTs_i:
        p = get_historical_price_day(
            coin, _format_parameter(currency), _MAX_LIMIT_HISTO_API, exchange, toTs_i, fields=fields
        )
        if p is None:
            return None

        validHist = [
            elem
            for elem in p
            if elem["time"] >= fromTs_i and elem["open"] != 0 and elem["close"] != 0
        ]
        allHist = validHist + allHist

        if len(validHist) < len(p):
            break
        toTs_i = (min(p, key=lambda x: x["time"]))["time"] - 1
        time.sleep(delay)

    return allHist


def get_historical_price_day_all(
    coin: str, currency: str = CURRENCY, exchange: str = "CCCAGG", fields: Optional[List[str]] = None
) -> Optional[List[Dict]]:
    """
    Get historical price (day, all).

    :param coin: symbolic name of the coin (e.g. BTC)
    :param currency: short hand description of the currency (e.g. EUR)
    :param exchange: exchange to use (default: 'CCCAGG')
    :returns: dict of coin and currency price pairs
    """
    response = _query_cryptocompare(
        _URL_HIST_PRICE_DAY.format(
            coin, _format_parameter(currency), 1, exchange, time.time()
        )
        + "&allData=true", fields=fields
    )
    if response:
        return response["Data"]["Data"]
    return None


def get_historical_price_hour(
    coin: str,
    currency: str = CURRENCY,
    limit: int = LIMIT,
    toTs: Timestamp = time.time(),
    aggregate: int = 1,
    fields: Optional[List[str]] = None
) -> Optional[List[Dict]]:
    """
    Get historical price (hourly).


    :param coin: symbolic name of the coin (e.g. BTC)
    :param currency: short hand description of the currency (e.g. EUR)
    :param limit: number of data points (max. 2000)
    :param toTs: return data before this timestamp. (Unix epoch time or datetime object)
    :param aggregate: aggregation factor (default: 1)
    :returns: dict of coin and currency price pairs
    """
    # retry with another exchange
    exchange = get_exchange(coin, currency)
    print("-========CryptoCompare API Wrapper========-")
    print(_URL_HIST_PRICE_HOUR.format(
            coin, _format_parameter(currency), limit, exchange, _format_timestamp(toTs), aggregate
        ))
    response = _query_cryptocompare(
        _URL_HIST_PRICE_HOUR.format(
            coin, _format_parameter(currency), limit, exchange, _format_timestamp(toTs), aggregate
        ),
        fields=fields
    )
    if response:
        print(response)
        if "Data" in response:
            return response["Data"]["Data"]
        else:
            return response["Data"]
    return None


def get_historical_price_hour_from(
    coin: str,
    currency: str = CURRENCY,
    exchange: str = "CCCAGG",
    toTs: Timestamp = time.time(),
    fromTs: Timestamp = 0,
    delay: float = 0.2,
    fields: Optional[List[str]] = None
) -> Optional[List[Dict]]:
    """
    Get historical price (day).

    :param coin: symbolic name of the coin (e.g. BTC)
    :param currency: short hand description of the currency (e.g. EUR)
    :param exchange: exchange to use (default: 'CCCAGG')
    :param toTs: return data before this timestamp. (Unix epoch time or datetime object)
    :param fromTs: return data after this timestamp. (Unix epoch time or datetime object)
    :param delay: time delay for API rate limit (default: 300 calls / 1 minute)
    :returns: dict of coin and currency price pairs
    """
    allHist: List[Dict] = []
    toTs_i = _format_timestamp(toTs)
    fromTs_i = _format_timestamp(fromTs)

    while fromTs_i <= toTs_i:
        p = get_historical_price_hour(
            coin, _format_parameter(currency), _MAX_LIMIT_HISTO_API, exchange, toTs_i, fields=fields
        )
        if p is None:
            return None

        validHist = [
            elem
            for elem in p
            if elem["time"] >= fromTs_i and elem["open"] != 0 and elem["close"] != 0
        ]
        allHist = validHist + allHist

        if len(validHist) < len(p):
            break
        toTs_i = (min(p, key=lambda x: x["time"]))["time"] - 1
        time.sleep(delay)

    return allHist


def get_historical_price_minute(
    coin: str,
    currency: str = CURRENCY,
    limit: int = LIMIT,
    toTs: Timestamp = time.time(),
    aggregate: int = 30,
    fields: Optional[List[str]] = None
) -> Optional[List[Dict]]:
    """
    Get historical price (minute).

    :param coin: symbolic name of the coin (e.g. BTC)
    :param currency: short hand description of the currency (e.g. EUR)
    :param limit: number of data points (max. 2000)
    :param toTs: return data before this timestamp. (Unix epoch time or datetime object)
    :returns: dict of coin and currency price pairs
    """
    exchange = get_exchange(coin, currency)
    response = _query_cryptocompare(
        _URL_HIST_PRICE_MINUTE.format(
            coin, _format_parameter(currency), limit, exchange, _format_timestamp(toTs), aggregate
        ),
        fields=fields
    )
    if response:
        return response["Data"]["Data"]
    return None


def get_avg(
    coin: str, currency: str = CURRENCY, exchange: str = "CCCAGG", fields: Optional[List[str]] = None
) -> Optional[Dict]:
    """
    Get the average price

    :param coin: symbolic name of the coin (e.g. BTC)
    :param currency: short hand description of the currency (e.g. EUR)
    :param exchange: exchange to use (default: 'CCCAGG')
    :returns: dict of coin and currency price pairs
    """
    response = _query_cryptocompare(
        _URL_AVG.format(coin, currency, _format_parameter(exchange)),
        fields=fields
    )
    if response:
        return response["RAW"]
    return None


def get_exchange(coin: str, currency: str = CURRENCY,fields: Optional[List[str]] = None) -> Optional[Dict]:
    """
    Get the list of available exchanges.

    :returns: list of available exchanges
    """
    response = _query_cryptocompare(_URL_EXCHANGES.format(coin, currency),fields=fields)
    if response:
        exchanges = response["Data"]
        if exchanges:
            exchange = exchanges[0].get("exchange", "CCCAGG")
        else:
            exchange = "CCCAGG"
        return exchange
    return None


def get_pairs(exchange: str = None, fields: Optional[List[str]] = None) -> Optional[Dict]:
    """
    Get the list of available pairs for a particular exchange or for
    all exchanges (if exchange is None)

    :param exchange: exchange to use (default: None)
    :returns: list of available exchanges
    """
    if exchange is None:
        response = _query_cryptocompare(_URL_PAIRS.split("?")[0], fields=fields)

    else:
        response = _query_cryptocompare(_URL_PAIRS.format(exchange), fields=fields)
    if response:
        return response["Data"]
    return None
