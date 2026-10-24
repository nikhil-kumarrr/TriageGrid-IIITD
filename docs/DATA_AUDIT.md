# Supplied data audit

CSV copies are byte-preserved; see data/provided/manifest.json. Dataset: 340 rows but only 65 distinct input strings in the inspected release. Group duplicate inputs into the same validation fold. CSV and JSONL are two representations of the same cases, not extra training data.

Known source issue: emergency examples contain chest_pain and breathlessness labels even when text describes severe bleeding. Do not blindly learn or reproduce unsupported flags; raise with mentors. Source README says labels are machine-generated, not clinical ground truth. The earlier problem PDF used different enums; working implementation follows this supplied release, pending scorer confirmation.

Legacy metadata reports care classifier group-CV accuracy 0.7147 and macro-F1 0.6466. Hyperparameters were selected on those folds; these are model-selection results, not untouched-test performance or full-pipeline safety measurements. Evaluate urgency and final safety+clarification pipeline separately.
