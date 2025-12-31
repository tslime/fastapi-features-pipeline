from pydantic import BaseModel


class MemberData(BaseModel):
    memberId: str
    lastTransactionUtcTs: str
    lastTransactionType: str
    lastTransactionPointsBought: float
    lastTransactionRevenueUsd: float

