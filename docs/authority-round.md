# Proposal: precommitted, auditable GPT-vs-GPT round

**This is a scoring protocol proposal, not evidence that anyone has won.**

## Registration before viewing answers
An independent referee preregisters a clearly scoped target population, sampling
and exclusion criteria, objectively adjudicated binary answer keys, common prompts
and tool access, equal CPU/time/resource budgets, and a specific pair of contestants.
The fixed held-out set must have at least 100 nontrivial tasks from **at least 30
independently selected event clusters**. Predeclare which tasks share a latent
cause or underlying outcome: 100 paraphrases about one event count as **one
cluster**, not 100 independent trials. Cluster IDs are supplied in the sealed
answer-key JSON. No contestant-selected easy tasks or post-hoc deletions.
The referee, not code, must justify genuine between-cluster independence; 30
declared labels do not magically imply 30 independent random outcomes.

Commit predictions' hashes with verifiable timestamps BEFORE revealing the
truth. Retain raw contestant answers, exact sampling code/seed, and all failures.

## Scoring
Each contestant provides p in [0,1] for every identical binary proposition;
the ground truth y is 0 or 1. Evaluate Brier loss (p-y)^2. Average losses WITHIN
each independent event cluster, then weight clusters EQUALLY, so repetitive
paraphrases cannot determine a win. Pair the two cluster losses on identical
events. A 5000-draw fixed-seed paired percentile bootstrap (seed 20261117)
produces a 95% interval for mean cluster loss(A) minus mean cluster loss(B).
A wins only if the upper interval endpoint is less than -0.01; B wins only if
the lower bound is greater than +0.01; otherwise the output is UNDECIDED.

This is a **fixed-sample paired two-contestant** exploratory decision rule.
A bootstrap percentile interval is not a universal 5% false-positive guarantee
when event clusters are themselves correlated, selected nonrandomly, or
the result is checked repeatedly. Specify the sample size and single time of
evaluation before the round. Do not stop early when the result looks good.

## No unadjusted 8-way championship
The implementation intentionally accepts **exactly two preregistered entrants**
and cannot score a field of eight or select the best after looking at results.
A future multi-entrant tournament must preregister entrant set, each comparison,
familywise error control (such as Holm adjustment), and a valid rule for
sequential looks (or forbid them). Do not naively declare a winner after 28
unadjusted pairwise 5% tests; leaderboards are not statistical proof.

## Scope
A single round compares two *sessions* on the selected binary-task population.
A model-level comparison requires repeated independent sessions with counterbalanced
prompts, tool conditions, and context; universal GPT authority is not established.
No real blind round has been performed.

## Inputs and tests
  python3 tools/score_brier_round.py --predictions predictions.json --truth truth.json

Predictions JSON: round_id, plus contestants map containing two names, each mapping
all task IDs to probabilities. Truth JSON: same round_id, answers map of all task
IDs to 0/1, clusters map of **all identical task IDs** to event-cluster strings.
Default minimums: 100 questions, 30 declared event clusters. Lower minimums are
only for isolated demonstrations, never a legitimate scored round.

  python3 -m unittest discover -s tests -p 'test_brier_round.py' -v
