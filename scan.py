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
#
# Synced from: https://github.com/Open-Paws/no-animal-violence/blob/main/rules.yaml
# Total rules: 158
# ---------------------------------------------------------------------------

RULES = [
    # kill-two-birds-with-one-stone
    {
        "patterns": [re.compile(
            'kill\\s+two\\s+birds\\s+with\\s+one\\s+stone', re.IGNORECASE)],
        "phrase": 'kill two birds with one stone',
        "reason": "This phrase frames killing animals as a routine way to solve a problem. Plain alternatives like 'accomplish two things at once' carry the same meaning without invoking harm.",
        "alternatives": ['accomplish two things at once', 'solve two problems with one action', 'hit two targets with one shot'],
    },
    # beat-a-dead-horse
    {
        "patterns": [re.compile(
            'beat(ing)?\\s+a\\s+dead\\s+horse', re.IGNORECASE)],
        "phrase": 'beat a dead horse',
        "reason": "This phrase uses an image of striking an animal's body as a metaphor for wasted effort. 'Belabor the point' is clearer and skips the imagery.",
        "alternatives": ['belabor the point', 'go over old ground', 'repeat unnecessarily'],
    },
    # skin-a-cat
    {
        "patterns": [re.compile(
            '(more\\s+than\\s+one|another|different|several)\\s+way[s]?\\s+to\\s+skin\\s+a\\s+cat', re.IGNORECASE)],
        "phrase": 'more than one way to skin a cat',
        "reason": "Cat skinning as a metaphor for having options. 'Multiple approaches available' or 'more than one way to peel an orange' carries the same meaning.",
        "alternatives": ['more than one way to peel an orange', 'multiple approaches available', 'several ways to do this'],
    },
    # let-the-cat-out-of-the-bag
    {
        "patterns": [re.compile(
            'let\\s+the\\s+cat\\s+out\\s+of\\s+the\\s+bag', re.IGNORECASE)],
        "phrase": 'let the cat out of the bag',
        "reason": "Traced to fraudulent livestock markets and implies trapping animals. 'Reveal the secret' says the same thing more directly.",
        "alternatives": ['reveal the secret', 'disclose prematurely', 'let it slip'],
    },
    # open-a-can-of-worms
    {
        "patterns": [re.compile(
            'open(ing)?\\s+a\\s+can\\s+of\\s+worms', re.IGNORECASE)],
        "phrase": 'open a can of worms',
        "reason": "References worms packaged as live bait to catch and kill fish. 'Open a difficult topic' or 'uncover hidden problems' is more precise.",
        "alternatives": ['create a complicated situation', 'uncover hidden problems', "open Pandora's box"],
    },
    # wild-goose-chase
    {
        "patterns": [re.compile(
            'wild\\s+goose\\s+chase', re.IGNORECASE)],
        "phrase": 'wild goose chase',
        "reason": "Casts pursuing a living bird as a pointless annoyance. 'Futile search' or 'fool's errand' says the same thing without the hunting framing.",
        "alternatives": ['futile search', 'pointless pursuit', "fool's errand"],
    },
    # shooting-fish-in-a-barrel
    {
        "patterns": [re.compile(
            '(like\\s+)?shoot(ing)?\\s+fish\\s+in\\s+a\\s+barrel', re.IGNORECASE)],
        "phrase": 'shooting fish in a barrel',
        "reason": "Mass-killing imagery used to mean 'easy.' 'Trivially easy' or 'a sure thing' says the same thing without it.",
        "alternatives": ['trivially easy', 'a sure thing', 'no challenge at all'],
    },
    # flog-a-dead-horse
    {
        "patterns": [re.compile(
            'flog(ging)?\\s+a\\s+dead\\s+horse', re.IGNORECASE)],
        "phrase": 'flog a dead horse',
        "reason": "Describes whipping an animal's corpse — the same image as 'beat a dead horse'. 'Belabor the point' is a direct replacement.",
        "alternatives": ['belabor the point', 'waste effort on a settled matter', 'repeat unnecessarily'],
    },
    # bigger-fish-to-fry
    {
        "patterns": [re.compile(
            '(bigger|other)\\s+fish\\s+to\\s+fry', re.IGNORECASE)],
        "phrase": 'bigger fish to fry',
        "reason": "Fish-as-food commodification for 'more important things.' 'More important matters' says the same thing.",
        "alternatives": ['more important matters to address', 'bigger fish to free'],
    },
    # guinea-pig
    {
        "patterns": [re.compile(
            '\\bguinea\\s+pig\\b', re.IGNORECASE)],
        "phrase": 'guinea pig',
        "reason": "Refers to using guinea pigs as expendable test subjects in harmful experiments. 'Test subject' or 'early adopter' is more precise in technical contexts.",
        "alternatives": ['test subject', 'first to try', 'early adopter'],
    },
    # bring-home-the-bacon
    {
        "patterns": [re.compile(
            '(?:bring(?:ing|s)?|brought)\\s+home\\s+the\\s+bacon', re.IGNORECASE)],
        "phrase": 'bring home the bacon',
        "reason": "Describes slaughtered pig flesh as the fruit of success. 'Bring home the results' or 'earn a living' carries the same meaning.",
        "alternatives": ['bring home the results', 'earn a living', 'win the prize'],
    },
    # take-the-bull-by-horns
    {
        "patterns": [re.compile(
            'tak(e|ing|es|en)\\s+the\\s+bull\\s+by\\s+the\\s+horns|took\\s+the\\s+bull\\s+by\\s+the\\s+horns', re.IGNORECASE)],
        "phrase": 'take the bull by the horns',
        "reason": "Bullfighting/rodeo imagery. 'Tackle the problem directly' or 'face it head-on' is cleaner.",
        "alternatives": ['tackle the problem directly', 'face it head-on', 'confront the issue'],
    },
    # lambs-to-slaughter
    {
        "patterns": [re.compile(
            '(like\\s+(a\\s+)?)?lambs?\\s+to\\s+the\\s+slaughter', re.IGNORECASE)],
        "phrase": 'lambs to the slaughter',
        "reason": "Direct slaughter imagery. 'Without resistance' or 'unknowingly walking into danger' captures the same meaning.",
        "alternatives": ['without resistance', 'unknowingly walking into danger', 'defenseless'],
    },
    # no-room-to-swing-a-cat
    {
        "patterns": [re.compile(
            '(no|not\\s+enough)\\s+room\\s+to\\s+swing\\s+a\\s+cat', re.IGNORECASE)],
        "phrase": 'no room to swing a cat',
        "reason": "Violent animal imagery for 'cramped.' 'Extremely tight space' says it directly.",
        "alternatives": ['extremely tight space', 'very cramped'],
    },
    # red-herring
    {
        "patterns": [re.compile(
            '\\bred\\s+herring\\b', re.IGNORECASE)],
        "phrase": 'red herring',
        "reason": "Originates from dead, smoked fish reportedly used to train hunting dogs. 'Distraction' or 'false lead' communicates the idea directly.",
        "alternatives": ['distraction', 'false lead', 'misleading clue'],
    },
    # curiosity-killed-the-cat
    {
        "patterns": [re.compile(
            'curiosity\\s+killed\\s+the\\s+cat', re.IGNORECASE)],
        "phrase": 'curiosity killed the cat',
        "reason": "A direct reference to killing a cat, used as a cautionary phrase. 'Curiosity backfired' or 'being nosy caused trouble' says the same thing.",
        "alternatives": ['curiosity backfired', 'being nosy caused trouble', 'curiosity led to trouble'],
    },
    # chicken-head-cut-off
    {
        "patterns": [re.compile(
            '(running\\s+around\\s+)?like\\s+a\\s+chicken\\s+with\\s+(its|their)\\s+head\\s+cut\\s+off', re.IGNORECASE)],
        "phrase": 'like a chicken with its head cut off',
        "reason": "Graphic slaughter imagery used to describe panic. 'In a panic' or 'like your hair is on fire' captures the same thing.",
        "alternatives": ['like your hair is on fire', 'in a panic', 'frantic and aimless'],
    },
    # goose-is-cooked
    {
        "patterns": [re.compile(
            '(your|their|his|her|my|our)\\s+goose\\s+is\\s+cooked', re.IGNORECASE)],
        "phrase": 'your goose is cooked',
        "reason": "Killing-and-cooking imagery used to mean someone is in trouble. 'You're in trouble' says it directly.",
        "alternatives": ["you're in trouble", "you're done for", "you're dead in the water"],
    },
    # throw-to-wolves
    {
        "patterns": [re.compile(
            'thr(ow|owing|own|ew)(\\s+(someone|them|him|her|us|me))?\\s+to\\s+the\\s+wolves', re.IGNORECASE)],
        "phrase": 'throw someone to the wolves',
        "reason": "Frames a person as prey. 'Abandon to criticism' or 'leave exposed' carries the same meaning without the imagery.",
        "alternatives": ['abandon to criticism', 'sacrifice someone', 'leave exposed'],
    },
    # hook-line-and-sinker
    {
        "patterns": [re.compile(
            'hook,?\\s+line,?\\s+and\\s+sinker', re.IGNORECASE)],
        "phrase": 'hook, line, and sinker',
        "reason": "References the equipment used to hook and kill fish. 'Completely' or 'without question' conveys total buy-in without the fishing imagery.",
        "alternatives": ['completely', 'without question', 'fell for it entirely'],
    },
    # clip-wings
    {
        "patterns": [re.compile(
            "clip(s|ped|ping)?\\s+(someone's|their|his|her)?\\s*wings", re.IGNORECASE)],
        "phrase": "clip someone's wings",
        "reason": "Wing-clipping is a real physical mutilation done to captive birds. 'Restrict freedom' or 'limit options' says the same thing directly.",
        "alternatives": ['restrict freedom', 'limit options', 'hold back'],
    },
    # straw-that-broke-camels-back
    {
        "patterns": [re.compile(
            "straw\\s+that\\s+broke\\s+the\\s+camel'?s\\s+back|last\\s+straw", re.IGNORECASE)],
        "phrase": "straw that broke the camel's back",
        "reason": "Overloading a pack animal until its back breaks. 'Tipping point' or 'breaking point' carries the same meaning.",
        "alternatives": ['tipping point', 'breaking point', 'final blow'],
    },
    # a-bird-in-the-hand
    {
        "patterns": [re.compile(
            '(a\\s+)?bird\\s+in\\s+the\\s+hand(\\s+is\\s+worth)?', re.IGNORECASE)],
        "phrase": 'a bird in the hand',
        "reason": "References trapping wild birds. 'A sure thing beats a possibility' carries the same meaning.",
        "alternatives": ['a sure thing beats a possibility', 'a guaranteed outcome is worth more'],
    },
    # eat-crow
    {
        "patterns": [re.compile(
            '\\beat(ing)?\\s+crow\\b', re.IGNORECASE)],
        "phrase": 'eat crow',
        "reason": "References eating a killed bird as humiliating punishment. 'Admit being wrong' or 'swallow one's pride' says the same thing directly.",
        "alternatives": ['admit being wrong', "swallow one's pride", 'accept humiliation'],
    },
    # fight-like-cats-and-dogs
    {
        "patterns": [re.compile(
            'f(ight|ights|ighting|ought)\\s+like\\s+cats\\s+and\\s+dogs', re.IGNORECASE)],
        "phrase": 'fight like cats and dogs',
        "reason": "Animal-fighting imagery. 'Constantly argue' or 'clash frequently' says it directly.",
        "alternatives": ['constantly argue', 'clash frequently'],
    },
    # take-the-bait
    {
        "patterns": [re.compile(
            '(?:take|taking|took)\\s+the\\s+bait', re.IGNORECASE)],
        "phrase": 'take the bait',
        "reason": "References baiting hooks and traps to catch and kill animals. 'Fall for it' or 'be deceived' is more direct.",
        "alternatives": ['fall for it', 'be lured in', 'be deceived'],
    },
    # dont-count-your-chickens
    {
        "patterns": [re.compile(
            "(don'?t\\s+)?count(ing)?\\s+your\\s+chickens(\\s+before)?", re.IGNORECASE)],
        "phrase": "don't count your chickens",
        "reason": "Commodity framing of chickens as a yield to be counted. 'Don't assume success prematurely' says it directly.",
        "alternatives": ["don't assume success prematurely", "don't celebrate too early"],
    },
    # livestock
    {
        "patterns": [re.compile(
            '\\blivestock\\b', re.IGNORECASE)],
        "phrase": 'livestock',
        "reason": "Commodity framing that groups sentient beings as 'stock.' 'Farmed animals' keeps the meaning without the commodity framing.",
        "alternatives": ['farmed animals'],
    },
    # poultry
    {
        "patterns": [re.compile(
            '\\bpoultry\\b', re.IGNORECASE)],
        "phrase": 'poultry',
        "reason": "Commodity framing for farmed birds. 'Farmed birds' or the specific species keeps the meaning without the commodity framing.",
        "alternatives": ['farmed birds', 'chickens and turkeys'],
    },
    # gestation-crate
    {
        "patterns": [re.compile(
            'gestation\\s+(crate|stall)s?', re.IGNORECASE)],
        "phrase": 'gestation crate',
        "reason": "Industry euphemism for a metal enclosure so small a pregnant sow cannot turn around for her entire 3.5-month pregnancy. 'Pregnancy cage' is accurate.",
        "alternatives": ['pregnancy cage'],
    },
    # depopulation
    {
        "patterns": [re.compile(
            '\\bdepopulat(ion|ed|ing)\\b', re.IGNORECASE)],
        "phrase": 'depopulation',
        "reason": "Industry euphemism for killing entire flocks or herds at once. 'Mass killing' is the accurate term. (Suppressed in database or population-statistics contexts where the word refers to removing records.)",
        "alternatives": ['mass killing', 'killed en masse'],
    },
    # processing-plant
    {
        "patterns": [re.compile(
            '(meat[\\s-]?packing|meat|packing|processing)\\s+(plant|facility)s?', re.IGNORECASE)],
        "phrase": 'meat plant',
        "reason": "Industry euphemisms for slaughterhouse. 'Slaughterhouse' is the accurate term. (Suppressed in clearly non-animal contexts like data or chemical processing.)",
        "alternatives": ['slaughterhouse'],
    },
    # farrowing-crate
    {
        "patterns": [re.compile(
            'farrowing\\s+(crate|stall)s?', re.IGNORECASE)],
        "phrase": 'farrowing crate',
        "reason": "Industry euphemism for the metal cage confining a sow during birth and nursing. 'Birthing cage' is accurate.",
        "alternatives": ['birthing cage'],
    },
    # battery-cage
    {
        "patterns": [re.compile(
            'battery[\\s-]cage[ds]?', re.IGNORECASE)],
        "phrase": 'battery cage',
        "reason": "Industry euphemism for wire enclosures that give each hen less floor space than a sheet of paper. 'Small wire cage' describes what it is.",
        "alternatives": ['small wire cage', 'confined cage'],
    },
    # spent-hen
    {
        "patterns": [re.compile(
            'spent\\s+hens?', re.IGNORECASE)],
        "phrase": 'spent hen',
        "reason": "'Spent' frames the hen as a depleted resource. Naming what actually happens — she is killed when her egg production falls — is more accurate.",
        "alternatives": ['hen killed after egg production declines'],
    },
    # humane-slaughter
    {
        "patterns": [re.compile(
            'humane(ly)?\\s+(slaughter(ed)?|killing|death)', re.IGNORECASE)],
        "phrase": 'humane slaughter',
        "reason": "Industry oxymoron — a killing cannot be 'humane' to the one being killed. Drop the modifier and use 'slaughter' or 'killing.'",
        "alternatives": ['slaughter', 'killing'],
    },
    # broiler-chicken
    {
        "patterns": [re.compile(
            'broiler\\s+(chickens?|hens?)|broilers', re.IGNORECASE)],
        "phrase": 'broiler chicken',
        "reason": "Industry term that defines a chicken by its commercial purpose. 'Chicken raised for meat' is the human-readable version. (The kitchen appliance is not flagged.)",
        "alternatives": ['chicken raised for meat'],
    },
    # dont-be-a-chicken
    {
        "patterns": [re.compile(
            "don'?t\\s+be\\s+a\\s+chicken", re.IGNORECASE)],
        "phrase": "don't be a chicken",
        "reason": "Uses a chicken as an insult for cowardice. 'Don't hesitate' or 'be brave' is direct and doesn't rely on a demeaning stereotype.",
        "alternatives": ["don't hesitate", 'be brave', 'go for it'],
    },
    # badger-someone
    {
        "patterns": [re.compile(
            '\\bbadger(ed|ing|s)?\\b', re.IGNORECASE)],
        "phrase": 'badger someone',
        "reason": "Comes from badger-baiting, a blood sport where dogs were set on captive badgers. 'Pester' or 'pressure' carries the same meaning without the origin.",
        "alternatives": ['pester', 'pressure', 'harass'],
    },
    # ferret-out
    {
        "patterns": [re.compile(
            '\\bferret(ed|ing)?\\s+out\\b', re.IGNORECASE)],
        "phrase": 'ferret out',
        "reason": "Refers to the historical use of ferrets to flush rabbits out of burrows to be killed. 'Uncover' or 'dig up' works just as well.",
        "alternatives": ['uncover', 'discover', 'dig up'],
    },
    # cattle-vs-pets
    {
        "patterns": [re.compile(
            'cattle[,]?\\s+(not|vs\\.?|versus)\\s+pets|pets\\s+not\\s+cattle', re.IGNORECASE)],
        "phrase": 'cattle not pets',
        "reason": "Infrastructure metaphor that Google's own style guide flags for removal as 'figurative language that relates to the slaughter of animals.' 'Ephemeral vs. persistent' or 'disposable vs. unique' captures the same architectural concept.",
        "alternatives": ['ephemeral vs. persistent', 'disposable vs. unique', 'numbered vs. named'],
    },
    # canary-in-a-coal-mine
    {
        "patterns": [re.compile(
            'canary\\s+in\\s+(a|the)\\s+coal\\s+mine', re.IGNORECASE)],
        "phrase": 'canary in a coal mine',
        "reason": "Refers to canaries historically placed in coal mines to die first as a warning to miners. 'Early warning signal' or 'sentinel' conveys the meaning without the harm.",
        "alternatives": ['early warning signal', 'leading indicator', 'sentinel'],
    },
    # fishing-expedition
    {
        "patterns": [re.compile(
            'fishing\\s+expeditions?', re.IGNORECASE)],
        "phrase": 'fishing expedition',
        "reason": "Frames speculative inquiry as fishing — the metaphor softens the catch. 'Exploratory investigation' is clearer, especially in legal writing.",
        "alternatives": ['exploratory investigation', 'speculative inquiry', 'unfocused search'],
    },
    # sacred-cow
    {
        "patterns": [re.compile(
            '\\bsacred\\s+cows?\\b', re.IGNORECASE)],
        "phrase": 'sacred cow',
        "reason": "Treats cattle as objects in an 'untouchable' metaphor while also trivializing Hindu beliefs. 'Unquestioned belief' or 'protected assumption' avoids both issues.",
        "alternatives": ['unquestioned belief', 'untouchable topic', 'protected assumption'],
    },
    # scapegoat
    {
        "patterns": [re.compile(
            '\\bscapegoat(ed|ing|s)?\\b', re.IGNORECASE)],
        "phrase": 'scapegoat',
        "reason": "Originates from the ritual sacrifice of goats to carry away blame. 'Blame target' or 'wrongly blamed' is more precise.",
        "alternatives": ['blame target', 'fall person', 'wrongly blamed'],
    },
    # dead-cat-bounce
    {
        "patterns": [re.compile(
            'dead[\\s_-]?cat[\\s_-]?bounce', re.IGNORECASE)],
        "phrase": 'dead cat bounce',
        "reason": "A financial term built on the image of a dead cat. 'Temporary rebound' or 'false recovery' is more professional and avoids the image.",
        "alternatives": ['temporary rebound', 'false recovery', 'brief uptick'],
    },
    # dog-eat-dog
    {
        "patterns": [re.compile(
            '\\bdog[\\s-]eat[\\s-]dog\\b', re.IGNORECASE)],
        "phrase": 'dog-eat-dog',
        "reason": "Frames dogs as inherently violent toward each other as a model for competition. 'Ruthlessly competitive' or 'cutthroat' conveys the meaning without the stereotype.",
        "alternatives": ['ruthlessly competitive', 'cutthroat', 'fiercely competitive'],
    },
    # whack-a-mole
    {
        "patterns": [re.compile(
            '\\bwhack[\\s-]a[\\s-]mole\\b', re.IGNORECASE)],
        "phrase": 'whack-a-mole',
        "reason": "References a game built around repeatedly striking animals as they pop up. 'Recurring problem' or 'endless loop' describes the pattern more precisely.",
        "alternatives": ['recurring problem', 'endless loop', 'unwinnable game'],
    },
    # cash-cow
    {
        "patterns": [re.compile(
            'cash\\s+cows?', re.IGNORECASE)],
        "phrase": 'cash cow',
        "reason": "Treats a cow as a thing to be extracted from for profit. 'Moneymaker' or 'profit center' carries the same meaning.",
        "alternatives": ['moneymaker', 'profit center', 'reliable revenue source'],
    },
    # sacrificial-lamb
    {
        "patterns": [re.compile(
            '\\bsacrificial\\s+lambs?\\b', re.IGNORECASE)],
        "phrase": 'sacrificial lamb',
        "reason": "References the ritual slaughter of lambs. 'Expendable person' or 'someone sacrificed for others' communicates the metaphor directly.",
        "alternatives": ['expendable person', 'person set up to fail', 'someone sacrificed for others'],
    },
    # sitting-duck
    {
        "patterns": [re.compile(
            '\\bsitting\\s+ducks?\\b', re.IGNORECASE)],
        "phrase": 'sitting duck',
        "reason": "Hunting imagery — a duck in the open, easy to shoot. 'Easy target' or 'vulnerable target' says the same thing.",
        "alternatives": ['easy target', 'vulnerable target', 'exposed'],
    },
    # open-season
    {
        "patterns": [re.compile(
            '\\bopen\\s+season\\b', re.IGNORECASE)],
        "phrase": 'open season',
        "reason": "Refers to the legal hunting period when killing animals is permitted. 'Free-for-all' or 'no holds barred' conveys the meaning without the hunting framing.",
        "alternatives": ['free-for-all', 'unrestricted criticism', 'no holds barred'],
    },
    # put-out-to-pasture
    {
        "patterns": [re.compile(
            'put(s|ting)?(\\s+(him|her|them))?\\s+out\\s+to\\s+pasture', re.IGNORECASE)],
        "phrase": 'put out to pasture',
        "reason": "Refers to the farm practice of disposing of animals once they're no longer productive. 'Retire,' 'phase out,' or 'sunset' is clearer and carries no harm.",
        "alternatives": ['retire', 'phase out', 'sunset'],
    },
    # dead-duck
    {
        "patterns": [re.compile(
            '\\bdead\\s+ducks?\\b', re.IGNORECASE)],
        "phrase": 'dead duck',
        "reason": "Hunting imagery — a duck that has been shot and killed. 'Lost cause' or 'doomed effort' is just as expressive.",
        "alternatives": ['lost cause', 'doomed effort', 'foregone conclusion'],
    },
    # cull
    {
        "patterns": [re.compile(
            '\\bcull(ed|ing|s)?\\b', re.IGNORECASE)],
        "phrase": 'cull',
        "reason": "Euphemism used in wildlife management and farming for mass killing. 'Remove', 'prune', 'trim', or 'filter out' is accurate in technical contexts.",
        "alternatives": ['remove', 'prune', 'trim', 'filter out'],
    },
    # veal
    {
        "patterns": [re.compile(
            '\\bveal(\\s+cal(f|ves))?\\b', re.IGNORECASE)],
        "phrase": 'veal',
        "reason": "'Veal' softens 'slaughtered-calf flesh' via a Norman-French borrowing. In advocacy or industry-critical writing, 'calf flesh' names what it is. (Suppressed in recipes and cooking contexts.)",
        "alternatives": ['calf flesh', 'calf meat'],
    },
    # lame-duck
    {
        "patterns": [re.compile(
            '\\blame[\\s-]duck\\b', re.IGNORECASE)],
        "phrase": 'lame duck',
        "reason": "Combines an ableist adjective with a reference to a bird unable to fly due to injury. 'Outgoing', 'transitional', or 'ineffective' is more precise.",
        "alternatives": ['outgoing', 'transitional', 'ineffective'],
    },
    # debeaking
    {
        "patterns": [re.compile(
            '\\bdebeak(ing|ed)\\b|\\bbeak\\s+(trimming|trim|conditioning)\\b', re.IGNORECASE)],
        "phrase": 'debeaking',
        "reason": "Industry euphemism for slicing or burning off hens' beaks, typically without anesthesia. 'Beak amputation' names what actually happens.",
        "alternatives": ['beak amputation', 'beak mutilation'],
    },
    # dehorning
    {
        "patterns": [re.compile(
            '\\bdehorn(ing|ed)\\b|\\bdisbud(ding|ded)\\b', re.IGNORECASE)],
        "phrase": 'dehorning',
        "reason": "Industry term for removing cattle horns, typically without anesthesia. 'Horn amputation' is accurate.",
        "alternatives": ['horn amputation', 'horn removal'],
    },
    # tail-docking
    {
        "patterns": [re.compile(
            'tail[\\s-]docking|tail\\s+docked|docked\\s+tail', re.IGNORECASE)],
        "phrase": 'tail docking',
        "reason": "Amputating pigs', sheep's, or dogs' tails. 'Tail amputation' is the accurate term.",
        "alternatives": ['tail amputation'],
    },
    # ear-notching
    {
        "patterns": [re.compile(
            'ear[\\s-]notch(ing|ed)', re.IGNORECASE)],
        "phrase": 'ear notching',
        "reason": "Industry identification practice of cutting notches in animals' ears. 'Ear mutilation' names what it is.",
        "alternatives": ['ear mutilation'],
    },
    # ventilation-shutdown
    {
        "patterns": [re.compile(
            'ventilation\\s+shutdown(\\s+plus)?|VSD\\+|VSD\\s+plus', re.IGNORECASE)],
        "phrase": 'ventilation shutdown',
        "reason": "Industry term for killing entire flocks by cutting off airflow — the animals die from suffocation and heat. 'Mass killing by suffocation' is the accurate term. (Suppressed in HVAC contexts.)",
        "alternatives": ['mass killing by suffocation', 'heat-and-suffocation killing'],
    },
    # maceration
    {
        "patterns": [re.compile(
            '(maceration\\s+of\\s+chicks|chick\\s+maceration|macerat(ed|ing)\\s+chicks)', re.IGNORECASE)],
        "phrase": 'maceration of chicks',
        "reason": "Industry euphemism for killing day-old male chicks by grinding them alive. Say what the process is. (Bare 'maceration' in culinary or chemistry contexts is not flagged.)",
        "alternatives": ['grinding newborn chicks alive', 'chick grinding'],
    },
    # abattoir
    {
        "patterns": [re.compile(
            '\\babattoirs?\\b', re.IGNORECASE)],
        "phrase": 'abattoir',
        "reason": "French-derived euphemism for slaughterhouse. 'Slaughterhouse' is the accurate English term.",
        "alternatives": ['slaughterhouse'],
    },
    # rendering-plant
    {
        "patterns": [re.compile(
            'rendering\\s+(plant|facility)s?', re.IGNORECASE)],
        "phrase": 'rendering plant',
        "reason": "Facility that processes animal bodies — roadkill, downed animals, slaughter byproducts — into meal, fat, and tallow. Naming it accurately makes the supply chain visible. (Only the full compound 'rendering plant' / 'rendering facility' is flagged; bare 'rendering' for graphics or UI is not.)",
        "alternatives": ['animal-body processing plant', 'carcass-processing facility'],
    },
    # stockyard
    {
        "patterns": [re.compile(
            '\\bstockyards?\\b', re.IGNORECASE)],
        "phrase": 'stockyard',
        "reason": "Euphemism for pre-slaughter holding pens. 'Slaughterhouse pens' describes what the facility actually is.",
        "alternatives": ['slaughterhouse pens', 'live-animal market'],
    },
    # laying-hen
    {
        "patterns": [re.compile(
            '(laying|layer)\\s+hens?', re.IGNORECASE)],
        "phrase": 'laying hen',
        "reason": "Defines a hen by her egg-laying function. When sex and species are relevant, 'hen' is sufficient.",
        "alternatives": ['hen'],
    },
    # use-category-naming
    {
        "patterns": [re.compile(
            '(dairy|beef)\\s+(cow|cows|cattle)|meat\\s+(birds?|rabbits?|goats?)', re.IGNORECASE)],
        "phrase": 'dairy cow',
        "reason": "Defines an animal by the product humans extract from them. The species name alone is sufficient unless the use is actively relevant.",
        "alternatives": ['cow', 'the species name alone'],
    },
    # brood-sow
    {
        "patterns": [re.compile(
            'brood\\s+sows?|breeding\\s+(stock|pair)', re.IGNORECASE)],
        "phrase": 'brood sow',
        "reason": "Defines a female animal by her reproductive function. Name the individual directly where possible.",
        "alternatives": ['pregnant pig', 'nursing mother pig'],
    },
    # cattle-call
    {
        "patterns": [re.compile(
            'cattle\\s+calls?', re.IGNORECASE)],
        "phrase": 'cattle call',
        "reason": "Likens human applicants to livestock being herded. 'Open call' or 'mass audition' carries the same meaning without the framing.",
        "alternatives": ['open call', 'mass audition'],
    },
    # pet-project
    {
        "patterns": [re.compile(
            'pet\\s+projects?', re.IGNORECASE)],
        "phrase": 'pet project',
        "reason": "Carries over the property framing of 'pet' (something owned) to the project. 'Side project' or 'passion project' captures the same idea without the ownership framing.",
        "alternatives": ['side project', 'passion project'],
    },
    # humanely-raised
    {
        "patterns": [re.compile(
            'humanely\\s+(raised|produced|farmed)', re.IGNORECASE)],
        "phrase": 'humanely raised',
        "reason": "USDA-unregulated marketing label — companies define their own standards, and the actual conditions often differ little from factory farming. Describe the actual conditions where possible.",
        "alternatives": ['factory-farmed', 'raised in [specific conditions]'],
    },
    # free-range
    {
        "patterns": [re.compile(
            'free[\\s-]rang(e|ing)|free[\\s-]roaming', re.IGNORECASE)],
        "phrase": 'free-range',
        "reason": "USDA requires only 'access to outdoors' — often a small door to a small porch that most birds never use. The label does not guarantee meaningful outdoor life.",
        "alternatives": ['minimally accessible outdoor pen', 'outdoor access (USDA minimum)'],
    },
    # pasture-raised
    {
        "patterns": [re.compile(
            'pasture[\\s-]raised|pastured', re.IGNORECASE)],
        "phrase": 'pasture-raised',
        "reason": "Not USDA-regulated; the meaning depends on whichever certifier the producer chooses. Name the certifier and the actual conditions where possible.",
        "alternatives": ['raised on pasture (certifier-dependent)'],
    },
    # grass-fed
    {
        "patterns": [re.compile(
            'grass[\\s-](fed|finished)', re.IGNORECASE)],
        "phrase": 'grass-fed',
        "reason": "Describes the cattle's feed, not their welfare. Slaughter, transport, and mother-calf separation happen the same way. The USDA dropped its 'grass-fed' definition in 2016; current usage is producer-defined.",
        "alternatives": ['grass-fed (USDA definition dropped 2016)', 'forage-finished'],
    },
    # cage-free-for-meat
    {
        "patterns": [re.compile(
            'cage[\\s-]free\\s+(chicken|turkey|meat|pork|beef)', re.IGNORECASE)],
        "phrase": 'cage-free chicken',
        "reason": "Meaningless for meat birds — broiler chickens and turkeys are almost never caged in industrial production. The label implies a welfare improvement that doesn't exist. (Cage-free for eggs IS a meaningful distinction; that usage is not flagged.)",
        "alternatives": ['crowded indoor housing', 'barn-raised'],
    },
    # humane-certifications
    {
        "patterns": [re.compile(
            'Certified\\s+Humane|Animal\\s+Welfare\\s+Approved|Global\\s+Animal\\s+Partnership|American\\s+Humane\\s+Certified|One\\s+Health\\s+Certified|GAP\\s+(certified|Step(\\s+\\d)?)', re.IGNORECASE)],
        "phrase": 'Certified Humane',
        "reason": "Third-party welfare certifications with widely varying standards — some are meaningful (Animal Welfare Approved), others are marketing (American Humane Certified). Name the specific standard if relevant.",
        "alternatives": ['name the certifier and standard'],
    },
    # ethically-sourced-animal
    {
        "patterns": [re.compile(
            '(ethically|responsibly)\\s+sourced\\s+(meat|dairy|eggs|beef|pork|chicken)|happy\\s+(meat|cows?)', re.IGNORECASE)],
        "phrase": 'ethically sourced meat',
        "reason": "Marketing language without a standard definition when applied to animal products. 'Ethically sourced' meat has no USDA definition. Describe the actual practices instead. (The phrase applied to coffee, chocolate, or textiles is not flagged.)",
        "alternatives": ['describe the actual farm practices'],
    },
    # dolphin-safe
    {
        "patterns": [re.compile(
            'dolphin[\\s-]safe|line[\\s-]caught|pole[\\s-](and[\\s-]line[\\s-])?caught|sustainab(ly\\s+caught|le\\s+seafood)', re.IGNORECASE)],
        "phrase": 'dolphin-safe',
        "reason": "Addresses specific bycatch concerns but not fish suffering. Fish feel pain, suffocate on deck, or are crushed in nets regardless of how the boat avoids catching dolphins or catches fish one at a time.",
        "alternatives": ['name the specific fishing method and bycatch statistics'],
    },
    # feed-to-predators
    {
        "patterns": [re.compile(
            '(feed|fed|feeding)\\s+to\\s+the\\s+(lions|sharks|dogs)', re.IGNORECASE)],
        "phrase": 'feed to the lions',
        "reason": "Human-as-prey imagery. 'Sacrifice' or 'leave exposed' captures the same meaning.",
        "alternatives": ['sacrifice', 'leave exposed', 'abandon to attack'],
    },
    # pig-to-slaughter
    {
        "patterns": [re.compile(
            '(like\\s+(a\\s+)?)?pigs?\\s+to\\s+slaughter', re.IGNORECASE)],
        "phrase": 'like a pig to slaughter',
        "reason": "Direct slaughter imagery. 'Defenseless' or 'walking into disaster' captures the same meaning.",
        "alternatives": ['defenseless', 'walking into disaster'],
    },
    # turkey-shoot
    {
        "patterns": [re.compile(
            'turkey[\\s-]shoot', re.IGNORECASE)],
        "phrase": 'turkey shoot',
        "reason": "One-sided-slaughter imagery for an easy win. 'Walkover' or 'trivially easy win' carries the same meaning.",
        "alternatives": ['trivially easy win', 'no-contest situation', 'walkover'],
    },
    # fox-guarding-henhouse
    {
        "patterns": [re.compile(
            'fox(es)?\\s+(guarding\\s+the|in\\s+the)\\s+hen[\\s-]?house', re.IGNORECASE)],
        "phrase": 'fox guarding the henhouse',
        "reason": "Frames predation as an inevitable natural order. 'Conflict of interest' or 'wrong person in charge' is the actual point being made.",
        "alternatives": ['conflict of interest', 'the wrong person in charge'],
    },
    # bull-in-china-shop
    {
        "patterns": [re.compile(
            '(like\\s+a\\s+)?bull\\s+in\\s+a\\s+china\\s+shop', re.IGNORECASE)],
        "phrase": 'bull in a china shop',
        "reason": "Bull-as-clumsy-brute stereotype — actually originates from a cartoon, not reality. 'Clumsy disruption' or 'careless and destructive' is more accurate.",
        "alternatives": ['tornado in a glass factory', 'clumsy disruption', 'careless and destructive'],
    },
    # build-a-better-mousetrap
    {
        "patterns": [re.compile(
            'build(s|ing)?\\s+a\\s+better\\s+mousetrap|better\\s+mousetrap', re.IGNORECASE)],
        "phrase": 'build a better mousetrap',
        "reason": "Mouse-killing device as innovation metaphor. 'Invent something better' or 'build a better mouse pad' captures the idea.",
        "alternatives": ['build a better mouse pad', 'invent something better'],
    },
    # packed-like-sardines
    {
        "patterns": [re.compile(
            '(packed|squeezed)\\s+(in\\s+)?like\\s+sardines', re.IGNORECASE)],
        "phrase": 'packed in like sardines',
        "reason": "Accurately describes industrial fishing and canning — the 'imagery' is the reality. 'Tightly crowded' or 'packed in like pickles' works without invoking it.",
        "alternatives": ['packed in like pickles', 'tightly crowded', 'crammed together'],
    },
    # pull-the-wool
    {
        "patterns": [re.compile(
            'pull(s|ing|ed)?\\s+the\\s+wool\\s+over', re.IGNORECASE)],
        "phrase": 'pull the wool over',
        "reason": "Wool (sheep exploitation) as a deception metaphor. 'Deceive' or 'mislead' is direct and clearer.",
        "alternatives": ['deceive', 'mislead', 'pull the polyester over your eyes'],
    },
    # lipstick-on-a-pig
    {
        "patterns": [re.compile(
            '(put(s|ting)?\\s+)?lipstick\\s+on\\s+a\\s+pig', re.IGNORECASE)],
        "phrase": 'lipstick on a pig',
        "reason": "Frames pigs as ugly objects. 'Superficially improve' or 'disguise the flaw' is the actual meaning.",
        "alternatives": ['superficially improve', 'disguise the flaw', 'dress up a bad product'],
    },
    # silk-purse-sows-ear
    {
        "patterns": [re.compile(
            "silk\\s+purse\\s+(out\\s+of|from)\\s+a\\s+sow's\\s+ear", re.IGNORECASE)],
        "phrase": "silk purse out of a sow's ear",
        "reason": "Pig body parts framed as worthless. 'Transform something unpromising' carries the same meaning.",
        "alternatives": ['diamond bracelet out of a lump of coal', 'transform something unpromising'],
    },
    # black-sheep
    {
        "patterns": [re.compile(
            'black\\s+sheep', re.IGNORECASE)],
        "phrase": 'black sheep',
        "reason": "Commodifies sheep coat color as a family-shame metaphor, with racial baggage. 'Outlier' or 'odd one out' works.",
        "alternatives": ['outlier', 'misfit', 'odd one out'],
    },
    # wolf-in-sheeps-clothing
    {
        "patterns": [re.compile(
            "wol(f|ves)\\s+in\\s+sheep'?s\\s+clothing", re.IGNORECASE)],
        "phrase": "wolf in sheep's clothing",
        "reason": "Wolves-as-deceivers trope. 'Hidden threat' or 'deceiver in disguise' carries the same meaning.",
        "alternatives": ['deceiver in disguise', 'hidden threat', 'threat wearing a friendly face'],
    },
    # chicken-out
    {
        "patterns": [re.compile(
            'chicken(s|ed|ing)\\s+out|chicken\\s+out', re.IGNORECASE)],
        "phrase": 'chicken out',
        "reason": "Chicken-as-coward framing. 'Back out' or 'lose nerve' carries the same meaning.",
        "alternatives": ['back out', 'lose nerve', 'get cold feet'],
    },
    # feeding-frenzy
    {
        "patterns": [re.compile(
            'feeding\\s+frenz(y|ies)', re.IGNORECASE)],
        "phrase": 'feeding frenzy',
        "reason": "Shark-predation imagery used for human behavior. 'Chaotic rush' or 'scramble to exploit' carries the same meaning.",
        "alternatives": ['chaotic rush', 'scramble to exploit', 'uncontrolled grab'],
    },
    # blood-in-the-water
    {
        "patterns": [re.compile(
            '(smell[s]?\\s+)?blood\\s+in\\s+the\\s+water', re.IGNORECASE)],
        "phrase": 'blood in the water',
        "reason": "Shark-predation imagery. 'Signs of weakness' or 'vulnerability visible' carries the same meaning.",
        "alternatives": ['signs of weakness', 'vulnerability visible', 'sensing a kill'],
    },
    # circling-vultures
    {
        "patterns": [re.compile(
            '(circl(e|ing)\\s+(like\\s+)?vultures|vultures\\s+circling)', re.IGNORECASE)],
        "phrase": 'circling like vultures',
        "reason": "Species defamation — the 'circling vulture' framing is factually wrong (vultures are ecological cleaners, not predators) and has driven real persecution; vulture populations are crashing globally. 'Waiting to exploit' carries the same meaning.",
        "alternatives": ['waiting to exploit', 'hovering opportunistically', 'waiting for weakness'],
    },
    # madder-than-wet-hen
    {
        "patterns": [re.compile(
            'mad(der)?\\s+(than|as)\\s+a\\s+wet\\s+hen', re.IGNORECASE)],
        "phrase": 'madder than a wet hen',
        "reason": "References the farm practice of dunking broody hens in water to break their nesting instinct. 'Furious' or 'livid' says it directly.",
        "alternatives": ['furious', 'livid', 'seething'],
    },
    # code-monkey
    {
        "patterns": [re.compile(
            'code\\s+monkeys?', re.IGNORECASE)],
        "phrase": 'code monkey',
        "reason": "Frames programmers as trained animals, and compounds with the long history of 'monkey' used as a racial slur. 'Developer' or 'engineer' is the accurate term.",
        "alternatives": ['developer', 'programmer', 'engineer'],
    },
    # hog-resource
    {
        "patterns": [re.compile(
            '(memory|CPU|bandwidth|resource|disk|space)\\s+hog|hogging\\s+(memory|CPU|bandwidth|resources|the)|hogs\\s+the|hog\\s+the\\s+spotlight', re.IGNORECASE)],
        "phrase": 'memory hog',
        "reason": "Builds on the pig-as-greedy stereotype (pigs are actually selective eaters). 'Resource-intensive' or 'monopolizes' is more accurate and avoids the framing.",
        "alternatives": ['resource-intensive', 'heavy consumer', 'monopolizes', 'dominates'],
    },
    # pigheaded
    {
        "patterns": [re.compile(
            '\\bpig[\\s-]?headed(ness)?\\b', re.IGNORECASE)],
        "phrase": 'pigheaded',
        "reason": "Pig-as-stubborn stereotype (pigs are intelligent, not stubborn). 'Obstinate' or 'unreasonable' says it directly.",
        "alternatives": ['obstinate', 'inflexible', 'unreasonable'],
    },
    # eat-like-a-pig
    {
        "patterns": [re.compile(
            'eat(s|ing|e)?\\s+like\\s+a\\s+pig|ate\\s+like\\s+a\\s+pig|pig(s|ged|ging)?\\s+out', re.IGNORECASE)],
        "phrase": 'eat like a pig',
        "reason": "Pig-as-glutton stereotype (actually wrong — pigs are selective eaters in natural conditions). 'Overeat' or 'gorge' says the same thing.",
        "alternatives": ['overeat', 'gorge', 'eat voraciously'],
    },
    # son-of-a-bitch
    {
        "patterns": [re.compile(
            'sons?[\\s-]of[\\s-]a[\\s-]bitch|sons\\s+of\\s+bitches', re.IGNORECASE)],
        "phrase": 'son of a bitch',
        "reason": "Female-dog insult that compounds misogyny with species defamation. A specific descriptor is clearer and doesn't land on anyone's mother or on dogs.",
        "alternatives": ['specific descriptor'],
    },
    # sheeple
    {
        "patterns": [re.compile(
            '\\bsheeple\\b', re.IGNORECASE)],
        "phrase": 'sheeple',
        "reason": "Coined term meaning 'sheep-people' — dehumanizes the target while defaming sheep (who are actually complex social animals). 'Conformists' or 'uncritical crowd' carries the same meaning.",
        "alternatives": ['conformists', 'unquestioning followers', 'uncritical crowd'],
    },
    # loan-shark
    {
        "patterns": [re.compile(
            '(loan|card)[\\s-]sharks?', re.IGNORECASE)],
        "phrase": 'loan shark',
        "reason": "Species-as-predator trope applied to exploitative humans, which misrepresents sharks and provides a convenient framing for financial harm. 'Predatory lender' or 'hustler' is direct and more accurate.",
        "alternatives": ['predatory lender', 'hustler', 'card hustler'],
    },
    # vulture-capitalist
    {
        "patterns": [re.compile(
            'vulture\\s+(capitalist|capitalism|fund)s?', re.IGNORECASE)],
        "phrase": 'vulture capitalist',
        "reason": "Species defamation that drives real-world vulture persecution — global vulture populations are crashing largely from this kind of cultural framing. 'Predatory investor' names the behavior without defaming an ecologically critical species.",
        "alternatives": ['predatory investor', 'scavenger capitalist', 'distressed-debt investor'],
    },
    # weasel-words
    {
        "patterns": [re.compile(
            'weasel\\s+words?|weasel(s|ed|ing)?\\s+out', re.IGNORECASE)],
        "phrase": 'weasel words',
        "reason": "Species-as-deceitful trope. 'Evasive language' or 'slippery phrasing' is more direct. (Wikipedia's Manual of Style uses 'weasel words' as an internal term of art; that context is suppressed.)",
        "alternatives": ['evasive language', 'evade', 'slippery phrasing'],
    },
    # leech-off
    {
        "patterns": [re.compile(
            'leech(es|ed|ing)?\\s+off|bloodsuckers?', re.IGNORECASE)],
        "phrase": 'leech off',
        "reason": "Species-as-parasite trope. 'Freeload' or 'mooch' is direct. (Bare 'leech' in medical contexts — leeches are still used in some surgeries — is not flagged.)",
        "alternatives": ['freeload', 'mooch', 'exploit', 'parasitic'],
    },
    # monkey-business
    {
        "patterns": [re.compile(
            'monkey\\s+business|monkey(s|ing|ed)?\\s+around|(make|makes|making|made)\\s+a\\s+monkey\\s+of', re.IGNORECASE)],
        "phrase": 'monkey business',
        "reason": "Primate-as-foolish stereotype with a long racial history. 'Mischief' or 'fool around' is direct and doesn't carry the baggage.",
        "alternatives": ['mischief', 'fool around', 'tamper with', 'make a fool of'],
    },
    # not-my-monkeys
    {
        "patterns": [re.compile(
            'not\\s+my\\s+(circus[,]?\\s+not\\s+my\\s+monkeys?|monkeys?|circus)', re.IGNORECASE)],
        "phrase": 'not my circus, not my monkeys',
        "reason": "Direct reference to circus-animal exploitation. 'Not my problem' carries the same meaning.",
        "alternatives": ['not my problem', 'not my concern', 'not my mess to clean up'],
    },
    # bird-brain
    {
        "patterns": [re.compile(
            '\\bbird[\\s-]?brain(ed)?\\b', re.IGNORECASE)],
        "phrase": 'bird brain',
        "reason": "Bird-as-stupid stereotype (corvids and parrots rank among the most cognitively sophisticated non-human animals). 'Forgetful' or 'absent-minded' is more accurate.",
        "alternatives": ['forgetful', 'absent-minded', 'scatter-brained'],
    },
    # foie-gras
    {
        "patterns": [re.compile(
            'foie[\\s-]gras', re.IGNORECASE)],
        "phrase": 'foie gras',
        "reason": "French for 'fat liver'; obscures that the product comes from force-feeding ducks or geese until their livers enlarge to ten times normal size. Name the process.",
        "alternatives": ['force-fed duck liver', 'force-fed goose liver'],
    },
    # chevon
    {
        "patterns": [re.compile(
            '\\bchevon\\b', re.IGNORECASE)],
        "phrase": 'chevon',
        "reason": "Marketing-constructed word (coined in the 1920s) to make goat meat palatable to Anglophone consumers. 'Goat flesh' or 'goat meat' is accurate.",
        "alternatives": ['goat flesh', 'goat meat'],
    },
    # sweetbread
    {
        "patterns": [re.compile(
            '\\bsweetbreads?\\b', re.IGNORECASE)],
        "phrase": 'sweetbread',
        "reason": "Opaque culinary term for calf or lamb thymus or pancreas. Naming the organ is clearer. (Suppressed in recipe/cooking contexts.)",
        "alternatives": ['calf thymus', 'calf pancreas', 'lamb thymus'],
    },
    # mutton
    {
        "patterns": [re.compile(
            '\\bmutton\\b', re.IGNORECASE)],
        "phrase": 'mutton',
        "reason": "'Mutton' obscures the species. 'Sheep flesh' names it. (Suppressed in recipe contexts.)",
        "alternatives": ['sheep flesh', 'sheep meat'],
    },
    # venison
    {
        "patterns": [re.compile(
            '\\bvenison\\b', re.IGNORECASE)],
        "phrase": 'venison',
        "reason": "'Venison' obscures the species. 'Deer flesh' names it. (Suppressed in recipe or hunting-regulation contexts.)",
        "alternatives": ['deer flesh', 'deer meat'],
    },
    # squab
    {
        "patterns": [re.compile(
            '\\bsquabs?\\b', re.IGNORECASE)],
        "phrase": 'squab',
        "reason": "Marketing term for young pigeon raised for slaughter. 'Pigeon flesh' names what it is. (Suppressed in recipe contexts.)",
        "alternatives": ['pigeon flesh', 'young pigeon meat'],
    },
    # spare-ribs
    {
        "patterns": [re.compile(
            '\\bspare[\\s-]?ribs\\b', re.IGNORECASE)],
        "phrase": 'spare ribs',
        "reason": "'Spare' frames body parts as disposable/extra. 'Pig ribs' is accurate. (Suppressed in recipe/BBQ contexts.)",
        "alternatives": ['pig ribs'],
    },
    # leather-product
    {
        "patterns": [re.compile(
            '\\b(genuine|real|top[\\s-]grain|full[\\s-]grain)?\\s*leather\\b', re.IGNORECASE)],
        "phrase": 'leather',
        "reason": "'Leather' obscures that the material is the skin of a killed cow (or pig, sheep, etc.). In advocacy or supply-chain writing, naming it is clearer. Suppressed in fashion/product contexts where the industry term is expected.",
        "alternatives": ['cow skin', 'animal skin', 'vegan leather', 'synthetic leather', 'plant leather'],
    },
    # wool-product
    {
        "patterns": [re.compile(
            '\\b(merino\\s+|lambs)?wool\\b', re.IGNORECASE)],
        "phrase": 'wool',
        "reason": "'Wool' obscures that the fiber is sheep hair, usually from sheep bred for extreme coat yields (mulesing, shearing injury, eventual slaughter). Advocacy writing names it directly. Suppressed in textile/fashion contexts.",
        "alternatives": ['sheep hair', 'synthetic fiber', 'plant fiber'],
    },
    # down-feathers
    {
        "patterns": [re.compile(
            'down\\s+(feathers|jacket|comforter|pillow|filling)|(goose|duck)\\s+down', re.IGNORECASE)],
        "phrase": 'down feathers',
        "reason": "Down is plucked from ducks and geese, often while alive and distressed. 'Plant-based insulation' or 'synthetic fill' describes the alternative. Bare 'down' (direction) is NOT flagged — only product compounds.",
        "alternatives": ['plant-based insulation', 'synthetic fill', 'recycled fill'],
    },
    # cashmere-mohair-angora
    {
        "patterns": [re.compile(
            '\\b(cashmere|mohair|angora)\\b', re.IGNORECASE)],
        "phrase": 'cashmere',
        "reason": "Luxury-marketing names that obscure the animal source. Cashmere and mohair come from goats; angora comes from rabbits (who are often plucked live and injured). Naming the species is clearer in advocacy writing.",
        "alternatives": ['goat hair', 'rabbit hair', 'recycled fiber', 'synthetic alternative'],
    },
    # silk-product
    {
        "patterns": [re.compile(
            '\\b(pure\\s+|mulberry\\s+|raw\\s+)?silk\\b', re.IGNORECASE)],
        "phrase": 'silk',
        "reason": "Silk production typically requires boiling silkworms alive inside their cocoons to prevent the thread from breaking. Peace silk, plant silk, and synthetics avoid this. Suppressed in textile/fashion contexts.",
        "alternatives": ['plant silk', 'peace silk', 'synthetic silk', 'recycled fiber'],
    },
    # royal-jelly-beeswax
    {
        "patterns": [re.compile(
            'royal\\s+jelly|beeswax|propolis', re.IGNORECASE)],
        "phrase": 'royal jelly',
        "reason": "Bee products are extracted through industrial beekeeping, which involves queen-clipping, smoke stressing, and often the destruction of hives. Plant-based waxes (candelilla, carnauba, soy) serve most of the same purposes.",
        "alternatives": ['plant alternative', 'candelilla wax', 'carnauba wax', 'soy wax'],
    },
    # downed-animal
    {
        "patterns": [re.compile(
            'down(ed|er)\\s+(animal|cow|cattle|pig)s?', re.IGNORECASE)],
        "phrase": 'downed animal',
        "reason": "'Downed' uses passive voice to elide why the animal is on the ground — untreated injury or illness in transport or on the farm. 'Too sick to walk' names the condition.",
        "alternatives": ['animal too sick or injured to walk', 'collapsed animal'],
    },
    # forced-insemination
    {
        "patterns": [re.compile(
            '(artificial|forced)\\s+insemination|AI\\s+in\\s+(cattle|cows|dairy|pigs|sheep|swine)', re.IGNORECASE)],
        "phrase": 'artificial insemination',
        "reason": "Industry-standard procedure involving restraint and reproductive invasion. 'Forced impregnation' is the accurate term when the animal cannot consent. (The bare abbreviation 'AI' is not flagged — too much overlap with artificial intelligence. The rule fires only on the specific animal-ag compounds.)",
        "alternatives": ['forced impregnation'],
    },
    # farrowing-as-process
    {
        "patterns": [re.compile(
            '\\bfarrow(ing|ed)\\b', re.IGNORECASE)],
        "phrase": 'farrowing',
        "reason": "Industry verb that erases the individual animal giving birth. 'Giving birth' is the plain-language version. (The compound 'farrowing crate' is flagged by its own rule.)",
        "alternatives": ['giving birth (for pigs)', 'piglet-birthing'],
    },
    # live-export
    {
        "patterns": [re.compile(
            'live\\s+(export(s|ing)?|transport|shipment)', re.IGNORECASE)],
        "phrase": 'live export',
        "reason": "Industry term for loading animals onto ships or trucks for days-to-weeks journeys to overseas slaughter. 'Transport to slaughter' names the destination.",
        "alternatives": ['transport to slaughter', 'export for slaughter'],
    },
    # meat-industry-self-naming
    {
        "patterns": [re.compile(
            '(pork|beef|dairy|poultry|veal|egg)\\s+industry', re.IGNORECASE)],
        "phrase": 'pork industry',
        "reason": "Each term names the product rather than the species it comes from. Naming the species (e.g. 'pig-flesh industry') makes the supply chain visible. Low priority — use in advocacy writing, not general documentation.",
        "alternatives": ['pig-flesh industry', 'cow-flesh industry', 'cow-milk industry', 'chicken-flesh industry'],
    },
    # trophy-hunting
    {
        "patterns": [re.compile(
            'trophy\\s+(hunt(ing|er|ers)?|kill(s)?)', re.IGNORECASE)],
        "phrase": 'trophy hunting',
        "reason": "Frames a killed animal as an achievement to be displayed. 'Killing for display' or 'recreational killing' names the activity.",
        "alternatives": ['killing for display', 'recreational killing'],
    },
    # big-game-hunter
    {
        "patterns": [re.compile(
            'big[\\s-]game\\s+hunt(ing|er|ers)?', re.IGNORECASE)],
        "phrase": 'big-game hunter',
        "reason": "'Big game' frames large wild animals as sport objects existing for human recreation. 'Large-animal hunter' names it; better still, name the species (elephant, lion, rhino).",
        "alternatives": ['large-animal hunter', 'elephant/lion/rhino hunter'],
    },
    # sport-fishing
    {
        "patterns": [re.compile(
            'sport[\\s]?fishing|recreational\\s+fishing|game\\s+fishing', re.IGNORECASE)],
        "phrase": 'sport fishing',
        "reason": "'Sport' frames killing fish as leisure. In contexts critical of the activity, 'recreational killing of fish' is accurate. (In neutral angling-industry writing, the scanner adds noise; tune the context or disable in those files.)",
        "alternatives": ['recreational fishing (if literal)', 'recreational killing of fish'],
    },
    # catch-and-release
    {
        "patterns": [re.compile(
            'catch[\\s-]and[\\s-]release', re.IGNORECASE)],
        "phrase": 'catch and release',
        "reason": "Frames hook injury, exhaustion, and stress as harmless. Studies show significant post-release mortality, especially for species caught from deep water. 'Capture and release' is more neutral.",
        "alternatives": ['capture and release', 'captured and released (with injury)'],
    },
    # thin-the-herd
    {
        "patterns": [re.compile(
            'thin(s|ning|ned)?\\s+(out\\s+)?the\\s+herd', re.IGNORECASE)],
        "phrase": 'thin the herd',
        "reason": "Culling euphemism that softens 'kill off selected animals.' 'Kill off' says it directly.",
        "alternatives": ['reduce numbers by killing', 'kill off'],
    },
    # humane-trap-removal
    {
        "patterns": [re.compile(
            'humane\\s+(traps?|removal|control)', re.IGNORECASE)],
        "phrase": 'humane trap',
        "reason": "'Humane' sanitizes the practice. Say whether it's lethal or non-lethal directly — 'non-lethal trap' is clearer and testable.",
        "alternatives": ['non-lethal trap', 'non-lethal removal', 'live-catch trap'],
    },
    # lethal-control
    {
        "patterns": [re.compile(
            'lethal\\s+(removal|control|management)', re.IGNORECASE)],
        "phrase": 'lethal removal',
        "reason": "Bureaucratic language for killing programs. 'Killing program' says it plainly.",
        "alternatives": ['killing program', 'culling program'],
    },
    # fur-facility
    {
        "patterns": [re.compile(
            '(fur|mink|fox)\\s+(farms?|ranch(es)?)', re.IGNORECASE)],
        "phrase": 'fur farm',
        "reason": "'Farm' or 'ranch' evokes pastoral imagery; these are intensive confinement facilities where animals live in wire cages before being gassed or electrocuted. Name them directly.",
        "alternatives": ['mink confinement facility', 'fox confinement facility', 'fur-industry facility'],
    },
    # fur-bearing-animal
    {
        "patterns": [re.compile(
            'fur[\\s-]bearing\\s+animals?', re.IGNORECASE)],
        "phrase": 'fur-bearing animal',
        "reason": "Defines wild animals by a human use. Naming the species (foxes, minks, coyotes, bobcats, chinchillas) is clearer.",
        "alternatives": ['named species', 'fur-industry species'],
    },
    # bycatch
    {
        "patterns": [re.compile(
            '\\bby[\\s-]?catch\\b', re.IGNORECASE)],
        "phrase": 'bycatch',
        "reason": "Neutralizes the massive incidental killing of non-target marine species — hundreds of thousands of dolphins, sea turtles, seabirds, and sharks each year. 'Incidental killing' names it.",
        "alternatives": ['incidental killing', 'non-target marine deaths'],
    },
    # fish-stocks
    {
        "patterns": [re.compile(
            'fish(ery)?\\s+stocks?', re.IGNORECASE)],
        "phrase": 'fish stocks',
        "reason": "Commodity framing of marine life as a renewable resource. 'Fish populations' is neutral and accurate.",
        "alternatives": ['fish populations', 'wild fish numbers'],
    },
    # aquaculture
    {
        "patterns": [re.compile(
            '\\baquaculture\\b|fish\\s+farming', re.IGNORECASE)],
        "phrase": 'aquaculture',
        "reason": "Neutral-sounding framing for intensive fish confinement and slaughter. In advocacy writing, 'industrial fish farming' is more accurate.",
        "alternatives": ['industrial fish farming', 'intensive fish confinement'],
    },
    # cry-wolf
    {
        "patterns": [re.compile(
            'cr(y|ied|ying|ies)\\s+wolf', re.IGNORECASE)],
        "phrase": 'cry wolf',
        "reason": "Rooted in Aesop's fable, the phrase reinforces the wolf-as-menace framing that has driven centuries of wolf persecution. 'Raise false alarms' captures the meaning.",
        "alternatives": ['raise false alarms', 'create alert fatigue', 'sound unjustified alerts'],
    },
    # pecking-order
    {
        "patterns": [re.compile(
            'pecking\\s+orders?', re.IGNORECASE)],
        "phrase": 'pecking order',
        "reason": "Derived from the actual behavior of hens in confinement, where crowding causes injurious pecking. 'Hierarchy' or 'chain of command' captures the same idea.",
        "alternatives": ['hierarchy', 'chain of command', 'ranking'],
    },
    # play-cat-and-mouse
    {
        "patterns": [re.compile(
            'play(s|ing|ed)?\\s+cat\\s+and\\s+mouse|(cat\\s+and\\s+mouse\\s+game|game\\s+of\\s+cat\\s+and\\s+mouse)', re.IGNORECASE)],
        "phrase": 'play cat and mouse',
        "reason": "Predator-prey torture metaphor — the game is about prolonging the suffering. 'Drawn-out pursuit' captures the meaning.",
        "alternatives": ['drawn-out pursuit', 'back-and-forth chase', 'evasive pursuit'],
    },
    # cat-who-swallowed-canary
    {
        "patterns": [re.compile(
            'cat\\s+(that|who)\\s+(swallowed|ate)\\s+the\\s+canary|canary[\\s-]eating\\s+grin', re.IGNORECASE)],
        "phrase": 'cat that swallowed the canary',
        "reason": "Predation imagery — a dead canary is the joke's punchline. 'Smug with secret knowledge' captures it.",
        "alternatives": ['smug with secret knowledge', 'self-satisfied grin'],
    },
    # chomping-at-the-bit
    {
        "patterns": [re.compile(
            '(chomping|champing|chomps|champs)\\s+at\\s+the\\s+bit', re.IGNORECASE)],
        "phrase": 'chomping at the bit',
        "reason": "References the metal 'bit' forced into a horse's mouth; the phrase describes the horse's attempt to relieve it. 'Eager to start' says the same thing.",
        "alternatives": ['eager to start', 'impatient to begin', 'raring to go'],
    },
    # whip-into-shape
    {
        "patterns": [re.compile(
            'whip(s|ped|ping)?\\s+into\\s+shape', re.IGNORECASE)],
        "phrase": 'whip into shape',
        "reason": "Whip-violence imagery from animal training. 'Get organized' or 'restore order' is direct. (Political 'whip' and culinary 'whip' — different usage — are suppressed.)",
        "alternatives": ['get organized', 'demand discipline', 'restore order'],
    },
    # whale-on
    {
        "patterns": [re.compile(
            'whal(e|es|ing|ed)\\s+on', re.IGNORECASE)],
        "phrase": 'whale on',
        "reason": "Whaling (whale slaughter) as metaphor for repeated hitting. 'Pummel' or 'hammer' is direct.",
        "alternatives": ['pummel', 'beat up', 'hammer'],
    },
    # fish-or-cut-bait
    {
        "patterns": [re.compile(
            'fish\\s+or\\s+cut\\s+bait', re.IGNORECASE)],
        "phrase": 'fish or cut bait',
        "reason": "Fishing imagery. 'Decide' or 'commit or move on' is direct.",
        "alternatives": ['decide', 'commit or move on'],
    },
    # pull-rabbit-out-of-hat
    {
        "patterns": [re.compile(
            'pull(s|ing|ed)?\\s+a\\s+rabbit\\s+out\\s+of\\s+a\\s+hat', re.IGNORECASE)],
        "phrase": 'pull a rabbit out of a hat',
        "reason": "Stage magic often uses live rabbits kept in distressing conditions. 'Magically solve' or 'produce unexpectedly' carries the meaning without referencing the practice.",
        "alternatives": ['pull a coin out of an ear', 'magically solve', 'produce unexpectedly'],
    },
    # walking-on-eggshells
    {
        "patterns": [re.compile(
            'walk(s|ing|ed)?\\s+on\\s+eggshells', re.IGNORECASE)],
        "phrase": 'walking on eggshells',
        "reason": "Commodifies eggs as fragile objects; erases the laying-hen origin. 'Walking on thin ice' carries the same meaning.",
        "alternatives": ['walking on thin ice', 'treading carefully', 'being extra cautious'],
    },
    # put-a-horse-out-of-misery
    {
        "patterns": [re.compile(
            'put\\s+(a|the)\\s+\\S+\\s+out\\s+of\\s+(its|their|the)\\s+misery|put\\s+(it|them)\\s+out\\s+of\\s+(its|their)\\s+misery|put\\s+out\\s+of\\s+(its|their|the)\\s+misery', re.IGNORECASE)],
        "phrase": 'put a horse out of its misery',
        "reason": "Horse-killing idiom. 'End the suffering' carries the same meaning without the imagery.",
        "alternatives": ['end the suffering', 'end it mercifully', 'conclude a painful situation'],
    },
    # kill-the-fatted-calf
    {
        "patterns": [re.compile(
            'kill(ing)?\\s+the\\s+fatted\\s+calf', re.IGNORECASE)],
        "phrase": 'kill the fatted calf',
        "reason": "Biblical animal-sacrifice imagery (Luke 15 — the Prodigal Son). 'Celebrate grandly' or 'roll out the red carpet' carries the same meaning.",
        "alternatives": ['celebrate grandly', 'roll out the red carpet', 'prepare a feast'],
    },
    # lemming-investor
    {
        "patterns": [re.compile(
            '(acting\\s+like\\s+lemmings|lemming\\s+(investor|investors|behavior)|like\\s+lemmings)', re.IGNORECASE)],
        "phrase": 'acting like lemmings',
        "reason": "Based on a Disney hoax — the 1958 'White Wilderness' staged lemmings being driven off a cliff. Lemmings don't mass-suicide. The metaphor defames the species and misleads the reader.",
        "alternatives": ['herd-following investor', 'unquestioning crowd', 'uncritical followers'],
    },
    # maggot-insult
    {
        "patterns": [re.compile(
            '(you|little|filthy|dirty)\\s+maggots?', re.IGNORECASE)],
        "phrase": 'you maggot',
        "reason": "Degrading insect insult. Most uses in documentation are quoting dialogue or user-generated content; otherwise, use a specific descriptor.",
        "alternatives": ['specific descriptor'],
    },
    # swine-pejorative
    {
        "patterns": [re.compile(
            '(filthy|dirty|you|capitalist|fascist|bourgeois)\\s+swine', re.IGNORECASE)],
        "phrase": 'filthy swine',
        "reason": "Pig-as-degraded pejorative. Naming the actual trait (greedy, exploitative, corrupt) is clearer. (Bare 'swine' in medical contexts like 'swine flu' is not flagged.)",
        "alternatives": ['specific descriptor'],
    },
    # cat-fight
    {
        "patterns": [re.compile(
            '\\bcat[\\s-]?fights?\\b', re.IGNORECASE)],
        "phrase": 'cat fight',
        "reason": "Gendered insult — almost exclusively applied to women arguing, framing them as cats fighting. 'Heated argument' or 'altercation' is neutral.",
        "alternatives": ['heated argument', 'altercation', 'confrontation'],
    },
    # humans-and-animals
    {
        "patterns": [re.compile(
            '(humans?\\s+and\\s+animals|animals\\s+and\\s+(humans?|people)|people\\s+and\\s+animals|man\\s+and\\s+beast)', re.IGNORECASE)],
        "phrase": 'humans and animals',
        "reason": "False dichotomy — humans ARE animals. The phrasing reproduces the speciesist framing animal-liberation writing opposes. 'Humans and other animals' preserves the meaning accurately.",
        "alternatives": ['humans and non-human animals', 'humans and other animals', 'people and other animals'],
    },
    # pet-owner
    {
        "patterns": [re.compile(
            '(pet|dog|cat|rabbit|bird)\\s+owners?', re.IGNORECASE)],
        "phrase": 'pet owner',
        "reason": "Property framing — 'owner' treats sentient beings as possessions. 'Guardian' preserves the legal and caregiving relationship without the property connotation. Used in legal reform jurisdictions (e.g. Boulder CO, West Hollywood) since the early 2000s.",
        "alternatives": ['pet guardian', 'dog guardian', 'cat guardian', 'human companion'],
    },
    # own-a-pet
    {
        "patterns": [re.compile(
            'own(s|ing|ed)?\\s+a\\s+(pet|dog|cat|rabbit|bird)', re.IGNORECASE)],
        "phrase": 'own a pet',
        "reason": "Property framing applied to companion animals. 'Live with a dog' or 'share a home with a cat' captures the relationship without the ownership frame.",
        "alternatives": ['live with a companion animal', 'share a home with', 'care for a'],
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
