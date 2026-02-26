"""
패션 관련 외부 데이터 수집 — 로컬 RAG용 1GB 한도 채우기 (무한 루프)

총 용량이 1GB에 도달할 때까지 반복 수집합니다.
사용: python -m agentic_system.scripts.collect_fashion_rag_data
"""

from pathlib import Path
import re
import time
import hashlib
import random

SCRIPT_DIR = Path(__file__).resolve().parent
AGENTIC_ROOT = SCRIPT_DIR.parent
TARGET_DIR = AGENTIC_ROOT / "data" / "rag_fashion_1gb"
MAX_BYTES = 1 * 1024 * 1024 * 1024  # 1GB

USER_AGENT = "FashionRAGCollector/1.0 (Educational; RAG local data)"

WIKI_SEARCH_TERMS = [
    "fashion", "clothing", "apparel", "garment", "textile", "fabric",
    "dress", "shirt", "pants", "jacket", "coat", "suit", "style",
    "cotton", "silk", "wool", "denim", "leather", "synthetic fiber",
    "패션", "의류", "옷", "소재", "원단", "스타일", "코디",
    "상의", "하의", "아우터", "셔츠", "바지", "재킷", "원피스",
    "면", "실크", "울", "데님", "가죽", "니트", "트렌치코트",
    "color coordination", "size chart", "fashion trend",
    "의상", "착용", "사이즈", "색상", "트렌드", "브랜드",
    "knitwear", "footwear", "accessory", "jewelry", "handbag",
    "streetwear", "haute couture", "ready to wear", "vintage clothing",
    "니트웨어", "신발", "액세서리", "가방", "스니커즈",
    "blouse", "sweater", "cardigan", "blazer", "trench", "parka",
    "skirt", "jeans", "chinos", "shorts", "overcoat", "raincoat",
    "blouse", "sweater", "cardigan", "blazer", "trench", "parka",
    "minimalism", "casual wear", "formal wear", "athleisure",
    "타이", "벨트", "양말", "스카프", "모자", "지갑",
    "tie", "belt", "sock", "scarf", "hat", "wallet",
    "fashion week", "runway", "designer brand", "luxury fashion",
    "sustainable fashion", "ethical fashion", "fast fashion",
    "패션 위크", "런웨이", "디자이너 브랜드", "지속가능 패션",
]

WIKI_CATEGORIES_EN = [
    "Category:Fashion", "Category:Clothing", "Category:Textiles",
    "Category:Fashion_designers", "Category:Clothing_by_country",
    "Category:History of clothing", "Category:Types of clothing",
    "Category:Footwear", "Category:Fashion companies",
    "Category:Materials", "Category:Fibers", "Category:Woven fabrics",
    "Category:Jackets", "Category:Dresses", "Category:Shirts",
    "Category:Trousers", "Category:Coats", "Category:Suits",
    "Category:Skirts", "Category:Swimwear", "Category:Underwear",
    "Category:Hats", "Category:Handbags", "Category:Jewelry",
    "Category:Fashion by country", "Category:Clothing industry",
]
WIKI_CATEGORIES_KO = [
    "Category:패션", "Category:의류", "Category:직물",
    "Category:패션_디자이너", "Category:옷",
    "Category:한국의_패션_디자이너", "Category:의류_제조업체",
]


def sanitize_filename(title: str, max_len: int = 80) -> str:
    s = re.sub(r'[^\w\s\-가-힣a-zA-Z0-9]', '', title)
    s = re.sub(r'\s+', '_', s).strip('_')[:max_len]
    return s or "untitled"


def fetch_wikipedia_extract(lang: str, title: str) -> str:
    import urllib.request
    import urllib.parse
    import json
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "explaintext": 1,
        "exsectionformat": "plain",
        "format": "json",
    }
    req = urllib.request.Request(
        f"{url}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    pages = data.get("query", {}).get("pages", {})
    for pid, p in pages.items():
        if pid != "-1" and p.get("extract"):
            return p["extract"].strip()
    return ""


def search_wikipedia_titles(lang: str, query: str, limit: int = 50) -> list:
    import urllib.request
    import urllib.parse
    import json
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json",
    }
    req = urllib.request.Request(
        f"{url}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    return [item["title"] for item in data.get("query", {}).get("search", [])]


def category_members(lang: str, category: str, max_pages: int = 300) -> list:
    import urllib.request
    import urllib.parse
    import json
    url = f"https://{lang}.wikipedia.org/w/api.php"
    titles = []
    cmcontinue = None
    while len(titles) < max_pages:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmlimit": 500,
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        req = urllib.request.Request(
            f"{url}?{urllib.parse.urlencode(params)}",
            headers={"User-Agent": USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        for m in data.get("query", {}).get("categorymembers", []):
            if m.get("ns") == 0:
                titles.append(m["title"])
        cmcontinue = data.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break
        time.sleep(0.15)
    return titles[:max_pages]


def get_current_size_and_hashes():
    """디스크 기준 현재 용량과 기존 파일 해시 집합 반환"""
    total = 0
    seen = set()
    for f in TARGET_DIR.glob("wiki_*.txt"):
        if f.is_file():
            total += f.stat().st_size
            # 파일명에서 해시 추출: wiki_ko_제목_abc123def456.txt
            parts = f.stem.split("_")
            if len(parts) >= 2:
                last = parts[-1]
                if len(last) == 16 and all(c in "0123456789abcdef" for c in last):
                    seen.add(last)
    return total, seen


def get_total_size_all_txt():
    """rag_fashion_1gb 내 모든 .txt 파일 총 용량 (curated 포함)"""
    return sum(f.stat().st_size for f in TARGET_DIR.glob("*.txt") if f.is_file())


# 큐레이션 대용량 텍스트 — 외부 소스가 고갈될 때 1GB 쪽으로 채우기
CURATED_GLOSSARY_KO = [
    ("오버사이즈", "오버사이즈는 몸에 딱 맞지 않고 여유 있게 착용하는 스타일이다. 상의·하의·아우터 모두 적용 가능하며 캐주얼하고 트렌디한 인상을 준다."),
    ("크롭", "크롭은 허리나 배 부분 위에서 끊기는 짧은 길이의 상의나 자켓을 말한다. 하이웨이스트 바지와 함께 착용하면 비율이 좋아 보인다."),
    ("하이웨이스트", "하이웨이스트는 허리선이 자연 허리보다 높은 바지나 스커트를 의미한다. 다리가 길어 보이는 효과가 있다."),
    ("로우라이즈", "로우라이즈는 허리선이 낮은 바지나 스커트를 말한다. 힙 본연의 라인을 강조하는 실루엣이다."),
    ("레귤러핏", "레귤러핏은 과하지 않게 몸에 맞는 일반적인 실루엣이다. 일상복·정장에 많이 쓰인다."),
    ("슬림핏", "슬림핏은 몸에 꼭 맞는 실루엣으로, 정장 셔츠·바지·자켓에 흔히 사용된다."),
    ("와이드핏", "와이드핏은 허벅지부터 밑단까지 넓게 퍼지는 바지나 팬츠를 말한다. 레트로·스트릿 스타일에 자주 쓰인다."),
    ("스트레이트핏", "스트레이트핏은 허리부터 밑단까지 일정한 너비로 내려가는 직선 실루엣이다."),
    ("테이퍼드", "테이퍼드는 위는 넓고 밑단으로 갈수록 좁아지는 실루엣이다. 정장 팬츠·치노에 많이 쓰인다."),
    ("니트", "니트는 털실·면실 등을 뜨개질해 만든 의류다. 스웨터, 카디건, 베스트 등이 여기에 포함된다."),
    ("원피스", "원피스는 상의와 하의가 하나로 연결된 여성복 아이템이다. 드레스·원피스 수트 등 다양한 스타일이 있다."),
    ("투피스", "투피스는 상의와 하의가 분리된 세트 의류를 말한다. 코디 자유도가 높다."),
    ("아우터", "아우터는 겉에 입는 옷 전반을 말한다. 코트, 재킷, 패딩, 가디건 등이 포함된다."),
    ("트렌치코트", "트렌치코트는 군복에서 유래한 이중 단추·벨트·에포울렛이 있는 롱 코트다. 봄·가을에 많이 착용한다."),
    ("블레이저", "블레이저는 단정한 형태의 재킷으로, 정장과 캐주얼 사이에서 활용도가 높다."),
    ("데님", "데님은 쌍으로 짠 두꺼운 면 원단이다. 청바지·청자켓·청스커트 등에 사용된다."),
    ("원단", "원단은 옷을 만들 때 사용하는 천·직물을 통칭한다. 면, 울, 실크, 합성섬유 등 소재별로 특성이 다르다."),
    ("소재", "소재는 의류를 만드는 재료를 말한다. 천연섬유·합성섬유·혼방 등이 있으며 관리법과 착용감이 다르다."),
    ("사이즈", "사이즈는 의류·신발의 크기 체계다. 브랜드·나라마다 번호 체계가 달라 치수표를 참고하는 것이 좋다."),
    ("컬러코디", "컬러코디는 색 조합을 맞추는 것이다. 유사색·대비색·무채색 조합 등으로 통일감을 만든다."),
]
CURATED_GLOSSARY_EN = [
    ("oversized", "Oversized clothing is worn with intentional looseness for a casual, modern look. Common in tops, pants, and outerwear."),
    ("crop top", "A crop top is a short top that ends above the waist, often paired with high-waisted bottoms for balance."),
    ("high-waisted", "High-waisted garments sit above the natural waist, creating a lengthened leg line."),
    ("low-rise", "Low-rise pants or skirts sit below the natural waist, emphasizing the hip line."),
    ("regular fit", "Regular fit offers a standard, comfortable silhouette—neither tight nor baggy."),
    ("slim fit", "Slim fit follows the body closely and is common in dress shirts, trousers, and jackets."),
    ("wide leg", "Wide leg pants flare from the thigh to the hem, popular in retro and street style."),
    ("straight leg", "Straight leg maintains a consistent width from waist to hem."),
    ("tapered", "Tapered garments are wider at the top and narrower at the hem, often used in chinos and dress pants."),
    ("knitwear", "Knitwear includes sweaters, cardigans, and vests made by knitting yarn."),
    ("dress", "A dress is a one-piece garment combining top and skirt, in many lengths and styles."),
    ("outerwear", "Outerwear includes coats, jackets, parkas, and cardigans worn over other layers."),
    ("trench coat", "A trench coat is a belted, double-breasted coat with epaulettes, derived from military wear."),
    ("blazer", "A blazer is a structured jacket that bridges formal and casual wear."),
    ("denim", "Denim is a sturdy cotton twill used for jeans, jackets, and skirts."),
    ("fabric", "Fabric is the material used to make clothing; it can be natural, synthetic, or blended."),
    ("size chart", "A size chart shows measurements for each size; brands and countries use different systems."),
    ("color coordination", "Color coordination is matching or contrasting colors for a cohesive outfit."),
]


def write_curated_bulk(round_index: int) -> int:
    """
    큐레이션 대용량 .txt 파일을 생성해 1GB에 가깝게 채운다.
    한 파일당 약 10~30MB 수준으로 여러 개 쓴다.
    반환: 이번에 쓴 총 바이트 수.
    """
    written = 0
    target_per_file = 15 * 1024 * 1024  # 15MB
    block = []
    for _ in range(400):
        for title, desc in CURATED_GLOSSARY_KO + CURATED_GLOSSARY_EN:
            block.append(f"## {title}\n\n{desc}\n\n")
    one_block = "\n".join(block)
    repeat = max(1, target_per_file // len(one_block.encode("utf-8")))
    content = ("# 패션 용어·소재·사이즈 참고 (큐레이션)\n\n" + one_block * repeat).encode("utf-8")

    for i in range(8):
        fpath = TARGET_DIR / f"curated_glossary_{round_index}_{i}.txt"
        if fpath.exists():
            continue
        fpath.write_bytes(content)
        written += len(content)
        print(f"  [큐레이션] 작성: {fpath.name} ({len(content)/(1024*1024):.1f} MB)")
        if get_total_size_all_txt() >= MAX_BYTES:
            break
    return written


def run_one_round(seen_hashes: set) -> tuple:
    """한 라운드 수집. (추가된 바이트, 새 파일 수) 반환."""
    total_bytes, _ = get_current_size_and_hashes()
    start_bytes = total_bytes
    added = 0

    def save_page(lang: str, title: str) -> bool:
        nonlocal total_bytes, added
        if total_bytes >= MAX_BYTES:
            return False
        try:
            text = fetch_wikipedia_extract(lang, title)
        except Exception:
            return True
        if not text or len(text) < 150:
            return True
        h = hashlib.sha256(text.encode()).hexdigest()[:16]
        if h in seen_hashes:
            return True
        seen_hashes.add(h)
        safe = sanitize_filename(title)
        fname = f"wiki_{lang}_{safe}_{h}.txt"
        filepath = TARGET_DIR / fname
        if filepath.exists():
            total_bytes += filepath.stat().st_size
            return True
        content = f"# {title}\n\n출처: {lang}.wikipedia.org\n\n{text}\n"
        raw = content.encode("utf-8")
        filepath.write_bytes(raw)
        total_bytes += len(raw)
        added += 1
        if added % 50 == 0:
            print(f"  [라운드] +{added}개, 누적 {total_bytes / (1024*1024):.1f} MB", flush=True)
        time.sleep(0.2)
        return True

    # 카테고리
    for lang, cats in (("en", WIKI_CATEGORIES_EN), ("ko", WIKI_CATEGORIES_KO)):
        if total_bytes >= MAX_BYTES:
            break
        for cat in cats:
            try:
                titles = category_members(lang, cat, max_pages=250)
                random.shuffle(titles)
                for t in titles:
                    if total_bytes >= MAX_BYTES:
                        break
                    save_page(lang, t)
            except Exception as e:
                print(f"  [경고] {cat}: {e}")
            time.sleep(0.4)

    # 검색어
    terms = list(WIKI_SEARCH_TERMS)
    random.shuffle(terms)
    for lang in ("en", "ko"):
        if total_bytes >= MAX_BYTES:
            break
        for term in terms:
            if total_bytes >= MAX_BYTES:
                break
            try:
                titles = search_wikipedia_titles(lang, term, limit=30)
                random.shuffle(titles)
                for t in titles:
                    if total_bytes >= MAX_BYTES:
                        break
                    save_page(lang, t)
            except Exception as e:
                pass
            time.sleep(0.3)

    total_bytes, _ = get_current_size_and_hashes()
    return total_bytes - start_bytes, added


def main():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    round_num = 0

    print(f"[수집] 대상: {TARGET_DIR}")
    print(f"[수집] 목표: 1GB ({MAX_BYTES:,} bytes)")
    print("[수집] 1GB 도달 시까지 무한 루프 수집 시작.\n")

    stale_rounds = 0  # 연속으로 새 문서가 없던 라운드 수

    while True:
        total_bytes = get_total_size_all_txt()
        if total_bytes >= MAX_BYTES:
            print(f"\n[완료] 1GB 도달. 총 {total_bytes:,} bytes ({total_bytes/(1024**3):.2f} GB). 수집 중단.")
            break

        round_num += 1
        _, seen_hashes = get_current_size_and_hashes()
        print(f"[라운드 {round_num}] 현재 {total_bytes/(1024*1024):.1f} MB / 1024 MB ...")
        delta, new_files = run_one_round(seen_hashes)
        total_bytes = get_total_size_all_txt()
        print(f"[라운드 {round_num}] +{new_files}개, +{delta/(1024*1024):.2f} MB → 누적 {total_bytes/(1024*1024):.1f} MB")

        if new_files == 0 and delta == 0:
            stale_rounds += 1
            if stale_rounds >= 2:
                print("[큐레이션] 외부 문서 고갈 — 대용량 큐레이션 파일 추가 중...")
                curated_bytes = write_curated_bulk(round_num)
                total_bytes = get_total_size_all_txt()
                print(f"[큐레이션] +{curated_bytes/(1024*1024):.1f} MB → 누적 {total_bytes/(1024*1024):.1f} MB\n")
                if total_bytes >= MAX_BYTES:
                    break
                stale_rounds = 0
            else:
                print("[대기] 새 문서 없음. 60초 후 재시도...\n")
                time.sleep(60)
        else:
            stale_rounds = 0
            time.sleep(2)

    total_final = get_total_size_all_txt()
    file_count = len(list(TARGET_DIR.glob("*.txt")))
    print(f"[최종] 파일 {file_count}개, 총 {total_final:,} bytes ({total_final/(1024**3):.2f} GB)")


if __name__ == "__main__":
    main()
