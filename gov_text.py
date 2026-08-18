"""
Flavor text pools for the Yen government personality.

Kept separate from main.py so the bureaucratic tone can be expanded or
tuned later without touching command logic.
"""

import random

DEPARTMENTS = [
    "Department of Linguistic Affairs",
    "Bureau of Compliance",
    "Ministry of Public Order",
    "Office of the Supreme Minister",
    "Department of Civic Standards",
    "Bureau of Message Regulation",
]

REJECTION_OPENERS = [
    "Your request has been rejected by the {dept}.",
    "This request has been denied by order of the {dept}.",
    "Request denied. The {dept} was not amused.",
    "The {dept} has declined to process this request.",
]

GRANT_SUCCESS_OPENERS = [
    "Your exemption has been approved.",
    "Government authorization granted.",
    "The {dept} has processed your exemption.",
    "Exemption approved and filed with the {dept}.",
]

DECLARE_INTROS = [
    "A new law has been announced.",
    "The government has issued a new decree.",
    "By unanimous vote of one, a new law is now in effect.",
    "The Supreme Minister of 67 has authorized a new law.",
]

REVOKE_SUCCESS_OPENERS = [
    "The law has been formally revoked.",
    "By order of the Supreme Minister of 67, this law is repealed.",
    "The {dept} confirms this law is no longer in effect.",
]

VIOLATION_HEADERS = [
    "LAW VIOLATION DETECTED.",
    "COMPLIANCE FAILURE DETECTED.",
    "VIOLATION LOGGED WITH THE {dept}.",
]


def _dept():
    return random.choice(DEPARTMENTS)


def rejection_opener():
    return random.choice(REJECTION_OPENERS).format(dept=_dept())


def grant_success_opener():
    return random.choice(GRANT_SUCCESS_OPENERS).format(dept=_dept())


def declare_intro():
    return random.choice(DECLARE_INTROS)


def revoke_success_opener():
    return random.choice(REVOKE_SUCCESS_OPENERS).format(dept=_dept())


def violation_header():
    return random.choice(VIOLATION_HEADERS).format(dept=_dept())


COMPLIANCE_STAGES = [
    "Processing compliance request...",
    "Checking citizenship...",
    "Checking government records...",
    "Consulting the Supreme Minister...",
    "Verifying compliance...",
]

COMPLIANCE_APPROVED_LINES = [
    "Compliance approved.",
    "Compliance approved. Your civic record has been updated.",
    "Compliance approved. The Bureau thanks you for your patience.",
    "Compliance approved. This interaction has been filed for the archives.",
]


def compliance_approved_line():
    return random.choice(COMPLIANCE_APPROVED_LINES)
