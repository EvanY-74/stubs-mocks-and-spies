from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass
class SaleRecord:
    product_id: str
    units_sold: int
    revenue: float

class SalesRepository(ABC):
    @abstractmethod
    def get_sales(self, month: int, year: int) -> List[SaleRecord]:
        pass