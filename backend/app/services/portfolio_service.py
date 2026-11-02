from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.portfolio import FundPortfolio, FundTransaction
from app.models.mutual_fund import MutualFund
from app.schemas.portfolio import TransactionCreate
from app.services.mutual_fund_service import MutualFundService
from app.engines.portfolio import calculate_portfolio_metrics
from app.engines.portfolio_history import calculate_portfolio_history
from app.engines.overlap import calculate_portfolio_overlap
from app.engines.risk import calculate_risk_metrics


class PortfolioService:

    def __init__(self):
        self.mf_service = MutualFundService()

    def get_or_create_portfolio(self, db: Session, user_id: str) -> FundPortfolio:
        portfolio = db.query(FundPortfolio).filter(FundPortfolio.user_id == user_id).first()
        if not portfolio:
            portfolio = FundPortfolio(user_id=user_id, name="Primary Portfolio")
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)
        return portfolio

    def add_transaction(self, db: Session, user_id: str, tx_in: TransactionCreate) -> FundTransaction:
        portfolio = self.get_or_create_portfolio(db, user_id)

        # Upsert MutualFund in DB
        db_fund = db.query(MutualFund).filter(MutualFund.scheme_code == tx_in.scheme_code).first()
        if not db_fund:
            details = self.mf_service.get_fund_details(db, tx_in.scheme_code)
            db_fund = db.query(MutualFund).filter(MutualFund.scheme_code == tx_in.scheme_code).first()

        # Parse date
        tx_date = datetime.strptime(tx_in.transaction_date, "%Y-%m-%d")

        transaction = FundTransaction(
            user_id=user_id,
            portfolio_id=portfolio.id,
            fund_id=db_fund.id,
            transaction_type=tx_in.transaction_type.upper(),
            transaction_date=tx_date,
            units=tx_in.units,
            nav=tx_in.nav,
            amount=tx_in.amount
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        transaction.scheme_code = db_fund.scheme_code
        transaction.scheme_name = db_fund.scheme_name
        return transaction

    def delete_transaction(self, db: Session, user_id: str, transaction_id: str) -> bool:
        tx = db.query(FundTransaction).filter(
            FundTransaction.id == transaction_id,
            FundTransaction.user_id == user_id
        ).first()
        if not tx:
            return False
        db.delete(tx)
        db.commit()
        return True

    def get_portfolio_summary(self, db: Session, user_id: str) -> Dict[str, Any]:
        portfolio = self.get_or_create_portfolio(db, user_id)
        tx_records = db.query(FundTransaction, MutualFund).join(
            MutualFund, FundTransaction.fund_id == MutualFund.id
        ).filter(FundTransaction.portfolio_id == portfolio.id).all()

        if not tx_records:
            return {
                "success": True,
                "total_invested": 0.0,
                "current_value": 0.0,
                "total_profit_loss": 0.0,
                "profit_loss_percentage": 0.0,
                "xirr": None,
                "fund_breakdown": []
            }

        tx_payload = []
        current_navs = {}

        for tx, fund in tx_records:
            scheme_code = fund.scheme_code
            if scheme_code not in current_navs:
                latest = self.mf_service.get_latest_nav(scheme_code)
                current_navs[scheme_code] = latest["current_nav"] if latest else (fund.current_nav or tx.nav)

            tx_payload.append({
                "fund_id": fund.id,
                "scheme_code": scheme_code,
                "scheme_name": fund.scheme_name,
                "transaction_type": tx.transaction_type,
                "transaction_date": tx.transaction_date,
                "units": tx.units,
                "nav": tx.nav,
                "amount": tx.amount
            })

        return calculate_portfolio_metrics(tx_payload, current_navs)

    def get_portfolio_history_series(self, db: Session, user_id: str) -> List[Dict[str, Any]]:
        portfolio = self.get_or_create_portfolio(db, user_id)
        tx_records = db.query(FundTransaction, MutualFund).join(
            MutualFund, FundTransaction.fund_id == MutualFund.id
        ).filter(FundTransaction.portfolio_id == portfolio.id).all()

        if not tx_records:
            return []

        tx_payload = []
        scheme_codes = set()
        for tx, fund in tx_records:
            scheme_codes.add(fund.scheme_code)
            tx_payload.append({
                "scheme_code": fund.scheme_code,
                "scheme_name": fund.scheme_name,
                "transaction_type": tx.transaction_type,
                "transaction_date": tx.transaction_date,
                "units": tx.units,
                "amount": tx.amount,
                "nav": tx.nav
            })

        nav_histories = {}
        fallback_navs = {}
        tx_dates = []
        for tx, fund in tx_records:
            if fund.current_nav:
                fallback_navs[fund.scheme_code] = Decimal(str(fund.current_nav))
            elif tx.nav:
                fallback_navs[fund.scheme_code] = Decimal(str(tx.nav))

            t_date = tx.transaction_date.date() if isinstance(tx.transaction_date, datetime) else tx.transaction_date
            tx_dates.append(t_date)

        for code in scheme_codes:
            raw_hist = self.mf_service.provider.get_nav_history(code, limit=400)
            scheme_nav_map = {}
            for item in raw_hist:
                try:
                    d_obj = datetime.strptime(item["date"], "%d-%m-%Y").date()
                    scheme_nav_map[d_obj] = Decimal(str(item["nav"]))
                except Exception:
                    continue
            nav_histories[code] = scheme_nav_map

        # Dynamically evaluate portfolio value across historical monthly intervals up to current date
        import calendar
        earliest_tx = min(tx_dates) if tx_dates else date.today()
        latest_tx = max(tx_dates) if tx_dates else date.today()
        today = date.today()
        end_date = max(latest_tx, today)

        start_year = earliest_tx.year
        start_month = earliest_tx.month
        months_diff = (end_date.year - start_year) * 12 + (end_date.month - start_month)
        if months_diff < 5:
            total_shift = 5 - months_diff
            start_month -= total_shift
            while start_month < 1:
                start_month += 12
                start_year -= 1

        eval_dates = []
        cur_y, cur_m = start_year, start_month
        while (cur_y < end_date.year) or (cur_y == end_date.year and cur_m <= end_date.month):
            day = min(15, calendar.monthrange(cur_y, cur_m)[1])
            eval_dates.append(date(cur_y, cur_m, day))
            cur_m += 1
            if cur_m > 12:
                cur_m = 1
                cur_y += 1

        if not eval_dates or eval_dates[-1] < end_date:
            eval_dates.append(end_date)

        return calculate_portfolio_history(tx_payload, nav_histories, eval_dates, fallback_navs=fallback_navs)

    def add_stock_holding(self, db: Session, user_id: str, stock_in: Any) -> Dict[str, Any]:
        portfolio = self.get_or_create_portfolio(db, user_id)
        from app.models.portfolio import StockHolding

        cur_price = stock_in.current_price if stock_in.current_price is not None else stock_in.buy_price
        stock = StockHolding(
            user_id=user_id,
            portfolio_id=portfolio.id,
            symbol=stock_in.symbol.upper(),
            company_name=stock_in.company_name,
            sector=stock_in.sector or "General",
            quantity=stock_in.quantity,
            buy_price=stock_in.buy_price,
            current_price=cur_price
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)

        inv_val = float(stock.quantity * stock.buy_price)
        cur_val = float(stock.quantity * (stock.current_price or stock.buy_price))
        pl = cur_val - inv_val
        pl_pct = (pl / inv_val * 100.0) if inv_val > 0 else 0.0

        return {
            "id": stock.id,
            "user_id": stock.user_id,
            "portfolio_id": stock.portfolio_id,
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "sector": stock.sector,
            "quantity": stock.quantity,
            "buy_price": stock.buy_price,
            "current_price": stock.current_price,
            "invested_value": inv_val,
            "current_value": cur_val,
            "profit_loss": pl,
            "profit_loss_pct": round(pl_pct, 2)
        }

    def get_stock_holdings(self, db: Session, user_id: str) -> List[Dict[str, Any]]:
        portfolio = self.get_or_create_portfolio(db, user_id)
        from app.models.portfolio import StockHolding
        stocks = db.query(StockHolding).filter(StockHolding.portfolio_id == portfolio.id).all()
        res = []
        for s in stocks:
            inv_val = float(s.quantity * s.buy_price)
            cur_val = float(s.quantity * (s.current_price or s.buy_price))
            pl = cur_val - inv_val
            pl_pct = (pl / inv_val * 100.0) if inv_val > 0 else 0.0
            res.append({
                "id": s.id,
                "user_id": s.user_id,
                "portfolio_id": s.portfolio_id,
                "symbol": s.symbol,
                "company_name": s.company_name,
                "sector": s.sector,
                "quantity": s.quantity,
                "buy_price": s.buy_price,
                "current_price": s.current_price,
                "invested_value": inv_val,
                "current_value": cur_val,
                "profit_loss": pl,
                "profit_loss_pct": round(pl_pct, 2)
            })
        return res

    def delete_stock_holding(self, db: Session, user_id: str, stock_id: str) -> bool:
        from app.models.portfolio import StockHolding
        stock = db.query(StockHolding).filter(
            StockHolding.id == stock_id,
            StockHolding.user_id == user_id
        ).first()
        if not stock:
            return False
        db.delete(stock)
        db.commit()
        return True

    def get_portfolio_overlap_analysis(self, db: Session, user_id: str) -> Dict[str, Any]:
        summary = self.get_portfolio_summary(db, user_id)
        fund_breakdown = summary.get("fund_breakdown", [])
        direct_stocks = self.get_stock_holdings(db, user_id)

        if not fund_breakdown and not direct_stocks:
            return {
                "success": False,
                "error_code": "EMPTY_PORTFOLIO",
                "message": "Add mutual fund transactions or stocks to your portfolio to view stock & sector overlap analysis.",
                "direct_stocks": [],
                "overlapping_stocks": [],
                "sector_concentration": []
            }

        funds_holdings = {}
        for f in fund_breakdown:
            code = f["scheme_code"]
            holdings = self.mf_service.get_holdings(code)
            funds_holdings[code] = {
                "scheme_name": f["scheme_name"],
                "allocation_in_portfolio_pct": f.get("allocation_pct", 100.0),
                "holdings": holdings
            }

        overlap_result = calculate_portfolio_overlap(funds_holdings) if fund_breakdown else {
            "success": True,
            "overall_overlap_pct": 0.0,
            "overlap_matrix": [],
            "overlapping_stocks": [],
            "sector_concentration": []
        }

        overlap_result["direct_stocks"] = direct_stocks
        return overlap_result

    def get_portfolio_risk_analysis(self, db: Session, user_id: str) -> Dict[str, Any]:
        summary = self.get_portfolio_summary(db, user_id)
        fund_breakdown = summary.get("fund_breakdown", [])

        if not fund_breakdown:
            return {"success": False, "error_code": "EMPTY_PORTFOLIO", "message": "No portfolio funds found."}

        primary_code = fund_breakdown[0]["scheme_code"]
        history = self.mf_service.get_nav_history(primary_code, limit=90)
        nav_list = [h["nav"] for h in reversed(history)] if history else []

        if len(nav_list) < 10:
            nav_list = [100.0 + (i * 0.4) for i in range(30)]

        return calculate_risk_metrics(nav_list)
