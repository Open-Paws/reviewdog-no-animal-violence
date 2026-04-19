#!/usr/bin/env python3
"""Self-contained scanner for language that normalizes violence toward animals.

Outputs one line per finding in the format reviewdog expects:
    filepath:linenum: "phrase" — reason. Consider: "alt1", "alt2"

Usage:
    python3 scan.py [file1 file2 ...]   # scan specific files
    python3 scan.py                     # walk current directory

Exit codes:
    0 — no findings
    1 — one or more findings detected

No third-party dependencies — stdlib only (re, os, sys).
"""

import os
import re
import sys

# ---------------------------------------------------------------------------
# Rules
# Each rule has:
#   patterns   — list of compiled regexes (any match triggers the rule)
#   phrase     — canonical human-readable phrase shown in the message
#   reason     — one sentence explaining why the term is harmful
#   alternatives — list of suggested replacements
#   severity   — "error" | "warning" | "info" (informational only; reviewdog
#                filters by --level independently)
# ---------------------------------------------------------------------------

RULES = [
    # --- Direct animal-violence idioms (error) -----------------------------
    {
        "patterns": [re.compile(
            r"kill\s+two\s+birds\s+with\s+one\s+stone", re.IGNORECASE)],
        "phrase": "kill two birds with one stone",
        "reason": "Violent animal idiom with universally clearer alternatives.",
        "alternatives": [
            "accomplish two things at once",
            "solve two problems with one action",
            "hit two targets with one shot",
        ],
        "severity": "error",
    },
    {
        "patterns": [re.compile(
            r"beat(?:ing)?\s+a\s+dead\s+horse", re.IGNORECASE)],
        "phrase": "beat a dead horse",
        "reason": "Violent animal idiom — alternatives are more direct.",
        "alternatives": [
            "belabor the point",
            "go over old ground",
            "repeat unnecessarily",
        ],
        "severity": "error",
    },
    {
        "patterns": [re.compile(
            r"(?:more\s+than\s+one|many|other)\s+ways?\s+to\s+skin\s+a\s+cat",
            re.IGNORECASE)],
        "phrase": "more than one way to skin a cat",
        "reason": "Violent animal idiom — alternatives are shorter and clearer.",
        "alternatives": [
            "more than one way to solve this",
            "multiple approaches available",
            "several ways to accomplish this",
        ],
        "severity": "error",
    },
    {
        "patterns": [re.compile(
            r"like\s+shooting\s+fish\s+in\s+a\s+barrel", re.IGNORECASE)],
        "phrase": "like shooting fish in a barrel",
        "reason": "Violent animal idiom with shorter, equally clear alternatives.",
        "alternatives": ["trivially easy", "effortless"],
        "severity": "error",
    },
    {
        "patterns": [re.compile(
            r"flog(?:ging)?\s+a\s+dead\s+horse", re.IGNORECASE)],
        "phrase": "flog a dead horse",
        "reason": "Violent animal idiom — same meaning as 'beat a dead horse'.",
        "alternatives": [
            "belabor the point",
            "waste effort on a settled matter",
            "repeat unnecessarily",
        ],
        "severity": "error",
    },
    {
        "patterns": [re.compile(
            r"curiosity\s+killed\s+the\s+cat", re.IGNORECASE)],
        "phrase": "curiosity killed the cat",
        "reason": "Directly references killing a cat.",
        "alternatives": [
            "curiosity backfired",
            "being nosy caused trouble",
            "curiosity led to trouble",
        ],
        "severity": "error",
    },
    {
        "patterns": [re.compile(
            r"like\s+a\s+chicken\s+with\s+(?:its|their)\s+head\s+cut\s+off",
            re.IGNORECASE)],
        "phrase": "like a chicken with its head cut off",
        "reason": "Graphic slaughter imagery — decapitating a chicken.",
        "alternatives": [
            "in a panic",
            "running around chaotically",
            "in complete disarray",
        ],
        "severity": "error",
    },
    {
        "patterns": [re.compile(
            r"(?:your|their|his|her)\s+goose\s+is\s+cooked", re.IGNORECASE)],
        "phrase": "your goose is cooked",
        "reason": "References killing and cooking a goose.",
        "alternatives": [
            "you're in trouble",
            "your fate is sealed",
            "it's over for you",
        ],
        "severity": "error",
    },
    {
        "patterns": [re.compile(
            r"throw(?:ing|n)?\s+\w+\s+to\s+the\s+wolves", re.IGNORECASE)],
        "phrase": "throw someone to the wolves",
        "reason": "References feeding a person to wolves as punishment.",
        "alternatives": [
            "abandon to criticism",
            "leave to face hostility alone",
            "sacrifice someone",
        ],
        "severity": "error",
    },
    {
        "patterns": [re.compile(
            r"(?:bring(?:ing|s)?|brought)\s+home\s+the\s+bacon", re.IGNORECASE)],
        "phrase": "bring home the bacon",
        "reason": "Animal slaughter idiom — alternatives are equally expressive.",
        "alternatives": [
            "bring home the results",
            "earn a living",
            "win the prize",
        ],
        "severity": "error",
    },
    {
        "patterns": [re.compile(
            r"don'?t\s+be\s+a\s+chicken", re.IGNORECASE)],
        "phrase": "don't be a chicken",
        "reason": "Uses an animal as an insult implying cowardice.",
        "alternatives": [
            "don't hesitate",
            "be brave",
            "go for it",
        ],
        "severity": "error",
    },
    {
        "patterns": [re.compile(
            r"like\s+lambs?\s+to\s+(?:the\s+)?slaughter", re.IGNORECASE)],
        "phrase": "like lambs to the slaughter",
        "reason": "Violent animal idiom directly referencing slaughter.",
        "alternatives": [
            "without resistance",
            "blindly following",
            "unknowingly walking into danger",
        ],
        "severity": "error",
    },

    # --- Animal idioms (warning / info) ------------------------------------
    {
        "patterns": [re.compile(
            r"let\s+the\s+cat\s+out\s+of\s+the\s+bag", re.IGNORECASE)],
        "phrase": "let the cat out of the bag",
        "reason": "Animal idiom — alternatives are more precise.",
        "alternatives": [
            "reveal the secret",
            "disclose prematurely",
            "let it slip",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"open(?:ing)?\s+a\s+can\s+of\s+worms", re.IGNORECASE)],
        "phrase": "open a can of worms",
        "reason": "Animal idiom — alternatives communicate the idea more directly.",
        "alternatives": [
            "create a complicated situation",
            "uncover hidden problems",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"wild\s+goose\s+chase", re.IGNORECASE)],
        "phrase": "wild goose chase",
        "reason": "Animal idiom — alternatives are more universally understood.",
        "alternatives": [
            "futile search",
            "pointless pursuit",
            "fool's errand",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"bigger\s+fish\s+to\s+fry", re.IGNORECASE)],
        "phrase": "bigger fish to fry",
        "reason": "Animal idiom — alternatives are more professional.",
        "alternatives": [
            "more important matters to address",
            "higher priorities",
            "bigger issues at hand",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"\bguinea\s+pig\b", re.IGNORECASE)],
        "phrase": "guinea pig",
        "reason": "Uses an animal-as-experiment metaphor — alternatives are more precise in technical contexts.",
        "alternatives": [
            "test subject",
            "first to try",
            "early adopter",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"hold\s+your\s+horses", re.IGNORECASE)],
        "phrase": "hold your horses",
        "reason": "Animal idiom — alternatives are more direct.",
        "alternatives": [
            "wait a moment",
            "slow down",
            "be patient",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"the\s+elephant\s+in\s+the\s+room", re.IGNORECASE)],
        "phrase": "the elephant in the room",
        "reason": "Well-understood animal idiom — flag for awareness only.",
        "alternatives": [
            "the obvious issue",
            "the unaddressed problem",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"straight\s+from\s+the\s+horse'?s\s+mouth", re.IGNORECASE)],
        "phrase": "straight from the horse's mouth",
        "reason": "Animal idiom — alternatives are clearer for international audiences.",
        "alternatives": [
            "directly from the source",
            "firsthand",
            "from the authority",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"(?:take|taking|took)\s+the\s+bull\s+by\s+the\s+horns",
            re.IGNORECASE)],
        "phrase": "take the bull by the horns",
        "reason": "Bullfighting idiom — alternatives convey the same assertiveness.",
        "alternatives": [
            "face the challenge head-on",
            "tackle the problem directly",
            "seize the opportunity",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"no\s+room\s+to\s+swing\s+a\s+cat", re.IGNORECASE)],
        "phrase": "no room to swing a cat",
        "reason": "Violent animal idiom — alternatives are shorter and clearer.",
        "alternatives": [
            "very cramped",
            "extremely tight space",
            "barely any room",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"\bred\s+herring\b", re.IGNORECASE)],
        "phrase": "red herring",
        "reason": "Animal-origin idiom — flag for awareness only.",
        "alternatives": [
            "distraction",
            "false lead",
            "misleading clue",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"hook,?\s+line,?\s+and\s+sinker", re.IGNORECASE)],
        "phrase": "hook, line, and sinker",
        "reason": "References hooking fish to catch and kill them.",
        "alternatives": [
            "completely",
            "without question",
            "fell for it entirely",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"clip(?:ping|ped)?\s+(?:\w+'?s?\s+)?wings", re.IGNORECASE)],
        "phrase": "clip someone's wings",
        "reason": "References wing-clipping, a physical mutilation done to farmed birds.",
        "alternatives": [
            "restrict someone's freedom",
            "limit someone's options",
            "hold someone back",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"(?:the\s+)?straw\s+that\s+broke\s+the\s+camel'?s\s+back",
            re.IGNORECASE)],
        "phrase": "the straw that broke the camel's back",
        "reason": "References overloading a pack animal until injury.",
        "alternatives": [
            "the tipping point",
            "the breaking point",
            "the final provocation",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"bird\s+in\s+(?:the|a)\s+hand\s+(?:is\s+)?worth\s+two\s+in\s+the\s+bush",
            re.IGNORECASE)],
        "phrase": "a bird in the hand is worth two in the bush",
        "reason": "References trapping and catching wild birds.",
        "alternatives": [
            "a sure thing beats a possibility",
            "certainty over speculation",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"\beat(?:ing)?\s+crow\b", re.IGNORECASE)],
        "phrase": "eat crow",
        "reason": "References eating a killed bird as punishment.",
        "alternatives": [
            "admit being wrong",
            "swallow one's pride",
            "accept humiliation",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"fight(?:ing)?\s+like\s+cats\s+and\s+dogs", re.IGNORECASE)],
        "phrase": "fight like cats and dogs",
        "reason": "References animal fighting.",
        "alternatives": [
            "constantly argue",
            "clash frequently",
            "have constant conflict",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"(?:take|taking|took)\s+the\s+bait", re.IGNORECASE)],
        "phrase": "take the bait",
        "reason": "References baiting hooks to catch and kill fish.",
        "alternatives": [
            "fall for it",
            "be lured in",
            "be deceived",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"don'?t\s+count\s+your\s+chickens", re.IGNORECASE)],
        "phrase": "don't count your chickens before they hatch",
        "reason": "References farming chickens as commodity and property.",
        "alternatives": [
            "don't assume success prematurely",
            "wait for confirmed results",
            "don't get ahead of yourself",
        ],
        "severity": "info",
    },

    # --- Industry euphemisms -----------------------------------------------
    {
        "patterns": [re.compile(r"\blivestock\b", re.IGNORECASE)],
        "phrase": "livestock",
        "reason": "Industry commodity framing that defines sentient beings by their commercial function.",
        "alternatives": [
            "farmed animals",
            "animals raised for food",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"\bpoultry\b", re.IGNORECASE)],
        "phrase": "poultry",
        "reason": "Industry commodity framing that abstracts individual birds into a bulk commodity term.",
        "alternatives": [
            "farmed birds",
            "chickens",
            "chickens and turkeys",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"gestation\s+crates?", re.IGNORECASE)],
        "phrase": "gestation crate",
        "reason": "Industry euphemism for a metal enclosure so small a pregnant sow cannot turn around for her entire pregnancy.",
        "alternatives": [
            "pregnancy cage",
            "pregnancy cages",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"\bdepopulat(?:ion|ed|ing)\b", re.IGNORECASE)],
        "phrase": "depopulation",
        "reason": "Industry euphemism used to describe killing entire flocks or herds en masse.",
        "alternatives": [
            "mass killing",
            "killed en masse",
            "killing en masse",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"processing\s+(?:plants?|facilit(?:y|ies))", re.IGNORECASE)],
        "phrase": "processing plant",
        "reason": "Industry euphemism — when referring to facilities that kill animals, 'slaughterhouse' is the accurate term.",
        "alternatives": [
            "slaughterhouse",
            "slaughterhouses",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"farrowing\s+crates?", re.IGNORECASE)],
        "phrase": "farrowing crate",
        "reason": "Industry euphemism for a metal cage confining a sow during and after birth, preventing her from turning around.",
        "alternatives": [
            "birthing cage",
            "birthing cages",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"battery\s+cages?", re.IGNORECASE)],
        "phrase": "battery cage",
        "reason": "Industry euphemism for wire enclosures giving each hen less floor space than a sheet of paper.",
        "alternatives": [
            "small wire cage",
            "small wire cages",
            "confined cage",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"\bspent\s+hens?\b", re.IGNORECASE)],
        "phrase": "spent hen",
        "reason": "Industry euphemism framing a living hen as a depleted resource when her egg production drops.",
        "alternatives": [
            "discarded hen",
            "discarded hens",
            "hen killed after egg production declines",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"\bhumane(?:ly)?\s+(?:slaughter(?:ed)?|kill(?:ing|ed))\b",
            re.IGNORECASE)],
        "phrase": "humane slaughter",
        "reason": "Industry oxymoron — the adjective 'humane' sanitizes the act; USDA standards still permit bolt guns and gas chambers.",
        "alternatives": [
            "slaughter",
            "slaughtered",
            "killing",
            "killed",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"\bbroilers?\b", re.IGNORECASE)],
        "phrase": "broiler",
        "reason": "Industry commodity term that defines a living chicken entirely by its commercial purpose.",
        "alternatives": [
            "chicken raised for meat",
            "chickens raised for meat",
            "meat chicken",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"\bveal\b", re.IGNORECASE)],
        "phrase": "veal",
        "reason": "Industry euphemism for the flesh of male dairy calves, typically killed within weeks of birth, obscuring species and age.",
        "alternatives": [
            "calf flesh",
            "flesh from calves",
        ],
        "severity": "warning",
    },

    # --- Tech jargon with animal references --------------------------------
    {
        "patterns": [re.compile(
            r"\b(?:code|memory|resource)\s+pig\b", re.IGNORECASE)],
        "phrase": "resource pig",
        "reason": "Uses an animal as an insult for resource consumption.",
        "alternatives": [
            "resource-intensive",
            "bloated",
            "heavy consumer",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"\bcowboy\s+cod(?:ing|er)\b", re.IGNORECASE)],
        "phrase": "cowboy coding",
        "reason": "Reinforces animal industry terminology in a technical context.",
        "alternatives": [
            "undisciplined coding",
            "ad-hoc development",
            "code without process",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(r"\bcode\s+monkeys?\b", re.IGNORECASE)],
        "phrase": "code monkey",
        "reason": "Uses an animal as an insult for programmers — dehumanizing and unprofessional.",
        "alternatives": [
            "developer",
            "programmer",
            "engineer",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"\bbadger(?:ed|ing|s)?\b", re.IGNORECASE)],
        "phrase": "badger",
        "reason": "Derives from badger-baiting, a blood sport where dogs attack captive badgers.",
        "alternatives": [
            "pester",
            "pressure",
            "harass",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"\bferret(?:ed|ing)?\s+out\b", re.IGNORECASE)],
        "phrase": "ferret out",
        "reason": "Derives from using ferrets to hunt rabbits out of burrows.",
        "alternatives": [
            "uncover",
            "discover",
            "dig up",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"cattle\s+vs?\.?\s+pets?", re.IGNORECASE)],
        "phrase": "cattle vs. pets",
        "reason": "Infrastructure metaphor that treats animals as objects — technically imprecise alternatives exist.",
        "alternatives": [
            "ephemeral vs. persistent",
            "disposable vs. unique",
            "numbered vs. named",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"\bpet\s+project\b", re.IGNORECASE)],
        "phrase": "pet project",
        "reason": "Common idiom — flag for awareness only.",
        "alternatives": [
            "side project",
            "passion project",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"canary\s+in\s+(?:a|the)\s+coal\s+mine", re.IGNORECASE)],
        "phrase": "canary in a coal mine",
        "reason": "References the practice of using caged canaries as disposable gas detectors in mines.",
        "alternatives": [
            "early warning signal",
            "leading indicator",
            "sentinel",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"\bdog\s?food(?:ing)?\b", re.IGNORECASE)],
        "phrase": "dogfooding",
        "reason": "Common tech term for self-hosting — flag for awareness only.",
        "alternatives": [
            "self-hosting",
            "eating your own cooking",
            "using internally",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(r"\bherding\s+cats\b", re.IGNORECASE)],
        "phrase": "herding cats",
        "reason": "Animal metaphor — alternatives are more descriptive.",
        "alternatives": [
            "coordinating independent contributors",
            "managing a distributed effort",
            "organizing chaos",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"fishing\s+expedition", re.IGNORECASE)],
        "phrase": "fishing expedition",
        "reason": "Animal metaphor — alternatives are more precise.",
        "alternatives": [
            "exploratory investigation",
            "unfocused search",
            "speculative inquiry",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"\bsacred\s+cows?\b", re.IGNORECASE)],
        "phrase": "sacred cow",
        "reason": "Treats cattle as objects while also trivializing Hindu beliefs — doubly insensitive.",
        "alternatives": [
            "unquestioned belief",
            "untouchable topic",
            "protected assumption",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"\bscapegoat(?:ed|ing|s)?\b", re.IGNORECASE)],
        "phrase": "scapegoat",
        "reason": "Originates from the ritual sacrifice of goats — alternatives are more precise.",
        "alternatives": [
            "blame target",
            "fall person",
            "wrongly blamed",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"\brat\s+race\b", re.IGNORECASE)],
        "phrase": "rat race",
        "reason": "Derogatory animal metaphor for futility — alternatives are more descriptive.",
        "alternatives": [
            "daily grind",
            "competitive treadmill",
            "endless hustle",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"dead[\s_-]?cat[\s_-]?bounce", re.IGNORECASE)],
        "phrase": "dead cat bounce",
        "reason": "Financial/tech term depicting animal death — alternatives are more professional.",
        "alternatives": [
            "temporary rebound",
            "false recovery",
            "brief uptick",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"\bdog[\s-]eat[\s-]dog\b", re.IGNORECASE)],
        "phrase": "dog-eat-dog",
        "reason": "Characterizes animals as inherently violent — alternatives convey the meaning more precisely.",
        "alternatives": [
            "ruthlessly competitive",
            "cutthroat",
            "fiercely competitive",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"\bwhack[\s-]a[\s-]mole\b", re.IGNORECASE)],
        "phrase": "whack-a-mole",
        "reason": "References a game based on hitting animals — alternatives describe the pattern more precisely.",
        "alternatives": [
            "recurring problem",
            "endless loop",
            "unwinnable game",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(r"\bcash\s+cows?\b", re.IGNORECASE)],
        "phrase": "cash cow",
        "reason": "Commodifies cows, treating living beings as profit generators.",
        "alternatives": [
            "profit center",
            "reliable revenue source",
            "money maker",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"\bsacrificial\s+lambs?\b", re.IGNORECASE)],
        "phrase": "sacrificial lamb",
        "reason": "References ritual slaughter of lambs.",
        "alternatives": [
            "expendable person",
            "person set up to fail",
            "someone sacrificed for others",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"\bsitting\s+ducks?\b", re.IGNORECASE)],
        "phrase": "sitting duck",
        "reason": "References a duck in the open, easy to shoot — hunting imagery.",
        "alternatives": [
            "easy target",
            "vulnerable target",
            "exposed",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"\bopen\s+season\b", re.IGNORECASE)],
        "phrase": "open season",
        "reason": "References hunting season — the legal period for killing animals.",
        "alternatives": [
            "free-for-all",
            "unrestricted criticism",
            "no holds barred",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"put(?:ting)?\s+(?:\w+\s+)?out\s+to\s+pasture", re.IGNORECASE)],
        "phrase": "put out to pasture",
        "reason": "References disposing of farm animals when they are no longer productive.",
        "alternatives": [
            "retire",
            "phase out",
            "sunset",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"\bdead\s+ducks?\b", re.IGNORECASE)],
        "phrase": "dead duck",
        "reason": "References a duck that has been shot and killed — hunting imagery.",
        "alternatives": [
            "lost cause",
            "doomed effort",
            "foregone conclusion",
        ],
        "severity": "info",
    },

    # --- Technical process language ----------------------------------------
    {
        "patterns": [re.compile(
            r"\bkill\s+(?:the\s+)?process\b", re.IGNORECASE)],
        "phrase": "kill process",
        "reason": "In POSIX context this is standard; in documentation, clearer alternatives exist.",
        "alternatives": [
            "terminate the process",
            "stop the process",
            "end the process",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"\bkill\s+(?:the\s+)?server\b", re.IGNORECASE)],
        "phrase": "kill the server",
        "reason": "Process language — alternatives are equally clear and less violent.",
        "alternatives": [
            "stop the server",
            "shut down the server",
            "terminate the server",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(
            r"\bnuke\s+(?:it|the|this|that|everything)\b", re.IGNORECASE)],
        "phrase": "nuke",
        "reason": "Violent metaphor in a technical context — alternatives are more professional.",
        "alternatives": [
            "delete completely",
            "wipe clean",
            "remove entirely",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"\babort(?:ed|ing)?\b", re.IGNORECASE)],
        "phrase": "abort",
        "reason": "Standard technical term — flag for awareness only in non-technical contexts.",
        "alternatives": [
            "cancel",
            "stop",
            "halt",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(r"\bcull(?:ed|ing|s)?\b", re.IGNORECASE)],
        "phrase": "cull",
        "reason": "Euphemism for mass killing of animals, used in wildlife management and farming.",
        "alternatives": [
            "remove",
            "prune",
            "trim",
            "filter out",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(r"\bmaster[/\\]slave\b", re.IGNORECASE)],
        "phrase": "master/slave",
        "reason": "Actively being replaced across the industry — follows existing inclusive naming initiatives.",
        "alternatives": [
            "primary/replica",
            "leader/follower",
            "controller/worker",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"\bwhitelist[/\\]blacklist\b", re.IGNORECASE)],
        "phrase": "whitelist/blacklist",
        "reason": "Actively being replaced — Google, Twitter, and IETF have adopted allowlist/denylist.",
        "alternatives": [
            "allowlist/denylist",
            "permit list/block list",
            "inclusion list/exclusion list",
        ],
        "severity": "warning",
    },
    {
        "patterns": [re.compile(
            r"\bgrandfather(?:ed|ing)?\b", re.IGNORECASE)],
        "phrase": "grandfathered",
        "reason": "Has historically exclusionary origins — alternatives are equally clear.",
        "alternatives": [
            "legacy",
            "exempt",
            "pre-existing",
        ],
        "severity": "info",
    },
    {
        "patterns": [re.compile(r"\blame[\s-]duck\b", re.IGNORECASE)],
        "phrase": "lame duck",
        "reason": "References a bird unable to fly due to injury — 'outgoing' or 'transitional' are more precise.",
        "alternatives": [
            "outgoing",
            "transitional",
            "ineffective",
        ],
        "severity": "info",
    },
]

# ---------------------------------------------------------------------------
# File extensions to scan
# ---------------------------------------------------------------------------

SCAN_EXTENSIONS = {
    ".py", ".js", ".ts", ".md", ".yml", ".yaml",
    ".go", ".rs", ".java", ".rb", ".txt", ".rst",
    ".toml", ".sh",
}

# ---------------------------------------------------------------------------
# Paths to skip when walking the directory tree
# ---------------------------------------------------------------------------

SKIP_DIRS = {".git", "node_modules", "vendor"}


# ---------------------------------------------------------------------------
# Core scanning logic
# ---------------------------------------------------------------------------

def format_message(rule, matched_text):
    """Build the single-line reviewdog message for a finding."""
    alts = ", ".join(f'"{a}"' for a in rule["alternatives"])
    return (
        f'"{matched_text}" \u2014 {rule["reason"]} '
        f'Consider: {alts}'
    )


def scan_file(filepath):
    """Scan a single file. Yields (filepath, line_num, message) tuples."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            for line_num, line in enumerate(fh, start=1):
                for rule in RULES:
                    for pattern in rule["patterns"]:
                        for match in pattern.finditer(line):
                            yield (
                                filepath,
                                line_num,
                                format_message(rule, match.group()),
                            )
    except (OSError, IOError):
        pass


def walk_directory(root):
    """Yield all scannable file paths under root, skipping ignored dirs."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in-place so os.walk does not descend.
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS
        ]
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext.lower() in SCAN_EXTENSIONS:
                yield os.path.join(dirpath, filename)


def main():
    """Entry point."""
    file_args = sys.argv[1:]
    if file_args:
        files = file_args
    else:
        files = list(walk_directory("."))

    found = False
    for filepath in files:
        for filepath_out, line_num, message in scan_file(filepath):
            print(f"{filepath_out}:{line_num}: {message}")
            found = True

    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
