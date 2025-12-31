from pydantic import BaseModel

class OfferRequest(BaseModel):
    ats_prediction: float
    resp_prediction: float