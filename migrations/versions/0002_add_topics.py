"""add_topics

Revision ID: 0002
Revises: 0001
Create Date: 2023-12-11 16:56:54.697550

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table("topics", sa.Column("name", sa.String(), nullable=False), sa.PrimaryKeyConstraint("name"))
    op.add_column("avatars", sa.Column("topics", sa.JSON(), nullable=True))
    op.add_column("avatars", sa.Column("name", sa.String(), nullable=True))
    op.add_column("avatars", sa.Column("text", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("avatars", "text")
    op.drop_column("avatars", "name")
    op.drop_column("avatars", "topics")
    op.drop_table("topics")
    # ### end Alembic commands ###
