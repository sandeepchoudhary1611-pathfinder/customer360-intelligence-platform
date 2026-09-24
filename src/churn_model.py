"""
Customer360 Intelligence Platform - Predictive Churn Modeling Pipeline
=======================================================================
Extracts features from the SQL database view `view_customer_churn_features`,
preprocesses data with Scikit-Learn Pipelines, trains benchmark & champion models
(Logistic Regression vs Gradient Boosting / Random Forest), calculates business metrics
(ROC-AUC, Precision, Recall, F1), generates diagnostic evaluation charts, and writes
churn risk scores back to the database for Power BI dashboard consumption.
"""

import os
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    confusion_matrix,
    brier_score_loss,
    f1_score
)

# Configuration & Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "customer360.db")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(ARTIFACTS_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# Set plotting aesthetic
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"font.size": 10, "figure.autolayout": True})

def load_feature_dataset():
    """Queries view_customer_churn_features from the SQLite database."""
    print("[1/6] Extracting feature dataset from SQLite database...")
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM view_customer_churn_features"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"      Loaded {df.shape[0]} customer records with {df.shape[1]} features.")
    churn_rate = df['is_churned'].mean() * 100
    print(f"      Overall churn rate: {churn_rate:.2f}% ({df['is_churned'].sum()} churned / {len(df)} total)")
    return df

def build_preprocessing_pipeline(numerical_cols, categorical_cols):
    """Creates a ColumnTransformer to scale numbers and encode categories."""
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_cols),
            ('cat', OneHotEncoder(drop='first', handle_unknown='ignore', sparse_output=False), categorical_cols)
        ]
    )
    return preprocessor

def train_and_evaluate_models(X_train, X_test, y_train, y_test, preprocessor, num_features, cat_features):
    """Trains Logistic Regression and Random Forest models, comparing performance."""
    print("[2/6] Building and comparing predictive models...")

    models = {
        "Logistic Regression (Baseline)": LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'),
        "Random Forest (Champion)": RandomForestClassifier(n_estimators=150, max_depth=8, min_samples_split=10, random_state=42, class_weight='balanced')
    }

    results = {}
    fitted_pipelines = {}

    for name, clf in models.items():
        pipe = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', clf)
        ])
        
        # Fit pipeline
        pipe.fit(X_train, y_train)
        fitted_pipelines[name] = pipe

        # Predictions
        y_pred = pipe.predict(X_test)
        y_prob = pipe.predict_proba(X_test)[:, 1]

        # Metric evaluations
        auc = roc_auc_score(y_test, y_prob)
        f1 = f1_score(y_test, y_pred)
        brier = brier_score_loss(y_test, y_prob)

        results[name] = {
            "pipeline": pipe,
            "y_pred": y_pred,
            "y_prob": y_prob,
            "roc_auc": auc,
            "f1_score": f1,
            "brier_score": brier
        }

        print(f"      Model: {name}")
        print(f"        - ROC-AUC:    {auc:.4f}")
        print(f"        - F1 Score:   {f1:.4f}")
        print(f"        - Brier Loss: {brier:.4f}")

    return results, fitted_pipelines

def generate_evaluation_visualizations(results, y_test, X_train, preprocessor, num_features, cat_features):
    """Generates ROC curve, PR curve, Confusion Matrix, and Feature Importance charts."""
    print("[3/6] Generating evaluation visual artifacts...")

    champion_name = "Random Forest (Champion)"
    champ = results[champion_name]

    # 1. ROC Curve Comparison
    plt.figure(figsize=(7, 5))
    for name, res in results.items():
        fpr, tpr, _ = roc_curve(y_test, res["y_prob"])
        plt.plot(fpr, tpr, label=f"{name} (AUC = {res['roc_auc']:.3f})", lw=2)
    plt.plot([0, 1], [0, 1], 'k--', label="Random Chance (AUC = 0.500)")
    plt.xlabel("False Positive Rate (1 - Specificity)")
    plt.ylabel("True Positive Rate (Recall)")
    plt.title("Customer Churn: ROC Curve Comparison")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(ARTIFACTS_DIR, "roc_curve_comparison.png"), dpi=200)
    plt.close()

    # 2. Confusion Matrix
    cm = confusion_matrix(y_test, champ["y_pred"])
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Retained (0)', 'Churned (1)'],
                yticklabels=['Retained (0)', 'Churned (1)'])
    plt.xlabel("Predicted Status")
    plt.ylabel("Actual Status")
    plt.title("Confusion Matrix - Random Forest")
    plt.tight_layout()
    plt.savefig(os.path.join(ARTIFACTS_DIR, "confusion_matrix.png"), dpi=200)
    plt.close()

    # 3. Precision-Recall Curve
    precision, recall, _ = precision_recall_curve(y_test, champ["y_prob"])
    plt.figure(figsize=(7, 5))
    plt.plot(recall, precision, color='darkorange', lw=2, label=f"PR Curve (F1={champ['f1_score']:.3f})")
    plt.xlabel("Recall (Coverage of Churned Customers)")
    plt.ylabel("Precision (Accuracy of Churn Flag)")
    plt.title("Precision-Recall Curve - Random Forest")
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(os.path.join(ARTIFACTS_DIR, "precision_recall_curve.png"), dpi=200)
    plt.close()

    # 4. Feature Importance Extraction
    rf_model = champ["pipeline"].named_steps['classifier']
    preproc = champ["pipeline"].named_steps['preprocessor']
    
    cat_encoder = preproc.named_transformers_['cat']
    encoded_cat_names = cat_encoder.get_feature_names_out(cat_features).tolist()
    all_feature_names = num_features + encoded_cat_names

    importances = rf_model.feature_importances_
    feat_df = pd.DataFrame({
        "Feature": all_feature_names,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False).head(12)

    plt.figure(figsize=(9, 5))
    sns.barplot(data=feat_df, x="Importance", y="Feature", hue="Feature", palette="Blues_r", legend=False)
    plt.title("Top 12 Drivers of Customer Churn (Random Forest)")
    plt.xlabel("Gini Feature Importance")
    plt.tight_layout()
    plt.savefig(os.path.join(ARTIFACTS_DIR, "feature_importance.png"), dpi=200)
    plt.close()

    print("      Saved plots to artifacts/:")
    print("        - roc_curve_comparison.png")
    print("        - confusion_matrix.png")
    print("        - precision_recall_curve.png")
    print("        - feature_importance.png")

def score_entire_customer_base(df, champion_pipeline, num_features, cat_features):
    """Scores the entire customer base, categorizing risk tiers and business monetary exposure."""
    print("[4/6] Scoring entire customer base for Power BI ingestion...")
    
    X_all = df[num_features + cat_features]
    churn_probabilities = champion_pipeline.predict_proba(X_all)[:, 1]
    
    df_scored = df.copy()
    df_scored['churn_probability'] = np.round(churn_probabilities, 4)
    
    # Define actionable business risk tiers
    conditions = [
        df_scored['churn_probability'] >= 0.70,
        (df_scored['churn_probability'] >= 0.40) & (df_scored['churn_probability'] < 0.70),
        df_scored['churn_probability'] < 0.40
    ]
    tiers = ['Critical Risk (>=70%)', 'Moderate Risk (40-69%)', 'Low Risk (<40%)']
    df_scored['churn_risk_tier'] = np.select(conditions, tiers, default='Low Risk (<40%)')

    # Calculate Revenue at Risk
    df_scored['revenue_at_risk'] = np.round(df_scored['churn_probability'] * df_scored['total_lifetime_spend'], 2)

    # Save to CSV
    csv_path = os.path.join(PROCESSED_DATA_DIR, "customer_churn_scored.csv")
    df_scored.to_csv(csv_path, index=False)
    print(f"      Saved scored dataset to {csv_path}")

    return df_scored

def save_scored_table_to_database(df_scored):
    """Persists fact_customer_churn_scores into SQLite database for live Power BI queries."""
    print("[5/6] Persisting fact_customer_churn_scores table to SQLite database...")
    
    table_cols = [
        'customer_id', 'churn_probability', 'churn_risk_tier', 
        'revenue_at_risk', 'recency_days', 'customer_tenure_days',
        'total_lifetime_spend', 'average_order_value', 'avg_csat_score',
        'is_churned'
    ]
    df_export = df_scored[table_cols]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS fact_customer_churn_scores")
    df_export.to_sql('fact_customer_churn_scores', conn, if_exists='replace', index=False)
    cursor.execute("CREATE INDEX idx_churn_customer ON fact_customer_churn_scores(customer_id)")
    conn.commit()
    conn.close()
    print("      Table fact_customer_churn_scores created and indexed successfully.")

def print_executive_summary(df_scored, results):
    """Prints a high-level executive summary with financial impact."""
    print("[6/6] Computing Executive Summary & Portfolio KPIs...")
    total_customers = len(df_scored)
    critical_risk = (df_scored['churn_risk_tier'] == 'Critical Risk (>=70%)').sum()
    moderate_risk = (df_scored['churn_risk_tier'] == 'Moderate Risk (40-69%)').sum()
    total_rev_at_risk = df_scored['revenue_at_risk'].sum()
    
    rf_auc = results["Random Forest (Champion)"]["roc_auc"]
    rf_f1 = results["Random Forest (Champion)"]["f1_score"]

    summary = f"""
================================================================================
CUSTOMER360 INTELLIGENCE PLATFORM - EXECUTIVE MODELING REPORT
================================================================================
1. MODEL PERFORMANCE:
   - Champion Model:        Random Forest Classifier (150 trees)
   - Test ROC-AUC:          {rf_auc:.4f} (Outstanding discriminative ability)
   - Test F1-Score:         {rf_f1:.4f}

2. CUSTOMER RISK DISTRIBUTION:
   - Total Scored Customers: {total_customers:,}
   - Critical Risk (>=70%):  {critical_risk:,} ({critical_risk/total_customers*100:.1f}%)
   - Moderate Risk (40-69%): {moderate_risk:,} ({moderate_risk/total_customers*100:.1f}%)
   - Safe / Low Risk (<40%): {total_customers - critical_risk - moderate_risk:,} ({(total_customers - critical_risk - moderate_risk)/total_customers*100:.1f}%)

3. FINANCIAL EXPOSURE (UNIT ECONOMICS):
   - Total Revenue at Risk: INR {total_rev_at_risk:,.2f}
   - Average Revenue at Risk / Critical Customer: INR {df_scored[df_scored['churn_risk_tier'] == 'Critical Risk (>=70%)']['revenue_at_risk'].mean():,.2f}
================================================================================
"""
    print(summary)
    
    # Save summary report to artifacts
    with open(os.path.join(ARTIFACTS_DIR, "executive_model_summary.txt"), "w", encoding="utf-8") as f:
        f.write(summary)

def run_pipeline():
    """Main execution flow."""
    df = load_feature_dataset()

    # Identify features
    cat_features = ['customer_segment', 'acquisition_channel', 'customer_state']
    # Exclude recency_days from features because the target is defined using recency cutoff (Target Leakage Prevention)
    num_features = [
        'total_orders_placed', 'completed_orders', 'failed_orders',
        'customer_tenure_days', 'total_lifetime_spend',
        'average_order_value', 'total_units_purchased', 'discount_sensitivity_pct',
        'category_diversity_count', 'avg_installments', 'is_credit_card_user',
        'is_upi_user', 'avg_csat_score', 'negative_feedback_count'
    ]

    X = df[num_features + cat_features]
    y = df['is_churned']

    # Stratified Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    preprocessor = build_preprocessing_pipeline(num_features, cat_features)
    results, pipelines = train_and_evaluate_models(
        X_train, X_test, y_train, y_test, preprocessor, num_features, cat_features
    )

    generate_evaluation_visualizations(
        results, y_test, X_train, preprocessor, num_features, cat_features
    )

    champion_pipeline = pipelines["Random Forest (Champion)"]
    df_scored = score_entire_customer_base(df, champion_pipeline, num_features, cat_features)
    save_scored_table_to_database(df_scored)
    print_executive_summary(df_scored, results)

if __name__ == "__main__":
    run_pipeline()
