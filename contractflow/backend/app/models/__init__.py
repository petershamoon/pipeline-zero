"""Model registry — import all models so Alembic can discover them."""
from app.models.approval_chain import ApprovalChain  # noqa: F401
from app.models.approval_step import ApprovalStep  # noqa: F401
from app.models.approval_template import ApprovalTemplate  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.base import Base, BaseModel  # noqa: F401
from app.models.contract import Contract  # noqa: F401
from app.models.contract_version import ContractVersion  # noqa: F401
from app.models.department import Department  # noqa: F401
from app.models.enums import (  # noqa: F401
    ApprovalChainStatus,
    ApprovalDecision,
    AuditAction,
    ContractStatus,
    UserRole,
)
from app.models.user import User  # noqa: F401
from app.models.user_session import UserSession  # noqa: F401
