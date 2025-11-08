"""Add multi-tenancy support

Revision ID: 7f8g9h0i1j2k
Revises: 6ef43ae90e64
Create Date: 2025-11-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7f8g9h0i1j2k'
down_revision: Union[str, Sequence[str], None] = '6ef43ae90e64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add multi-tenancy support.

    Creates tables for:
    - Tenants
    - Tenant users
    - Tenant subscriptions
    - Tenant invitations
    - Tenant audit logs
    """
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('plan', sa.String(length=50), nullable=False, server_default='free'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),

        # Limits
        sa.Column('max_users', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_storage_gb', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_simulations', sa.Integer(), nullable=False, server_default='100'),

        # Settings
        sa.Column('settings', sa.JSON(), nullable=False, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_tenants_slug'),
        sa.UniqueConstraint('domain', name='uq_tenants_domain'),
    )

    # Create indexes
    op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=True)
    op.create_index('ix_tenants_domain', 'tenants', ['domain'], unique=False)
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'], unique=False)

    # Create tenant_users table
    op.create_table(
        'tenant_users',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='member'),
        sa.Column('permissions', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),

        # Invitation tracking
        sa.Column('invited_by', sa.String(length=50), nullable=True),
        sa.Column('invited_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tenant_id', 'user_id', name='uq_tenant_users_tenant_user'),
    )

    # Create indexes
    op.create_index('ix_tenant_users_tenant_id', 'tenant_users', ['tenant_id'], unique=False)
    op.create_index('ix_tenant_users_user_id', 'tenant_users', ['user_id'], unique=False)
    op.create_index('ix_tenant_users_role', 'tenant_users', ['role'], unique=False)

    # Create tenant_subscriptions table
    op.create_table(
        'tenant_subscriptions',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('billing_cycle', sa.String(length=50), nullable=False, server_default='monthly'),

        # Subscription period
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),

        # Billing
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_tenant_subscriptions_tenant_id', 'tenant_subscriptions', ['tenant_id'], unique=False)
    op.create_index('ix_tenant_subscriptions_status', 'tenant_subscriptions', ['status'], unique=False)
    op.create_index('ix_tenant_subscriptions_stripe_subscription_id', 'tenant_subscriptions', ['stripe_subscription_id'], unique=False)

    # Create tenant_invitations table
    op.create_table(
        'tenant_invitations',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='member'),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),

        # Invitation metadata
        sa.Column('invited_by', sa.String(length=50), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('token', name='uq_tenant_invitations_token'),
    )

    # Create indexes
    op.create_index('ix_tenant_invitations_tenant_id', 'tenant_invitations', ['tenant_id'], unique=False)
    op.create_index('ix_tenant_invitations_email', 'tenant_invitations', ['email'], unique=False)
    op.create_index('ix_tenant_invitations_token', 'tenant_invitations', ['token'], unique=True)
    op.create_index('ix_tenant_invitations_status', 'tenant_invitations', ['status'], unique=False)

    # Create tenant_audit_logs table
    op.create_table(
        'tenant_audit_logs',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),

        # Resource tracking
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=50), nullable=True),

        # Additional context
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),

        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_tenant_audit_logs_tenant_id', 'tenant_audit_logs', ['tenant_id'], unique=False)
    op.create_index('ix_tenant_audit_logs_user_id', 'tenant_audit_logs', ['user_id'], unique=False)
    op.create_index('ix_tenant_audit_logs_action', 'tenant_audit_logs', ['action'], unique=False)
    op.create_index('ix_tenant_audit_logs_created_at', 'tenant_audit_logs', ['created_at'], unique=False)
    op.create_index('ix_tenant_audit_logs_resource', 'tenant_audit_logs', ['resource_type', 'resource_id'], unique=False)

    # Add tenant_id to existing tables for multi-tenancy support
    # Note: This assumes existing tables need to be tenant-aware
    # Uncomment and adjust as needed for your specific tables

    # op.add_column('simulations', sa.Column('tenant_id', sa.String(length=50), nullable=True))
    # op.create_foreign_key('fk_simulations_tenant_id', 'simulations', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    # op.create_index('ix_simulations_tenant_id', 'simulations', ['tenant_id'], unique=False)

    # op.add_column('analyses', sa.Column('tenant_id', sa.String(length=50), nullable=True))
    # op.create_foreign_key('fk_analyses_tenant_id', 'analyses', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    # op.create_index('ix_analyses_tenant_id', 'analyses', ['tenant_id'], unique=False)

    # op.add_column('datasets', sa.Column('tenant_id', sa.String(length=50), nullable=True))
    # op.create_foreign_key('fk_datasets_tenant_id', 'datasets', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    # op.create_index('ix_datasets_tenant_id', 'datasets', ['tenant_id'], unique=False)


def downgrade() -> None:
    """
    Remove multi-tenancy support.

    WARNING: This will delete all tenant-related data!
    """
    # Remove tenant_id from existing tables (if added)
    # Uncomment if you added tenant_id columns in upgrade()

    # op.drop_index('ix_datasets_tenant_id', table_name='datasets')
    # op.drop_constraint('fk_datasets_tenant_id', 'datasets', type_='foreignkey')
    # op.drop_column('datasets', 'tenant_id')

    # op.drop_index('ix_analyses_tenant_id', table_name='analyses')
    # op.drop_constraint('fk_analyses_tenant_id', 'analyses', type_='foreignkey')
    # op.drop_column('analyses', 'tenant_id')

    # op.drop_index('ix_simulations_tenant_id', table_name='simulations')
    # op.drop_constraint('fk_simulations_tenant_id', 'simulations', type_='foreignkey')
    # op.drop_column('simulations', 'tenant_id')

    # Drop tenant_audit_logs
    op.drop_index('ix_tenant_audit_logs_resource', table_name='tenant_audit_logs')
    op.drop_index('ix_tenant_audit_logs_created_at', table_name='tenant_audit_logs')
    op.drop_index('ix_tenant_audit_logs_action', table_name='tenant_audit_logs')
    op.drop_index('ix_tenant_audit_logs_user_id', table_name='tenant_audit_logs')
    op.drop_index('ix_tenant_audit_logs_tenant_id', table_name='tenant_audit_logs')
    op.drop_table('tenant_audit_logs')

    # Drop tenant_invitations
    op.drop_index('ix_tenant_invitations_status', table_name='tenant_invitations')
    op.drop_index('ix_tenant_invitations_token', table_name='tenant_invitations')
    op.drop_index('ix_tenant_invitations_email', table_name='tenant_invitations')
    op.drop_index('ix_tenant_invitations_tenant_id', table_name='tenant_invitations')
    op.drop_table('tenant_invitations')

    # Drop tenant_subscriptions
    op.drop_index('ix_tenant_subscriptions_stripe_subscription_id', table_name='tenant_subscriptions')
    op.drop_index('ix_tenant_subscriptions_status', table_name='tenant_subscriptions')
    op.drop_index('ix_tenant_subscriptions_tenant_id', table_name='tenant_subscriptions')
    op.drop_table('tenant_subscriptions')

    # Drop tenant_users
    op.drop_index('ix_tenant_users_role', table_name='tenant_users')
    op.drop_index('ix_tenant_users_user_id', table_name='tenant_users')
    op.drop_index('ix_tenant_users_tenant_id', table_name='tenant_users')
    op.drop_table('tenant_users')

    # Drop tenants
    op.drop_index('ix_tenants_is_active', table_name='tenants')
    op.drop_index('ix_tenants_domain', table_name='tenants')
    op.drop_index('ix_tenants_slug', table_name='tenants')
    op.drop_table('tenants')
