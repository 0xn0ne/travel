"""add chat_messages table

Revision ID: 15_chat_messages
Revises: a422b22ab4c1
Create Date: 2026-04-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '15_chat_messages'
down_revision: Union[str, Sequence[str], None] = 'a422b22ab4c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('chat_messages',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('session_id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_user_id'), 'chat_messages', ['user_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_session_id'), 'chat_messages', ['session_id'], unique=False)
    op.create_index('ix_chat_messages_user_session_created', 'chat_messages', ['user_id', 'session_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_chat_messages_user_session_created', table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_session_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_user_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
