from abc import ABC, abstractmethod
from typing import List

from app.schemas.fiscal import (
    FiscalCompany,
    FiscalDashboardResponse,
)


class FiscalDataProvider(ABC):

    @abstractmethod
    def list_companies(
        self
    ) -> List[FiscalCompany]:
        """
        Retorna as empresas disponíveis
        para consulta fiscal.
        """
        raise NotImplementedError


    @abstractmethod
    def list_competences(
        self,
        company_id: int
    ) -> List[str]:
        """
        Retorna as competências disponíveis
        para uma empresa.
        """
        raise NotImplementedError


    @abstractmethod
    def get_dashboard(
        self,
        company_id: int,
        competence: str
    ) -> FiscalDashboardResponse:
        """
        Retorna os dados completos do
        Dashboard Fiscal.
        """
        raise NotImplementedError