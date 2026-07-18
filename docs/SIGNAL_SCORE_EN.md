# EvenOddBasketBot --- Signal Score Specification

**Version:** 1.0 (Draft)

## Purpose

Signal Score is a historical quality assessment of a signal on a scale
from **0 to 100**.

> **Important:** Signal Score is **not** the probability of winning the
> next bet. It reflects only the strength and reliability of the
> historical data behind the signal.

------------------------------------------------------------------------

# Main Principles

1.  Every point must be explainable.
2.  Small samples never receive a high score.
3.  ROI is evaluated together with sample size.
4.  Negative history lowers the score.
5.  Version 1 is informational only.
6.  Automatic filtering is disabled until enough data is collected.

------------------------------------------------------------------------

# Architecture

``` text
Flashscore
    │
    ▼
Parser Engine
    │
    ▼
Strategy Engine
    │
    ▼
Analytics Engine
    ├── Country
    ├── League
    ├── Match Type
    └── Sample Size
            │
            ▼
      Signal Score
            │
            ▼
      Telegram Bot
```

------------------------------------------------------------------------

# Score Components

  Component                  Max
  -------------------- ---------
  Country                     20
  League                      35
  Match Type                  15
  Sample Reliability          20
  ROI                         10
  **Total**              **100**

------------------------------------------------------------------------

# Sample Reliability

    Finished signals   Points
  ------------------ --------
                0--9        0
              10--24        5
              25--49       10
              50--99       15
                100+       20

The smallest sample among Country, League and Match Type defines this
block.

------------------------------------------------------------------------

# ROI

          ROI   Points
  ----------- --------
    below -10        0
       -10..0        2
         0..5        5
        5..10        8
     above 10       10

Current strategy model:

-   WIN = +0.9
-   LOSE = -1.0

------------------------------------------------------------------------

# Example

``` text
Country          12
League           25
Match Type       10
Reliability      15
ROI               8

Signal Score = 70 / 100
```

------------------------------------------------------------------------

# Interpretation

      Score Meaning
  --------- ------------------------------
      0--29 insufficient history
     30--49 weak historical quality
     50--64 average
     65--79 good
    80--100 excellent historical quality

Signal Score is **not** a win probability.

------------------------------------------------------------------------

# Future

Version 2: - last 30 signals - last 100 signals - trend analysis

Version 3: - Bayesian smoothing - confidence intervals

Version 4: - Machine Learning experiments

------------------------------------------------------------------------

# Roadmap

-   [x] Design methodology
-   [ ] Implement Signal Score
-   [ ] Display Score in Telegram
-   [ ] Validate on large dataset
-   [ ] Decision Engine
