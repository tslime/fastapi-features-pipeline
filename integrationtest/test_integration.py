import os 
import sys 
import pytest 
import datetime 

from unittest.mock import patch, MagicMock 
from perk_app import calculate_member_features, get_ats_resp, offer_request,calculate_offer
from src.applications.prediction import MemberFeatures 
from src.applications.offer_engine import OfferRequest 


def test_caluclate_offer(): 
    logs = {}
    member_data = {
        "memberId": "member1",
        "lastTransactionPointsBought": 300,
        "lastTransactionRevenueUsd": 100,
        "lastTransactionType": "buy",
        "lastTransactionUtcTs": "2025-12-17 14:00:00"
    }

    with patch("requests.get") as fake_server, patch("perk_app.calculate_member_features") as fake_features, \
     patch("perk_app.get_ats_resp") as fake_ats_resp, patch("perk_app.offer_request") as fake_offer:
     
     fake_server.return_value.status_code = 404
     
     fake_features.return_value = MemberFeatures(
            AVG_POINTS_BOUGHT=200,
            AVG_REVENUE_USD=100,
            LAST_3_TRANSACTIONS_AVG_POINTS_BOUGHT=150,
            LAST_3_TRANSACTIONS_AVG_REVENUE_USD=100,
            PCT_BUY_TRANSACTIONS=1.0,
            PCT_GIFT_TRANSACTIONS=2.0,
            PCT_REDEEM_TRANSACTIONS=3.0,
            DAYS_SINCE_LAST_TRANSACTION=4 
        )

     fake_ats_resp.return_value = {"ats":1,"resp":2}
     fake_offer.return_value = {"offer":"35% bonus"}
     
     result = calculate_offer("member1",member_data,logs)


    assert result["memberId"] == "member1"
    assert result["offer"] == "35% bonus"