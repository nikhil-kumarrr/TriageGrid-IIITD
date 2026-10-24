"""Smoke/coverage evaluation only: no gold labels, no accuracy calculation."""
from pathlib import Path
import sys,json,collections
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from triagegrid.schemas import TriageRequest,HistoryMessage
from triagegrid.services.engine import predict
from triagegrid.services.clinical_guidance import topic
rows=[json.loads(line) for line in (ROOT/'data/evaluation/synthetic108/patient_inputs.jsonl').read_text().splitlines()]
results=[]
for row in rows:
 history=[]
 for turn,text in enumerate(row['patient_turns'],1):
  try:
   response=predict(TriageRequest(user_input=text,conversation_history=history)).model_dump()
   results.append({'case_id':row['case_id'],'turn':turn,'schema_valid':True,'care_type':response['care_type'],'urgency':response['urgency'],'clarification':response['follow_up_question'] is not None,'curated_topic':topic(text)})
  except Exception as e:results.append({'case_id':row['case_id'],'turn':turn,'schema_valid':False,'error_type':type(e).__name__})
  history.append(HistoryMessage(role='user',text=text))
summary={'scope':'Local routing/schema coverage, not full LLM advice or clinical correctness','cases':len(rows),'turn_checks':len(results),'valid_schema_count':sum(r['schema_valid'] for r in results),'gold_labels_available':False,'accuracy':None,'not_for_official_scoring':True,'care_type_distribution':dict(collections.Counter(r.get('care_type') or 'clarification' for r in results)),'results':results}
(ROOT/'reports/synthetic108_evaluation.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2))
