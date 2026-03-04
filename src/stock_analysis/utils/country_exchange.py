# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Maps country codes (ISO 3166-1 alpha-2) to yfinance exchange ticker suffixes.
Default country is India (IN) using NSE suffix (.NS).
"""


class CountryExchangeMap:
    """
    Provides country-code to yfinance ticker suffix mappings and helpers
    for building qualified ticker symbols across markets.
    """

    # Primary exchange suffix per country (ISO 3166-1 alpha-2 -> yfinance suffix)
    _COUNTRY_SUFFIX: dict[str, str] = {
        "IN": ".NS",  # India – NSE (default)
        "IN_BSE": ".BO",  # India – BSE (alternative)
        "US": "",  # United States – no suffix
        "GB": ".L",  # United Kingdom – London Stock Exchange
        "DE": ".DE",  # Germany – XETRA
        "FR": ".PA",  # France – Euronext Paris
        "JP": ".T",  # Japan – Tokyo Stock Exchange
        "AU": ".AX",  # Australia – ASX
        "CA": ".TO",  # Canada – Toronto Stock Exchange
        "HK": ".HK",  # Hong Kong – HKEX
        "SG": ".SI",  # Singapore – SGX
        "CN": ".SS",  # China – Shanghai Stock Exchange
        "CN_SZ": ".SZ",  # China – Shenzhen Stock Exchange
        "KR": ".KS",  # South Korea – KRX KOSPI
        "TW": ".TW",  # Taiwan – TWSE
        "BR": ".SA",  # Brazil – B3
        "ZA": ".JO",  # South Africa – JSE
        "MX": ".MX",  # Mexico – BMV
        "IT": ".MI",  # Italy – Borsa Italiana
        "ES": ".MC",  # Spain – BME
        "NL": ".AS",  # Netherlands – Euronext Amsterdam
        "SE": ".ST",  # Sweden – Nasdaq Stockholm
        "NO": ".OL",  # Norway – Oslo Bors
        "DK": ".CO",  # Denmark – Nasdaq Copenhagen
        "FI": ".HE",  # Finland – Nasdaq Helsinki
        "NZ": ".NZ",  # New Zealand – NZX
        "TH": ".BK",  # Thailand – SET
        "MY": ".KL",  # Malaysia – Bursa Malaysia
        "ID": ".JK",  # Indonesia – IDX
        "PH": ".PS",  # Philippines – PSE
        "VN": ".VN",  # Vietnam – HOSE
        "CH": ".SW",  # Switzerland – SIX
        "AT": ".VI",  # Austria – Wiener Borse
        "BE": ".BR",  # Belgium – Euronext Brussels
        "PT": ".LS",  # Portugal – Euronext Lisbon
        "PK": ".KA",  # Pakistan – KSE
        "BD": ".DS",  # Bangladesh – DSE
    }

    # Human-readable country names
    _COUNTRY_NAMES: dict[str, str] = {
        "IN": "India (NSE)",
        "IN_BSE": "India (BSE)",
        "US": "United States",
        "GB": "United Kingdom",
        "DE": "Germany",
        "FR": "France",
        "JP": "Japan",
        "AU": "Australia",
        "CA": "Canada",
        "HK": "Hong Kong",
        "SG": "Singapore",
        "CN": "China (Shanghai)",
        "CN_SZ": "China (Shenzhen)",
        "KR": "South Korea",
        "TW": "Taiwan",
        "BR": "Brazil",
        "ZA": "South Africa",
        "MX": "Mexico",
        "IT": "Italy",
        "ES": "Spain",
        "NL": "Netherlands",
        "SE": "Sweden",
        "NO": "Norway",
        "DK": "Denmark",
        "FI": "Finland",
        "NZ": "New Zealand",
        "TH": "Thailand",
        "MY": "Malaysia",
        "ID": "Indonesia",
        "PH": "Philippines",
        "VN": "Vietnam",
        "CH": "Switzerland",
        "AT": "Austria",
        "BE": "Belgium",
        "PT": "Portugal",
        "PK": "Pakistan",
        "BD": "Bangladesh",
    }

    DEFAULT_COUNTRY = "IN"

    @classmethod
    def get_suffix(cls, country_code: str | None = None) -> str:
        """
        Return the yfinance ticker suffix for the given country code.
        Defaults to India (NSE) if no country_code is provided.

        Args:
            country_code: ISO 3166-1 alpha-2 code (e.g. "US", "IN", "GB").
                          Case-insensitive. Pass None to use default (India).

        Returns:
            Ticker suffix string (e.g. ".NS", ".L", "" for US).

        Raises:
            ValueError: If the country_code is not recognised.
        """
        if country_code is None:
            return cls._COUNTRY_SUFFIX[cls.DEFAULT_COUNTRY]

        normalised = country_code.upper().strip()
        if normalised not in cls._COUNTRY_SUFFIX:
            supported = ", ".join(sorted(cls._COUNTRY_SUFFIX.keys()))
            raise ValueError(
                f"Unknown country code '{country_code}'. "
                f"Supported codes: {supported}"
            )
        return cls._COUNTRY_SUFFIX[normalised]

    @classmethod
    def build_ticker(cls, symbol: str, country_code: str | None = None) -> str:
        """
        Build a fully-qualified yfinance ticker symbol.

        For Indian stocks the symbol is upper-cased and '.NS' is appended
        unless the symbol already carries a suffix.

        Args:
            symbol:       Raw ticker symbol (e.g. "RELIANCE", "AAPL").
            country_code: Country code. Defaults to "IN".

        Returns:
            Qualified ticker (e.g. "RELIANCE.NS", "AAPL").
        """
        symbol = symbol.upper().strip()
        # If the symbol already contains a dot-suffix, return as-is
        if "." in symbol:
            return symbol
        suffix = cls.get_suffix(country_code)
        return f"{symbol}{suffix}"

    @classmethod
    def list_supported_countries(cls) -> list[dict[str, str]]:
        """Return a list of supported country codes with their names and suffixes."""
        return [
            {
                "code": code,
                "name": cls._COUNTRY_NAMES.get(code, code),
                "suffix": suffix,
            }
            for code, suffix in sorted(cls._COUNTRY_SUFFIX.items())
        ]
