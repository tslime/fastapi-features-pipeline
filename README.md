# Introduction 

This project implements a FastAPI-based application that processes member transaction data, calculates behavioral features, retrieves predictions from external applications, and assigns personalized offers based on those predictions.

# Approach & Analysis


When a member has no previous purchase history, we initialize their features with actual values from their current transaction rather than zeros. This approach avoids artificially penalizing new members.

## Why not use zeros for features

- Zero features would make new members appear inactive or unengaged
- This could result in poor offer assignments (e.g., 35% Bonus for all new users)
- New members deserve fair evaluation based on their current behavior

## Example

### Scenario: New Member A's First Transaction

Transaction: 5000 points purchased, $50 revenue

If we used zero initialization:

- AVG_POINTS_BOUGHT = 0
- AVG_REVENUE_USD = 0
- ATS prediction ≈ 0 (based on zeros)
- Offer assigned: 35% Bonus (low-value offer for inactive users)
- Result: New member penalized despite healthy first purchase

With actual transaction values:

- AVG_POINTS_BOUGHT = 5000
- AVG_REVENUE_USD = 50
- ATS prediction ≈ 5000 (based on actual purchase)
- Offer assigned: 50% Discount (better offer for engaged user)
- Result: New member fairly rewarded for their purchase behavior

## Proposed implementation

We append the current transaction to an empty history list and calculate features normally. This ensures new members receive offers proportional to their actual engagement.


# How to run

## Non-verbose mode

For non-verbose, which shows only progress from the event_streamer.py use the bashscript in simulator.sh


## Verbose mode

To test the app in verbose mode open five terminals and run the following:

PYTHONPATH=$(pwd) fastapi dev src/applications/member_data.py --port 6001 (terminal 1)
PYTHONPATH=$(pwd) fastapi dev src/applications/prediction.py --port 6002 (terminal 2)
PYTHONPATH=$(pwd) fastapi dev src/applications/offer_engine.py --port 6003 (terminal 3)
PYTHONPATH=$(pwd) fastapi dev myapp/perk_app.py --port 6000  (terminal 4)

python3 events_streamer 

# Logs 

At the end of the simulation, the app generates the following logs in the `logs/` folder:

- requests_sent.log: HTTP records of all requests sent to perk_app, with a summary of successfully sent, failed, and skipped requests.

- transactions.csv**: Essential metrics and feature values for each processed request, including member features, predictions, offer assigned, and latency measurements.


# Project structure

```
Plusgrade/
├── myapp/
│   ├── perk_app.py
│   └── events_streamer.py
├── src/
│   ├── applications/
│   │   ├── member_data.py
│   │   ├── prediction.py
│   │   ├── offer_engine.py
│   │   └── base_application.py
│   └── requirements.txt
├── tests/
│   ├── unittests/
│   │   └── test_units.py
│   └── integrationtest/
│       └── test_integration.py
├── data/
│   └── member_data.csv
├── logs/
│   ├── requests_sent.log
│   └── transactions.csv
├── simulator.sh
└── .gitlab-ci.yml
```

# CI/CD

A CI/CD pipeline (`.gitlab-ci.yml`) has been provided which:

- Installs dependencies
- Runs unit and integration tests
- Launches all supporting applications
- Executes the end-to-end test with events_streamer
- Generates and saves logs as artifacts