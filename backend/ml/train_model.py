from pathlib import Path
import argparse, json
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

BASE = Path(__file__).resolve().parent
FEATURES = ["problem_clarity","solution_differentiation","market_demand","competition_intensity",
 "founder_experience","team_completeness","traction_level","revenue_model_clarity",
 "financial_runway_months","customer_validation_count","monthly_revenue","monthly_burn",
 "funding_needed","target_market_size_millions","has_prototype","has_competitor_research"]
TARGET = "positive_outcome"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default=str(BASE/"data"/"synthetic_startups.csv"),help="CSV with feature columns and observed 0/1 target label")
    parser.add_argument("--real-data",action="store_true",help="Marks the artifact as real-labeled data; only use when this is genuinely true")
    args=parser.parse_args()
    path=Path(args.input)
    if not path.exists(): raise SystemExit(f"CSV not found: {path}. Generate demo data or provide a CSV.")
    df=pd.read_csv(path)
    missing=[c for c in FEATURES+[TARGET] if c not in df.columns]
    if missing: raise SystemExit("Missing required columns: "+", ".join(missing))
    df=df[FEATURES+[TARGET]].dropna()
    if not set(df[TARGET].unique()).issubset({0,1}) or df[TARGET].nunique()!=2:
        raise SystemExit("positive_outcome must contain both classes coded as 0 and 1.")
    X,y=df[FEATURES],df[TARGET].astype(int)
    X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=.2,random_state=42,stratify=y)
    model=RandomForestClassifier(n_estimators=250,max_depth=12,min_samples_leaf=4,class_weight="balanced",random_state=42,n_jobs=-1)
    model.fit(X_train,y_train)
    pred=model.predict(X_test); prob=model.predict_proba(X_test)[:,1]
    metrics={"rows_used":int(len(df)),"train_rows":len(X_train),"test_rows":len(X_test),
      "accuracy":round(float(accuracy_score(y_test,pred)),4),
      "precision":round(float(precision_score(y_test,pred,zero_division=0)),4),
      "recall":round(float(recall_score(y_test,pred,zero_division=0)),4),
      "f1":round(float(f1_score(y_test,pred,zero_division=0)),4),
      "roc_auc":round(float(roc_auc_score(y_test,prob)),4),
      "data_provenance":"real-labeled" if args.real_data else "synthetic-or-unverified",
      "warning":"Metrics only mean what the label and dataset quality support. Synthetic results are not real-world evidence."}
    out=BASE.parent/"artifacts"; out.mkdir(parents=True,exist_ok=True)
    joblib.dump(model,out/"venture_model.joblib")
    (out/"model_metadata.json").write_text(json.dumps({"features":FEATURES,**metrics},indent=2),encoding="utf-8")
    print(json.dumps(metrics,indent=2))
    print(f"Model saved: {out/'venture_model.joblib'}")
    if not args.real_data: print("DEMO ONLY: artifact must not be described as a validated real-world model.")
if __name__=="__main__": main()
