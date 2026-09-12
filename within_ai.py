import json, os, sys
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

DATA_FILE = "data.json"
MODEL = "claude-haiku-4-5-20251001"

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

EXTRACT_PROMPT = """你從使用者描述自己生活的句子中，抽出可以未來搜尋回來的關鍵字。

規則：
- 只抽出句子裡真的出現的資訊，絕對不要編造使用者沒說的東西
- 不要抽出價格、店名、地址，除非使用者明確說了
- 如果使用者說「好像」「應該」，保留那個不確定性在關鍵字裡
- 人名、店名、品牌、地點、物品是最重要的關鍵字
- 關鍵字要簡短，2-6 個字
- 保留使用者原本的語言

只輸出 JSON，不要有任何說明文字、不要有 markdown 標記：
{"object": "這筆記錄主要關於什麼，2-6個字", "keywords": ["3到8個關鍵字"]}"""


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


def extract_keywords(text):
    msg = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=EXTRACT_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    raw = msg.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
        return parsed.get("object", ""), parsed.get("keywords", [])
    except Exception:
        print("AI 回傳格式有問題：", raw)
        return "", []


def record(text):
    obj, keywords = extract_keywords(text)
    if not keywords:
        return
    data = load_data()
    new_id = next_id(data)
    today = datetime.now().strftime("%Y/%m/%d")
    data.append({
        "id": new_id,
        "object": obj,
        "created": today,
        "records": [{"date": today, "keywords": keywords, "original": text}]
    })
    save_data(data)
    print(f"\n✅ 已建立 #{new_id}（{obj}）\n")
    print(today)
    print(" · ".join(keywords))
    print()


def add(obj_id, text):
    data = load_data()
    obj_id = obj_id.zfill(3)
    target = next((o for o in data if o["id"] == obj_id), None)
    if not target:
        print(f"\n找不到 #{obj_id}")
        return
    _, keywords = extract_keywords(text)
    if not keywords:
        return
    today = datetime.now().strftime("%Y/%m/%d")
    target["records"].insert(0, {"date": today, "keywords": keywords, "original": text})
    save_data(data)
    print(f"\n✅ 已加入 #{obj_id}\n")
    print(today)
    print(" · ".join(keywords))
    print()


def search(query):
    data = load_data()
    if not data:
        print("\n還沒有任何記錄。")
        return

    summary = "\n".join(
        f"#{o['id']} ({o.get('object','')}): " +
        " | ".join(" ".join(r["keywords"]) + " " + r["original"] for r in o["records"])
        for o in data
    )

    msg = client.messages.create(
        model=MODEL,
        max_tokens=200,
        system="""你是個人記錄的搜尋引擎。使用者會給你一個搜尋句，和他所有的記錄。
找出相關的記錄編號，只輸出編號的 JSON 陣列，例如：["001","003"]
如果都不相關就輸出 []
不要有任何說明文字。""",
        messages=[{"role": "user", "content": f"搜尋：{query}\n\n記錄：\n{summary}"}],
    )

    raw = msg.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        ids = json.loads(raw)
    except Exception:
        ids = []

    results = [o for o in data if o["id"] in ids]
    if not results:
        print("\n找不到相關記錄。")
        return

    print(f"\n找到 {len(results)} 筆：\n")
    for o in results:
        print(f"#{o['id']}")
        for r in o["records"]:
            print(f"  {r['date']}  {' · '.join(r['keywords'])}")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("新增：python3 within_ai.py record '你想記錄的事'")
        print("補充：python3 within_ai.py add 001 '補充內容'")
        print("搜尋：python3 within_ai.py search '你想找的東西'")
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "add":
        add(sys.argv[2], " ".join(sys.argv[3:]))
    else:
        text = " ".join(sys.argv[2:])
        if mode == "record":
            record(text)
        elif mode == "search":
            search(text)
        else:
            print("請用 record、add 或 search")
