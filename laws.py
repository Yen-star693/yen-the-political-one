"""
Law type registry for the Yen government system.

To add a new law type later:

1. Write a `make_*()` function that returns a dict with the keys:
   id, description, params, violation_text, permission_action.
2. Write a matching `check_*(content, params)` function that returns True
   if the given message content VIOLATES the law.
3. Register both in LAW_TYPES under a unique type key.

That's it. `yen declare a new martial law` and the enforcement loop in
main.py both work off LAW_TYPES automatically, so no other code needs to
change to add a new law.

The MESSAGE LIMIT law type is a special case: its violation depends on
timing, not just message content, so it is handled separately in the
enforcement loop in main.py rather than through a plain check() function.
Its entry in LAW_TYPES still needs a "make" function, and its "check" is
set to None as a marker.
"""

import random
import string

FORBIDDEN_WORD_POOL = [
    "banana", "moist", "bureaucracy", "committee", "paperwork",
    "election", "taxes", "duck", "spreadsheet", "quorum",
    "napkin", "stapler", "broccoli", "raccoon", "yodel",
    "gravy", "pigeon", "spatula", "loophole", "casserole",
]

GOVERNMENT_PREFIXES = [
    "By order of the Ministry,",
    "As decreed by the state,",
    "In accordance with government policy,",
    "Under official sanction,",
    "For the official record,",
    "With the blessing of the Bureau,",
]

MESSAGE_LIMIT_OPTIONS = [15, 20, 30, 45, 60, 90]


def make_no_b():
    return {
        "id": "NO B",
        "description": "Users aren't allowed to use the letter B/b.",
        "params": {},
        "violation_text": "Unauthorized use of the letter B/b was detected.",
        "permission_action": "use the letter B",
    }


def check_no_b(content, params):
    return "b" in content.lower()


def make_no_numbers():
    return {
        "id": "NO NUMBERS",
        "description": "Users aren't allowed to use numerical digits.",
        "params": {},
        "violation_text": "Unauthorized use of a numerical digit was detected.",
        "permission_action": "use numbers",
    }


def check_no_numbers(content, params):
    return any(ch.isdigit() for ch in content)


def make_no_caps():
    return {
        "id": "NO CAPS",
        "description": "Users aren't allowed to use uppercase letters.",
        "params": {},
        "violation_text": "Unauthorized use of uppercase lettering was detected.",
        "permission_action": "use uppercase letters",
    }


def check_no_caps(content, params):
    return any(ch.isupper() for ch in content)


def make_seven_words():
    return {
        "id": "SEVEN WORDS",
        "description": "Messages must contain exactly seven words.",
        "params": {},
        "violation_text": "Your message did not contain exactly seven words.",
        "permission_action": "send messages that are not exactly seven words long",
    }


def check_seven_words(content, params):
    words = content.split()
    return len(words) != 7


def make_no_punctuation():
    return {
        "id": "NO PUNCTUATION",
        "description": "Users aren't allowed to use punctuation.",
        "params": {},
        "violation_text": "Unauthorized punctuation was detected in your message.",
        "permission_action": "use punctuation",
    }


def check_no_punctuation(content, params):
    return any(ch in string.punctuation for ch in content)


def make_government_prefix():
    phrase = random.choice(GOVERNMENT_PREFIXES)
    return {
        "id": "GOVERNMENT PREFIX",
        "description": 'Every message must begin with the phrase "{}"'.format(phrase),
        "params": {"phrase": phrase},
        "violation_text": (
            'Your message did not begin with the mandated government prefix: '
            '"{}"'.format(phrase)
        ),
        "permission_action": "send messages without the mandated government prefix",
    }


def check_government_prefix(content, params):
    return not content.strip().lower().startswith(params["phrase"].lower())


def make_forbidden_word():
    word = random.choice(FORBIDDEN_WORD_POOL)
    return {
        "id": "FORBIDDEN WORD",
        "description": 'The word "{}" has been declared illegal.'.format(word),
        "params": {"word": word},
        "violation_text": 'Your message contained the illegal word "{}".'.format(word),
        "permission_action": 'use the word "{}"'.format(word),
    }


def check_forbidden_word(content, params):
    target = params["word"].lower()
    tokens = content.lower().split()
    stripped_tokens = [tok.strip(string.punctuation) for tok in tokens]
    return target in stripped_tokens


def make_message_limit():
    seconds = random.choice(MESSAGE_LIMIT_OPTIONS)
    return {
        "id": "MESSAGE LIMIT",
        "description": "Users may only send one message every {} seconds.".format(seconds),
        "params": {"seconds": seconds},
        "violation_text": (
            "You attempted to send a message before the mandated waiting "
            "period of {} seconds had elapsed.".format(seconds)
        ),
        "permission_action": "send messages without the mandated waiting period",
    }


# check is intentionally None here; MESSAGE LIMIT is timing-based and is
# enforced directly in main.py using last_message_ts, not this function.
LAW_TYPES = {
    "NO B": {"make": make_no_b, "check": check_no_b},
    "NO NUMBERS": {"make": make_no_numbers, "check": check_no_numbers},
    "NO CAPS": {"make": make_no_caps, "check": check_no_caps},
    "SEVEN WORDS": {"make": make_seven_words, "check": check_seven_words},
    "NO PUNCTUATION": {"make": make_no_punctuation, "check": check_no_punctuation},
    "GOVERNMENT PREFIX": {"make": make_government_prefix, "check": check_government_prefix},
    "FORBIDDEN WORD": {"make": make_forbidden_word, "check": check_forbidden_word},
    "MESSAGE LIMIT": {"make": make_message_limit, "check": None},
}
