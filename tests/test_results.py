import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from results import check_all_waiting_signals

check_all_waiting_signals()

print("Проверка результатов завершена.")