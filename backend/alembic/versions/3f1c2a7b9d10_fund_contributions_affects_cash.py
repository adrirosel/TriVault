"""fund contributions affects_cash, value checks and unique position per account/ISIN

Revision ID: 3f1c2a7b9d10
Revises: 9554e14f4961
Create Date: 2026-11-27 12:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '3f1c2a7b9d10'
down_revision: str | Sequence[str] | None = '9554e14f4961'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CHECKS = {
    'ck_fund_contributions_shares_positive': 'shares > 0',
    'ck_fund_contributions_nav_positive': 'purchase_nav > 0',
    'ck_fund_contributions_gross_positive': 'gross_amount > 0',
    'ck_fund_contributions_fee_non_negative': 'fee >= 0',
}


def upgrade() -> None:
    """Apply migration."""
    op.add_column(
        'fund_contributions',
        sa.Column('affects_cash', sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    for name, condition in _CHECKS.items():
        op.create_check_constraint(name, 'fund_contributions', condition)
    op.create_unique_constraint(
        'uq_fund_positions_user_account_isin', 'fund_positions', ['user_id', 'account_id', 'isin']
    )


def downgrade() -> None:
    """Revert migration."""
    # Safe on MySQL: user_id keeps its own FK-backing index (ix_fund_positions_user_id).
    op.drop_constraint('uq_fund_positions_user_account_isin', 'fund_positions', type_='unique')
    for name in _CHECKS:
        op.drop_constraint(name, 'fund_contributions', type_='check')
    op.drop_column('fund_contributions', 'affects_cash')
