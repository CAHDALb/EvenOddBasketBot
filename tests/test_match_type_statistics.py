import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from statistics import print_match_type_statistics


print_match_type_statistics()