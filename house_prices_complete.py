"""
House Prices - Advanced Regression Techniques
Kaggle Competition Solution

This script provides a complete, reproducible pipeline for predicting house sale prices
from the Ames Housing dataset. It includes data preprocessing, feature engineering,
model training, hyperparameter tuning, ensemble methods, and submission generation.

Author: Advanced ML Pipeline
Date: 2025-11-08
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from scipy import stats
from scipy.stats import skew, norm
from scipy.special import boxcox1p

# Scikit-learn imports
from sklearn.model_selection import KFold, cross_val_score, GridSearchCV, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline

# Advanced models
import xgboost as xgb
import lightgbm as lgb

# Optional: category encoders
try:
    from category_encoders import TargetEncoder
    CATEGORY_ENCODERS_AVAILABLE = True
except ImportError:
    CATEGORY_ENCODERS_AVAILABLE = False
    print("Warning: category_encoders not available. Using one-hot encoding only.")

# Configuration
warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Set random seed for reproducibility
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# ==================== DATA LOADING ====================

def load_data(train_path='train.csv', test_path='test.csv'):
    """
    Load training and test datasets from CSV files.
    
    Args:
        train_path (str): Path to training data CSV
        test_path (str): Path to test data CSV
    
    Returns:
        tuple: (train_df, test_df)
    """
    print("=" * 80)
    print("LOADING DATA")
    print("=" * 80)
    
    try:
        train = pd.read_csv(train_path)
        test = pd.read_csv(test_path)
        
        print(f"Training data shape: {train.shape}")
        print(f"Test data shape: {test.shape}")
        print(f"\nTraining columns: {train.shape[1]}")
        print(f"Test columns: {test.shape[1]}")
        
        return train, test
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure train.csv and test.csv are in the working directory.")
        raise


# ==================== EXPLORATORY DATA ANALYSIS ====================

def perform_eda(train_df):
    """
    Perform exploratory data analysis on the training dataset.
    
    Args:
        train_df (pd.DataFrame): Training dataset
    """
    print("\n" + "=" * 80)
    print("EXPLORATORY DATA ANALYSIS")
    print("=" * 80)
    
    # Basic statistics
    print("\n--- Dataset Info ---")
    print(train_df.info())
    
    print("\n--- Target Variable (SalePrice) Statistics ---")
    print(train_df['SalePrice'].describe())
    
    # Missing values analysis
    print("\n--- Missing Values Analysis ---")
    missing = train_df.isnull().sum()
    missing_pct = 100 * missing / len(train_df)
    missing_table = pd.concat([missing, missing_pct], axis=1, 
                              keys=['Missing Count', 'Percentage'])
    missing_table = missing_table[missing_table['Missing Count'] > 0].sort_values(
        'Percentage', ascending=False)
    
    print(f"\nFeatures with missing values: {len(missing_table)}")
    print(missing_table.head(20))
    
    # Numerical vs Categorical features
    numerical_features = train_df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = train_df.select_dtypes(include=['object']).columns.tolist()
    
    print(f"\n--- Feature Types ---")
    print(f"Numerical features: {len(numerical_features)}")
    print(f"Categorical features: {len(categorical_features)}")
    
    # Target variable distribution
    print("\n--- Target Variable Distribution ---")
    print(f"Skewness: {train_df['SalePrice'].skew():.4f}")
    print(f"Kurtosis: {train_df['SalePrice'].kurt():.4f}")
    
    # Visualizations
    visualize_data(train_df, numerical_features)
    
    return numerical_features, categorical_features


def visualize_data(train_df, numerical_features):
    """
    Create visualizations for EDA.
    
    Args:
        train_df (pd.DataFrame): Training dataset
        numerical_features (list): List of numerical feature names
    """
    print("\n--- Creating Visualizations ---")
    
    # Figure 1: SalePrice distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Original distribution
    sns.histplot(train_df['SalePrice'], kde=True, ax=axes[0])
    axes[0].set_title('SalePrice Distribution', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('SalePrice')
    
    # Log-transformed distribution
    sns.histplot(np.log1p(train_df['SalePrice']), kde=True, ax=axes[1], color='green')
    axes[1].set_title('Log-Transformed SalePrice Distribution', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Log(SalePrice)')
    
    plt.tight_layout()
    plt.savefig('saleprice_distribution.png', dpi=100, bbox_inches='tight')
    print("Saved: saleprice_distribution.png")
    plt.close()
    
    # Figure 2: Correlation with SalePrice
    if 'SalePrice' in train_df.columns:
        correlations = train_df[numerical_features].corr()['SalePrice'].sort_values(ascending=False)
        top_features = correlations.head(11).index.tolist()  # Top 10 + SalePrice itself
        
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(train_df[top_features].corr(), annot=True, fmt='.2f', 
                    cmap='coolwarm', center=0, ax=ax)
        ax.set_title('Top 10 Features Correlation Heatmap', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('correlation_heatmap.png', dpi=100, bbox_inches='tight')
        print("Saved: correlation_heatmap.png")
        plt.close()
        
        # Figure 3: Top correlated features scatter plots
        top_features_scatter = correlations.head(6).index.tolist()[1:]  # Exclude SalePrice
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        for idx, feature in enumerate(top_features_scatter):
            if feature != 'SalePrice':
                axes[idx].scatter(train_df[feature], train_df['SalePrice'], alpha=0.5)
                axes[idx].set_xlabel(feature)
                axes[idx].set_ylabel('SalePrice')
                axes[idx].set_title(f'{feature} vs SalePrice\n(Corr: {correlations[feature]:.3f})')
        
        plt.tight_layout()
        plt.savefig('top_features_scatter.png', dpi=100, bbox_inches='tight')
        print("Saved: top_features_scatter.png")
        plt.close()
    
    print("Visualizations complete.\n")


# ==================== DATA PREPROCESSING ====================

def handle_missing_values(df, is_train=True):
    """
    Handle missing values in the dataset.
    
    Args:
        df (pd.DataFrame): Input dataframe
        is_train (bool): Whether this is training data
    
    Returns:
        pd.DataFrame: Dataframe with missing values handled
    """
    df = df.copy()
    
    # Features where missing means 'None'
    none_features = ['Alley', 'BsmtQual', 'BsmtCond', 'BsmtExposure', 'BsmtFinType1', 
                     'BsmtFinType2', 'FireplaceQu', 'GarageType', 'GarageFinish', 
                     'GarageQual', 'GarageCond', 'PoolQC', 'Fence', 'MiscFeature']
    
    for feature in none_features:
        if feature in df.columns:
            df[feature] = df[feature].fillna('None')
    
    # Features where missing means 0
    zero_features = ['BsmtFinSF1', 'BsmtFinSF2', 'BsmtUnfSF', 'TotalBsmtSF', 
                     'BsmtFullBath', 'BsmtHalfBath', 'GarageCars', 'GarageArea',
                     'MasVnrArea']
    
    for feature in zero_features:
        if feature in df.columns:
            df[feature] = df[feature].fillna(0)
    
    # Categorical features - fill with mode or 'None'
    categorical_features = df.select_dtypes(include=['object']).columns
    for feature in categorical_features:
        if df[feature].isnull().sum() > 0:
            df[feature] = df[feature].fillna(df[feature].mode()[0] if len(df[feature].mode()) > 0 else 'None')
    
    # Numerical features - fill with median
    numerical_features = df.select_dtypes(include=[np.number]).columns
    for feature in numerical_features:
        if df[feature].isnull().sum() > 0:
            df[feature] = df[feature].fillna(df[feature].median())
    
    # Special cases
    if 'LotFrontage' in df.columns:
        # Fill LotFrontage by neighborhood median
        df['LotFrontage'] = df.groupby('Neighborhood')['LotFrontage'].transform(
            lambda x: x.fillna(x.median()))
    
    if 'MSZoning' in df.columns:
        df['MSZoning'] = df['MSZoning'].fillna(df['MSZoning'].mode()[0])
    
    if 'Utilities' in df.columns:
        df['Utilities'] = df['Utilities'].fillna('AllPub')
    
    if 'Functional' in df.columns:
        df['Functional'] = df['Functional'].fillna('Typ')
    
    if 'Electrical' in df.columns:
        df['Electrical'] = df['Electrical'].fillna(df['Electrical'].mode()[0])
    
    if 'KitchenQual' in df.columns:
        df['KitchenQual'] = df['KitchenQual'].fillna(df['KitchenQual'].mode()[0])
    
    if 'Exterior1st' in df.columns:
        df['Exterior1st'] = df['Exterior1st'].fillna(df['Exterior1st'].mode()[0])
    
    if 'Exterior2nd' in df.columns:
        df['Exterior2nd'] = df['Exterior2nd'].fillna(df['Exterior2nd'].mode()[0])
    
    if 'SaleType' in df.columns:
        df['SaleType'] = df['SaleType'].fillna(df['SaleType'].mode()[0])
    
    if 'MasVnrType' in df.columns:
        df['MasVnrType'] = df['MasVnrType'].fillna('None')
    
    if 'GarageYrBlt' in df.columns:
        df['GarageYrBlt'] = df['GarageYrBlt'].fillna(df['YearBuilt'])
    
    return df


def create_features(df):
    """
    Create new features through feature engineering.
    
    Args:
        df (pd.DataFrame): Input dataframe
    
    Returns:
        pd.DataFrame: Dataframe with new features
    """
    df = df.copy()
    
    # Temporal features
    if 'YearBuilt' in df.columns and 'YrSold' in df.columns:
        df['HouseAge'] = df['YrSold'] - df['YearBuilt']
        df['HouseAge'] = df['HouseAge'].apply(lambda x: max(x, 0))  # No negative ages
    
    if 'YearRemodAdd' in df.columns and 'YrSold' in df.columns:
        df['RemodAge'] = df['YrSold'] - df['YearRemodAdd']
        df['RemodAge'] = df['RemodAge'].apply(lambda x: max(x, 0))
    
    if 'YearBuilt' in df.columns and 'YearRemodAdd' in df.columns:
        df['IsRemodeled'] = (df['YearBuilt'] != df['YearRemodAdd']).astype(int)
    
    if 'GarageYrBlt' in df.columns and 'YrSold' in df.columns:
        df['GarageAge'] = df['YrSold'] - df['GarageYrBlt']
        df['GarageAge'] = df['GarageAge'].apply(lambda x: max(x, 0))
    
    # Total square footage features
    if 'TotalBsmtSF' in df.columns and 'GrLivArea' in df.columns:
        df['TotalSF'] = df['TotalBsmtSF'] + df['GrLivArea']
    
    if '1stFlrSF' in df.columns and '2ndFlrSF' in df.columns:
        df['TotalFlrSF'] = df['1stFlrSF'] + df['2ndFlrSF']
    
    # Bathroom features
    if all(col in df.columns for col in ['FullBath', 'HalfBath', 'BsmtFullBath', 'BsmtHalfBath']):
        df['TotalBath'] = (df['FullBath'] + 
                          df['BsmtFullBath'] + 
                          0.5 * df['HalfBath'] + 
                          0.5 * df['BsmtHalfBath'])
    
    # Porch features
    porch_features = ['OpenPorchSF', 'EnclosedPorch', '3SsnPorch', 'ScreenPorch']
    if all(col in df.columns for col in porch_features):
        df['TotalPorchSF'] = df[porch_features].sum(axis=1)
    
    # Binary features
    if '2ndFlrSF' in df.columns:
        df['Has2ndFloor'] = (df['2ndFlrSF'] > 0).astype(int)
    
    if 'GarageArea' in df.columns:
        df['HasGarage'] = (df['GarageArea'] > 0).astype(int)
    
    if 'TotalBsmtSF' in df.columns:
        df['HasBasement'] = (df['TotalBsmtSF'] > 0).astype(int)
    
    if 'Fireplaces' in df.columns:
        df['HasFireplace'] = (df['Fireplaces'] > 0).astype(int)
    
    if 'PoolArea' in df.columns:
        df['HasPool'] = (df['PoolArea'] > 0).astype(int)
    
    # Interaction features
    if 'OverallQual' in df.columns and 'GrLivArea' in df.columns:
        df['QualGrLiv'] = df['OverallQual'] * df['GrLivArea']
    
    if 'OverallQual' in df.columns and 'TotalBsmtSF' in df.columns:
        df['QualBsmt'] = df['OverallQual'] * df['TotalBsmtSF']
    
    if 'OverallQual' in df.columns and 'GarageArea' in df.columns:
        df['QualGarage'] = df['OverallQual'] * df['GarageArea']
    
    if 'GrLivArea' in df.columns and 'TotalBsmtSF' in df.columns:
        df['LiveAreaRatio'] = df['GrLivArea'] / (df['TotalBsmtSF'] + 1)  # +1 to avoid division by zero
    
    # Quality-based features
    quality_features = ['ExterQual', 'ExterCond', 'BsmtQual', 'BsmtCond', 
                       'HeatingQC', 'KitchenQual', 'FireplaceQu', 'GarageQual', 'GarageCond']
    
    quality_map = {'Ex': 5, 'Gd': 4, 'TA': 3, 'Fa': 2, 'Po': 1, 'None': 0}
    
    for feature in quality_features:
        if feature in df.columns:
            df[f'{feature}_Ordinal'] = df[feature].map(quality_map).fillna(0)
    
    # Overall quality score
    ordinal_cols = [col for col in df.columns if col.endswith('_Ordinal')]
    if len(ordinal_cols) > 0:
        df['TotalQualityScore'] = df[ordinal_cols].sum(axis=1)
    
    return df


def encode_categorical_features(train_df, test_df, target_col='SalePrice'):
    """
    Encode categorical features using one-hot encoding.
    
    Args:
        train_df (pd.DataFrame): Training dataframe
        test_df (pd.DataFrame): Test dataframe
        target_col (str): Name of target column
    
    Returns:
        tuple: (encoded_train, encoded_test)
    """
    train_df = train_df.copy()
    test_df = test_df.copy()
    
    # Get categorical columns
    categorical_features = train_df.select_dtypes(include=['object']).columns.tolist()
    
    print(f"\nEncoding {len(categorical_features)} categorical features...")
    
    # Combine train and test for consistent encoding
    train_len = len(train_df)
    combined = pd.concat([train_df, test_df], axis=0, sort=False)
    
    # One-hot encoding
    combined = pd.get_dummies(combined, columns=categorical_features, drop_first=True)
    
    # Split back
    train_encoded = combined.iloc[:train_len, :]
    test_encoded = combined.iloc[train_len:, :]
    
    print(f"Shape after encoding - Train: {train_encoded.shape}, Test: {test_encoded.shape}")
    
    return train_encoded, test_encoded


def fix_skewness(train_df, test_df, threshold=0.75):
    """
    Fix skewed numerical features using Box-Cox transformation.
    
    Args:
        train_df (pd.DataFrame): Training dataframe
        test_df (pd.DataFrame): Test dataframe
        threshold (float): Skewness threshold for transformation
    
    Returns:
        tuple: (transformed_train, transformed_test)
    """
    train_df = train_df.copy()
    test_df = test_df.copy()
    
    # Get numerical features (exclude Id and target)
    numerical_features = train_df.select_dtypes(include=[np.number]).columns.tolist()
    numerical_features = [f for f in numerical_features if f not in ['Id', 'SalePrice']]
    
    # Calculate skewness
    skewed_features = train_df[numerical_features].apply(lambda x: skew(x.dropna()))
    skewed_features = skewed_features[abs(skewed_features) > threshold]
    
    print(f"\nFound {len(skewed_features)} skewed features (threshold={threshold})")
    
    # Apply Box-Cox transformation
    for feature in skewed_features.index:
        if feature in train_df.columns and feature in test_df.columns:
            # Add 1 to avoid log(0) issues, then apply boxcox1p (Box-Cox with lambda)
            train_df[feature] = boxcox1p(train_df[feature], 0.15)
            test_df[feature] = boxcox1p(test_df[feature], 0.15)
    
    return train_df, test_df


def preprocess_data(train_df, test_df):
    """
    Complete preprocessing pipeline.
    
    Args:
        train_df (pd.DataFrame): Training dataframe
        test_df (pd.DataFrame): Test dataframe
    
    Returns:
        tuple: (processed_train, processed_test, target, test_ids)
    """
    print("\n" + "=" * 80)
    print("DATA PREPROCESSING & FEATURE ENGINEERING")
    print("=" * 80)
    
    # Save IDs and target
    train_id = train_df['Id'].copy()
    test_id = test_df['Id'].copy()
    target = train_df['SalePrice'].copy()
    
    # Drop Id from both datasets
    train_df = train_df.drop(['Id'], axis=1)
    test_df = test_df.drop(['Id'], axis=1)
    
    # Remove outliers from training data
    print("\n--- Removing Outliers ---")
    # Based on Kaggle analysis, remove houses with GrLivArea > 4000 and low price
    outlier_indices = train_df[(train_df['GrLivArea'] > 4000) & (train_df['SalePrice'] < 300000)].index
    train_df = train_df.drop(outlier_indices)
    target = target.drop(outlier_indices)
    print(f"Removed {len(outlier_indices)} outlier(s)")
    
    # Separate target from train
    train_df = train_df.drop(['SalePrice'], axis=1)
    
    # Handle missing values
    print("\n--- Handling Missing Values ---")
    print(f"Train missing values before: {train_df.isnull().sum().sum()}")
    print(f"Test missing values before: {test_df.isnull().sum().sum()}")
    
    train_df = handle_missing_values(train_df, is_train=True)
    test_df = handle_missing_values(test_df, is_train=False)
    
    print(f"Train missing values after: {train_df.isnull().sum().sum()}")
    print(f"Test missing values after: {test_df.isnull().sum().sum()}")
    
    # Feature engineering
    print("\n--- Feature Engineering ---")
    train_df = create_features(train_df)
    test_df = create_features(test_df)
    print(f"Shape after feature engineering - Train: {train_df.shape}, Test: {test_df.shape}")
    
    # Encode categorical features
    print("\n--- Encoding Categorical Features ---")
    train_df, test_df = encode_categorical_features(train_df, test_df)
    
    # Fix skewness
    print("\n--- Fixing Skewed Features ---")
    train_df, test_df = fix_skewness(train_df, test_df, threshold=0.75)
    
    # Ensure both datasets have the same columns
    # Get common columns
    common_cols = train_df.columns.intersection(test_df.columns)
    train_df = train_df[common_cols]
    test_df = test_df[common_cols]
    
    print(f"\nFinal shape - Train: {train_df.shape}, Test: {test_df.shape}")
    print(f"Missing values - Train: {train_df.isnull().sum().sum()}, Test: {test_df.isnull().sum().sum()}")
    
    # Fill any remaining NaN values
    train_df = train_df.fillna(0)
    test_df = test_df.fillna(0)
    
    return train_df, test_df, target, test_id


# ==================== MODEL TRAINING & EVALUATION ====================

def rmse_cv(model, X, y, cv=5):
    """
    Calculate cross-validated RMSE score.
    
    Args:
        model: ML model
        X (pd.DataFrame): Feature matrix
        y (pd.Series): Target variable
        cv (int): Number of cross-validation folds
    
    Returns:
        tuple: (mean_rmse, std_rmse)
    """
    # Use negative MSE (sklearn convention), then convert to RMSE
    kfold = KFold(n_splits=cv, shuffle=True, random_state=RANDOM_STATE)
    rmse_scores = np.sqrt(-cross_val_score(model, X, y, 
                                           scoring='neg_mean_squared_error',
                                           cv=kfold))
    return rmse_scores.mean(), rmse_scores.std()


def train_ridge(X_train, y_train):
    """
    Train Ridge Regression model with hyperparameter tuning.
    
    Args:
        X_train (pd.DataFrame): Training features
        y_train (pd.Series): Training target
    
    Returns:
        trained model
    """
    print("\n--- Training Ridge Regression ---")
    
    # Log transform target
    y_train_log = np.log1p(y_train)
    
    # Hyperparameter tuning
    alphas = [0.05, 0.1, 0.3, 1, 3, 5, 10, 15, 20, 30, 50, 75, 100]
    
    ridge = Ridge(random_state=RANDOM_STATE)
    grid_search = GridSearchCV(ridge, {'alpha': alphas}, 
                              cv=5, scoring='neg_mean_squared_error',
                              verbose=0, n_jobs=-1)
    grid_search.fit(X_train, y_train_log)
    
    best_alpha = grid_search.best_params_['alpha']
    best_score = np.sqrt(-grid_search.best_score_)
    
    print(f"Best alpha: {best_alpha}")
    print(f"Best CV RMSE: {best_score:.5f}")
    
    return grid_search.best_estimator_


def train_lasso(X_train, y_train):
    """
    Train Lasso Regression model with hyperparameter tuning.
    
    Args:
        X_train (pd.DataFrame): Training features
        y_train (pd.Series): Training target
    
    Returns:
        trained model
    """
    print("\n--- Training Lasso Regression ---")
    
    # Log transform target
    y_train_log = np.log1p(y_train)
    
    # Hyperparameter tuning
    alphas = [0.0001, 0.0003, 0.0005, 0.0007, 0.001, 0.003, 0.005, 0.007, 0.01]
    
    # Increased max_iter to 50000 and adjusted tol to ensure convergence
    lasso = Lasso(random_state=RANDOM_STATE, max_iter=50000, tol=0.001)
    grid_search = GridSearchCV(lasso, {'alpha': alphas}, 
                              cv=5, scoring='neg_mean_squared_error',
                              verbose=0, n_jobs=-1)
    grid_search.fit(X_train, y_train_log)
    
    best_alpha = grid_search.best_params_['alpha']
    best_score = np.sqrt(-grid_search.best_score_)
    
    print(f"Best alpha: {best_alpha}")
    print(f"Best CV RMSE: {best_score:.5f}")
    
    return grid_search.best_estimator_


def train_random_forest(X_train, y_train):
    """
    Train Random Forest model.
    
    Args:
        X_train (pd.DataFrame): Training features
        y_train (pd.Series): Training target
    
    Returns:
        trained model
    """
    print("\n--- Training Random Forest ---")
    
    # Log transform target
    y_train_log = np.log1p(y_train)
    
    # Train with reasonable default parameters (full grid search would be too slow)
    rf = RandomForestRegressor(n_estimators=200,
                               max_depth=15,
                               min_samples_split=10,
                               min_samples_leaf=4,
                               max_features='sqrt',
                               random_state=RANDOM_STATE,
                               n_jobs=-1,
                               verbose=0)
    
    rf.fit(X_train, y_train_log)
    
    # Calculate CV score
    cv_mean, cv_std = rmse_cv(rf, X_train, y_train_log, cv=5)
    print(f"CV RMSE: {cv_mean:.5f} (+/- {cv_std:.5f})")
    
    return rf


def train_xgboost(X_train, y_train):
    """
    Train XGBoost model with hyperparameter tuning.
    
    Args:
        X_train (pd.DataFrame): Training features
        y_train (pd.Series): Training target
    
    Returns:
        trained model
    """
    print("\n--- Training XGBoost ---")
    
    # Log transform target
    y_train_log = np.log1p(y_train)
    
    # Define model with good default parameters
    xgb_model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=500,
        learning_rate=0.05,
        max_depth=3,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        gamma=0,
        reg_alpha=0.001,
        reg_lambda=1,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbosity=0
    )
    
    # Train model
    xgb_model.fit(X_train, y_train_log,
                  eval_set=[(X_train, y_train_log)],
                  verbose=False)
    
    # Calculate CV score
    cv_mean, cv_std = rmse_cv(xgb_model, X_train, y_train_log, cv=5)
    print(f"CV RMSE: {cv_mean:.5f} (+/- {cv_std:.5f})")
    
    return xgb_model


def train_lightgbm(X_train, y_train):
    """
    Train LightGBM model.
    
    Args:
        X_train (pd.DataFrame): Training features
        y_train (pd.Series): Training target
    
    Returns:
        trained model
    """
    print("\n--- Training LightGBM ---")
    
    # Log transform target
    y_train_log = np.log1p(y_train)
    
    # Define model
    lgb_model = lgb.LGBMRegressor(
        objective='regression',
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.001,
        reg_lambda=1,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=-1
    )
    
    # Train model
    lgb_model.fit(X_train, y_train_log)
    
    # Calculate CV score
    cv_mean, cv_std = rmse_cv(lgb_model, X_train, y_train_log, cv=5)
    print(f"CV RMSE: {cv_mean:.5f} (+/- {cv_std:.5f})")
    
    return lgb_model


def train_gradient_boosting(X_train, y_train):
    """
    Train Gradient Boosting model.
    
    Args:
        X_train (pd.DataFrame): Training features
        y_train (pd.Series): Training target
    
    Returns:
        trained model
    """
    print("\n--- Training Gradient Boosting ---")
    
    # Log transform target
    y_train_log = np.log1p(y_train)
    
    # Define model
    gb_model = GradientBoostingRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=4,
        min_samples_split=10,
        min_samples_leaf=4,
        subsample=0.8,
        max_features='sqrt',
        random_state=RANDOM_STATE,
        verbose=0
    )
    
    # Train model
    gb_model.fit(X_train, y_train_log)
    
    # Calculate CV score
    cv_mean, cv_std = rmse_cv(gb_model, X_train, y_train_log, cv=5)
    print(f"CV RMSE: {cv_mean:.5f} (+/- {cv_std:.5f})")
    
    return gb_model


def train_all_models(X_train, y_train):
    """
    Train all models and return them in a dictionary.
    
    Args:
        X_train (pd.DataFrame): Training features
        y_train (pd.Series): Training target
    
    Returns:
        dict: Dictionary of trained models
    """
    print("\n" + "=" * 80)
    print("MODEL TRAINING")
    print("=" * 80)
    
    models = {}
    
    # Train Ridge
    models['ridge'] = train_ridge(X_train, y_train)
    
    # Train Lasso
    models['lasso'] = train_lasso(X_train, y_train)
    
    # Train Random Forest
    models['random_forest'] = train_random_forest(X_train, y_train)
    
    # Train XGBoost
    models['xgboost'] = train_xgboost(X_train, y_train)
    
    # Train LightGBM
    models['lightgbm'] = train_lightgbm(X_train, y_train)
    
    # Train Gradient Boosting
    models['gradient_boosting'] = train_gradient_boosting(X_train, y_train)
    
    return models


# ==================== ENSEMBLE & PREDICTIONS ====================

def create_ensemble_predictions(models, X_test):
    """
    Create ensemble predictions using weighted averaging.
    
    Args:
        models (dict): Dictionary of trained models
        X_test (pd.DataFrame): Test features
    
    Returns:
        np.array: Ensemble predictions
    """
    print("\n" + "=" * 80)
    print("ENSEMBLE PREDICTIONS")
    print("=" * 80)
    
    # Get predictions from each model
    predictions = {}
    
    for name, model in models.items():
        pred = model.predict(X_test)
        predictions[name] = np.expm1(pred)  # Reverse log transformation
        print(f"{name}: mean={predictions[name].mean():.2f}, std={predictions[name].std():.2f}")
    
    # Weighted ensemble (weights based on typical performance)
    weights = {
        'ridge': 0.10,
        'lasso': 0.10,
        'random_forest': 0.10,
        'xgboost': 0.30,
        'lightgbm': 0.30,
        'gradient_boosting': 0.10
    }
    
    print(f"\nEnsemble weights: {weights}")
    
    # Calculate weighted average
    ensemble_pred = np.zeros(len(X_test))
    for name, weight in weights.items():
        ensemble_pred += weight * predictions[name]
    
    print(f"\nEnsemble predictions: mean={ensemble_pred.mean():.2f}, std={ensemble_pred.std():.2f}")
    
    return ensemble_pred


def visualize_feature_importance(models, feature_names, top_n=20):
    """
    Visualize feature importance from tree-based models.
    
    Args:
        models (dict): Dictionary of trained models
        feature_names (list): List of feature names
        top_n (int): Number of top features to display
    """
    print("\n--- Feature Importance Analysis ---")
    
    # Get feature importance from tree-based models
    importance_dfs = []
    
    for name in ['random_forest', 'xgboost', 'lightgbm', 'gradient_boosting']:
        if name in models:
            if hasattr(models[name], 'feature_importances_'):
                importance = models[name].feature_importances_
                df = pd.DataFrame({
                    'feature': feature_names,
                    'importance': importance,
                    'model': name
                })
                importance_dfs.append(df)
    
    if len(importance_dfs) > 0:
        # Combine all importances
        all_importance = pd.concat(importance_dfs)
        
        # Average importance across models
        avg_importance = all_importance.groupby('feature')['importance'].mean().sort_values(ascending=False)
        
        # Plot top features
        fig, ax = plt.subplots(figsize=(10, 8))
        top_features = avg_importance.head(top_n)
        top_features.sort_values().plot(kind='barh', ax=ax)
        ax.set_title(f'Top {top_n} Most Important Features (Average across models)', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Average Importance')
        plt.tight_layout()
        plt.savefig('feature_importance.png', dpi=100, bbox_inches='tight')
        print("Saved: feature_importance.png")
        plt.close()
        
        print(f"\nTop {top_n} features:")
        print(avg_importance.head(top_n))


# ==================== SUBMISSION ====================

def create_submission(test_ids, predictions, filename='submission.csv'):
    """
    Create submission file for Kaggle.
    
    Args:
        test_ids (pd.Series): Test set IDs
        predictions (np.array): Predictions for test set
        filename (str): Output filename
    """
    print("\n" + "=" * 80)
    print("CREATING SUBMISSION")
    print("=" * 80)
    
    # Ensure predictions are positive
    predictions = np.maximum(predictions, 0)
    
    # Create submission dataframe
    submission = pd.DataFrame({
        'Id': test_ids,
        'SalePrice': predictions
    })
    
    # Save to CSV
    submission.to_csv(filename, index=False)
    
    print(f"\nSubmission file created: {filename}")
    print(f"Shape: {submission.shape}")
    print(f"\nFirst few predictions:")
    print(submission.head(10))
    print(f"\nPrediction statistics:")
    print(submission['SalePrice'].describe())
    
    return submission


# ==================== MAIN EXECUTION ====================

def main():
    """
    Main execution function.
    """
    print("\n" + "=" * 80)
    print("HOUSE PRICES - ADVANCED REGRESSION TECHNIQUES")
    print("Kaggle Competition Solution")
    print("=" * 80)
    
    # Load data
    train, test = load_data('train.csv', 'test.csv')
    
    # Perform EDA
    numerical_features, categorical_features = perform_eda(train)
    
    # Preprocess data
    X_train, X_test, y_train, test_ids = preprocess_data(train, test)
    
    # Train models
    models = train_all_models(X_train, y_train)
    
    # Visualize feature importance
    visualize_feature_importance(models, X_train.columns.tolist())
    
    # Create ensemble predictions
    predictions = create_ensemble_predictions(models, X_test)
    
    # Create submission
    submission = create_submission(test_ids, predictions, 'submission.csv')
    
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    print("\nFiles created:")
    print("  - submission.csv (Kaggle submission file)")
    print("  - saleprice_distribution.png (EDA visualization)")
    print("  - correlation_heatmap.png (EDA visualization)")
    print("  - top_features_scatter.png (EDA visualization)")
    print("  - feature_importance.png (Model analysis)")
    print("\nReady to submit to Kaggle!")


if __name__ == "__main__":
    main()

