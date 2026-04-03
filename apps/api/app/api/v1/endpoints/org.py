from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import get_principal
from app.models.governance import PortfolioRecord, PortfolioSummary, TeamRecord, UserRecord
from app.models.security import Principal
from app.services.governance_service import governance_service

router = APIRouter()


@router.get("/users", response_model=list[UserRecord])
def list_users(
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[UserRecord]:
    return governance_service.list_users(principal)


@router.get("/teams", response_model=list[TeamRecord])
def list_teams(
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[TeamRecord]:
    return governance_service.list_teams(principal)


@router.get("/portfolios", response_model=list[PortfolioRecord])
def list_portfolios(
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[PortfolioRecord]:
    return governance_service.list_portfolios(principal)


@router.get("/portfolio-summaries", response_model=list[PortfolioSummary])
def list_portfolio_summaries(
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[PortfolioSummary]:
    return governance_service.list_portfolio_summaries(principal)
