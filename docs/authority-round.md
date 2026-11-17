# Proposal: precommitted, auditable GPT-vs-GPT round

**This is a scoring protocol proposal, not evidence that anyone has won.**

## Registration
Before contestants answer, an independent referee pre-registers the target
task population, sampling and exclusion criteria, ground-truth adjudication,
shared instructions/tool access and equal resource budget. Select 100 or more
hidden, nontrivial, objectively decidable binary propositions. Neither contestant
may add self-chosen easy tasks. Seal the questions until submissions begin.
Commit answer hashes before the truth is revealed; preserve all raw answers.

## Scoring
Each participant assigns probability p in [0,1] to each identical statement.
The outcome y is either zero or one. Score mean squared error (p-y)^2:
the mean Brier loss; lower is better. Every question counts; p=0.5 expresses
maximum uncertainty. The included standard-library scorer rejects omissions,
duplicates, nonfinite answers, and mismatched task sets.

Pairwise inference uses 5000 paired bootstrap resamples with fixed seed 20261117.
A wins if the upper 95% percentile interval for mean loss(A)-loss(B)
is below -0.01; B wins if the lower bound exceeds 0.01; otherwise the
result is 'undecided'. This is an explicitly precommitted exploratory method,
not a claim of universal 5% false-positive control for arbitrary correlated
or non-random tasks. An independent judge must accept the inference rule
and justify task sampling before the first legitimate round.

## Limitations and verification
The output compares one *pair of sessions* on a particular binary-question
distribution. Model-level differences require many runs counterbalancing
prompts/context/tools. Neither this artifact nor a single tournament establishes
global superiority. External referee must authenticate contestant identity,
timestamp/hashes, trial budgets, and preregistration; the program does not.

CLI:
  python3 tools/score_brier_round.py --predictions predictions.json --truth truth.json

Prediction JSON schema: round_id plus contestants object with exactly
two named contestant objects mapping identical task IDs to probabilities.
Truth JSON schema: same round_id and answers object mapping task IDs to 0/1.
Default minimum task count: 100. An optional --min-items is only for demos.

Tests:
  python3 -m unittest discover -s tests -p 'test_brier_round.py' -v
