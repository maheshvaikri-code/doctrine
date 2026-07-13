---
description: Verify a Gold Build record before deployment (enterprise profile)
---

Run the deploy gate for the tag given in $ARGUMENTS (format vX.Y.Z):

1. `python tools/doctrine_gold.py check --tag $ARGUMENTS`
2. Paste the REAL output. Deploy only on "check OK"; on CHECK FAILED,
   list the findings and STOP — a broken gold chain blocks all deploys
   until repaired, and only the human can decide the repair.
