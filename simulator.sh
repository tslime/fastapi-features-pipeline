#!/bin/bash

rm logs/transactions.csv
rm logs/requests_sent.log
rm logs/processed_requests.log

export MEMBER_DATA_URL="http://localhost:6001"
export ML_SERVICE_URL="http://localhost:6002"
export OFFER_SERVICE_URL="http://localhost:6003"

python3 -m pytest -s

PYTHONPATH=$(pwd) fastapi dev src/applications/member_data.py --port 6001 > /dev/null 2>&1 &
PYTHONPATH=$(pwd) fastapi dev src/applications/prediction.py --port 6002 > /dev/null 2>&1 &
PYTHONPATH=$(pwd) fastapi dev src/applications/offer_engine.py --port 6003 > /dev/null 2>&1 &
PYTHONPATH=$(pwd) fastapi dev myapp/perk_app.py --port 6000 > /dev/null 2>&1 &

sleep 3

python3 myapp/events_streamer.py

pkill -f "fastapi dev"