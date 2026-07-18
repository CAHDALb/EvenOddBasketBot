import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from parser import get_match_by_id


match = get_match_by_id("U3RX1Dxg")

print(match)

from parser import get_match_by_id

match = get_match_by_id("0YSjLrdD")

print(match)

