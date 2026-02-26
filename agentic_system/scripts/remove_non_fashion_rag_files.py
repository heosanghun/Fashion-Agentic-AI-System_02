"""
rag_fashion_1gb 내 패션과 무관한 위키 문서 파일 삭제.
파일명에서 제목을 추출해, 패션 관련 키워드가 없고 비패션 지시어가 있으면 삭제.
사용: python -m agentic_system.scripts.remove_non_fashion_rag_files
"""
from pathlib import Path
import re

SCRIPT_DIR = Path(__file__).resolve().parent
AGENTIC_ROOT = SCRIPT_DIR.parent
TARGET_DIR = AGENTIC_ROOT / "data" / "rag_fashion_1gb"

# 파일명 패턴: wiki_ko_제목_<16자 hex>.txt 또는 wiki_en_제목_<16자 hex>.txt
TITLE_PATTERN = re.compile(r"^wiki_(?:ko|en)_(.+)_[0-9a-f]{16}\.txt$", re.IGNORECASE)

# 패션 관련 키워드 (제목에 하나라도 있으면 유지)
FASHION_KEYWORDS_KO = [
    "의류", "옷", "패션", "바지", "반바지", "코트", "재킷", "자켓", "티셔츠", "원단", "직물",
    "모자", "스커트", "치마", "니트", "가방", "신발", "양말", "벨트", "넥타이", "조끼",
    "원피스", "블라우스", "셔츠", "브랜드", "잠옷", "수영복", "웨딩", "란제리", "속옷",
    "코스튬", "의상", "스웨터", "카디건", "점퍼", "패딩", "후드", "가죽", "실크", "울",
    "면", "데님", "청바지", "트렌치", "아우터", "상의", "하의", "소재", "스타일", "코디",
    "트렌드", "편직", "능직", "레이스", "지갑", "스카프", "액세서리", "악세서리",
    "런웨이", "디자이너", "니트웨어", "의복", "착용", "직물", "원사", "섬유", "천",
    "로에베", "꼼데가르송", "구찌", "샤넬", "에르메스", "루이비통", "프라다", "버버리",
]
FASHION_KEYWORDS_EN = [
    "shirt", "dress", "coat", "jacket", "skirt", "hat", "cap", "fabric", "textile",
    "cloth", "clothing", "fashion", "garment", "sweater", "knit", "jeans", "denim",
    "silk", "wool", "cotton", "linen", "leather", "suit", "tie", "bag", "shoe",
    "sock", "bra", "lingerie", "swimwear", "wedding", "runway", "apparel", "vest",
    "blouse", "jumper", "cardigan", "hoodie", "trench", "overcoat", "blazer", "parka",
    "wear", "knitwear", "footwear", "accessory", "handbag", "sneaker", "couture",
    "vintage", "dalmatic", "gown", "jersey", "chinos", "shorts", "raincoat",
    "fedora", "beret", "beanie", "scarf", "glove", "belt", "wallet", "jewelry",
    "chloe", "adidas", "tom_ford", "brand", "designer", "runway", "style",
]

# 비패션 지시어 (제목에 있고, 패션 키워드가 없으면 삭제)
NON_FASHION_KEYWORDS = [
    # 영화/드라마/예능
    "영화", "_film", "_movie", "게임", "_game", "닌텐도", "스위치", "음반", "_album",
    "_episode", "드라마", "_series", "animation", "애니", "애니메이션", "만화",
    "List_of_animated", "List_of_Disney", "List_of_Columbo", "List_of_animated_feature",
    # 지리/기관
    "스코틀랜드", "Scotland", "위키백과", "Wikipedia", "부석사", "금강제화",
    "여주시", "신라", "백제", "대학교",
    # 기술/회사(비패션)
    "자동차", "스마트폰", "인터넷", "로켓_인터넷", "로에베",  # 로에베는 패션브랜드라 위에 유지
    # 인물/직업 (패션 디자이너 제외)
    "_singer", "_actor", "_actress", "_politician", "_football", "_baseball",
    "_basketball", "_soccer", "_musician", "_band", "_group",
    # 과학/의료
    "genome", "logic", "medicine", "_drug", "아지트로마이신", "virus",
    # 기타 비패션
    "악마의_열매", "똥", "붕괴", "스타레일", "뮤직뱅크", "JYP_엔터", "엔터테인먼트",
    "_chart", "Radar_chart", "Minimal_genome", "Minimal_logic",
    "Tom_and_Jerry", "Nmixx", "파이브_아이즈", "라이트웨이브", "검열",
    "Raising_Hell", "맥스웰_페리_코턴",  # 인명
    "Park_Gyu-young", "Krystal_Jung", "Roger_Moore", "Dorothea_Puente",
    "Oh_Dae-hwan", "Song_Seung-heon", "Zhang_Hao_singer", "Chyno_Miranda",
    "Barry_Sloane", "Becca_Bloom", "Gisèle_Pelicot", "James_Cotton",
    "George_II_of_Great_Britain", "Mary_Cotton",  # 인명 (Mary Cotton 등)
    "Baked_potato", "Coffin", "Soona_film", "Hattytown_Tales",
    "Runway_end_identifier_light",  # 활주로 등명
    "NATO_Accessory_Rail", "Colombian_necktie",  # 비의류
    "Leather_album", "Overcoats_album", "Rizal_Without_the_Overcoat",
    "José_and_his_Amazing_Technicolor_Overcoat",
    "Medicine_Hat",  # 지명
    "American_football", "Navajo_dolls", "Fugu_Day_Ghana",
    "Seal_mechanical", "Nominal_Pipe_Size", "Thread_Routes",
    "뮤직뱅크", "닌텐도", "스마트폰", "여주시", "부석사", "금강제화", "닌텐도의_역사",
    "소녀시대", "현대자동차", "위키백과", "소정환", "어이", "좌우대칭동물", "킬리만자로",
    "JYP_엔터", "로켓_인터넷", "백제_금동", "붕괴_스타레일",
    "Stain_", "Supplementary_weaving", "Tog_unit", "Tarpaulin",
    "Floating_canvas", "Mark_I_trench_knife", "Christina_piercing",
]

# 로에베는 패션 브랜드이므로 NON에서 제거
NON_FASHION_KEYWORDS = [x for x in NON_FASHION_KEYWORDS if x != "로에베"]

# 내용 첫 800자에 있으면 비패션 문서로 간주 (인물/영화/음악 등)
CONTENT_NON_FASHION_MARKERS = [
    "배우이다", "가수이다", "정치인이다", "축구 선수", "야구 선수", "영화이다", "드라마이다",
    "음반", "앨범", "텔레비전 프로그램", "비디오 게임", "애니메이션", "만화",
    "위키백과", "대한민국의 배우", "대한민국의 가수", "대한민국의 정치인", "대한민국의 연예인",
    "출연 작품", "발매한 음반", "수상 내역", "영화 목록", "등장 인물",
    "is a South Korean actor", "is an American actor", "is a British actor",
    "is a singer", "is a film", "is a video game", "is a television",
    "is an American singer", "is a South Korean singer", "is a politician",
    "is a football player", "is a baseball player", "is a basketball player",
    "is a fictional character", "is a manga series", "is an anime",
]


def extract_title(filename: str) -> str | None:
    m = TITLE_PATTERN.match(filename)
    if m:
        return m.group(1)
    return None


def is_fashion_related(title: str) -> bool:
    t = title.lower().replace("-", "_")
    for kw in FASHION_KEYWORDS_KO + FASHION_KEYWORDS_EN:
        if kw.lower() in t:
            return True
    return False


def has_non_fashion_indicator(title: str) -> bool:
    t = title.lower().replace("-", "_")
    for kw in NON_FASHION_KEYWORDS:
        if kw.lower() in t:
            return True
    return False


def content_indicates_non_fashion(filepath: Path) -> bool:
    try:
        raw = filepath.read_bytes()
        text = raw[:800].decode("utf-8", errors="ignore")
        for m in CONTENT_NON_FASHION_MARKERS:
            if m in text:
                return True
    except Exception:
        pass
    return False


def should_delete(filepath: Path) -> bool:
    filename = filepath.name
    title = extract_title(filename)
    if title is None:
        return False  # curated_glossary 등 다른 형식은 유지
    if is_fashion_related(title):
        return False
    if has_non_fashion_indicator(title):
        return True
    # 제목에 패션 키워드 없고, 내용이 배우/가수/영화 등이면 삭제
    if content_indicates_non_fashion(filepath):
        return True
    return False


def main():
    if not TARGET_DIR.exists():
        print(f"경로 없음: {TARGET_DIR}")
        return
    to_delete = []
    to_keep = []
    for f in TARGET_DIR.iterdir():
        if not f.is_file() or f.suffix != ".txt":
            continue
        if should_delete(f):
            to_delete.append(f)
        else:
            to_keep.append(f.name)
    print(f"총 파일: {len(to_delete) + len(to_keep)}")
    print(f"삭제 대상(비패션): {len(to_delete)}")
    print(f"유지: {len(to_keep)}")
    if not to_delete:
        print("삭제할 파일 없음.")
        return
    # 삭제 실행
    deleted = 0
    for i, f in enumerate(to_delete):
        try:
            f.unlink()
            deleted += 1
            if (i + 1) % 500 == 0 or i == len(to_delete) - 1:
                print(f"  삭제 진행: {deleted}/{len(to_delete)}")
        except Exception as e:
            print(f"  실패: {f.name} - {e}")
    print(f"완료: {deleted}개 삭제됨.")


if __name__ == "__main__":
    main()
