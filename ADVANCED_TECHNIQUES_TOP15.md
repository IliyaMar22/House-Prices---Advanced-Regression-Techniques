# Advanced Techniques for Top 15% Leaderboard

## 🎯 Goal: Push from Top 30% → Top 15%

Current CV RMSE: **0.11223** (Lasso)  
Target CV RMSE: **<0.11** (for Top 15%)

**Strategy:** Add 5-7 advanced techniques that each contribute 0.001-0.003 RMSE improvement.

---

## 🏆 **Priority Ranking (Based on Impact)**

### **Tier 1: MUST IMPLEMENT** (Biggest Impact)

#### 1. **Stacking Ensemble** 🥇
**Expected Improvement:** 0.01 - 0.02 RMSE  
**Difficulty:** Medium  
**Why:** Combines models in a smarter way than averaging

```python
from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import Ridge

# Use your best models as base estimators
stacking_model = StackingRegressor(
    estimators=[
        ('lasso', lasso_model),
        ('ridge', ridge_model),
        ('xgb', xgb_model),
        ('lgb', lgb_model)
    ],
    final_estimator=Ridge(alpha=0.1),  # Meta-learner
    cv=10  # More folds = better generalization
)

stacking_model.fit(train_processed, np.log1p(target))
stacking_pred = np.expm1(stacking_model.predict(test_processed))
```

**Why This Works:**
- Learns optimal combination weights from data
- Final Ridge layer smooths predictions
- Often 0.01-0.02 RMSE better than simple averaging

---

#### 2. **Target Encoding for Neighborhood** 🥈  
**Expected Improvement:** 0.005 - 0.01 RMSE  
**Difficulty:** Easy  
**Why:** Neighborhood is highly predictive but has 25+ categories

```python
from category_encoders import TargetEncoder

# Target encode high-cardinality categoricals
high_card_features = ['Neighborhood', 'Exterior1st', 'Exterior2nd']

target_encoder = TargetEncoder(cols=high_card_features)
train_encoded = target_encoder.fit_transform(train_processed, target)
test_encoded = target_encoder.transform(test_processed)
```

**Why This Works:**
- Captures neighborhood price patterns directly
- Much more informative than one-hot (which creates 25+ sparse features)
- Handles rare categories gracefully

**⚠️ Warning:** Add regularization to prevent overfitting:
```python
target_encoder = TargetEncoder(cols=high_card_features, 
                               smoothing=10.0,  # Regularization
                               min_samples_leaf=5)
```

---

#### 3. **Feature Selection (Remove Noise)** 🥉  
**Expected Improvement:** 0.003 - 0.008 RMSE  
**Difficulty:** Easy  
**Why:** Your 300+ features likely include noise

```python
from sklearn.feature_selection import SelectKBest, f_regression

# Method 1: Select top K features
selector = SelectKBest(score_func=f_regression, k=150)
train_selected = selector.fit_transform(train_processed, np.log1p(target))
test_selected = selector.transform(test_processed)

# Method 2: Use Lasso for feature selection (it's already doing this!)
important_features = np.abs(lasso_model.coef_) > 0.001
print(f"Lasso selected {important_features.sum()} features")
train_selected = train_processed.iloc[:, important_features]
test_selected = test_processed.iloc[:, important_features]
```

**Why This Works:**
- Removes features that add noise without signal
- Reduces overfitting
- Makes models faster

---

### **Tier 2: RECOMMENDED** (Good Impact)

#### 4. **RobustScaler Instead of Standard/Box-Cox** 📊  
**Expected Improvement:** 0.002 - 0.005 RMSE  
**Difficulty:** Very Easy  
**Why:** More resistant to outliers

```python
from sklearn.preprocessing import RobustScaler

scaler = RobustScaler()
train_scaled = scaler.fit_transform(train_processed)
test_scaled = scaler.transform(test_processed)
```

**Why This Works:**
- Uses median and IQR instead of mean and std
- Less affected by extreme values
- Better for house prices (which have outliers)

---

#### 5. **Polynomial Features for Top Interactions** 🔄  
**Expected Improvement:** 0.002 - 0.004 RMSE  
**Difficulty:** Medium  
**Why:** Captures non-linear relationships

```python
from sklearn.preprocessing import PolynomialFeatures

# ONLY use for top 5-10 features (to avoid explosion)
top_features = ['OverallQual', 'GrLivArea', 'TotalBsmtSF', 'GarageCars', '1stFlrSF']

poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
train_poly = poly.fit_transform(train_processed[top_features])
test_poly = poly.transform(test_processed[top_features])

# Combine with original features
train_final = np.hstack([train_processed, train_poly])
test_final = np.hstack([test_processed, test_poly])
```

**Why This Works:**
- Captures interactions like OverallQual × GrLivArea
- You already created some manually, but this creates ALL combinations
- Limited to top features to avoid overfitting

---

#### 6. **QuantileTransformer for Extreme Skewness** 📈  
**Expected Improvement:** 0.001 - 0.003 RMSE  
**Difficulty:** Easy  
**Why:** Better than Box-Cox for highly skewed features

```python
from sklearn.preprocessing import QuantileTransformer

qt = QuantileTransformer(output_distribution='normal', n_quantiles=1000)

# Apply to extremely skewed features only
extremely_skewed = train_processed.columns[
    train_processed.apply(lambda x: abs(skew(x.dropna())) > 2.0)
]

train_qt = train_processed.copy()
test_qt = test_processed.copy()

for feature in extremely_skewed:
    train_qt[feature] = qt.fit_transform(train_processed[[feature]])
    test_qt[feature] = qt.transform(test_processed[[feature]])
```

**Why This Works:**
- Maps to uniform distribution, then to normal
- Handles extreme values better than log/box-cox
- Good for features like LotArea, LotFrontage

---

### **Tier 3: OPTIONAL** (Nice to Have)

#### 7. **Leave-One-Out Encoding** 🎲  
**Expected Improvement:** 0.001 - 0.002 RMSE  
**Difficulty:** Medium  
**Why:** Even better than target encoding sometimes

```python
from category_encoders import LeaveOneOutEncoder

loo_encoder = LeaveOneOutEncoder(cols=['Neighborhood'])
train_loo = loo_encoder.fit_transform(train_processed, target)
test_loo = loo_encoder.transform(test_processed)
```

**Why This Works:**
- Prevents data leakage (doesn't use same row's target)
- More robust than target encoding
- Great for high-cardinality features

---

#### 8. **KNN Imputation** 🔍  
**Expected Improvement:** 0.001 - 0.002 RMSE  
**Difficulty:** Easy  
**Why:** Smarter than median/mode imputation

```python
from sklearn.impute import KNNImputer

# Before filling missing values
imputer = KNNImputer(n_neighbors=5)
train_imputed = imputer.fit_transform(train_with_missing)
test_imputed = imputer.transform(test_with_missing)
```

**Why This Works:**
- Uses similar houses to impute values
- More accurate than simple median
- Especially good for LotFrontage

**⚠️ Note:** You're already handling missing values well, so this is optional.

---

#### 9. **PCA for Correlated Features** 🎨  
**Expected Improvement:** 0.001 - 0.002 RMSE  
**Difficulty:** Medium  
**Why:** Reduces multicollinearity

```python
from sklearn.decomposition import PCA

# Apply PCA to groups of highly correlated features
pca = PCA(n_components=0.95)  # Keep 95% of variance
train_pca = pca.fit_transform(train_processed)
test_pca = pca.transform(test_processed)
```

**Why This Works:**
- Combines correlated features into fewer components
- Reduces noise
- Can help with regularization

**⚠️ Warning:** Linear models (Lasso/Ridge) already handle multicollinearity well, so this is less critical.

---

## 🎯 **RECOMMENDED IMPLEMENTATION ORDER**

### **Phase 1: Quick Wins** (Do First)
1. ✅ **Target Encoding** (30 minutes, big impact)
2. ✅ **Feature Selection** (20 minutes, good impact)
3. ✅ **RobustScaler** (10 minutes, easy win)

**Expected improvement:** 0.01 - 0.02 RMSE  
**Time investment:** 1 hour  
**Result:** Should push you to ~0.10-0.11 CV RMSE

---

### **Phase 2: Advanced** (Do If Phase 1 Works)
4. ✅ **Stacking Ensemble** (1 hour, biggest single impact)
5. ✅ **Polynomial Features** (30 minutes, moderate impact)
6. ✅ **QuantileTransformer** (20 minutes, small impact)

**Expected improvement:** 0.015 - 0.03 RMSE  
**Time investment:** 2 hours  
**Result:** Should push you to ~0.09-0.10 CV RMSE → **Top 10-15%**

---

### **Phase 3: Fine-Tuning** (Optional)
7. Leave-One-Out Encoding
8. KNN Imputation
9. PCA

**Expected improvement:** 0.002 - 0.005 RMSE  
**Time investment:** 1-2 hours  
**Result:** Squeeze out last bit of performance

---

## 📝 **Complete Implementation Code**

Here's a complete implementation combining the top techniques:

```python
# ============================================================================
# PHASE 1: ADVANCED PREPROCESSING
# ============================================================================

import numpy as np
import pandas as pd
from category_encoders import TargetEncoder, LeaveOneOutEncoder
from sklearn.preprocessing import RobustScaler, QuantileTransformer, PolynomialFeatures
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import Ridge, Lasso
import xgboost as xgb
import lightgbm as lgb

# Assuming you have train_processed, test_processed, target from your existing code

# ============================================================================
# 1. TARGET ENCODING
# ============================================================================
print("Step 1: Target Encoding for high-cardinality features")

# Identify high-cardinality categorical features
high_card_features = ['Neighborhood', 'Exterior1st', 'Exterior2nd', 'MSSubClass']

# Target encode with regularization
target_encoder = TargetEncoder(
    cols=high_card_features,
    smoothing=10.0,  # Regularization
    min_samples_leaf=5
)

# Fit on training data only
train_encoded = target_encoder.fit_transform(train_processed, target)
test_encoded = target_encoder.transform(test_processed)

print(f"Target encoding complete. Shape: {train_encoded.shape}")

# ============================================================================
# 2. ROBUST SCALING
# ============================================================================
print("\nStep 2: Robust Scaling")

# Get numerical features only
numerical_features = train_encoded.select_dtypes(include=[np.number]).columns

scaler = RobustScaler()
train_scaled = train_encoded.copy()
test_scaled = test_encoded.copy()

train_scaled[numerical_features] = scaler.fit_transform(train_encoded[numerical_features])
test_scaled[numerical_features] = scaler.transform(test_encoded[numerical_features])

print(f"Robust scaling complete")

# ============================================================================
# 3. POLYNOMIAL FEATURES (Top 5 features only)
# ============================================================================
print("\nStep 3: Creating polynomial interactions")

top_features = ['OverallQual', 'GrLivArea', 'TotalBsmtSF', 'GarageCars', 'TotalSF']
# Make sure these features exist after encoding
top_features = [f for f in top_features if f in train_scaled.columns]

poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
train_poly = poly.fit_transform(train_scaled[top_features])
test_poly = poly.transform(test_scaled[top_features])

# Create feature names
poly_feature_names = [f"poly_{i}" for i in range(train_poly.shape[1])]

# Combine with original
train_with_poly = pd.concat([
    train_scaled.reset_index(drop=True),
    pd.DataFrame(train_poly, columns=poly_feature_names)
], axis=1)

test_with_poly = pd.concat([
    test_scaled.reset_index(drop=True),
    pd.DataFrame(test_poly, columns=poly_feature_names)
], axis=1)

print(f"Polynomial features added. New shape: {train_with_poly.shape}")

# ============================================================================
# 4. FEATURE SELECTION
# ============================================================================
print("\nStep 4: Feature Selection")

# Select top 150 features using correlation with target
selector = SelectKBest(score_func=f_regression, k=min(150, train_with_poly.shape[1]))
train_selected = selector.fit_transform(train_with_poly, np.log1p(target))
test_selected = selector.transform(test_with_poly)

# Get selected feature names
selected_features_mask = selector.get_support()
selected_feature_names = train_with_poly.columns[selected_features_mask]

print(f"Selected {train_selected.shape[1]} features out of {train_with_poly.shape[1]}")
print(f"Top 10 selected features: {list(selected_feature_names[:10])}")

# Convert back to DataFrame for easier handling
train_final = pd.DataFrame(train_selected, columns=selected_feature_names)
test_final = pd.DataFrame(test_selected, columns=selected_feature_names)

# ============================================================================
# 5. TRAIN MODELS
# ============================================================================
print("\n" + "="*80)
print("TRAINING MODELS WITH ADVANCED PREPROCESSING")
print("="*80)

y_train_log = np.log1p(target)

# Train base models
print("\nTraining base models...")

# Lasso (your best model)
lasso_advanced = Lasso(alpha=0.0003, max_iter=50000, tol=0.001, random_state=42)
lasso_advanced.fit(train_final, y_train_log)
print("✅ Lasso trained")

# Ridge
ridge_advanced = Ridge(alpha=15, random_state=42)
ridge_advanced.fit(train_final, y_train_log)
print("✅ Ridge trained")

# XGBoost
xgb_advanced = xgb.XGBRegressor(
    objective='reg:squarederror',
    n_estimators=1000,
    learning_rate=0.03,
    max_depth=3,
    min_child_weight=3,
    subsample=0.8,
    colsample_bytree=0.8,
    gamma=0,
    reg_alpha=0.001,
    reg_lambda=1,
    random_state=42,
    n_jobs=-1,
    verbosity=0
)
xgb_advanced.fit(train_final, y_train_log)
print("✅ XGBoost trained")

# LightGBM
lgb_advanced = lgb.LGBMRegressor(
    objective='regression',
    n_estimators=1000,
    learning_rate=0.03,
    max_depth=6,
    num_leaves=31,
    min_child_samples=20,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.001,
    reg_lambda=1,
    random_state=42,
    n_jobs=-1,
    verbose=-1
)
lgb_advanced.fit(train_final, y_train_log)
print("✅ LightGBM trained")

# ============================================================================
# 6. STACKING ENSEMBLE (THE GAME-CHANGER!)
# ============================================================================
print("\n" + "="*80)
print("CREATING STACKING ENSEMBLE")
print("="*80)

stacking_model = StackingRegressor(
    estimators=[
        ('lasso', lasso_advanced),
        ('ridge', ridge_advanced),
        ('xgb', xgb_advanced),
        ('lgb', lgb_advanced)
    ],
    final_estimator=Ridge(alpha=0.1),  # Meta-learner
    cv=10,  # 10-fold CV for robustness
    n_jobs=-1
)

print("Training stacking ensemble (this may take a few minutes)...")
stacking_model.fit(train_final, y_train_log)
print("✅ Stacking ensemble trained!")

# ============================================================================
# 7. GENERATE PREDICTIONS
# ============================================================================
print("\n" + "="*80)
print("GENERATING PREDICTIONS")
print("="*80)

# Stacking predictions (RECOMMENDED)
stacking_pred_log = stacking_model.predict(test_final)
stacking_pred = np.expm1(stacking_pred_log)
stacking_pred = np.maximum(stacking_pred, 0)

print(f"Stacking predictions: mean=${stacking_pred.mean():,.2f}, std=${stacking_pred.std():,.2f}")

# Individual model predictions for comparison
lasso_pred = np.expm1(lasso_advanced.predict(test_final))
ridge_pred = np.expm1(ridge_advanced.predict(test_final))
xgb_pred = np.expm1(xgb_advanced.predict(test_final))
lgb_pred = np.expm1(lgb_advanced.predict(test_final))

# Weighted ensemble (backup option)
weights = {'lasso': 0.25, 'ridge': 0.20, 'xgb': 0.30, 'lgb': 0.25}
weighted_pred = (weights['lasso'] * lasso_pred + 
                 weights['ridge'] * ridge_pred + 
                 weights['xgb'] * xgb_pred + 
                 weights['lgb'] * lgb_pred)

print(f"Weighted predictions: mean=${weighted_pred.mean():,.2f}, std=${weighted_pred.std():,.2f}")

# ============================================================================
# 8. CREATE SUBMISSIONS
# ============================================================================
print("\n" + "="*80)
print("CREATING SUBMISSION FILES")
print("="*80)

# Submission 1: Stacking (RECOMMENDED FOR TOP 15%)
submission_stacking = pd.DataFrame({
    'Id': test_id,
    'SalePrice': stacking_pred
})
submission_stacking.to_csv('submission_stacking_advanced.csv', index=False)
print("✅ 1. submission_stacking_advanced.csv (TOP 15% TARGET)")

# Submission 2: Weighted ensemble with advanced preprocessing
submission_weighted = pd.DataFrame({
    'Id': test_id,
    'SalePrice': weighted_pred
})
submission_weighted.to_csv('submission_weighted_advanced.csv', index=False)
print("✅ 2. submission_weighted_advanced.csv (BACKUP)")

# Submission 3: Lasso only with advanced preprocessing
submission_lasso = pd.DataFrame({
    'Id': test_id,
    'SalePrice': np.maximum(lasso_pred, 0)
})
submission_lasso.to_csv('submission_lasso_advanced.csv', index=False)
print("✅ 3. submission_lasso_advanced.csv (BASELINE)")

print("\n" + "="*80)
print("✅ ADVANCED PIPELINE COMPLETE!")
print("="*80)
print("\n🎯 Expected Results:")
print("   Stacking Ensemble: RMSE ~0.10-0.11 (TOP 15%)")
print("   Weighted Ensemble: RMSE ~0.11-0.12 (TOP 20-30%)")
print("   Lasso Advanced: RMSE ~0.11-0.12 (TOP 20-30%)")
print("\n📤 Submit 'submission_stacking_advanced.csv' first!")
```

---

## 📊 **Expected Performance Breakdown**

| Technique | RMSE Improvement | Cumulative RMSE | Leaderboard Position |
|-----------|------------------|-----------------|----------------------|
| **Baseline** | - | 0.11223 | Top 30% |
| + Target Encoding | -0.005 | 0.10723 | Top 25% |
| + Feature Selection | -0.003 | 0.10423 | Top 20% |
| + RobustScaler | -0.002 | 0.10223 | Top 18% |
| + Polynomial Features | -0.003 | 0.09923 | Top 16% |
| + **Stacking Ensemble** | -0.010 | **0.08923** | **Top 12-15%** 🎯 |

**Total Expected Improvement:** 0.023 RMSE  
**Final Target:** Top 15% (RMSE ~0.09-0.10)

---

## ⚠️ **Important Warnings**

### 1. **Overfitting Risk**
With all these techniques, you risk overfitting:

**Prevention:**
- Use 10-fold CV in stacking (not 5)
- Add regularization to target encoding (`smoothing=10.0`)
- Keep polynomial features limited to top 5-10 features
- Use feature selection to remove noise

### 2. **Computation Time**
Stacking with 10-fold CV can take 10-20 minutes:

**Solutions:**
- Reduce CV folds to 5 (faster but less robust)
- Use fewer base estimators
- Run on GPU if available

### 3. **Data Leakage**
Target encoding can leak if not done carefully:

**Prevention:**
- ALWAYS use `fit_transform` on train, `transform` on test
- Use LeaveOneOut encoder for extra safety
- Add smoothing/regularization

---

## 🎓 **Learning Points**

### **What Makes These Techniques Powerful:**

1. **Target Encoding**
   - Captures neighborhood price patterns directly
   - 10x more informative than one-hot for high-cardinality features

2. **Stacking**
   - Learns optimal combination from data (not hand-tuned)
   - Meta-learner (Ridge) smooths predictions
   - Typically 0.01-0.02 RMSE better than averaging

3. **Feature Selection**
   - Removes noisy features that confuse models
   - Lasso at 0.11223 suggests you have good features, but removing weak ones helps

4. **Robust Scaling**
   - House prices have outliers (mansions, etc.)
   - RobustScaler handles these better than StandardScaler

5. **Polynomial Features**
   - OverallQual × GrLivArea is highly predictive
   - But only for top features (to avoid overfitting)

---

## 🚀 **Next Steps**

### **Immediate:**
1. Implement Phase 1 (Target Encoding + Feature Selection + RobustScaler)
2. Retrain models and check CV scores
3. If CV improves, submit to Kaggle

### **If Phase 1 Works:**
4. Add Stacking Ensemble
5. Add Polynomial Features
6. Submit stacking ensemble to Kaggle

### **Fine-Tuning:**
7. Adjust stacking meta-learner (try ElasticNet instead of Ridge)
8. Tune regularization parameters
9. Experiment with different feature selection thresholds

---

## 🏆 **Success Criteria**

**You'll know you're on track to Top 15% when:**
- ✅ CV RMSE drops below 0.10
- ✅ Stacking outperforms simple weighted average by 0.01+
- ✅ Public leaderboard score is 0.11-0.12

**If you hit these metrics, you're in Top 15% territory!** 🎉

---

## 📞 **Troubleshooting**

**Q: My CV score got worse after adding these techniques**  
A: You're likely overfitting. Try:
- Increase regularization in target encoding
- Reduce polynomial degree to 2
- Use fewer features in feature selection (try k=100 instead of 150)

**Q: Stacking is taking forever**  
A: Reduce CV folds from 10 to 5, or use fewer estimators

**Q: Target encoding isn't helping**  
A: You might already have good encodings from one-hot. Try LeaveOneOut instead.

---

**Good luck reaching Top 15%! You've got this! 🚀**

