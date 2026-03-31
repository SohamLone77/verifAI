"""Budget management for VerifAI"""

import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from verifai.models.cost_models import BudgetAlert, BudgetAlertLevel, BudgetConfig
from verifai.environment.cost_tracker import CostTracker


class BudgetState(Enum):
    """Budget state machine"""
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"
    PAUSED = "paused"


class BudgetManager:
    """
    Manage budgets and enforce spending limits.

    Features:
    - Multi-timeframe budgets (daily, weekly, monthly)
    - Automatic enforcement
    - Alert notifications
    - Budget rollover handling
    """

    def __init__(
        self,
        cost_tracker: CostTracker,
        config: Optional[BudgetConfig] = None,
        auto_enforce: bool = True,
    ):
        self.cost_tracker = cost_tracker
        self.config = config or BudgetConfig()
        self.auto_enforce = auto_enforce
        self.state = BudgetState.OK
        self._monitor_thread = None
        self._stop_monitoring = False

        self._daily_spending: Dict[str, float] = {}
        self._weekly_spending: Dict[str, float] = {}
        self._monthly_spending: Dict[str, float] = {}

    def start_monitoring(self, interval_seconds: int = 60) -> None:
        """Start background budget monitoring"""
        if self._monitor_thread:
            return

        self._stop_monitoring = False
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval_seconds,)
        )
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop background monitoring"""
        self._stop_monitoring = True
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int) -> None:
        """Background monitoring loop"""
        while not self._stop_monitoring:
            self.check_budgets()
            time.sleep(interval)

    def check_budgets(self) -> Tuple[bool, List[BudgetAlert]]:
        """
        Check all budgets and enforce if needed.

        Returns:
            Tuple of (is_allowed, alerts)
        """
        alerts: List[BudgetAlert] = []

        if self.config.daily_budget:
            daily_total = self._get_daily_spending()
            if daily_total >= self.config.daily_budget:
                alert = BudgetAlert(
                    alert_id=f"daily_{datetime.now().date()}",
                    level=BudgetAlertLevel.EXCEEDED,
                    current_cost=daily_total,
                    budget_limit=self.config.daily_budget,
                    percentage_used=1.0,
                    message=(
                        f"Daily budget exceeded: ${daily_total:.2f} / "
                        f"${self.config.daily_budget:.2f}"
                    ),
                    recommended_action="Reduce usage or increase daily budget",
                )
                alerts.append(alert)

                if self.auto_enforce:
                    self.state = BudgetState.EXCEEDED

        if self.config.weekly_budget:
            weekly_total = self._get_weekly_spending()
            usage = weekly_total / self.config.weekly_budget

            if usage >= self.config.critical_threshold:
                alert = BudgetAlert(
                    alert_id=f"weekly_{datetime.now().isocalendar()[1]}",
                    level=BudgetAlertLevel.CRITICAL,
                    current_cost=weekly_total,
                    budget_limit=self.config.weekly_budget,
                    percentage_used=usage,
                    message=(
                        f"Weekly budget at {usage:.1%}: "
                        f"${weekly_total:.2f} / ${self.config.weekly_budget:.2f}"
                    ),
                    recommended_action="Reduce usage or increase budget",
                )
                alerts.append(alert)

                if self.auto_enforce:
                    self.state = BudgetState.CRITICAL

            elif usage >= self.config.alert_threshold:
                alert = BudgetAlert(
                    alert_id=f"weekly_{datetime.now().isocalendar()[1]}",
                    level=BudgetAlertLevel.WARNING,
                    current_cost=weekly_total,
                    budget_limit=self.config.weekly_budget,
                    percentage_used=usage,
                    message=f"Weekly budget at {usage:.1%}",
                    recommended_action="Consider cost optimization",
                )
                alerts.append(alert)

                if self.auto_enforce:
                    self.state = BudgetState.WARNING

        if self.config.monthly_budget:
            monthly_total = self._get_monthly_spending()
            usage = monthly_total / self.config.monthly_budget

            if usage >= self.config.critical_threshold:
                alert = BudgetAlert(
                    alert_id=f"monthly_{datetime.now().month}",
                    level=BudgetAlertLevel.CRITICAL,
                    current_cost=monthly_total,
                    budget_limit=self.config.monthly_budget,
                    percentage_used=usage,
                    message=(
                        f"Monthly budget at {usage:.1%}: "
                        f"${monthly_total:.2f} / ${self.config.monthly_budget:.2f}"
                    ),
                    recommended_action="Reduce usage or increase monthly budget",
                )
                alerts.append(alert)

            elif usage >= self.config.alert_threshold and self.state != BudgetState.CRITICAL:
                alert = BudgetAlert(
                    alert_id=f"monthly_{datetime.now().month}",
                    level=BudgetAlertLevel.WARNING,
                    current_cost=monthly_total,
                    budget_limit=self.config.monthly_budget,
                    percentage_used=usage,
                    message=f"Monthly budget at {usage:.1%}",
                    recommended_action="Consider cost optimization",
                )
                alerts.append(alert)

        for alert in alerts:
            self.cost_tracker.alerts.append(alert)

        is_allowed = self.state not in [BudgetState.EXCEEDED, BudgetState.PAUSED]

        return is_allowed, alerts

    def _get_daily_spending(self) -> float:
        """Get today spending"""
        today = datetime.now().date()

        daily_total = sum(e.cost for e in self.cost_tracker.events if e.timestamp.date() == today)

        self._daily_spending[str(today)] = daily_total
        return daily_total

    def _get_weekly_spending(self) -> float:
        """Get this week spending"""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())

        weekly_total = sum(e.cost for e in self.cost_tracker.events if e.timestamp >= week_start)

        week_key = f"{week_start.date()}"
        self._weekly_spending[week_key] = weekly_total
        return weekly_total

    def _get_monthly_spending(self) -> float:
        """Get this month spending"""
        today = datetime.now()
        month_start = today.replace(day=1)

        monthly_total = sum(e.cost for e in self.cost_tracker.events if e.timestamp >= month_start)

        month_key = f"{month_start.year}-{month_start.month}"
        self._monthly_spending[month_key] = monthly_total
        return monthly_total

    def can_make_request(self, estimated_cost: float) -> bool:
        """Check if a request can be made given current budget"""
        if self.state in [BudgetState.PAUSED, BudgetState.EXCEEDED]:
            return False

        if estimated_cost > self.config.max_cost_per_request:
            return False

        remaining = self.get_remaining_budget()
        if remaining is not None and estimated_cost > remaining:
            return False

        return True

    def get_remaining_budget(self) -> Optional[float]:
        """Get remaining budget for the current period"""
        if self.config.monthly_budget:
            monthly_spent = self._get_monthly_spending()
            return max(0, self.config.monthly_budget - monthly_spent)
        return None

    def get_budget_forecast(
        self, days_ahead: int = 7, days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Forecast budget usage for upcoming days"""
        if days is not None:
            days_ahead = days
        current_spending = self.cost_tracker.total_cost()
        daily_avg = self.cost_tracker.average_cost_per_review() * 100

        forecast = []
        cumulative = current_spending

        for day in range(1, days_ahead + 1):
            cumulative += daily_avg
            forecast.append(
                {
                    "day": day,
                    "projected_cost": cumulative,
                    "budget_limit": self.config.monthly_budget,
                    "percentage": cumulative / self.config.monthly_budget
                    if self.config.monthly_budget
                    else 0,
                }
            )

        will_exceed = any(
            f["projected_cost"] > (self.config.monthly_budget or float("inf")) for f in forecast
        )

        return {
            "current_spending": current_spending,
            "daily_average": daily_avg,
            "forecast": forecast,
            "will_exceed": will_exceed,
        }

    def pause_spending(self) -> None:
        """Pause all spending"""
        self.state = BudgetState.PAUSED

    def resume_spending(self) -> None:
        """Resume spending"""
        self.state = BudgetState.OK

    def reset(self) -> None:
        """Reset budget manager"""
        self._daily_spending.clear()
        self._weekly_spending.clear()
        self._monthly_spending.clear()
        self.state = BudgetState.OK
