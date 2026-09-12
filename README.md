# Within

**Your personal search engine. Not for the world — for your own life.**

Google helps you search the world. Within helps you search your own important experiences.

---

## The Problem

We are not trying to solve *"humans don't have enough memory."*

We are trying to solve something different:

> **"I knew this before, but I can't find it when I need it."**

Where was that great restaurant I visited before?
Where did I buy that refrigerator?
How did I get to that place last time?

We once knew these things, but often cannot remember them when we actually need them.

---

## What It Does

Within is an AI agent-powered personal search engine. Users describe something naturally:

> "I bought a Philips refrigerator from PChome."

Within understands the statement, extracts searchable information, adds a timestamp, and preserves the original wording.

Months later, the user simply searches:

> "Where did I buy that Philips refrigerator?"

And Within retrieves:
2026/09/08
PChome · Refrigerator · Philips


**Be vague when recording. Be precise when searching.**

---

## Core Principles

**1. Remember only what matters**
We don't want you to remember more. We want you to keep only what is worth finding again.

**2. No forms, no categories**
Users never decide whether something belongs under "Food" or "Shopping." They just speak.

**3. Capture what was actually said**
If the user says "I think it was on Yangming Road," Within preserves that uncertainty. It never turns a guess into a fact.

**4. History is never overwritten**
A restaurant visited three times accumulates three records, each with its own date. Experiences change; the history stays.

**5. Dates are part of memory**
Within does not guarantee the information is still correct today. It guarantees this is what you recorded then.

**6. AI understands you, but doesn't chat with you**
This is a search tool, not a companion.

---

## Why No Photos or Screenshots

Not because we can't — but because we believe:

> **The act of choosing what to record is itself part of remembering.**

Photos are easy to capture. People end up with thousands of images and still cannot find the one thing they need. Text makes experiences genuinely searchable, and keeps other people's faces out of your records.

---

## Architecture

Built with **AWS Strands Agents SDK**, using Anthropic's Claude as the model provider.

Within ships in two versions that share the same data format:

- **`within_ai.py`** — the AI version. Strands Agents handles natural language understanding, keyword extraction, and semantic search.
- **`within.py`** — an offline version with no AI calls. Same data structure, same search, no network required.

We built both deliberately. The core value of Within does not depend on AI. AI makes it smarter, not possible.

The agent has two responsibilities:

**On record:**
1. Understand natural language
2. Extract information that actually appears in the statement
3. Create searchable index data
4. Preserve the original content
5. Add automatic timestamp
6. Associate with the relevant object

**On search:**
1. Understand search intent
2. Search personal history
3. Use both keyword and semantic matching
4. Retrieve relevant records, newest first

---

## Tech Stack

- AWS Strands Agents SDK
- Claude Haiku 4.5 (Anthropic API)
- Python 3.14

---

## Track

**Everyday Agents** — Agents for Humans Hackathon 2026

---

## License

MIT