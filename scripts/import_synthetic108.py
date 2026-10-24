"""Import patient-only exploratory cases; never ingest model prescriptions or code."""
import argparse, ast, csv, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--csv',type=Path,required=True);p.add_argument('--jsonl',type=Path,required=True);p.add_argument('--bot',type=Path,required=True);args=p.parse_args()
with args.csv.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
records=[json.loads(line) for line in args.jsonl.read_text().splitlines() if line.strip()]
assert len({r['case_id'] for r in rows})==len(rows),'Duplicate case identifiers'
assert len(rows)==len(records),'CSV/JSONL case count mismatch'
for row,record in zip(rows,records):
 user=[turn['parts'][0]['text'] for turn in record['contents'] if turn['role']=='user']
 assert user==[row['user_turn_1_symptom'],row['user_turn_2_details']],f"Patient-turn mismatch: {row['case_id']}"
# Only the patient text is written. No teacher replies, diagnosis titles, patient
# age metadata, system instructions or medicine columns are runtime references.
clean=[{'case_id':row['case_id'],'provenance':'user-supplied Gemini-generated; clinically unreviewed','usage':'offline exploratory evaluation only','patient_turns':[row['user_turn_1_symptom'],row['user_turn_2_details']]} for row in rows]
out=ROOT/'data/evaluation/synthetic108';out.mkdir(parents=True,exist_ok=True)
(out/'patient_inputs.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in clean))
try:ast.parse(args.bot.read_text());syntax={'valid':True}
except SyntaxError as e:syntax={'valid':False,'line':e.lineno,'message':e.msg}
manifest={'case_count':len(rows),'csv_jsonl_patient_turns_match':True,'clinically_reviewed':False,'training_enabled':False,'runtime_retrieval_enabled':False,'bot_executed':False,'bot_syntax':syntax,'source_sha256':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in [args.csv,args.jsonl,args.bot]},'review_required_examples':{'CASE_003':'Child fever sponging conflicts with NHS guidance; dose not clinician verified.','CASE_066':'Fresh-burn cream advice conflicts with NHS first-aid guidance.','CASE_001':'Fixed fluid target and medicine schedule not individualised or clinically verified.'},'missing_labels':['organiser care_type','organiser urgency','clinician-reviewed prescription ground truth'],'categories_for_audit':{k:sum(r['category']==k for r in rows) for k in sorted({r['category'] for r in rows})}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'imported_patient_cases':len(clean),'teacher_answers_imported':0,'bot_syntax':syntax,'training_enabled':False}))
