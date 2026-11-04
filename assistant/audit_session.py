from dataclasses import dataclass, field


@dataclass
class AuditSession:

    metadata: dict = field(default_factory=dict)

    dataset: dict = field(default_factory=dict)

    duplicates: dict = field(default_factory=dict)

    analysis: dict = field(default_factory=dict)

    findings: dict = field(default_factory=dict)

    explainability: dict = field(default_factory=dict)

    review: dict = field(default_factory=dict)

    reporting: dict = field(default_factory=dict)

    conversation: list = field(default_factory=list)

    audit_log: list = field(default_factory=list)

    evaluation_session_id: str = field(default="")
    