# adds the english names to the db
import regex as re


def jap_to_eng_conversion() -> dict[str]:

    csvfile = open("./res/song_names.csv", encoding='utf-8')
    next(csvfile)
    jap_to_eng = {}
    for row in csvfile:
        row_data = row.split(sep='\t')
        jap_name = row_data[1]
        if jap_name == "": continue
        eng_name = row_data[2].removesuffix("\n")
        jap_to_eng[jap_name] = eng_name

    return jap_to_eng


def is_english_name(jap_name) -> bool:

    chinese_japanese_chars = re.compile(r'([\p{IsHan}\p{IsBopo}\p{IsHira}\p{IsKatakana}]+)', re.UNICODE)
    return len(chinese_japanese_chars.findall(jap_name)) == 0


if __name__ == "__main__":
    jap_to_eng = jap_to_eng_conversion()

