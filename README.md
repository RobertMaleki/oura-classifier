# Battery Escalation Classifier

A lightweight, rule-based Python classifier designed to determine whether a support ticket in the **battery / charging / power** category should be escalated from **Finn** to a human agent.

This project was created as part of an Oura case study focused on designing an escalation flow that balances safe containment in self-service with deliberate, context-rich escalation when human intervention is more likely to resolve the issue.

## Purpose

The classifier mirrors the escalation framework defined in Task A of the case study:

1. Confirm the ticket belongs to the battery/power category
2. Escalate immediately for safety signals
3. Escalate for hard failure after troubleshooting
4. Escalate for human request after a reasonable attempt
5. Escalate for persistent unresolved issues
6. Otherwise retain in Finn

The goal is to keep the logic **simple, explainable, and easy to iterate on**, rather than over-engineering the solution.

## Output Schema

The classifier returns a structured dictionary with:

- `category_match`: whether the ticket matches the battery/power category
- `should_escalate`: whether the ticket should be escalated
- `escalation_reason`: the primary reason for the decision
- `matched_signals`: grouped matched keywords/phrases by signal type
- `confidence`: lightweight confidence score based on rule path

Example output:

```python
{
  "category_match": True,
  "should_escalate": True,
  "escalation_reason": "hard_failure_after_troubleshooting",
  "matched_signals": {
    "category": ["won't charge"],
    "safety": [],
    "hard_failure": ["won't charge"],
    "troubleshooting_completed": ["already tried", "tried another outlet"],
    "human_request": [],
    "persistent_unresolved": ["still won't charge"]
  },
  "confidence": 0.90
}