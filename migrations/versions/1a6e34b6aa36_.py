"""empty message

Revision ID: 1a6e34b6aa36
Revises: f190e7468752
Create Date: 2016-03-31 11:25:02.296719

"""

# revision identifiers, used by Alembic.
revision = '1a6e34b6aa36'
down_revision = 'f190e7468752'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('wish', sa.Column('list_', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'wish', 'wish_list', ['list_'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'wish', type_='foreignkey')
    op.drop_column('wish', 'list_')
    ### end Alembic commands ###