from typing import Dict, List
import re


CATEGORY_KEYWORDS = [
    "battery",
    "charge",
    "charging",
    "charger",
    "power",
    "dead",
    "draining",
    "drains fast",
    "battery drain",
    "not holding charge",
    "won't charge",
    "will not charge",
    "not charging",
    "won't turn on",
    "will not turn on",
    "not turning on",
    "won't power on",
    "will not power on",
    "not powering on",
]

SAFETY_SIGNALS = [
    "hot",
    "overheating",
    "overheat",
    "burning",
    "burn",
    "smoke",
    "swelling",
    "unsafe",
]

HARD_FAILURE_SIGNALS = [
    "won't charge",
    "will not charge",
    "not charging",
    "won't turn on",
    "will not turn on",
    "not turning on",
    "won't power on",
    "will not power on",
    "not powering on",
    "dead",
    "completely dead",
    "doesn't charge",
    "does not charge",
    "stopped charging",
    "won't hold a charge",
    "not holding charge",
]

TROUBLESHOOTING_COMPLETED_SIGNALS = [
    "already tried",
    "i tried",
    "tried that",
    "did that already",
    "followed the steps",
    "went through the troubleshooting",
    "restarted",
    "reset it",
    "soft reset",
    "used another outlet",
    "tried another outlet",
    "tried a different outlet",
    "used another charger",
    "tried another charger",
    "left it on the charger",
    "updated firmware",
    "updated the firmware",
]

HUMAN_REQUEST_SIGNALS = [
    "human",
    "agent",
    "representative",
    "real person",
    "support person",
    "customer support",
    "connect me to",
    "let me talk to",
    "speak to someone",
]

PERSISTENT_UNRESOLVED_SIGNALS = [
    "still not working",
    "still won't charge",
    "still wont charge",
    "still won't turn on",
    "still wont turn on",
    "still happening",
    "same issue",
    "again",
    "keeps happening",
    "nothing worked",
    "nothing helped",
    "didn't help",
    "did not help",
    "no change",
    "not fixed",
]


def _normalize_text(subject: str, body: str) -> str:
    return f"{subject} {body}".lower().strip()

def _find_matches(text: str, signals: List[str]) -> List[str]:
    matches = []

    for signal in sorted(signals, key=len, reverse=True):
        pattern = r"\b" + re.escape(signal) + r"\b"
        if re.search(pattern, text):
            # Skip shorter matches that are contained inside a longer one already matched
            if not any(signal in existing for existing in matches):
                matches.append(signal)

    return sorted(matches)


def should_escalate(subject: str, body: str) -> Dict:
    """
    Determine whether a battery/power-related support ticket should be
    escalated from Finn to a human agent.

    This lightweight, rule-based classifier mirrors the Task A escalation logic:
    1. Confirm category match
    2. Escalate immediately for safety signals
    3. Escalate for hard failure after troubleshooting
    4. Escalate for human request after a reasonable attempt
    5. Escalate for persistent unresolved issues
    6. Otherwise retain in Finn
    """

    text = _normalize_text(subject, body)

    matched_category = _find_matches(text, CATEGORY_KEYWORDS)
    matched_safety = _find_matches(text, SAFETY_SIGNALS)
    matched_hard_failure = _find_matches(text, HARD_FAILURE_SIGNALS)
    matched_troubleshooting = _find_matches(text, TROUBLESHOOTING_COMPLETED_SIGNALS)
    matched_human_request = _find_matches(text, HUMAN_REQUEST_SIGNALS)
    matched_persistent = _find_matches(text, PERSISTENT_UNRESOLVED_SIGNALS)

    matched_signals = {
        "category": matched_category,
        "safety": matched_safety,
        "hard_failure": matched_hard_failure,
        "troubleshooting_completed": matched_troubleshooting,
        "human_request": matched_human_request,
        "persistent_unresolved": matched_persistent,
    }

    category_match = len(matched_category) > 0

    if not category_match:
        return {
            "category_match": False,
            "should_escalate": False,
            "escalation_reason": "no_category_match",
            "matched_signals": matched_signals,
            "confidence": 0.50,
        }

    if matched_safety:
        return {
            "category_match": True,
            "should_escalate": True,
            "escalation_reason": "safety_signal",
            "matched_signals": matched_signals,
            "confidence": 0.95,
        }

    if matched_hard_failure and matched_troubleshooting:
        return {
            "category_match": True,
            "should_escalate": True,
            "escalation_reason": "hard_failure_after_troubleshooting",
            "matched_signals": matched_signals,
            "confidence": 0.90,
        }

    reasonable_attempt = bool(matched_troubleshooting or matched_persistent)
    if matched_human_request and reasonable_attempt:
        return {
            "category_match": True,
            "should_escalate": True,
            "escalation_reason": "human_request_after_reasonable_attempt",
            "matched_signals": matched_signals,
            "confidence": 0.85,
        }

    if matched_persistent:
        return {
            "category_match": True,
            "should_escalate": True,
            "escalation_reason": "persistent_unresolved_issue",
            "matched_signals": matched_signals,
            "confidence": 0.80,
        }

    return {
        "category_match": True,
        "should_escalate": False,
        "escalation_reason": "retain_in_finn",
        "matched_signals": matched_signals,
        "confidence": 0.70,
    }

#  Example test cases
if __name__ == "__main__":
    samples = [
        {
            "name": "Safety escalation",
            "subject": "Ring overheating while charging",
            "body": "My ring gets hot while charging and I’m worried it’s unsafe.",
        },
        {
            "name": "Hard failure after troubleshooting",
            "subject": "Ring won't charge",
            "body": "I already tried another outlet and left it on the charger, but it still won't charge.",
        },
        {
            "name": "Retain in Finn",
            "subject": "Battery question",
            "body": "What can I do to improve battery life?",
        },
        {
            "name": "Human request after reasonable attempt",
            "subject": "Battery still draining quickly",
            "body": "I already tried restarting it and updated the firmware. I need to talk to a human.",
        },
        {
            "name": "Persistent unresolved issue",
            "subject": "Same battery issue again",
            "body": "My ring is still not working. This is the same issue again and nothing helped.",
        },
    ]

    for sample in samples:
        result = should_escalate(sample["subject"], sample["body"])
        print(f"\n--- {sample['name']} ---")
        print(result)