"""Unit tests for the contract status state machine (ALLOWED_TRANSITIONS)."""
from __future__ import annotations

import pytest

from app.api.v1.contracts import ALLOWED_TRANSITIONS
from app.models.enums import ContractStatus


@pytest.mark.unit
class TestAllowedTransitions:
    """Verify every valid and invalid transition in the state machine."""

    # ------------------------------------------------------------------
    # Valid transitions (should be in ALLOWED_TRANSITIONS)
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("from_status", "to_status"),
        [
            # From DRAFT
            (ContractStatus.DRAFT, ContractStatus.PENDING_APPROVAL),
            (ContractStatus.DRAFT, ContractStatus.ARCHIVED),
            # From PENDING_APPROVAL
            (ContractStatus.PENDING_APPROVAL, ContractStatus.ACTIVE),
            (ContractStatus.PENDING_APPROVAL, ContractStatus.DRAFT),
            (ContractStatus.PENDING_APPROVAL, ContractStatus.ARCHIVED),
            # From ACTIVE
            (ContractStatus.ACTIVE, ContractStatus.EXPIRED),
            (ContractStatus.ACTIVE, ContractStatus.TERMINATED),
            (ContractStatus.ACTIVE, ContractStatus.ARCHIVED),
            # From EXPIRED
            (ContractStatus.EXPIRED, ContractStatus.ARCHIVED),
            # From TERMINATED
            (ContractStatus.TERMINATED, ContractStatus.ARCHIVED),
        ],
        ids=[
            "draft->pending_approval",
            "draft->archived",
            "pending_approval->active",
            "pending_approval->draft",
            "pending_approval->archived",
            "active->expired",
            "active->terminated",
            "active->archived",
            "expired->archived",
            "terminated->archived",
        ],
    )
    def test_valid_transition_is_allowed(
        self, from_status: ContractStatus, to_status: ContractStatus
    ) -> None:
        """Valid transitions must be present in the allowed set."""
        assert to_status in ALLOWED_TRANSITIONS[from_status], (
            f"Expected {from_status.value} -> {to_status.value} to be allowed"
        )

    # ------------------------------------------------------------------
    # Invalid transitions (should NOT be in ALLOWED_TRANSITIONS)
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("from_status", "to_status"),
        [
            # From DRAFT — cannot go directly to ACTIVE, EXPIRED, TERMINATED
            (ContractStatus.DRAFT, ContractStatus.ACTIVE),
            (ContractStatus.DRAFT, ContractStatus.EXPIRED),
            (ContractStatus.DRAFT, ContractStatus.TERMINATED),
            # Self-transition from DRAFT
            (ContractStatus.DRAFT, ContractStatus.DRAFT),
            # From PENDING_APPROVAL — cannot go to EXPIRED, TERMINATED
            (ContractStatus.PENDING_APPROVAL, ContractStatus.EXPIRED),
            (ContractStatus.PENDING_APPROVAL, ContractStatus.TERMINATED),
            # Self-transition from PENDING_APPROVAL
            (ContractStatus.PENDING_APPROVAL, ContractStatus.PENDING_APPROVAL),
            # From ACTIVE — cannot go back to DRAFT or PENDING_APPROVAL
            (ContractStatus.ACTIVE, ContractStatus.DRAFT),
            (ContractStatus.ACTIVE, ContractStatus.PENDING_APPROVAL),
            # Self-transition from ACTIVE
            (ContractStatus.ACTIVE, ContractStatus.ACTIVE),
            # From EXPIRED — cannot go anywhere except ARCHIVED
            (ContractStatus.EXPIRED, ContractStatus.DRAFT),
            (ContractStatus.EXPIRED, ContractStatus.PENDING_APPROVAL),
            (ContractStatus.EXPIRED, ContractStatus.ACTIVE),
            (ContractStatus.EXPIRED, ContractStatus.TERMINATED),
            # Self-transition from EXPIRED
            (ContractStatus.EXPIRED, ContractStatus.EXPIRED),
            # From TERMINATED — cannot go anywhere except ARCHIVED
            (ContractStatus.TERMINATED, ContractStatus.DRAFT),
            (ContractStatus.TERMINATED, ContractStatus.PENDING_APPROVAL),
            (ContractStatus.TERMINATED, ContractStatus.ACTIVE),
            (ContractStatus.TERMINATED, ContractStatus.EXPIRED),
            # Self-transition from TERMINATED
            (ContractStatus.TERMINATED, ContractStatus.TERMINATED),
            # From ARCHIVED — terminal state, cannot go anywhere
            (ContractStatus.ARCHIVED, ContractStatus.DRAFT),
            (ContractStatus.ARCHIVED, ContractStatus.PENDING_APPROVAL),
            (ContractStatus.ARCHIVED, ContractStatus.ACTIVE),
            (ContractStatus.ARCHIVED, ContractStatus.EXPIRED),
            (ContractStatus.ARCHIVED, ContractStatus.TERMINATED),
            # Self-transition from ARCHIVED
            (ContractStatus.ARCHIVED, ContractStatus.ARCHIVED),
        ],
        ids=[
            "draft-X->active",
            "draft-X->expired",
            "draft-X->terminated",
            "draft-X->draft",
            "pending-X->expired",
            "pending-X->terminated",
            "pending-X->pending",
            "active-X->draft",
            "active-X->pending",
            "active-X->active",
            "expired-X->draft",
            "expired-X->pending",
            "expired-X->active",
            "expired-X->terminated",
            "expired-X->expired",
            "terminated-X->draft",
            "terminated-X->pending",
            "terminated-X->active",
            "terminated-X->expired",
            "terminated-X->terminated",
            "archived-X->draft",
            "archived-X->pending",
            "archived-X->active",
            "archived-X->expired",
            "archived-X->terminated",
            "archived-X->archived",
        ],
    )
    def test_invalid_transition_is_rejected(
        self, from_status: ContractStatus, to_status: ContractStatus
    ) -> None:
        """Invalid transitions must NOT be present in the allowed set."""
        assert to_status not in ALLOWED_TRANSITIONS[from_status], (
            f"Expected {from_status.value} -> {to_status.value} to be disallowed"
        )

    # ------------------------------------------------------------------
    # Structural checks
    # ------------------------------------------------------------------

    def test_every_status_has_an_entry(self) -> None:
        """ALLOWED_TRANSITIONS must contain a key for every ContractStatus."""
        for status in ContractStatus:
            assert status in ALLOWED_TRANSITIONS, (
                f"{status.value} is missing from ALLOWED_TRANSITIONS"
            )

    def test_archived_is_terminal_state(self) -> None:
        """ARCHIVED should have zero outgoing transitions."""
        assert ALLOWED_TRANSITIONS[ContractStatus.ARCHIVED] == set()

    def test_all_transition_targets_are_valid_statuses(self) -> None:
        """Every target in a transition set must be a valid ContractStatus."""
        for from_status, targets in ALLOWED_TRANSITIONS.items():
            for target in targets:
                assert isinstance(target, ContractStatus), (
                    f"Invalid target {target!r} in transitions for {from_status.value}"
                )

    def test_no_self_transitions(self) -> None:
        """No status should be able to transition to itself."""
        for from_status, targets in ALLOWED_TRANSITIONS.items():
            assert from_status not in targets, (
                f"{from_status.value} should not self-transition"
            )

    def test_every_non_terminal_status_has_at_least_one_transition(self) -> None:
        """Every status except ARCHIVED should have at least one valid transition."""
        for status in ContractStatus:
            if status == ContractStatus.ARCHIVED:
                continue
            assert len(ALLOWED_TRANSITIONS[status]) >= 1, (
                f"{status.value} should have at least one valid transition"
            )

    def test_all_statuses_can_reach_archived(self) -> None:
        """Every status should be able to transition to ARCHIVED (directly)."""
        for status in ContractStatus:
            if status == ContractStatus.ARCHIVED:
                continue
            assert ContractStatus.ARCHIVED in ALLOWED_TRANSITIONS[status], (
                f"{status.value} should have ARCHIVED as a valid target"
            )
