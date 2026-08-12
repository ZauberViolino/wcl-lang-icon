from pathlib import Path
import iso639


def get_code(lang):
    """
    優先使用 ISO 639-1。
    沒有 639-1 時才使用 ISO 639-3。
    """
    part1 = getattr(lang, "part1", None)
    part3 = getattr(lang, "part3", None)

    if part1:
        return part1

    return part3


def is_retired(lang):
    """
    python-iso639 的 language status：
    A = Active
    其他狀態視為非 Active / retired 等歷史資料。
    """
    return getattr(lang, "status", None) != "A"


def main():
    active_codes = set()
    retired_codes = set()

    # 先建立所有 639-1 code。
    # 這一步很重要：
    # 例如 en -> eng 不會再被加入，
    # zh -> zho 不會再被加入。
    iso639_1_codes = {
        lang.part1
        for lang in iso639.ALL_LANGUAGES
        if getattr(lang, "part1", None)
    }

    for lang in iso639.ALL_LANGUAGES:
        code = get_code(lang)

        if not code:
            continue

        # 如果這個 639-3 有對應的 639-1，
        # 永遠使用 639-1，而不是三碼版本。
        if lang.part3 and lang.part3 != code:
            if lang.part3 in iso639_1_codes:
                continue

        # 任何 retired/deprecated 的 639-1 都保留。
        # retired/deprecated 的 639-3 也保留，但最後輸出。
        if is_retired(lang):
            retired_codes.add(code)
        else:
            active_codes.add(code)

    # 防止 retired code 同時出現在 active
    retired_codes -= active_codes

    # 最終 set
    language_codes = active_codes | retired_codes

    # 排序：
    # 1. Active 兩碼
    # 2. Active 三碼
    # 3. Retired 兩碼
    # 4. Retired 三碼
    def sort_key(code):
        return (
            len(code) == 3,
            code,
        )

    active_sorted = sorted(active_codes, key=sort_key)
    retired_sorted = sorted(retired_codes, key=sort_key)

    # 產生 Python 檔案
    output = Path("language_codes_all.py") #重新生成时记得删掉_all

    with output.open("w", encoding="utf-8") as f:
        f.write("# Generated from ISO 639 data\n")
        f.write("# Active codes first; retired/deprecated codes last.\n\n")

        f.write("LANGUAGE_CODES = {\n")

        for code in active_sorted:
            f.write(f'    "{code}",\n')

        for code in retired_sorted:
            f.write(f'    "{code}",\n')

        f.write("}\n\n")

        f.write("ACTIVE_LANGUAGE_CODES = {\n")
        for code in active_sorted:
            f.write(f'    "{code}",\n')
        f.write("}\n\n")

        f.write("RETIRED_LANGUAGE_CODES = {\n")
        for code in retired_sorted:
            f.write(f'    "{code}",\n')
        f.write("}\n")

    print(f"Generated: {output}")
    print(f"Active:   {len(active_codes)}")
    print(f"Retired:  {len(retired_codes)}")
    print(f"Total:    {len(language_codes)}")

    # 幾個 sanity checks
    expected_present = {
        "en",
        "zh",
        "ja",
        "yue",
        "grc",
    }

    expected_absent = {
        "eng",
        "zho",
        "jpn",
    }

    print("\nChecks:")

    for code in sorted(expected_present):
        print(f"  {'OK' if code in language_codes else 'MISSING'}  {code}")

    for code in sorted(expected_absent):
        print(f"  {'ERROR' if code in language_codes else 'OK'}  {code}")


if __name__ == "__main__":
    main()