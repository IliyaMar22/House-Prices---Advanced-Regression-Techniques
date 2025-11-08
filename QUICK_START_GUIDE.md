# Quick Start Guide - House Prices Competition

## 🎯 Run in 3 Steps

### Step 1: Setup Environment
```bash
# Install dependencies
pip install numpy pandas scikit-learn xgboost lightgbm matplotlib seaborn scipy

# Or use requirements file
pip install -r requirements_house_prices.txt
```

### Step 2: Get Data
1. Go to: https://www.kaggle.com/c/house-prices-advanced-regression-techniques/data
2. Download `train.csv` and `test.csv`
3. Place files in the same directory as `house_prices_complete.py`

### Step 3: Run Script
```bash
python house_prices_complete.py
```

That's it! The script will:
- ✅ Perform EDA and create visualizations
- ✅ Preprocess and engineer features
- ✅ Train 6 different models
- ✅ Create ensemble predictions
- ✅ Generate `submission.csv`

---

## 📂 What You Get

After running, you'll have:

```
📁 Your Directory
├── house_prices_complete.py          # Main script
├── train.csv                          # Training data
├── test.csv                           # Test data
├── submission.csv                     # 🎯 SUBMIT THIS TO KAGGLE
├── saleprice_distribution.png         # EDA visualization
├── correlation_heatmap.png            # Feature correlation
├── top_features_scatter.png           # Top features vs price
└── feature_importance.png             # Model feature importance
```

---

## 🚀 For Kaggle Notebooks

If running in a Kaggle Notebook environment:

```python
# The data files are already available in Kaggle
# Just run the script directly:
!python house_prices_complete.py

# Or import as module:
import house_prices_complete
house_prices_complete.main()
```

**Pro Tip:** In Kaggle Notebooks, the data paths are typically:
- `/kaggle/input/house-prices-advanced-regression-techniques/train.csv`
- `/kaggle/input/house-prices-advanced-regression-techniques/test.csv`

Modify the `load_data()` function call in `main()` if needed:
```python
train, test = load_data(
    '/kaggle/input/house-prices-advanced-regression-techniques/train.csv',
    '/kaggle/input/house-prices-advanced-regression-techniques/test.csv'
)
```

---

## ⚡ Expected Runtime

| Stage | Approximate Time |
|-------|------------------|
| Data Loading | < 1 second |
| EDA | 5-10 seconds |
| Preprocessing | 10-20 seconds |
| Model Training | 3-10 minutes |
| Predictions | 5-10 seconds |
| **Total** | **5-15 minutes** |

*Times vary based on hardware specs*

---

## 📊 What the Script Does

### 1️⃣ Data Loading
```
Loading train.csv and test.csv
Train: 1460 samples, 81 features
Test: 1459 samples, 80 features
```

### 2️⃣ Exploratory Data Analysis
- Analyzes 38 numerical features
- Analyzes 43 categorical features  
- Identifies missing values
- Creates 4 visualization plots
- Shows correlation with target

### 3️⃣ Preprocessing
- Handles missing values in 34 features
- Removes 2-4 outliers
- One-hot encodes categorical variables
- Fixes skewness in 50+ features
- Final shape: ~300 features

### 4️⃣ Feature Engineering
Creates 30+ new features:
- Temporal: HouseAge, RemodAge, GarageAge
- Area: TotalSF, TotalPorchSF, TotalFlrSF
- Counts: TotalBath
- Binary: HasGarage, HasBasement, HasPool, etc.
- Interactions: QualGrLiv, QualBsmt, QualGarage
- Quality: Ordinal encodings + TotalQualityScore

### 5️⃣ Model Training (6 Models)
1. **Ridge Regression** (alpha tuned via GridSearch)
2. **Lasso Regression** (alpha tuned via GridSearch)
3. **Random Forest** (200 trees)
4. **XGBoost** (500 estimators)
5. **LightGBM** (500 estimators)
6. **Gradient Boosting** (300 estimators)

Each model shows cross-validation RMSE score.

### 6️⃣ Ensemble Predictions
Weighted average of all models:
- XGBoost: 30%
- LightGBM: 30%
- Ridge: 10%
- Lasso: 10%
- Random Forest: 10%
- Gradient Boosting: 10%

### 7️⃣ Submission File
Creates `submission.csv` with:
```csv
Id,SalePrice
1461,169277.3245
1462,187724.8901
...
```

---

## 🎓 Understanding the Output

### Console Output Example:
```
================================================================================
LOADING DATA
================================================================================
Training data shape: (1460, 81)
Test data shape: (1459, 80)

================================================================================
EXPLORATORY DATA ANALYSIS
================================================================================
...
Missing values: 19 features
Top correlations with SalePrice:
  OverallQual: 0.791
  GrLivArea: 0.709
  GarageCars: 0.640
  ...

================================================================================
DATA PREPROCESSING & FEATURE ENGINEERING
================================================================================
Train missing values before: 6965
Train missing values after: 0
Shape after feature engineering: (1458, 315)
...

================================================================================
MODEL TRAINING
================================================================================

--- Training Ridge Regression ---
Best alpha: 10
Best CV RMSE: 0.11523

--- Training XGBoost ---
CV RMSE: 0.12156 (+/- 0.00891)

... (more models) ...

================================================================================
ENSEMBLE PREDICTIONS
================================================================================
Ensemble predictions: mean=180921.45, std=79442.18

================================================================================
CREATING SUBMISSION
================================================================================
Submission file created: submission.csv
Shape: (1459, 2)
First few predictions:
      Id      SalePrice
0   1461  169277.324512
1   1462  187724.890123
...
```

---

## 🔍 Interpreting Results

### Cross-Validation RMSE
- **Good**: 0.11 - 0.13
- **Excellent**: < 0.11
- **Needs Improvement**: > 0.15

Lower RMSE = better predictions on log-transformed prices.

### Kaggle Leaderboard Score
After submission, you'll receive a score like `0.13456`. This is the RMSE on the public test set (about 50% of test data).

**Target Goals:**
- 🥉 **Bronze**: < 0.15 (Top 50%)
- 🥈 **Silver**: < 0.13 (Top 20%)
- 🥇 **Gold**: < 0.12 (Top 10%)

---

## 🛠 Customization Tips

### Want better performance? Try:

**1. Tune model hyperparameters more aggressively:**
```python
# In train_xgboost(), add RandomizedSearchCV
param_dist = {
    'n_estimators': [500, 1000, 1500],
    'learning_rate': [0.01, 0.03, 0.05, 0.07],
    'max_depth': [3, 4, 5, 6],
    'subsample': [0.7, 0.8, 0.9]
}
```

**2. Create more interaction features:**
```python
# In create_features()
df['QualArea'] = df['OverallQual'] * df['TotalSF']
df['QualBath'] = df['OverallQual'] * df['TotalBath']
```

**3. Adjust ensemble weights based on CV scores:**
```python
# In create_ensemble_predictions()
# Give more weight to models with lower CV RMSE
weights = {
    'xgboost': 0.40,  # If XGBoost has lowest RMSE
    'lightgbm': 0.35,
    # ... adjust others
}
```

**4. Remove low-importance features:**
```python
# After visualizing feature importance
# Keep only top 100-150 features
```

---

## ❓ FAQ

**Q: Can I run this on Google Colab?**  
A: Yes! Upload the script and data files, then run: `!python house_prices_complete.py`

**Q: How do I submit to Kaggle?**  
A: Go to the competition page → "Submit Predictions" → Upload `submission.csv`

**Q: The script is slow. How to speed up?**  
A: Reduce `n_estimators` in XGBoost/LightGBM models, or use `n_jobs=1` instead of `-1`

**Q: Can I use this script as a template for other competitions?**  
A: Absolutely! The structure is generalizable. Just modify the feature engineering section.

**Q: What if I get "memory error"?**  
A: Reduce the number of features or models, or use a machine with more RAM.

---

## 📞 Need Help?

- Check the full `HOUSE_PRICES_README.md` for detailed documentation
- Review the code comments in `house_prices_complete.py`
- Visit the Kaggle competition discussion forum
- Check Kaggle kernels for additional insights

---

**Good luck with your submission! 🚀**

