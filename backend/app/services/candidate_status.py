"""Candidate status state machine.

Defines valid status transitions and role-based restrictions.
"""

STATUS_ALIASES: dict[str, str] = {
    "screening": "in_review",
    "interview": "interviewing",
    "offer": "offer_extended",
    "hired": "placed",
}

def normalize_status(status: str) -> str:
    """Normalize status aliases to canonical state machine statuses."""
    s = str(status or "").strip().lower()
    return STATUS_ALIASES.get(s, s)

TRANSITIONS: dict[str, list[str]] = {
    "sourced": ["in_review", "rejected", "archived"],
    "in_review": ["submitted", "sourced", "rejected", "archived"],
    "submitted": ["interviewing", "in_review", "rejected", "archived"],
    "interviewing": ["shortlisted", "submitted", "rejected", "archived"],
    "shortlisted": ["offer_extended", "interviewing", "rejected", "archived"],
    "offer_extended": ["placed", "shortlisted", "rejected", "archived"],
    "placed": [],
    "rejected": [],
    "archived": [],
}

ROLE_RESTRICTIONS: dict[str, dict[str, list[str]]] = {
    "recruiter": {
        "sourced": ["in_review"],
        "in_review": ["submitted", "sourced"],
        "submitted": ["interviewing", "in_review"],
        "interviewing": ["shortlisted", "submitted"],
        "shortlisted": ["offer_extended", "interviewing"],
        "offer_extended": ["placed", "shortlisted"],
        "placed": [],
        "rejected": [],
        "archived": [],
    },
    "manager": {
        "sourced": ["in_review", "submitted"],
        "in_review": ["submitted", "interviewing"],
        "submitted": ["interviewing", "shortlisted"],
        "interviewing": ["shortlisted", "offer_extended"],
        "shortlisted": ["offer_extended", "placed"],
        "offer_extended": ["placed"],
        "placed": [],
        "rejected": [],
        "archived": [],
    },
    "admin": {
        "sourced": ["in_review", "submitted", "interviewing", "shortlisted", "offer_extended", "placed"],
        "in_review": ["sourced", "submitted", "interviewing", "shortlisted", "offer_extended", "placed"],
        "submitted": ["sourced", "in_review", "interviewing", "shortlisted", "offer_extended", "placed"],
        "interviewing": ["sourced", "in_review", "submitted", "shortlisted", "offer_extended", "placed"],
        "shortlisted": ["sourced", "in_review", "submitted", "interviewing", "offer_extended", "placed"],
        "offer_extended": ["sourced", "in_review", "submitted", "interviewing", "shortlisted", "placed"],
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
    """
    from_status = normalize_status(from_status)
    to_status = normalize_status(to_status)

    if from_status == to_status:
        return True

    if from_status not in TRANSITIONS:
        return False
    if to_status not in TRANSITIONS and to_status not in {"archived"}:
        return False

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
    status = normalize_status(status)
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
