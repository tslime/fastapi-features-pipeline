import os
import sys
import pytest
import datetime

from unittest.mock import patch, MagicMock
from perk_app import calculate_member_features, get_ats_resp, offer_request
from src.applications.prediction import MemberFeatures
from src.applications.offer_engine import OfferRequest


#Features calculations tests

def test_member_features():
    logs ={}

    transactions = [{
            "lastTransactionPointsBought": 100,
            "lastTransactionRevenueUsd": 50,
            "lastTransactionType": "buy",
            "lastTransactionUtcTs": "2025-12-14 10:00:00"
        },

        {
            "lastTransactionPointsBought": 150,
            "lastTransactionRevenueUsd": 100,
            "lastTransactionType": "redeem",
            "lastTransactionUtcTs": "2025-12-15 11:00:00"
        },
        {
            "lastTransactionPointsBought": 200,
            "lastTransactionRevenueUsd": 150,
            "lastTransactionType": "buy",
            "lastTransactionUtcTs": "2025-12-16 12:00:00"
        },
        {
            "lastTransactionPointsBought": 250,
            "lastTransactionRevenueUsd": 200,
            "lastTransactionType": "gift",
            "lastTransactionUtcTs": "2025-12-17 13:00:00"
        },
        {
            "lastTransactionPointsBought": 300,
            "lastTransactionRevenueUsd": 250,
            "lastTransactionType": "redeem",
            "lastTransactionUtcTs": "2025-12-18 14:00:00"
        }
        ]
    
    features_result = calculate_member_features(transactions,logs)
    
    assert features_result.AVG_POINTS_BOUGHT == 200
    assert features_result.AVG_REVENUE_USD == 150
    assert features_result.LAST_3_TRANSACTIONS_AVG_POINTS_BOUGHT == 250
    assert features_result.LAST_3_TRANSACTIONS_AVG_REVENUE_USD == 200
    assert features_result.PCT_BUY_TRANSACTIONS == pytest.approx(0.4)
    assert features_result.PCT_GIFT_TRANSACTIONS == pytest.approx(0.2)
    assert features_result.PCT_REDEEM_TRANSACTIONS == pytest.approx(0.4)

    projected_days = expected_days = (datetime.datetime.now() - datetime.datetime.strptime("2025-12-18 14:00:00", "%Y-%m-%d %H:%M:%S")).days
    assert features_result.DAYS_SINCE_LAST_TRANSACTION == projected_days



def test_member_features_edge_case():
    logs ={}

    transactions = [{
            "lastTransactionPointsBought": 100,
            "lastTransactionRevenueUsd": 50,
            "lastTransactionType": "buy",
            "lastTransactionUtcTs": "2025-12-14 10:00:00"
        },

        {
            "lastTransactionPointsBought": 150,
            "lastTransactionRevenueUsd": 100,
            "lastTransactionType": "redeem",
            "lastTransactionUtcTs": "2025-12-15 11:00:00"
        }
        ]
    
    features_result = calculate_member_features(transactions,logs)
    
    assert features_result.AVG_POINTS_BOUGHT == 125
    assert features_result.AVG_REVENUE_USD == 75
    assert features_result.LAST_3_TRANSACTIONS_AVG_POINTS_BOUGHT == 125
    assert features_result.LAST_3_TRANSACTIONS_AVG_REVENUE_USD == 75
    assert features_result.PCT_BUY_TRANSACTIONS == pytest.approx(0.5)
    assert features_result.PCT_GIFT_TRANSACTIONS == pytest.approx(0.0)
    assert features_result.PCT_REDEEM_TRANSACTIONS == pytest.approx(0.5)

    projected_days = (datetime.datetime.now() - datetime.datetime.strptime("2025-12-15 11:00:00", "%Y-%m-%d %H:%M:%S")).days
    assert features_result.DAYS_SINCE_LAST_TRANSACTION == projected_days


#ats and resp feching test

def test_ats_resp_fetching():

    logs = {}
    memb_features = MemberFeatures(AVG_POINTS_BOUGHT=20, 
                                   AVG_REVENUE_USD=50, 
                                   LAST_3_TRANSACTIONS_AVG_POINTS_BOUGHT=10,
                                   LAST_3_TRANSACTIONS_AVG_REVENUE_USD=20, 
                                   PCT_BUY_TRANSACTIONS=2, 
                                   PCT_GIFT_TRANSACTIONS=3,
                                   PCT_REDEEM_TRANSACTIONS=4, 
                                   DAYS_SINCE_LAST_TRANSACTION=5)
    
    with patch("requests.post") as fake_server:
        fake_server.side_effect = [
        MagicMock(
            json=lambda: {"prediction": 5},
            raise_for_status=lambda: None,
            status_code=200
        ),
        MagicMock(
            json=lambda: {"prediction": 9},
            raise_for_status=lambda: None,
            status_code=200
        )
        ]
        
        ats_resp_results = get_ats_resp(memb_features,logs)

        assert ats_resp_results["ats"] == 5
        assert ats_resp_results["resp"] == 9
        assert logs["ats"] == 5
        assert logs["resp"] == 9



def test_offer_request():
    target_offer = OfferRequest(ats_prediction=10, resp_prediction=20)

    with patch("requests.post") as fake_server:
        fake_server.return_value = MagicMock(
            json=lambda: {"offer": "50% discount"},
            raise_for_status=lambda: None,
            status_code=200,
        )

        my_offer = offer_request(target_offer)

    assert my_offer == {"offer": "50% discount"}
