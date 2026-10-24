"""Use the same prediction service as the API. Output format pending organizer confirmation."""
import argparse,csv,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from triagegrid.schemas import TriageRequest
from triagegrid.services.engine import predict
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');a=p.parse_args()
with open(a.input) as f,open(a.output,'w',newline='') as out:
 reader=csv.DictReader(f);writer=csv.DictWriter(out,fieldnames=['id','care_type','urgency','red_flags','follow_up_question']);writer.writeheader()
 for row in reader:
  loc={'lat':float(row['lat']),'lng':float(row['lng'])} if row.get('lat') and row.get('lng') else None
  r=predict(TriageRequest(user_input=row['user_input'],location=loc)).model_dump()
  writer.writerow({'id':row.get('id',''),'care_type':r['care_type'],'urgency':r['urgency'],'red_flags':json.dumps(r['red_flags']),'follow_up_question':r['follow_up_question']})
