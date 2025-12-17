# backend/app/services/company_parser.py
import re

EVENT_WORDS = [
    "面接", "説明会", "選考", "案内",
    "一次", "二次", "最終",
    "インターン", "グループディスカッション", "GD",
]

# NOTE:
# 「サイバーエージェント」を殺さないために "エージェント" はNGに入れない
NG_WORDS = [
    "ご案内", "結果", "通過", "受付",
    "担当", "採用チーム", "採用担当",
    "就職", "新卒", "マイナビ", "リクナビ",
]

LEGAL_SUFFIX = [
    "株式会社", "合同会社", "有限会社", "合資会社", "合名会社",
]

def _clean(s: str) -> str:
    s = (s or "").replace("\u3000", " ").strip()
    # 余計な引用符
    s = s.strip('"\'')

    # 前後の装飾を落とす（よくある）
    s = re.sub(r"^[【\[\(（]+", "", s)
    s = re.sub(r"[】\]\)）]+$", "", s)
    return s.strip()

def _looks_like_company(s: str) -> bool:
    s = _clean(s)
    if not s:
        return False

    # イベント語そのものは会社名ではない
    if any(w in s for w in EVENT_WORDS):
        return False

    # 明らかに会社名じゃないワード
    if any(w in s for w in NG_WORDS):
        return False

    # 長すぎ・短すぎ除外（雑だけど効く）
    if len(s) < 2 or len(s) > 40:
        return False

    return True

def _extract_from_from_address(from_address: str) -> str | None:
    """
    例: '"星歩夢" <ayusyuukatu.2025@gmail.com>' -> '星歩夢'
        'Sky株式会社 <recruit@skygroup.jp>' -> 'Sky株式会社'
    """
    f = (from_address or "").strip()

    # 表示名 "xxx" <...>
    m = re.search(r'^"([^"]+)"\s*<', f)
    if m:
        cand = _clean(m.group(1))
    else:
        # xxx <...>
        m = re.search(r'^([^<]+)\s*<', f)
        cand = _clean(m.group(1)) if m else ""

    # 自分の名前っぽい/個人名っぽい/空は除外（完全ではないが被害軽減）
    # ここは必要なら後で強化（ユーザ名がDBにあるなら比較するのがベスト）
    if not cand:
        return None
    if re.search(r"[ぁ-んァ-ン一-龥]{2,4}", cand) and "株式会社" not in cand and "合同会社" not in cand:
        # 日本語2〜4文字の短い個人名っぽいものは弾く（例: 星歩夢）
        return None

    return cand if _looks_like_company(cand) else None

def extract_company_name(*, subject: str, body: str, from_address: str) -> str | None:
    subject = _clean(subject)
    body = _clean(body)
    text = subject + "\n" + body

    # 0) from_address（会社ドメインのメールだと強いが、個人名も混ざるので最後寄り）
    #    ※ここは最後のフォールバックに回す
    from_cand = _extract_from_from_address(from_address)

    # 1) 「株式会社◯◯ / ◯◯株式会社 / 合同会社◯◯ / ◯◯合同会社」などを最優先
    legal_pat = r"(?:%s)" % "|".join(map(re.escape, LEGAL_SUFFIX))
    m = re.search(rf"({legal_pat}[^\s　]{1,30}|[^\s　]{1,30}{legal_pat})", text)
    if m:
        return _clean(m.group(1))

    # 2) 件名が「【…】会社名」 → 最後の 】 の “後ろ” を会社候補にする
    #    例: 【会社説明会のご案内】サイバーエージェント
    if "】" in subject:
        after = _clean(subject.split("】")[-1])
        if _looks_like_company(after):
            return after

    # 3) 件名末尾の（会社名）
    #    例: 【選考案内】...（ライトハウスコンサルティング）
    m = re.search(r"[（(]([^）)]+)[）)]\s*$", subject)
    if m:
        cand = _clean(m.group(1))
        if _looks_like_company(cand):
            return cand

    # 4) 「— 会社名」「- 会社名」「ー 会社名」末尾パターン
    #    例: 【選考通過】面接のご案内 — 楽天株式会社
    m = re.search(r"[—\-ー]\s*([^\s　]{2,40})\s*$", subject)
    if m:
        cand = _clean(m.group(1))
        if _looks_like_company(cand):
            return cand

    # 5) 本文の「◯◯ 採用担当です」「◯◯ 採用チームです」などから拾う
    m = re.search(r"([^\n]{2,40}?)(?:採用担当|採用チーム)です", body)
    if m:
        cand = _clean(m.group(1))
        if _looks_like_company(cand):
            return cand

    # 6) from_address を最後の保険で使う
    if from_cand:
        return from_cand

    return None
