#!/usr/bin/env python3
"""Precommitted paired Brier score for exactly two contestants on matched tasks."""
import argparse, json, math, random
from pathlib import Path

def score(predictions, reveal, *, min_items=100, min_clusters=30,
          resamples=5000, seed=20261117, margin=0.01):
    if predictions.get("round_id") != reveal.get("round_id"):
        raise ValueError("round_id mismatch")
    contestants = predictions.get("contestants")
    answers = reveal.get("answers")
    clusters = reveal.get("clusters")
    if not isinstance(contestants, dict) or len(contestants) != 2:
        raise ValueError("exactly two distinct preregistered contestants required")
    if not isinstance(answers, dict) or len(answers) < min_items:
        raise ValueError("too few independently selected questions")
    if any(type(y) is not int or y not in (0, 1) for y in answers.values()):
        raise ValueError("truth values must be integer zero or one")
    names = sorted(contestants)
    ids = set(answers)
    if not isinstance(clusters,dict) or set(clusters) != ids:
        raise ValueError("every task ID needs one predeclared event cluster ID")
    if any(not isinstance(c,str) or not c.strip() for c in clusters.values()):
        raise ValueError("cluster IDs must be nonempty strings")
    groups = {}
    for qid,cluster in clusters.items():
        groups.setdefault(cluster,[]).append(qid)
    if len(groups) < min_clusters:
        raise ValueError("too few independent event clusters; paraphrases are not distinct trials")
    for name in names:
        ps=contestants[name]
        if not isinstance(ps,dict) or set(ps) != ids:
            raise ValueError("each contestant must answer exactly the same task IDs")
        if any(type(p) not in (int,float) or not math.isfinite(p) or not 0 <= p <= 1 for p in ps.values()):
            raise ValueError("each answer must be a finite probability between zero and one")
    # Equal cluster weights stop 70 paraphrases of one event from swamping 30 real events.
    cluster_losses = {
        name:[
            sum((contestants[name][q]-answers[q])**2 for q in groups[c])/len(groups[c])
            for c in sorted(groups)
        ] for name in names
    }
    means={name:sum(cluster_losses[name])/len(groups) for name in names}
    deltas=[a-b for a,b in zip(cluster_losses[names[0]],cluster_losses[names[1]])]
    rng=random.Random(seed)
    boots=sorted(sum(deltas[rng.randrange(len(deltas))] for _ in deltas)/len(deltas)
                 for _ in range(resamples))
    ci=[boots[int(.025*resamples)],boots[min(resamples-1,int(.975*resamples))]]
    winner=names[0] if ci[1] < -margin else (names[1] if ci[0]>margin else "undecided")
    return {
        "round_id":predictions["round_id"],"questions":len(ids),
        "declared_event_clusters":len(groups),
        "contestants":names,"mean_cluster_weighted_brier_loss":means,
        "paired_cluster_loss_difference_A_minus_B":means[names[0]]-means[names[1]],
        "paired_cluster_bootstrap_95pct_interval":ci,
        "practical_margin":margin, "winner":winner,
        "method":f"paired event-cluster bootstrap; {resamples} resamples; seed={seed}",
        "scope":"exactly two preregistered sessions; one fixed sample, no peeking, no multi-entrant winner",
        "caution":"Cluster independence and target-population sampling must be certified externally; this code cannot prove them."
    }

def no_duplicates(pairs):
    d={}
    for k,v in pairs:
        if k in d: raise ValueError("duplicate JSON key: "+k)
        d[k]=v
    return d

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--predictions",required=True,type=Path)
    a.add_argument("--truth",required=True,type=Path)
    a.add_argument("--min-items",type=int,default=100)
    a.add_argument("--min-clusters",type=int,default=30)
    args=a.parse_args()
    if args.min_items<2 or args.min_clusters<2:
        a.error("--min-items and --min-clusters must be at least 2")
    x=json.loads(args.predictions.read_text(),object_pairs_hook=no_duplicates)
    y=json.loads(args.truth.read_text(),object_pairs_hook=no_duplicates)
    print(json.dumps(score(x,y,min_items=args.min_items,min_clusters=args.min_clusters),
                     indent=2,sort_keys=True))

if __name__=="__main__": main()
