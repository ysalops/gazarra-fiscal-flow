from copy import deepcopy
from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException

from app.data.fiscal_mock import FISCAL_MOCK_DATA
from app.schemas.fiscal import (
    FiscalCompany,
    FiscalDashboardResponse,
)
from app.services.fiscal.base_provider import FiscalDataProvider


class MockFiscalProvider(FiscalDataProvider):

    def list_companies(self) -> List[FiscalCompany]:
        companies = []

        for company_data in FISCAL_MOCK_DATA.values():
            companies.append(
                FiscalCompany(
                    **company_data["company"]
                )
            )

        return companies

    def list_competences(
        self,
        company_id: int
    ) -> List[str]:
        company_data = FISCAL_MOCK_DATA.get(company_id)

        if not company_data:
            raise HTTPException(
                status_code=404,
                detail="Empresa não encontrada."
            )

        return [
            item["competence"]
            for item in company_data["history"]
        ]

    def get_dashboard(
        self,
        company_id: int,
        competence: str
    ) -> FiscalDashboardResponse:
        company_data = FISCAL_MOCK_DATA.get(company_id)

        if not company_data:
            raise HTTPException(
                status_code=404,
                detail="Empresa não encontrada."
            )

        history = company_data["history"]

        current_index = next(
            (
                index
                for index, item in enumerate(history)
                if item["competence"] == competence
            ),
            None
        )

        if current_index is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Competência não encontrada "
                    "para esta empresa."
                )
            )

        current_item = history[current_index]
        result = deepcopy(company_data)

        result["metadata"] = {
            "source": "mock",
            "environment": "demo",
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        result["competence"] = competence

        result["revenue"] = {
            "without_st": current_item[
                "revenue_without_st"
            ],
            "with_st": current_item[
                "revenue_with_st"
            ],
        }

        result["taxes"] = {
            "das": current_item["das"],
            "effective_rate": current_item[
                "effective_rate"
            ],
            "st": current_item["st"],
            "difal": current_item["difal"],
        }

        result["monthly_comparison"] = (
            self._build_monthly_comparison(
                history,
                current_index
            )
        )

        result["yearly_comparison"] = (
            self._build_yearly_comparison(
                history,
                current_index
            )
        )

        result["history"] = self._history_until(
            history,
            current_index
        )

        result["obligations"] = (
            self._filter_obligations(
                company_data["obligations"],
                competence
            )
        )

        return FiscalDashboardResponse(**result)

    def _build_monthly_comparison(
        self,
        history: list,
        current_index: int
    ) -> list:
        if current_index == 0:
            return []

        current = history[current_index]
        previous = history[current_index - 1]

        return [
            self._comparison_item(
                "DAS",
                current["das"],
                previous["das"]
            ),
            self._comparison_item(
                "ST",
                current["st"],
                previous["st"]
            ),
            self._comparison_item(
                "DIFAL",
                current["difal"],
                previous["difal"]
            ),
        ]

    def _build_yearly_comparison(
        self,
        history: list,
        current_index: int
    ) -> list:
        if current_index < 12:
            return []

        current = history[current_index]
        previous_year = history[
            current_index - 12
        ]

        return [
            self._comparison_item(
                "DAS",
                current["das"],
                previous_year["das"]
            ),
            self._comparison_item(
                "ST",
                current["st"],
                previous_year["st"]
            ),
            self._comparison_item(
                "DIFAL",
                current["difal"],
                previous_year["difal"]
            ),
        ]

    def _comparison_item(
        self,
        name: str,
        current_value: float,
        previous_value: float
    ) -> dict:
        if previous_value == 0:
            variation = 0
        else:
            variation = (
                (
                    current_value - previous_value
                ) / previous_value
            ) * 100

        return {
            "name": name,
            "current_value": round(
                current_value,
                2
            ),
            "previous_value": round(
                previous_value,
                2
            ),
            "variation_percentage": round(
                variation,
                2
            ),
        }

    def _history_until(
        self,
        history: list,
        current_index: int
    ) -> list:
        start_index = max(
            0,
            current_index - 11
        )

        return history[
            start_index:current_index + 1
        ]

    def _filter_obligations(
        self,
        obligations: list,
        competence: str
    ) -> list:
        return [
            item
            for item in obligations
            if item["competence"] == competence
        ]
