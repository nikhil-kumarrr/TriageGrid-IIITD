"""In-sample integration audit only, not generalization accuracy."""
import sys,json,csv,time,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from triagegrid.services.engine import predict,models
from triagegrid.schemas import TriageRequest
from triagegrid.config import settings
models();times=[];rows=[]
with (settings.data_dir/'triage_dataset_flat.csv').open() as f:
 for x in csv.DictReader(f):
  req=TriageRequest(user_input=x['user_input'],location={'lat':float(x['lat']),'lng':float(x['lng'])})
  t=time.perf_counter();r=predict(req);times.append((time.perf_counter()-t)*1000)
  rows.append({'id':x['id'],'care_type':r.care_type,'urgency':r.urgency,'reference_care_type':x['care_type'] or None,'reference_urgency':x['urgency'] or None})
report={'scope':'In-sample integration audit; training rows, NOT held-out accuracy or clinical validation','requests':len(rows),'p50_ms':statistics.median(times),'p95_ms':sorted(times)[int(.95*(len(times)-1))],'care_agreement':sum(x['care_type']==x['reference_care_type'] for x in rows)/len(rows),'urgency_agreement':sum(x['urgency']==x['reference_urgency'] for x in rows)/len(rows),'schema_failures':0,'rows':rows}
Path('reports/pipeline_integration.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
