import pandas as pd
from unittest.mock import patch
import nyc_commuter_homes
import nyc_commuter_homes_comprehensive


def test_search_location_port_authority_nyc_commuter_homes():
    stop = pd.Series({
        "stop_name": "Port Authority Bus Terminal",
        "stop_lat": 40.757,
        "stop_lon": -73.990,
        "source": "bus"
    })
    with patch('nyc_commuter_homes.scrape_property') as mock_scrape:
        mock_scrape.return_value = pd.DataFrame()
        nyc_commuter_homes.search_properties_near_stop(stop)
        assert mock_scrape.call_args[1]['location'] == "New York, NY"


def test_infer_search_location_port_authority_comprehensive():
    stop = pd.Series({
        "stop_name": "Port Authority Bus Terminal",
        "stop_lat": 40.757,
        "stop_lon": -73.990,
        "source": "bus"
    })
    result = nyc_commuter_homes_comprehensive.infer_search_location(stop)
    assert result == "New York, NY"
