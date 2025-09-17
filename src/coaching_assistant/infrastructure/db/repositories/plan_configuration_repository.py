"""Plan configuration repository implementation using SQLAlchemy with Clean Architecture."""

from typing import List, Optional
from sqlalchemy.orm import Session

from ....core.repositories.ports import PlanConfigurationRepoPort
from ....core.models.plan_configuration import PlanConfiguration
from ....core.models.user import UserPlan
from ..models.plan_configuration_model import PlanConfigurationModel


class PlanConfigurationRepository(PlanConfigurationRepoPort):
    """SQLAlchemy implementation of PlanConfigurationRepoPort using infrastructure models."""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_by_plan_type(self, plan_type: UserPlan) -> Optional[PlanConfiguration]:
        """Get plan configuration by plan type."""
        # Convert enum to string value for SQLAlchemy query (Clean Architecture: domain → infrastructure conversion)
        plan_value = plan_type.value if isinstance(plan_type, UserPlan) else plan_type
        orm_plan = (
            self.db_session.query(PlanConfigurationModel)
            .filter(PlanConfigurationModel.plan_type == plan_value)
            .first()
        )
        return orm_plan.to_domain() if orm_plan else None

    def get_all_active_plans(self) -> List[PlanConfiguration]:
        """Get all active plan configurations."""
        orm_plans = (
            self.db_session.query(PlanConfigurationModel)
            .filter(PlanConfigurationModel.is_active == True)
            .order_by(PlanConfigurationModel.sort_order)
            .all()
        )
        return [plan.to_domain() for plan in orm_plans]

    def save(self, plan_config: PlanConfiguration) -> PlanConfiguration:
        """Save or update plan configuration."""
        # Check if plan already exists
        existing = (
            self.db_session.query(PlanConfigurationModel)
            .filter(PlanConfigurationModel.id == plan_config.id)
            .first()
        )

        if existing:
            # Update existing plan
            existing.update_from_domain(plan_config)
            self.db_session.flush()
            self.db_session.refresh(existing)
            return existing.to_domain()
        else:
            # Create new plan
            orm_plan = PlanConfigurationModel.from_domain(plan_config)
            self.db_session.add(orm_plan)
            self.db_session.flush()
            self.db_session.refresh(orm_plan)
            return orm_plan.to_domain()


def create_plan_configuration_repository(db_session: Session) -> PlanConfigurationRepoPort:
    """Factory function to create PlanConfigurationRepository instance."""
    return PlanConfigurationRepository(db_session)