from pathlib import Path
import numpy as np
import pandas as pd

SEED, N_ROWS = 42, 10_000
OUT = Path(__file__).resolve().parent / "data" / "synthetic_startups.csv"

def main():
    rng = np.random.default_rng(SEED)
    df = pd.DataFrame({
        "problem_clarity":rng.integers(1,6,N_ROWS),
        "solution_differentiation":rng.integers(1,6,N_ROWS),
        "market_demand":rng.integers(1,6,N_ROWS),
        "competition_intensity":rng.integers(1,6,N_ROWS),
        "founder_experience":rng.integers(1,6,N_ROWS),
        "team_completeness":rng.integers(1,6,N_ROWS),
        "traction_level":rng.integers(1,6,N_ROWS),
        "revenue_model_clarity":rng.integers(1,6,N_ROWS),
        "financial_runway_months":rng.integers(0,37,N_ROWS),
        "customer_validation_count":rng.integers(0,301,N_ROWS),
        "monthly_revenue":np.round(rng.lognormal(8,2,N_ROWS),2),
        "monthly_burn":np.round(rng.lognormal(8.5,1.5,N_ROWS),2),
        "funding_needed":np.round(rng.lognormal(12,1.5,N_ROWS),2),
        "target_market_size_millions":np.round(rng.lognormal(4,1.2,N_ROWS),2),
        "has_prototype":rng.integers(0,2,N_ROWS),
        "has_competitor_research":rng.integers(0,2,N_ROWS)
    })
    latent = (0.55*df.problem_clarity + 0.65*df.solution_differentiation +
              0.70*df.market_demand - 0.45*df.competition_intensity +
              0.35*df.founder_experience + 0.35*df.team_completeness +
              0.75*df.traction_level + 0.50*df.revenue_model_clarity +
              0.06*df.financial_runway_months +
              0.006*np.minimum(df.customer_validation_count,100) +
              0.8*df.has_prototype + 0.6*df.has_competitor_research +
              rng.normal(0,1.8,N_ROWS))
    df["positive_outcome"] = (latent >= latent.quantile(.58)).astype(int)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(OUT,index=False)
    print(f"Created {len(df):,} synthetic records at {OUT}")
    print("Synthetic labels follow an artificial rule; they are not observed business outcomes.")
if __name__ == "__main__": main()
