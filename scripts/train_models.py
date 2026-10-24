"""Explicit, reproducible baseline training. No auto-training on API startup."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import pandas as pd,joblib,sklearn
from sklearn.pipeline import Pipeline,FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold,cross_val_predict
from sklearn.metrics import classification_report
from triagegrid.config import settings
frame=pd.read_csv(settings.data_dir/'triage_dataset_flat.csv')
X=frame.user_input.str.strip();groups=X.str.casefold()
def pipeline():return Pipeline([('features',FeatureUnion([('word',TfidfVectorizer(token_pattern=r"[^\s.,!?;:()\"'।]+",ngram_range=(1,2),sublinear_tf=True)),('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(2,5),sublinear_tf=True))])),('classifier',LogisticRegression(C=30,max_iter=3000,class_weight='balanced',random_state=42))])
meta={'sklearn_version':sklearn.__version__,'conf_threshold':.45,'n_rows':len(frame),'n_unique_texts':groups.nunique(),'training_sha256':hashlib.sha256((settings.data_dir/'triage_dataset_flat.csv').read_bytes()).hexdigest(),'metrics_scope':'Grouped baseline classifier CV, not independent clinical validation or final pipeline performance; C inherited from prior tuning.'}
settings.model_dir.mkdir(parents=True,exist_ok=True)
for col,name in [('care_type','care_type_pipeline.pkl'),('urgency','urgency_pipeline.pkl')]:
 y=frame[col].fillna('needs_clarification')
 pred=cross_val_predict(pipeline(),X,y,groups=groups,cv=StratifiedGroupKFold(5,shuffle=True,random_state=42))
 meta[col+'_report']=classification_report(y,pred,output_dict=True,zero_division=0)
 joblib.dump(pipeline().fit(X,y),settings.model_dir/name,compress=3)
(settings.model_dir/'model_meta.json').write_text(json.dumps(meta,indent=2))
print(json.dumps({k:v for k,v in meta.items() if k.endswith('_report')},indent=2))
