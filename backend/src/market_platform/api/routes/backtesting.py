from fastapi import APIRouter, HTTPException
from ..schemas import BacktestRequest, BacktestResponse
from ...services import backtesting_service
from ...backtesting.backtest_config import BacktestConfig

router = APIRouter(prefix="/backtesting", tags=["backtesting"])

@router.post("/run", response_model=BacktestResponse)
def run_backtesting(request: BacktestRequest):
    try:
        return backtesting_service.run_backtesting(
            tickers=request.tickers,
            strategy_name=request.strategy,
            config=BacktestConfig(**request.config.model_dump()),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))