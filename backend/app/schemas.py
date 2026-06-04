from pydantic import BaseModel
from typing import List, Optional

class AuditCheck(BaseModel):
    id: str
    name: str
    status: str  # "verified" | "attention" | "pending"

class Scorecard(BaseModel):
    score: int
    checks: List[AuditCheck]
    summary: str

class TraceStep(BaseModel):
    id: str
    name: str
    description: str
    status: str  # "completed" | "active" | "pending"
    timestamp: Optional[str] = None
    progress: Optional[int] = None

# Input Requests
class CreateDocumentRequest(BaseModel):
    archetype: str  # "Technical" | "Legal" | "Financial" | "Creative"
    payloadText: str
    loopGuard: int = 3
    semanticEnrichment: bool = True
    conflictDetection: bool = False

class FeedbackRequest(BaseModel):
    feedback: str

# Response Models
class DocumentSessionResponse(BaseModel):
    sessionId: str
    archetype: str
    documentContent: str
    status: str  # "idle" | "running" | "paused" | "completed" | "error"
    loopCount: int
    maxLoops: int
    scorecard: Scorecard
    trace: List[TraceStep]

def get_default_checks(archetype: str, conflict_detection: bool = False) -> list:
    if archetype == "Legal":
        checks = [
            {"id": "reg", "name": "Regulatory Conformity", "status": "pending"},
            {"id": "lia", "name": "Liability Limitations", "status": "pending"},
            {"id": "ipr", "name": "Intellectual Property", "status": "pending"},
            {"id": "jur", "name": "Jurisdictional Clauses", "status": "pending"},
        ]
    elif archetype == "Financial":
        checks = [
            {"id": "mpr", "name": "Mathematical Precision", "status": "pending"},
            {"id": "aud", "name": "Audit Trail Integrity", "status": "pending"},
            {"id": "tax", "name": "Tax Compliance", "status": "pending"},
            {"id": "fdi", "name": "Fiscal Disclosures", "status": "pending"},
        ]
    elif archetype == "Creative":
        checks = [
            {"id": "nst", "name": "Narrative Structure", "status": "pending"},
            {"id": "tvo", "name": "Tone & Voice Alignment", "status": "pending"},
            {"id": "pla", "name": "Plagiarism Verification", "status": "pending"},
            {"id": "sgu", "name": "Style Guide Adherence", "status": "pending"},
        ]
    else:  # Technical
        checks = [
            {"id": "sec", "name": "Security Layer", "status": "pending"},
            {"id": "sov", "name": "Data Sovereignty", "status": "pending"},
            {"id": "tok", "name": "Token Handling", "status": "pending"},
            {"id": "rat", "name": "Rate Limiting", "status": "pending"},
        ]
    
    if conflict_detection:
        checks.append({"id": "con", "name": "Contradiction & Conflict Detection", "status": "pending"})
    return checks

def get_verified_checks(archetype: str, conflict_detection: bool = False) -> list:
    checks = get_default_checks(archetype, conflict_detection)
    for c in checks:
        c["status"] = "verified"
    return checks

