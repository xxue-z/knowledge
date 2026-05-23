from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'search_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.String(500), nullable=False),
        sa.Column('query_embedding', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(128), nullable=True),
        sa.Column('dept_id', sa.String(64), nullable=True),
        sa.Column('hit_doc_ids', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('hit_scores', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('filter_conditions', postgresql.JSONB(), nullable=True),
        sa.Column('search_duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_search_events_created_at', 'search_events', ['created_at'])
    op.create_index('idx_search_events_user_id', 'search_events', ['user_id'])
    op.create_index('idx_search_events_query_text', 'search_events', ['query_text'])

    op.create_table(
        'heatmap_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stat_type', sa.String(20), nullable=False),
        sa.Column('stat_key', sa.String(500), nullable=False),
        sa.Column('stat_date', sa.Date(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=True, default=0),
        sa.Column('unique_users', sa.Integer(), nullable=True, default=0),
        sa.Column('avg_duration_ms', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_heatmap_stats_type_date', 'heatmap_stats', ['stat_type', 'stat_date'])
    op.create_index('idx_heatmap_stats_unique', 'heatmap_stats', ['stat_type', 'stat_key', 'stat_date'], unique=True)

def downgrade():
    op.drop_table('heatmap_stats')
    op.drop_table('search_events')
