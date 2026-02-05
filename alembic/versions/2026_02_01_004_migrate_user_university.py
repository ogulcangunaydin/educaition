"""migrate_user_university_from_username

Revision ID: 92e0df0e3aa7
Revises: 705261ddbf64
Create Date: 2026-02-01 18:05:28.131918

This migration updates existing users' university and role based on their username suffix.

Username suffix mapping:
- .izu → university: izu, role: viewer
- .29mayis or .mayis → university: mayis, role: viewer
- .fsm → university: fsm, role: viewer
- .ibnhaldun → university: ibnhaldun, role: viewer
- .halic → university: halic, role: viewer
- No suffix → university: halic, role: admin

Viewers are redirected to university comparison page.
Admins/teachers are redirected to dashboard.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '92e0df0e3aa7'
down_revision: Union[str, None] = '705261ddbf64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Mapping of username suffixes to university keys
UNIVERSITY_SUFFIX_MAP = {
    '.izu': 'izu',
    '.29mayis': 'mayis',
    '.mayis': 'mayis',
    '.fsm': 'fsm',
    '.ibnhaldun': 'ibnhaldun',
    '.halic': 'halic',
}


def upgrade() -> None:
    conn = op.get_bind()
    
    # Get all users
    result = conn.execute(text("SELECT id, username FROM users"))
    users = result.fetchall()
    
    for user_id, username in users:
        if not username:
            continue
            
        username_lower = username.lower()
        university_found = None
        
        # Check for university suffix in username
        for suffix, university_key in UNIVERSITY_SUFFIX_MAP.items():
            if username_lower.endswith(suffix):
                university_found = university_key
                break
        
        if university_found:
            # User has a university suffix - update their university and set as viewer
            conn.execute(
                text("UPDATE users SET university = :university, role = :role WHERE id = :user_id"),
                {"university": university_found, "role": "viewer", "user_id": user_id}
            )
        else:
            # No university suffix - make them admin with halic
            conn.execute(
                text("UPDATE users SET role = :role, university = :university WHERE id = :user_id"),
                {"role": "admin", "university": "halic", "user_id": user_id}
            )


def downgrade() -> None:
    # Reset all users to default halic university and student role
    # Note: This is a destructive operation - we can't perfectly restore original state
    conn = op.get_bind()
    conn.execute(text("UPDATE users SET university = 'halic', role = 'student'"))
