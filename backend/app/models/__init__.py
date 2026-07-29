from app.models.audit_log import AuditLog
from app.models.blacklist import TokenBlacklist
from app.models.client_contact import ClientContact
from app.models.candidate import Candidate
from app.models.candidate_document import CandidateDocument
from app.models.candidate_skill import CandidateSkill
from app.models.candidate_timeline import CandidateTimeline
from app.models.organization import Organization
from app.models.platform_user import PlatformUser
from app.models.user import User

# Agent portal models
from app.models.recruiter_preference import RecruiterPreference
from app.models.agent_conversation import AgentConversationSession, AgentConversationMessage
from app.models.agent_action import AgentAction
from app.models.agent_alert import AgentProactiveAlert
from app.models.preference_learning_event import PreferenceLearningEvent

__all__ = [
    # Existing models
    "AuditLog",
    "Candidate",
    "CandidateDocument",
    "CandidateSkill",
    "CandidateTimeline",
    "ClientContact",
    "Organization",
    "PlatformUser",
    "TokenBlacklist",
    "User",
    # Agent portal models
    "RecruiterPreference",
    "AgentConversationSession",
    "AgentConversationMessage",
    "AgentAction",
    "AgentProactiveAlert",
    "PreferenceLearningEvent",
]
