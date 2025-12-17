# ML Application Engineer Take Home Exam
Welcome to the ML Application Engineer take home assignment.

Your task is to build a FastAPI application that will take in requests, process it and send it to various applications to assign a member an offer based on the predictions created.

## Setup
This project uses python 3.11. The requirements can be installed by `pip install -r requirements.txt`

The member_data.csv file represents the data your application will be receiving.

The applications in the applications folder represent external applications the application you create will be sending requests to. You can run them locally, but cannot change their code as they should be treated as applications created outside of your team.

## The Task
- Create a Python process which will:

    1. Convert the `member_data.csv` file into a stream you will send to your application. This stream will act as the requests being sent to the application you will be designing, where each row is a request to your application. The stream should send requests to your application in the order they appear in the member_data.csv.
       1. The stream should send requests one at a time, but can do so in quick succession. 
       2. Your application should be able to process multiple requests it receives at the same time.
    
    2. Get the previous data for that member from the `member_data` application. Both incoming and existing data will be required to calculate member features in the next step.

    3. Transform the data received into member features that will be used for predictions, which has the following features:

        - AVG_POINTS_BOUGHT, calculated as $\text{total points bought} / \text{number of transactions}$
        - AVG_REVENUE_USD, calculated as $\text{total transaction revenue} / \text{number of transactions}$
        - LAST_3_TRANSACTIONS_AVG_POINTS_BOUGHT, which is the AVG_POINTS_BOUGHT for the 3 most recent transactions
        - LAST_3_TRANSACTIONS_AVG_REVENUE_USD, which is the AVG_REVENUE_USD for the 3 most recent transactions
        - PCT_BUY_TRANSACTIONS, calculated as $\text{Number of transactions where transaction type was BUY} / \text{number of transactions}$
        - PCT_GIFT_TRANSACTIONS, calculated as $\text{Number of transactions where transaction type was GIFT} / \text{number of transactions}$
        - PCT_REDEEM_TRANSACTIONS, calculated as $\text{Number of transactions where transaction type was REDEEM} / \text{number of transactions}$
        - DAYS_SINCE_LAST_TRANSACTION, which is the number of days since a member's last transaction. (ie. Current day in UTC - last day of transaction in UTC)

    4. POST these inputs to the ATS (Average Transaction Size) and RESP (Probability to respond) prediction endpoints to get the estimated amount and likelihood of purchase respectively per member. These endpoints are a part of the `prediction` application

    5. Combine the ATS and RESP predictions from the previous step into the OfferRequest object (found in `offer_engine.py`). This object can then be sent to the offer application found in the same module, which determines what offer should be given to the member

    6. Respond to the request you have received in step #1 with the offer. The response's format should be like `{"memeberId": "member1", "offer": "50% Discount"}`

    7. Log any data you produce thorougout the process. The logs should easily be able to be used for data analysis and analyzing application performance, and should include the following:
        - Member features
        - Predictions
        - Offers assigned to each member
        - Latency and throughput of each step (e.g. time taken to read member data, to transformm...)
        - Any other data that can be used for performance analysis

    8. At some point send the request you receive in step #1 to the member_data application so the member data is there the next time the request is made for that member.



## What we're looking for
- Processing speed/Parallelism/Latency
- Design patterns/programming paradigm
- Scalability
- Basic explanation of how to run the code and what the code does
- Unit testing
- Error handling
- Code readability
- Logging

## Nice to Have
- CI/CD
- Integration and End-to-end tests
