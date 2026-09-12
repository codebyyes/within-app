import json, os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from strands import Agent
from strands.models.anthropic import AnthropicModel
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
DATA_FILE = "data.json"

model = AnthropicModel(
    client_args={"api_key": os.getenv("ANTHROPIC_API_KEY")},
    model_id="claude-haiku-4-5-20251001",
    max_tokens=400,
)

EXTRACT_PROMPT = """You extract searchable keywords from a sentence where someone
describes something from their own life.

RULES:
- Only extract information that literally appears in the sentence. Never invent
  a price, a name, a brand or a place the person did not say.
- If the person is uncertain ("I think", "maybe", "好像"), keep that uncertainty.
- Names, places, brands, shops and objects are the most valuable keywords.
- Keep each keyword short.
- CRITICAL: Output keywords in the SAME language as the input. English input means
  English keywords. Chinese input means Chinese keywords. Never translate.

CORRECTIONS:
If the sentence corrects or negates something ("it's not X, it's Y",
"不是X，是Y", "turns out it wasn't X"), then:
- include BOTH X and Y in "keywords"
- list X in "corrected" (the outdated value that is being replaced)
If nothing is being corrected, "corrected" must be an empty list.
NEVER summarise a correction as "correction" or "location correction".
Always keep the actual old value and the actual new value as keywords.

Example input: "Hafa restaurant is not on Yangming Road, it's on Zhongshan Road"
Example output:
{"object": "Hafa restaurant location", "keywords": ["Hafa restaurant", "Yangming Road", "Zhongshan Road"], "corrected": ["Yangming Road"]}

Output ONLY valid JSON. No explanation, no markdown fences:
{"object": "what this record is mainly about, 2-6 words",
 "keywords": ["3 to 8 short keywords"],
 "corrected": ["keywords that are now outdated, usually 0 or 1"]}"""

SEARCH_PROMPT = """You are a search engine over someone's own personal records.
You receive a search query and all of their records.
Return the ids of the relevant records as a JSON array, e.g. ["001","003"].
If nothing is relevant, return [].
No explanation, no markdown fences."""

extractor = Agent(model=model, system_prompt=EXTRACT_PROMPT, callback_handler=None)
searcher = Agent(model=model, system_prompt=SEARCH_PROMPT, callback_handler=None)


def clean_json(raw):
    return raw.strip().replace("```json", "").replace("```", "").strip()


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def next_id(data):
    if not data:
        return "001"
    return str(max(int(o["id"]) for o in data) + 1).zfill(3)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/extract", methods=["POST"])
def api_extract():
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400
    raw = clean_json(str(extractor(text)))
    try:
        parsed = json.loads(raw)
        return jsonify({
            "object": parsed.get("object", ""),
            "keywords": parsed.get("keywords", []),
            "corrected": parsed.get("corrected", []),
            "date": datetime.now().strftime("%Y/%m/%d"),
        })
    except Exception:
        return jsonify({"error": "parse_failed"}), 500


@app.route("/api/records", methods=["GET"])
def api_records():
    return jsonify(load_data())


@app.route("/api/record", methods=["POST"])
def api_record():
    body = request.json
    text = body.get("text", "").strip()
    keywords = body.get("keywords", [])
    corrected = body.get("corrected", [])
    obj = body.get("object", "")
    parent = body.get("parent")

    data = load_data()
    today = datetime.now().strftime("%Y/%m/%d")
    entry = {
        "date": today,
        "keywords": keywords,
        "corrected": corrected,
        "original": text,
    }

    if parent:
        target = next((o for o in data if o["id"] == parent), None)
        if not target:
            return jsonify({"error": "not_found"}), 404
        target["records"].insert(0, entry)
        save_data(data)
        return jsonify({"id": parent, "date": today,
                        "keywords": keywords, "corrected": corrected})

    new_id = next_id(data)
    data.append({"id": new_id, "object": obj, "created": today, "records": [entry]})
    save_data(data)
    return jsonify({"id": new_id, "date": today,
                    "keywords": keywords, "corrected": corrected})


@app.route("/api/search", methods=["POST"])
def api_search():
    query = request.json.get("query", "").strip()
    data = load_data()
    if not data or not query:
        return jsonify([])

    summary = "\n".join(
        "#" + o["id"] + " (" + o.get("object", "") + "): " +
        " | ".join(" ".join(r["keywords"]) + " " + r["original"] for r in o["records"])
        for o in data
    )
    raw = clean_json(str(searcher("Query: " + query + "\n\nRecords:\n" + summary)))
    try:
        ids = json.loads(raw)
    except Exception:
        ids = []
    return jsonify([o for o in data if o["id"] in ids])


@app.route("/api/delete", methods=["POST"])
def api_delete():
    body = request.json
    obj_id = body.get("id")
    index = body.get("index")
    data = load_data()
    target = next((o for o in data if o["id"] == obj_id), None)
    if not target:
        return jsonify({"error": "not_found"}), 404
    if 0 <= index < len(target["records"]):
        target["records"].pop(index)
    if not target["records"]:
        data = [o for o in data if o["id"] != obj_id]
    save_data(data)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5050)
