import os
import sys
import csv
import logging
import requests

from pathlib import Path

logging.basicConfig(
    level = logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename = 'processed_requests.log',
    filemode = 'a'
)

class Eventstreamer:
    
    def __init__(self,p:str):
        self.path = p
        file = Path(p)
        if not file.is_file():
            raise FileNotFoundError("File does not exist! \n")
        elif file.stat().st_size == 0:
            raise ValueError("File is empty! \n")

        

    def requests_manager(self):
        try:

            with open(self.path,"r",encoding="utf-8") as f:
                stream = csv.DictReader(f)
                self.send_requests(stream)
                
        except FileNotFoundError:
            logging.error("Error opening file!")
        except csv.Error as e:
            logging.error(f"CSV error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

    
    def send_requests(self,s):
        skipped_count = 0
        sent_count = 0
        failed_count = 0
        i = 1
        
        for row in s:
            if row["memberId"] == "" or row["lastTransactionUtcTs"] == "" or row["lastTransactionType"] == "" or row["lastTransactionPointsBought"] == "" or row["lastTransactionRevenueUSD"] == "":
                logging.info(f"Row {i} skipped: empty fields found")
                skipped_count += 1
                continue
            else:
                try:
                    row = self.transform_row(row)
                    request_response = requests.post("http://localhost:6000/api/requests/v1",json=row)
                    if  200 <= request_response.status_code < 300:
                        logging.info(f"Row {i} sent successfully: {request_response.status_code}")
                        sent_count += 1 
                    else:
                        logging.warning(f"Error while attempting to process row {i} {request_response.status_code}")
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    logging.error(f"Exception sending row {i}: {e}")

              
            i += 1

        logging.info("\n\n")
        logging.info("===================================================================")
        logging.info(f"Successfully sent rows count: {sent_count}")
        logging.info(f"Skipped row count: {skipped_count}")
        logging.info(f"Unsuccesful sent rows count: {failed_count}")
    
    
    def transform_row(self,r):
        #Case mismatch in the revenue field (cf. lastTransactionRevenueUSD in member_data.csv and lastTransactionRevenueUsd in member_data.py)
        #Solution: rename field for it to be accepted and inserted 
        #We also need float convertion for these fields because they are in a string format
        r["lastTransactionRevenueUsd"] = float(r.pop("lastTransactionRevenueUSD"))          
        r["lastTransactionPointsBought"] = float(r["lastTransactionPointsBought"])
        return r



print("\nStream started.... \n")
print("========================\n\n")

s = Eventstreamer("member_data.csv")
s.requests_manager()

print("========================\n")
print("Stream ended! \n")