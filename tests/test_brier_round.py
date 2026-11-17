import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from score_brier_round import score,no_duplicates
class BrierRoundTests(unittest.TestCase):
 def make(self,a,b,y=1):
  ids=[f"hidden-{i:03}" for i in range(100)]
  return ({"round_id":"round1","contestants":{"A":{k:a for k in ids},"B":{k:b for k in ids}}},
          {"round_id":"round1","answers":{k:y for k in ids},"clusters":{k:k for k in ids}})
 def test_perfect_beats_uncertain(self):
  p,t=self.make(1,.5);r=score(p,t,resamples=100)
  self.assertEqual(r["winner"],"A")
  self.assertEqual(r["mean_cluster_weighted_brier_loss"]["A"],0)
  self.assertEqual(r["mean_cluster_weighted_brier_loss"]["B"],.25)
 def test_confident_error_loses(self):
  p,t=self.make(0,.8)
  self.assertEqual(score(p,t,resamples=100)["winner"],"B")
 def test_identical_probs_undecided(self):
  p,t=self.make(.7,.7)
  self.assertEqual(score(p,t,resamples=100)["winner"],"undecided")
 def test_missing_task_rejected(self):
  p,t=self.make(1,.5);p["contestants"]["B"].pop(next(iter(t["answers"])))
  with self.assertRaisesRegex(ValueError,"same task IDs"):score(p,t,resamples=100)
 def test_invalid_probability(self):
  p,t=self.make(1,.5);p["contestants"]["B"][next(iter(t["answers"]))]=float("nan")
  with self.assertRaisesRegex(ValueError,"finite probability"):score(p,t,resamples=100)
 def test_too_few_tasks(self):
  p,t=self.make(1,.5);t["answers"].pop(next(iter(t["answers"])))
  with self.assertRaisesRegex(ValueError,"too few"):score(p,t,resamples=100)
 def test_bogus_truth_value(self):
  p,t=self.make(1,.5);t["answers"][next(iter(t["answers"]))]=True
  with self.assertRaisesRegex(ValueError,"integer zero or one"):score(p,t,resamples=100)
 def test_duplicate_keys_rejected(self):
  with self.assertRaisesRegex(ValueError,"duplicate JSON"):no_duplicates([("X",1),("X",2)])
 def test_one_hidden_event_100_paraphrases_not_100_trials(self):
  p,t=self.make(.99,.5);t["clusters"]={k:"same-event" for k in t["answers"]}
  with self.assertRaisesRegex(ValueError,"too few independent event clusters"):
   score(p,t,resamples=100)
 def test_missing_cluster_rejected(self):
  p,t=self.make(1,.5);t["clusters"].pop(next(iter(t["clusters"])))
  with self.assertRaisesRegex(ValueError,"predeclared event cluster"):
   score(p,t,resamples=100)
 def test_paraphrases_do_not_outweigh_independent_events(self):
  p,t=self.make(0,1)
  for i in range(70):
   k=f"hidden-{i:03}"
   p["contestants"]["A"][k]=1
   p["contestants"]["B"][k]=0
   t["clusters"][k]="one-event"
  r=score(p,t,resamples=100)
  self.assertEqual(r["declared_event_clusters"],31)
  self.assertEqual(r["winner"],"B")
if __name__=="__main__":unittest.main()
