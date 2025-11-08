# House Prices - Advanced Regression Techniques
## Kaggle Competition Solution

A complete, production-ready machine learning pipeline for predicting house sale prices from the Ames Housing dataset.

---

## 📋 Overview

This script provides a comprehensive solution for the Kaggle competition "House Prices – Advanced Regression Techniques". It includes:

- **Exploratory Data Analysis (EDA)** with visualizations
- **Data Preprocessing** with missing value handling
- **Feature Engineering** with 20+ new features
- **Multiple ML Models** (Ridge, Lasso, Random Forest, XGBoost, LightGBM, Gradient Boosting)
- **Hyperparameter Tuning** using GridSearchCV
- **Ensemble Methods** with weighted averaging
- **Submission File Generation** ready for Kaggle

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_house_prices.txt
```

### 2. Download Data

Download the competition data from Kaggle:
- [House Prices Competition](https://www.kaggle.com/c/house-prices-advanced-regression-techniques/data)

Required files:
- `train.csv`
- `test.csv`

Place these files in the same directory as the script.

### 3. Run the Script

```bash
python house_prices_complete.py
```

### 4. Submit to Kaggle

Upload the generated `submission.csv` file to the Kaggle competition.

---

## 📂 Output Files

The script generates several output files:

| File | Description |
|------|-------------|
| `submission.csv` | Kaggle submission file with predictions |
| `saleprice_distribution.png` | Distribution of target variable |
| `correlation_heatmap.png` | Correlation matrix of top features |
| `top_features_scatter.png` | Scatter plots of most correlated features |
| `feature_importance.png` | Feature importance from tree-based models |

---

## 🔍 Script Structure

### 1. Data Loading
```python
load_data(train_path, test_path)
```
- Loads train and test datasets
- Validates data shapes and columns

### 2. Exploratory Data Analysis
```python
perform_eda(train_df)
visualize_data(train_df, numerical_features)
```
- Descriptive statistics
- Missing value analysis
- Distribution analysis
- Correlation analysis
- Visualization generation

### 3. Data Preprocessing
```python
preprocess_data(train_df, test_df)
```
Key steps:
- **Missing Value Handling**
  - Categorical: filled with 'None' or mode
  - Numerical: filled with median or 0
  - Special handling for LotFrontage (by neighborhood)
  
- **Outlier Removal**
  - Removes houses with GrLivArea > 4000 and SalePrice < 300000

- **Categorical Encoding**
  - One-hot encoding for all categorical features
  
- **Skewness Correction**
  - Box-Cox transformation for features with |skewness| > 0.75

### 4. Feature Engineering
```python
create_features(df)
```
Creates 30+ new features:

**Temporal Features:**
- `HouseAge` = YrSold - YearBuilt
- `RemodAge` = YrSold - YearRemodAdd
- `GarageAge` = YrSold - GarageYrBlt
- `IsRemodeled` = YearBuilt != YearRemodAdd

**Area Features:**
- `TotalSF` = TotalBsmtSF + GrLivArea
- `TotalFlrSF` = 1stFlrSF + 2ndFlrSF
- `TotalPorchSF` = Sum of all porch areas

**Bathroom Features:**
- `TotalBath` = FullBath + BsmtFullBath + 0.5*(HalfBath + BsmtHalfBath)

**Binary Features:**
- `Has2ndFloor`, `HasGarage`, `HasBasement`, `HasFireplace`, `HasPool`

**Interaction Features:**
- `QualGrLiv` = OverallQual × GrLivArea
- `QualBsmt` = OverallQual × TotalBsmtSF
- `QualGarage` = OverallQual × GarageArea
- `LiveAreaRatio` = GrLivArea / TotalBsmtSF

**Quality Features:**
- Ordinal encoding for quality ratings (Ex=5, Gd=4, TA=3, Fa=2, Po=1, None=0)
- `TotalQualityScore` = Sum of all ordinal quality features

### 5. Model Training
```python
train_all_models(X_train, y_train)
```

Models trained:

| Model | Hyperparameters Tuned | CV Strategy |
|-------|----------------------|-------------|
| Ridge Regression | alpha | GridSearchCV |
| Lasso Regression | alpha | GridSearchCV |
| Random Forest | n_estimators, max_depth, min_samples_split | Default optimized |
| XGBoost | learning_rate, max_depth, subsample | Default optimized |
| LightGBM | learning_rate, max_depth, num_leaves | Default optimized |
| Gradient Boosting | learning_rate, max_depth, n_estimators | Default optimized |

**Target Transformation:**
- All models trained on log-transformed target: `np.log1p(SalePrice)`
- Predictions transformed back: `np.expm1(predictions)`

**Evaluation Metric:**
- RMSE (Root Mean Squared Error) on log-transformed predictions
- Cross-validation with 5 folds

### 6. Ensemble Predictions
```python
create_ensemble_predictions(models, X_test)
```

**Weighted Averaging:**
```python
weights = {
    'ridge': 0.10,
    'lasso': 0.10,
    'random_forest': 0.10,
    'xgboost': 0.30,
    'lightgbm': 0.30,
    'gradient_boosting': 0.10
}
```

Ensemble typically provides better generalization than individual models.

### 7. Submission Generation
```python
create_submission(test_ids, predictions, 'submission.csv')
```
- Ensures all predictions are positive
- Formats output for Kaggle submission
- Includes validation statistics

---

## 🎯 Best Practices Implemented

### ✅ Reproducibility
- Fixed random seed: `RANDOM_STATE = 42`
- Consistent data splitting and model initialization

### ✅ Code Quality
- Modular functions with clear docstrings
- Comprehensive comments throughout
- Type hints in function signatures
- Clean separation of concerns

### ✅ Data Quality
- Thorough missing value handling
- Outlier detection and removal
- Feature scaling and normalization
- Skewness correction

### ✅ Model Performance
- Multiple model architectures
- Hyperparameter optimization
- Cross-validation for reliable estimates
- Ensemble methods for improved predictions

### ✅ Monitoring & Debugging
- Extensive print statements for pipeline visibility
- Shape and statistics tracking at each step
- Visualization of data distributions and model outputs

---

## 🔧 Customization Options

### Adjust Model Weights
Modify the `weights` dictionary in `create_ensemble_predictions()`:

```python
weights = {
    'xgboost': 0.40,      # Increase XGBoost weight
    'lightgbm': 0.40,     # Increase LightGBM weight
    'ridge': 0.05,        # Decrease linear models
    # ... etc
}
```

### Add More Models
Extend the `train_all_models()` function:

```python
def train_all_models(X_train, y_train):
    models = {}
    # ... existing models ...
    
    # Add your custom model
    models['custom'] = train_custom_model(X_train, y_train)
    
    return models
```

### Modify Feature Engineering
Add custom features in `create_features()`:

```python
def create_features(df):
    df = df.copy()
    # ... existing features ...
    
    # Add your custom features
    df['MyCustomFeature'] = df['Feature1'] * df['Feature2']
    
    return df
```

### Tune Hyperparameters
Modify parameter grids in model training functions:

```python
def train_xgboost(X_train, y_train):
    # Modify these parameters
    xgb_model = xgb.XGBRegressor(
        n_estimators=1000,      # Increase trees
        learning_rate=0.03,     # Decrease learning rate
        max_depth=4,            # Adjust depth
        # ... etc
    )
```

---

## 📊 Expected Performance

With default settings, the script typically achieves:

- **Cross-validation RMSE**: ~0.11 - 0.13 (on log-transformed target)
- **Kaggle Public Leaderboard**: Top 20-30% (with proper feature engineering)
- **Training Time**: 5-15 minutes (depending on hardware)

**Note:** Performance can be improved by:
1. More aggressive hyperparameter tuning
2. Advanced feature engineering
3. Stacking/blending ensemble methods
4. External data sources

---

## 🐛 Troubleshooting

### Issue: "FileNotFoundError: train.csv not found"
**Solution:** Download data files from Kaggle and place in script directory.

### Issue: "ModuleNotFoundError: No module named 'xgboost'"
**Solution:** Install missing dependencies:
```bash
pip install -r requirements_house_prices.txt
```

### Issue: Script runs but RMSE is very high
**Solution:** Check for:
- Missing value handling errors
- Incorrect feature encoding
- Data leakage between train/test
- Target variable transformation issues

### Issue: Memory errors on large datasets
**Solution:** 
- Reduce number of trees in ensemble models
- Use `n_jobs=1` instead of `n_jobs=-1`
- Process data in chunks if possible

---

## 📈 Advanced Techniques (Optional Enhancements)

### 1. Stacking Ensemble
Instead of simple weighted averaging, use a meta-model:

```python
from sklearn.ensemble import StackingRegressor

stacking_model = StackingRegressor(
    estimators=[('ridge', ridge_model), ('xgb', xgb_model)],
    final_estimator=Ridge()
)
```

### 2. Feature Selection
Use feature importance to select top features:

```python
from sklearn.feature_selection import SelectFromModel

selector = SelectFromModel(xgb_model, threshold='median')
X_train_selected = selector.fit_transform(X_train, y_train)
```

### 3. Target Engineering
Try different target transformations:

```python
# Square root transformation
y_train_sqrt = np.sqrt(y_train)

# Box-Cox transformation
y_train_boxcox, lambda_param = stats.boxcox(y_train)
```

### 4. Cross-Validation Predictions
Generate out-of-fold predictions for better ensemble:

```python
def get_oof_predictions(model, X, y, n_folds=5):
    kfold = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    oof_preds = np.zeros(len(X))
    
    for train_idx, val_idx in kfold.split(X):
        X_train_fold, X_val_fold = X.iloc[train_idx], X.iloc[val_idx]
        y_train_fold = y.iloc[train_idx]
        
        model.fit(X_train_fold, y_train_fold)
        oof_preds[val_idx] = model.predict(X_val_fold)
    
    return oof_preds
```

---

## 📚 Additional Resources

- [Kaggle Competition Page](https://www.kaggle.com/c/house-prices-advanced-regression-techniques)
- [Comprehensive EDA Notebook](https://www.kaggle.com/pmarcelino/comprehensive-data-exploration-with-python)
- [Feature Engineering Guide](https://www.kaggle.com/c/house-prices-advanced-regression-techniques/discussion/36364)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [LightGBM Documentation](https://lightgbm.readthedocs.io/)

---

## 📝 License

This script is provided as-is for educational and competition purposes.

---

## 🤝 Contributing

Feel free to:
- Add new features
- Improve model performance
- Optimize code efficiency
- Fix bugs

---

## ⭐ Acknowledgments

- Kaggle for hosting the competition
- The amazing data science community for sharing insights
- Contributors to scikit-learn, XGBoost, and LightGBM

---

**Happy Kaggling! 🏆**

