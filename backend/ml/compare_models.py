from pathlib import Path
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

BASE=Path(__file__).resolve().parent
DATA=BASE/"data"/"synthetic_startups.csv"
FEATURES=["problem_clarity","solution_differentiation","market_demand","competition_intensity",
"founder_experience","team_completeness","traction_level","revenue_model_clarity","financial_runway_months",
"customer_validation_count","monthly_revenue","monthly_burn","funding_needed","target_market_size_millions",
"has_prototype","has_competitor_research"]
def main():
    if not DATA.exists(): raise SystemExit("Run python -m ml.generate_demo_data first.")
    df=pd.read_csv(DATA); X=df[FEATURES]; y=df["positive_outcome"]
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,random_state=42,stratify=y)
    models={"Random Forest":RandomForestClassifier(n_estimators=200,max_depth=12,min_samples_leaf=4,random_state=42,n_jobs=-1),
            "Gradient Boosting":GradientBoostingClassifier(random_state=42),
            "Hist Gradient Boosting":HistGradientBoostingClassifier(random_state=42)}
    try:
        from xgboost import XGBClassifier
        models["XGBoost"]=XGBClassifier(n_estimators=250,max_depth=5,learning_rate=.05,subsample=.85,colsample_bytree=.85,
                                         eval_metric="logloss",random_state=42,n_jobs=-1)
    except ImportError:
        print("XGBoost not installed; skipping it. Install requirements-ml.txt to include it.")
    results=[]
    for name,model in models.items():
        model.fit(Xtr,ytr); pred=model.predict(Xte); prob=model.predict_proba(Xte)[:,1]
        results.append({"model":name,"accuracy":round(accuracy_score(yte,pred),4),
            "precision":round(precision_score(yte,pred,zero_division=0),4),
            "recall":round(recall_score(yte,pred,zero_division=0),4),
            "f1":round(f1_score(yte,pred,zero_division=0),4),"roc_auc":round(roc_auc_score(yte,prob),4)})
    print(json.dumps({"data":"synthetic demonstration data only","results":results},indent=2))
    print("Do not select a model for real use from synthetic-data scores.")
if __name__=="__main__": main()
