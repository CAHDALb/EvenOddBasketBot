import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from statistics import print_total_statistics


print_total_statistics()