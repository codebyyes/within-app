import json, os, sys
import jieba
from datetime import datetime

DATA_FILE = "data.json"

STOP = set([
    "我","的","了","在","是","也","都","和","與","及","或","但","而","以","為",
    "就","這","那","有","一","個","很","不","嗎","呢","啊","吧","啦","去","來",
    "要","會","把","被","讓","給","跟","從","到","於","對","裡","上","下","中",
    "你","他","她","它","們","之","其","所","此","該","些","說","用","做","買",
    "看","想","覺得","因為","所以","然後","可以","沒有","這個","那個","什麼",
    "一個","一些","已經","還是","如果","雖然","但是","而且","或者","不是",
    "今天","明天","昨天","下次","一家","不錯","還不錯","好像","一下","一起",
    "現在","不要","叫做","名叫","下次不要","不要來","一直","一樣","一定",
    "真的","其實","應該","感覺","有點","時候","方式","情況","問題","時間",
])

def setup_jieba():
    jieba.setLogLevel(20)
    jieba.add_word("峇里島")
    jieba.add_word("峇里島風格")
    jieba.add_word("凱撒沙拉")
    jieba.add_word("雞肉凱撒沙拉")
    jieba.add_word("陽明路")
    jieba.add_word("中山路")
    jieba.add_word("PChome")
    jieba.add_word("Uber Eats")
    jieba.add_word("小美")
    jieba.add_word("哈發")
    jieba.add_word("哈發餐廳")
    jieba.add_word("服務變差")
    jieba.add_word("保固兩年")

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
    last = max(int(obj["id"]) for obj in data)
    return str(last + 1).zfill(3)

def extract_keywords(text):
    setup_jieba()
    words = jieba.cut(text)
    keywords = []
    seen = set()
    for w in words:
        w = w.strip()
        if (w and w not in STOP and len(w) >= 2
                and w not in seen and not w.isdigit()):
            keywords.append(w)
            seen.add(w)
        if len(keywords) >= 8:
            break
    return keywords

def record(text):
    keywords = extract_keywords(text)
    data = load_data()
    new_id = next_id(data)
    entry = {
        "id": new_id,
        "created": datetime.now().strftime("%Y/%m/%d"),
        "records": [
            {
                "date": datetime.now().strftime("%Y/%m/%d"),
                "keywords": keywords,
                "original": text
            }
        ]
    }
    data.append(entry)
    save_data(data)
    print(f"\n✅ 已建立 #{new_id}\n")
    print(f"{entry['records'][0]['date']}")
    print(" · ".join(keywords))
    print()

def add(obj_id, text):
    data = load_data()
    obj_id = obj_id.zfill(3)
    target = next((o for o in data if o["id"] == obj_id), None)
    if not target:
        print(f"\n找不到 #{obj_id}")
        return
    keywords = extract_keywords(text)
    new_record = {
        "date": datetime.now().strftime("%Y/%m/%d"),
        "keywords": keywords,
        "original": text
    }
    target["records"].insert(0, new_record)
    save_data(data)
    print(f"\n✅ 已加入 #{obj_id}\n")
    print(f"{new_record['date']}")
    print(" · ".join(keywords))
    print()

def search(query):
    data = load_data()
    if not data:
        print("\n還沒有任何記錄。")
        return
    setup_jieba()
    query_words = [w.strip() for w in jieba.cut(query)
                   if w.strip() and len(w.strip()) >= 2]
    results = []
    for obj in data:
        all_text = " ".join(
            " ".join(r["keywords"]) + " " + r["original"]
            for r in obj["records"]
        )
        score = sum(1 for w in query_words if w in all_text)
        if score > 0:
            results.append((score, obj))
    results.sort(key=lambda x: x[0], reverse=True)
    if not results:
        print("\n找不到相關記錄。")
        return
    print(f"\n找到 {len(results)} 筆：\n")
    for _, obj in results:
        print(f"#{obj['id']}")
        for r in obj["records"]:
            print(f"  {r['date']}  {' · '.join(r['keywords'])}")
        print()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("新增：python3 within.py record '你想記錄的事'")
        print("補充：python3 within.py add 001 '補充內容'")
        print("搜尋：python3 within.py search '你想找的東西'")
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "add":
        if len(sys.argv) < 4:
            print("用法：python3 within.py add 001 '補充內容'")
            sys.exit(1)
        add(sys.argv[2], " ".join(sys.argv[3:]))
    else:
        text = " ".join(sys.argv[2:])
        if mode == "record":
            record(text)
        elif mode == "search":
            search(text)
        else:
            print("請用 record、add 或 search")
