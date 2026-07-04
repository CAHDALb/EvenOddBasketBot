from os.path import split
import requests
from config import HEADERS, FEED


def to_int(value):
    """
    Безопасно переводит значение в число.
    Если значения нет, возвращает None.
    """

    if value is None:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def quarter_total(home_score, away_score):
    """
    Считает сумму очков в четверти.
    """

    if home_score is None or away_score is None:
        return None

    return home_score + away_score


def get_quarter(ac):
    """
    Переводит код Flashscore AC в номер четверти.
    """

    if ac == "22":
        return 1

    if ac == "23":
        return 2

    if ac == "24":
        return 3

    if ac == "25":
        return 4

    return None


def normalize_match(raw_match):
    """
    Переводит сырые поля Flashscore в понятный формат.
    """

    match_id = raw_match.get("~AA")

    q1_home = to_int(raw_match.get("BA"))
    q1_away = to_int(raw_match.get("BB"))

    q2_home = to_int(raw_match.get("BC"))
    q2_away = to_int(raw_match.get("BD"))

    q3_home = to_int(raw_match.get("BE"))
    q3_away = to_int(raw_match.get("BF"))

    q4_home = to_int(raw_match.get("BG"))
    q4_away = to_int(raw_match.get("BH"))

    home_score = to_int(raw_match.get("AG"))
    away_score = to_int(raw_match.get("AH"))

    ab = raw_match.get("AB")
    ac = raw_match.get("AC")

    live = ab == "2"
    finished = ab == "3" and ac == "3"

    return {
        "id": match_id,
        "match_url": f"https://www.flashscorekz.com/match/{match_id}",

        "country": raw_match.get("country"),
        "league": raw_match.get("league"),

        "home_name": raw_match.get("AE"),
        "away_name": raw_match.get("AF"),

        "home_score": home_score,
        "away_score": away_score,

        "q1_home": q1_home,
        "q1_away": q1_away,
        "q1_total": quarter_total(q1_home, q1_away),

        "q2_home": q2_home,
        "q2_away": q2_away,
        "q2_total": quarter_total(q2_home, q2_away),

        "q3_home": q3_home,
        "q3_away": q3_away,
        "q3_total": quarter_total(q3_home, q3_away),

        "q4_home": q4_home,
        "q4_away": q4_away,
        "q4_total": quarter_total(q4_home, q4_away),

        "raw_ab": ab,
        "raw_ac": ac,

        "quarter": get_quarter(ac),

        "live": live,
        "finished": finished,
    }


def get_matches():
    """
    Получает матчи Flashscore и возвращает их в понятном формате.
    """

    url = f"https://local-ruua.flashscore.ninja/32/x/feed/{FEED}"

    response = requests.get(
        url=url,
        headers=HEADERS
    )

    data = response.text.split("¬")

    raw_matches = []

    current_match = None
    current_country = None
    current_league = None

    for item in data:

        if "÷" not in item:
            continue

        key = item.split("÷")[0]
        value = item.split("÷")[-1]

        # Новый блок лиги
        if key == "~ZA":
            current_league = value
            continue

        # Страна турнира
        if key == "ZY":
            current_country = value
            continue

        # Новый матч
        if key == "~AA":

            if current_match:
                raw_matches.append(current_match)

            current_match = {
                "~AA": value,
                "country": current_country,
                "league": current_league
            }

            continue

        # Поля текущего матча
        if current_match is not None:
            current_match[key] = value

    # Добавляем последний матч
    if current_match:
        raw_matches.append(current_match)

    # Переводим сырые матчи в понятный формат
    matches = []

    for raw_match in raw_matches:
        normalized = normalize_match(raw_match)

        if normalized["id"]:
            matches.append(normalized)

    return matches

def get_match_by_id(match_id):
    """
    Ищет матч по его ID.

    Зачем нужна функция:
    - results.py будет использовать её, чтобы проверить,
      закончился ли матч;
    - если матч найден, возвращаем его данные;
    - если не найден, возвращаем None.
    """

    # Получаем все матчи из Flashscore
    matches = get_matches()

    # Перебираем все матчи
    for match in matches:

        # Если ID совпал — возвращаем этот матч
        if match["id"] == match_id:
            return match

    # Если матч не найден
    return None