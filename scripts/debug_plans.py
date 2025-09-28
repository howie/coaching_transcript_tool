#!/usr/bin/env python3
"""Debug script to see what plans exist in database."""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from coaching_assistant.infrastructure.db.models.plan_configuration_model import (
    PlanConfigurationModel,
)

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

with SessionLocal() as db:
    plans = db.query(PlanConfigurationModel).all()
    print(f"Found {len(plans)} plans:")
    for plan in plans:
        print(
            f"  - Type: '{plan.plan_type}', Display: '{plan.display_name}', Active: {plan.is_active}"
        )
