"""Unit tests for CountryExchangeMap."""

import pytest

from stock_analysis.utils.country_exchange import CountryExchangeMap


class TestGetSuffix:
    def test_default_returns_india_nse(self):
        assert CountryExchangeMap.get_suffix(None) == ".NS"

    def test_india_nse(self):
        assert CountryExchangeMap.get_suffix("IN") == ".NS"

    def test_india_nse_lowercase(self):
        assert CountryExchangeMap.get_suffix("in") == ".NS"

    def test_india_bse(self):
        assert CountryExchangeMap.get_suffix("IN_BSE") == ".BO"

    def test_us_empty_suffix(self):
        assert CountryExchangeMap.get_suffix("US") == ""

    def test_uk(self):
        assert CountryExchangeMap.get_suffix("GB") == ".L"

    def test_japan(self):
        assert CountryExchangeMap.get_suffix("JP") == ".T"

    def test_unknown_country_raises(self):
        with pytest.raises(ValueError, match="Unknown country code"):
            CountryExchangeMap.get_suffix("XX")


class TestBuildTicker:
    def test_indian_stock_appends_ns(self):
        assert CountryExchangeMap.build_ticker("reliance", "IN") == "RELIANCE.NS"

    def test_us_stock_no_suffix(self):
        assert CountryExchangeMap.build_ticker("AAPL", "US") == "AAPL"

    def test_already_qualified_symbol_unchanged(self):
        assert CountryExchangeMap.build_ticker("RELIANCE.BO", "IN") == "RELIANCE.BO"

    def test_default_country_is_india(self):
        assert CountryExchangeMap.build_ticker("TCS") == "TCS.NS"

    def test_symbol_uppercased(self):
        assert CountryExchangeMap.build_ticker("wipro", "IN") == "WIPRO.NS"

    def test_london_stock(self):
        assert CountryExchangeMap.build_ticker("HSBA", "GB") == "HSBA.L"


class TestListSupportedCountries:
    def test_returns_list(self):
        result = CountryExchangeMap.list_supported_countries()
        assert isinstance(result, list)
        assert len(result) > 10

    def test_each_entry_has_required_keys(self):
        for entry in CountryExchangeMap.list_supported_countries():
            assert "code" in entry
            assert "name" in entry
            assert "suffix" in entry

    def test_in_is_present(self):
        codes = [e["code"] for e in CountryExchangeMap.list_supported_countries()]
        assert "IN" in codes

    def test_us_is_present(self):
        codes = [e["code"] for e in CountryExchangeMap.list_supported_countries()]
        assert "US" in codes
