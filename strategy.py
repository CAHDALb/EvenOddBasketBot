def check_strategy(match):
    """
    Проверяет стратегию:
    Q1, Q2 и Q3 должны быть одной чётности.
    Сигнал только в LIVE и только в 4-й четверти.
    """

    if not match["live"]:
        return False

    if match["quarter"] != 4:
        return False

    q1 = match["q1_total"]
    q2 = match["q2_total"]
    q3 = match["q3_total"]

    if q1 is None or q2 is None or q3 is None:
        return False

    return q1 % 2 == q2 % 2 == q3 % 2