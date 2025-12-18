import os
import sys
import json
import logging
import requests
import time
import csv


from fastapi import FastAPI
from typing import Dict, Any, List
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.applications.member_data import MemberData
from src.applications.prediction import MemberFeatures
from src.applications.offer_engine import OfferRequest
from httpx import AsyncClient
from contextlib import asynccontextmanager

c = None

#http logs
logging.basicConfig(
    level = logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename = 'logs/processed_requests.log',
    filemode = 'a'
)


#Log file for relevant metrics initialization 
logs_file = "logs/transactions.csv"
csv_columns = ['memberId', 'AVG_POINTS_BOUGHT', 'AVG_REVENUE_USD', 'LAST_3_TRANSACTIONS_AVG_POINTS_BOUGHT',
'LAST_3_TRANSACTIONS_AVG_REVENUE_USD', 'PCT_BUY_TRANSACTIONS', 'PCT_GIFT_TRANSACTIONS', 'PCT_REDEEM_TRANSACTIONS', 
'DAYS_SINCE_LAST_TRANSACTION', 'ats', 'resp', 'offer', 'fetch_member_data_latency', 'calculate_features_latency', 
'get_predictions_latency', 'assign_offer_latency', 'total_latency']

if not os.path.exists(logs_file):
    with open(logs_file,"w",newline="") as f:
        w = csv.DictWriter(f,fieldnames=csv_columns)
        w.writeheader()



#Application code starts here

@asynccontextmanager
async def lifespan(app: FastAPI):
    global c
    c = AsyncClient()
    yield
    await c.aclose()

app = FastAPI(lifespan=lifespan)


@app.post("/api/requests/v1")
async def handle_request(data: Dict[str,Any]):

    request_logs = {"memberId": data["memberId"]}

    member_offer = await calculate_offer(data["memberId"],data,request_logs)
    await save_member_data(data["memberId"],data)
    record_logs(request_logs)

    return member_offer
    

#Core algorithm, namely the orchestrator, that calculates an offer
async def calculate_offer(m_id:str,data: Dict[str,Any],r_logs):

    member_start_time = time.time()
    
    transactions = await c.get(f"http://localhost:6001/member_data/{m_id}")
    if transactions.status_code == 404:
        logging.info(f"Member {m_id} does not have purchase history: {transactions.status_code}")
        transactions = []
    else:
        logging.info(f"Member history fetched successfully: {transactions.status_code}")
        transactions = transactions.json()
        
    member_end_time = time.time()


    features_start_time = time.time()
    transactions.append(data)
    mem_features = calculate_member_features(transactions,r_logs)
    features_end_time = time.time()
   
    prediction_start_time = time.time()
    ats_resp = await get_ats_resp(mem_features,r_logs)
    prediction_end_time = time.time()

    offer_start_time = time.time()
    offer_object = OfferRequest(ats_prediction = ats_resp["ats"],
                    resp_prediction = ats_resp["resp"])
    special_offer = await offer_request(offer_object)
    offer_end_time = time.time()

    r_logs["offer"] = special_offer['offer']

    #Latency calculations
    r_logs["fetch_member_data_latency"] = member_end_time - member_start_time
    r_logs["calculate_features_latency"] = features_end_time - features_start_time
    r_logs["get_predictions_latency"] = prediction_end_time - prediction_start_time
    r_logs["assign_offer_latency"] = offer_end_time - offer_start_time
    r_logs["total_latency"] = r_logs["fetch_member_data_latency"] + r_logs["calculate_features_latency"] + r_logs["get_predictions_latency"] + r_logs["assign_offer_latency"]
    
    return {"memberId":m_id,"offer":special_offer["offer"]}


#Support function that calculate a member's features
def calculate_member_features(m_data:List[Dict[str,Any]],r_logs):
    mf = MemberFeatures(AVG_POINTS_BOUGHT=0,AVG_REVENUE_USD=0,
    LAST_3_TRANSACTIONS_AVG_POINTS_BOUGHT=0,LAST_3_TRANSACTIONS_AVG_REVENUE_USD=0,
    PCT_BUY_TRANSACTIONS=0,PCT_GIFT_TRANSACTIONS=0,PCT_REDEEM_TRANSACTIONS=0,
    DAYS_SINCE_LAST_TRANSACTION=0
    )

    r_logs["AVG_POINTS_BOUGHT"] = mf.AVG_POINTS_BOUGHT = sum(x["lastTransactionPointsBought"] for x in m_data)/len(m_data)
    r_logs["AVG_REVENUE_USD"]= mf.AVG_REVENUE_USD = sum(x["lastTransactionRevenueUsd"] for x in m_data)/len(m_data)

    last_3 = m_data[-3:]
    r_logs["LAST_3_TRANSACTIONS_AVG_POINTS_BOUGHT"] =  mf.LAST_3_TRANSACTIONS_AVG_POINTS_BOUGHT = sum(x["lastTransactionPointsBought"] for x in last_3)/len(last_3)
    r_logs["LAST_3_TRANSACTIONS_AVG_REVENUE_USD"] = mf.LAST_3_TRANSACTIONS_AVG_REVENUE_USD = sum(x["lastTransactionRevenueUsd"] for x in last_3)/len(last_3)

    
    r_logs["PCT_BUY_TRANSACTIONS"] = mf.PCT_BUY_TRANSACTIONS = sum(x["lastTransactionType"] == "buy" for x in m_data)/len(m_data)
    r_logs["PCT_GIFT_TRANSACTIONS"] = mf.PCT_GIFT_TRANSACTIONS = sum(x["lastTransactionType"] == "gift" for x in m_data)/len(m_data)
    r_logs["PCT_REDEEM_TRANSACTIONS"] = mf.PCT_REDEEM_TRANSACTIONS = sum(x["lastTransactionType"] == "redeem" for x in m_data)/len(m_data)

    r_logs["DAYS_SINCE_LAST_TRANSACTION"] = mf.DAYS_SINCE_LAST_TRANSACTION = (datetime.now() - datetime.strptime(m_data[-1]["lastTransactionUtcTs"], '%Y-%m-%d %H:%M:%S')).days
    

    return mf

#Support function that retrives he ats and resp predictions
async def get_ats_resp(memb_features: MemberFeatures,r_logs):
    try:
        ats_request = await c.post("http://localhost:6002/ml/ats/predict",json=memb_features.model_dump())
        ats_request.raise_for_status() 
        r_logs["ats"] = ats_pred = ats_request.json()["prediction"]
        logging.info(f"ATS fetched successfuly: {ats_request.status_code} | ")
    except Exception as e:
        logging.info(f"ATS fetching failed: {e}")
        raise 

    try:
        resp_request = await c.post("http://localhost:6002/ml/resp/predict",json=memb_features.model_dump())
        resp_request.raise_for_status() 
        r_logs["resp"] = resp_pred = resp_request.json()["prediction"]
        logging.info(f"RESP fetched successfully: {resp_request.status_code} | ")
    except Exception as e:
        logging.info(f"RESP fetching failed: {e}")
        raise

    return {"ats": ats_pred, "resp": resp_pred}

#support function that calculates the offer on the basis of the values retrieved by get_ats_resp function
async def offer_request(offer: OfferRequest):
    try:
        calc_offer = await c.post("http://localhost:6003/offer/assign",json=offer.model_dump())
        calc_offer.raise_for_status() 
        logging.info(f"Offer fetched successfully: {calc_offer.status_code}")
    except Exception as e:
        logging.info(f"Error fetching offer: {e}")
        raise

    return calc_offer.json()

async def save_member_data(m_id:str,d:Dict[str,Any]):
    try:
        save_member_transcation = await c.post("http://localhost:6001/member_data",json=d)
        logging.info(f"Member {m_id} data successfully saved: {save_member_transcation.status_code}")
    except Exception as e:
        logging.info(f"Error while attempting to save member {m_id} data: {e}")
        #raise #No raising here or else we dont record all the features of the member. Though we have it logged at least 


#support function that stores relevant metrics in a csv format ready to be used for stochastic analysis
def record_logs(logs: Dict):
    with open(logs_file,"a",newline="") as f:
        w = csv.DictWriter(f,fieldnames=csv_columns)
        w.writerow(logs)



