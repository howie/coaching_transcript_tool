"""Plan configuration repository implementation using SQLAlchemy."""

from typing import List, Optional
from sqlalchemy.orm import Session

from ....core.repositories.ports import PlanConfigurationRepoPort
from ....models.plan_configuration import PlanConfiguration
from ....models.user import UserPlan


class PlanConfigurationRepository(PlanConfigurationRepoPort):
    """SQLAlchemy implementation of PlanConfigurationRepoPort."""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_by_plan_type(self, plan_type: UserPlan) -> Optional[PlanConfiguration]:
        """Get plan configuration by plan type."""
        return (
            self.db_session.query(PlanConfiguration)
            .filter(PlanConfiguration.plan_type == plan_type)
            .first()
        )

    def get_all_active_plans(self) -> List[PlanConfiguration]:
        """Get all active plan configurations."""
        return (
            self.db_session.query(PlanConfiguration)
            .filter(PlanConfiguration.is_active == True)
            .order_by(PlanConfiguration.sort_order)
            .all()
        )

    def save(self, plan_config: PlanConfiguration) -> PlanConfiguration:
        """Save or update plan configuration."""
        self.db_session.add(plan_config)
        self.db_session.commit()
        self.db_session.refresh(plan_config)
        return plan_config


def create_plan_configuration_repository(db_session: Session) -> PlanConfigurationRepoPort:
    """Factory function to create PlanConfigurationRepository instance."""
    return PlanConfigurationRepository(db_session)