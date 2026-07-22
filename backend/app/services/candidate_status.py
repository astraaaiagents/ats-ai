"""Candidate status state machine.

Defines valid status transitions and role-based restrictions.
"""

# Valid transitions: from_status -> [allowed to_statuses]
TRANSITIONS: dict[str, list[str]] = {
    "sourced": ["in_review", "rejected"],
    "in_review": ["submitted", "rejected"],
    "submitted": ["interviewing", "rejected"],
    "interviewing": ["shortlisted", "rejected"],
    "shortlisted": ["offer_extended", "rejected"],
    "offer_extended": ["placed", "rejected"],
    "placed": [],  # terminal
    "rejected": [],  # terminal
    "archived": [],  # terminal
}

# Role requirements for transitions
# recruiter: can move sourced -> in_review, in_review -> submitted
# manager: can approve submissions, extend offers
# admin: full access
ROLE_RESTRICTIONS: dict[str, dict[str, list[str]]] = {
    "recruiter": {
        "sourced": ["in_review"],
        "in_review": ["submitted"],
    },
    "manager": {
        "sourced": ["in_review", "submitted", "interviewing", "shortlisted", "offer_extended"],
        "in_review": ["submitted", "interviewing"],
        "submitted": ["interviewing"],
        "interviewing": ["shortlisted", "offer_extended"],
        "shortlisted": ["offer_extended"],
        "offer_extended": ["placed"],
    },
    "admin": {
        # Admin can do any transition
        "sourced": ["in_review", "rejected"],
        "in_review": ["submitted", "rejected"],
        "submitted": ["interviewing", "rejected"],
        "interviewing": ["shortlisted", "rejected"],
        "shortlisted": ["offer_extended", "rejected"],
        "offer_extended": ["placed", "rejected"],
        "placed": [],
        "rejected": [],
        "archived": [],
    },
}


def validate_transition(from_status: str, to_status: str, user_role: str = "recruiter") -> bool:
    """Validate if a status transition is allowed.

    Args:
        from_status: Current candidate status
        to_status: Target status
        user_role: Role of the user making the transition

    Returns:
        True if the transition is allowed

    Raises:
        ValueError: If from_status or to_status is invalid
    """
    if from_status not in TRANSITIONS:
        raise ValueError(f"Invalid from_status: {from_status}")
    if to_status not in TRANSITIONS and to_status not in {"archived"}:
        raise ValueError(f"Invalid to_status: {to_status}")

    # Terminal states cannot transition anywhere
    if from_status in ("placed", "rejected", "archived"):
        return False

    # Get allowed transitions for this role
    role_transitions = ROLE_RESTRICTIONS.get(user_role, ROLE_RESTRICTIONS["recruiter"])
    allowed = role_transitions.get(from_status, [])

    # Also allow any role to reject or archive
    if to_status in ("rejected", "archived"):
        return True

    return to_status in allowed


def get_allowed_transitions(status: str, user_role: str = "recruiter") -> list[str]:
    """Get list of allowed target statuses for a given status and role.

    Args:
        status: Current candidate status
        user_role: Role of the user

    Returns:
        List of allowed target statuses
    """
    if status not in TRANSITIONS:
        return []

    # Terminal states have no transitions
    if status in ("placed", "rejected", "archived"):
        return []

    role_transitions = ROLE_RESTRICTIONS.get(user_role, ROLE_RESTRICTIONS["recruiter"])
    allowed = list(role_transitions.get(status, []))

    # All roles can reject or archive
    if status not in ("placed", "rejected", "archived"):
        allowed.extend(["rejected", "archived"])

    return sorted(set(allowed))
