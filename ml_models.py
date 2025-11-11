"""
Machine Learning Models for Travel Time Prediction
Production-grade ML pipeline with advanced feature engineering
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.preprocessing import LabelEncoder, StandardScaler
import xgboost as xgb
from typing import Dict, Tuple, List


class TravelTimePredictionPipeline:
    """
    Production-grade ML pipeline for travel time prediction.
    """

    def __init__(self):
        self.models = {}
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_names = []
        self.best_model_name = None

    def extract_advanced_features(self, edges_gdf):
        """
        Extract advanced features from road network.

        Features include:
        - Basic: length, speed, lanes
        - Road type: highway category
        - Geometry: bridges, tunnels, oneway
        - Traffic: expected congestion based on road type
        - Connectivity: degree centrality
        - Time-based: rush hour factors

        Parameters:
        -----------
        edges_gdf : GeoDataFrame
            Edges from street network

        Returns:
        --------
        DataFrame : Edges with advanced features
        """
        df = edges_gdf.copy()

        # Basic features
        df['highway_type'] = df['highway'].apply(
            lambda x: x[0] if isinstance(x, list) else x
        )

        # Road category
        df['road_category'] = df['highway_type'].apply(self._categorize_road)

        # Lanes
        df['lanes'] = df['lanes'].apply(
            lambda x: int(x[0]) if isinstance(x, list) and len(x) > 0 else
                      (int(x) if pd.notna(x) and str(x).isdigit() else 1)
        )

        # One-way
        df['is_oneway'] = df['oneway'].astype(int) if 'oneway' in df.columns else 0

        # Bridge/tunnel
        df['is_bridge'] = df['bridge'].notna().astype(int) if 'bridge' in df.columns else 0
        df['is_tunnel'] = df['tunnel'].notna().astype(int) if 'tunnel' in df.columns else 0

        # Advanced features

        # 1. Speed-to-length ratio (longer roads may have different patterns)
        df['speed_length_ratio'] = df['speed_kph'] / (df['length'] / 1000 + 1)

        # 2. Road capacity score (lanes * speed)
        df['capacity_score'] = df['lanes'] * df['speed_kph']

        # 3. Expected congestion factor (based on road type)
        congestion_factors = {
            'motorway': 1.1,      # 10% slower during peak
            'primary': 1.3,       # 30% slower
            'secondary': 1.4,
            'tertiary': 1.5,
            'residential': 1.6,   # 60% slower during peak
            'other': 1.5
        }
        df['congestion_factor'] = df['road_category'].map(congestion_factors)

        # 4. Road importance score
        importance_scores = {
            'motorway': 5,
            'primary': 4,
            'secondary': 3,
            'tertiary': 2,
            'residential': 1,
            'other': 0
        }
        df['importance_score'] = df['road_category'].map(importance_scores)

        # 5. Length category (short, medium, long)
        df['length_category'] = pd.cut(
            df['length'],
            bins=[0, 50, 200, float('inf')],
            labels=['short', 'medium', 'long']
        )

        # 6. Speed category
        df['speed_category'] = pd.cut(
            df['speed_kph'],
            bins=[0, 30, 50, 80, float('inf')],
            labels=['slow', 'moderate', 'fast', 'very_fast']
        )

        # 7. Turn penalty indicator (short roads = more turns)
        df['turn_penalty'] = (df['length'] < 50).astype(int)

        # 8. Intersection complexity (bridge/tunnel adds complexity)
        df['intersection_complexity'] = df['is_bridge'] + df['is_tunnel'] + df['turn_penalty']

        # 9. Time factors (simulate rush hour)
        # Morning rush: 7-9 AM (factor 1.4)
        # Evening rush: 5-7 PM (factor 1.5)
        # Normal: factor 1.0
        df['rush_hour_morning_time'] = df['travel_time'] * df['congestion_factor'] * 1.2
        df['rush_hour_evening_time'] = df['travel_time'] * df['congestion_factor'] * 1.3
        df['off_peak_time'] = df['travel_time'] * 0.95  # Slightly faster off-peak

        # Target variable
        df['actual_travel_time'] = df['travel_time']

        return df

    def _categorize_road(self, highway_type):
        """Categorize road types."""
        if pd.isna(highway_type):
            return 'other'
        highway_type = str(highway_type).lower()

        if 'motorway' in highway_type:
            return 'motorway'
        elif any(x in highway_type for x in ['primary', 'trunk']):
            return 'primary'
        elif 'secondary' in highway_type:
            return 'secondary'
        elif 'tertiary' in highway_type:
            return 'tertiary'
        elif 'residential' in highway_type:
            return 'residential'
        else:
            return 'other'

    def prepare_training_data(self, edges_with_features, add_noise=True):
        """
        Prepare data for ML training.

        Parameters:
        -----------
        edges_with_features : DataFrame
            Edges with extracted features
        add_noise : bool
            Add realistic noise to simulate traffic variability

        Returns:
        --------
        tuple : (X_train, X_test, y_train, y_test, feature_names)
        """
        # Select numerical features
        numerical_features = [
            'length', 'speed_kph', 'lanes',
            'is_bridge', 'is_tunnel', 'is_oneway',
            'speed_length_ratio', 'capacity_score',
            'congestion_factor', 'importance_score',
            'turn_penalty', 'intersection_complexity'
        ]

        # Select categorical features to encode
        categorical_features = ['road_category', 'length_category', 'speed_category']

        # Prepare data
        ml_data = edges_with_features[numerical_features + categorical_features + ['actual_travel_time']].copy()
        ml_data = ml_data.dropna()

        # Encode categorical variables
        for cat_feature in categorical_features:
            le = LabelEncoder()
            ml_data[f'{cat_feature}_encoded'] = le.fit_transform(ml_data[cat_feature])
            self.label_encoders[cat_feature] = le

        # Final feature list
        feature_columns = numerical_features + [f'{cat}_encoded' for cat in categorical_features]
        self.feature_names = feature_columns

        X = ml_data[feature_columns]
        y = ml_data['actual_travel_time']

        # Add realistic noise to simulate real-world variability
        if add_noise:
            np.random.seed(42)
            # Traffic, weather, driver behavior adds ~15-25% variability
            noise = np.random.normal(1.0, 0.18, size=len(y))
            y = y * noise

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        return X_train, X_test, y_train, y_test, feature_columns

    def train_multiple_models(self, X_train, X_test, y_train, y_test):
        """
        Train and compare multiple ML models.

        Models:
        - Random Forest
        - Gradient Boosting
        - XGBoost (production standard for routing)

        Parameters:
        -----------
        X_train, X_test, y_train, y_test : arrays
            Training and testing data

        Returns:
        --------
        dict : Results for all models
        """
        results = {}

        print("🤖 Training Multiple ML Models...\n")

        # 1. Random Forest (baseline)
        print("1️⃣ Training Random Forest...")
        rf_model = RandomForestRegressor(
            n_estimators=150,
            max_depth=20,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)
        rf_pred = rf_model.predict(X_test)

        results['Random Forest'] = {
            'model': rf_model,
            'predictions': rf_pred,
            'mae': mean_absolute_error(y_test, rf_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, rf_pred)),
            'r2': r2_score(y_test, rf_pred)
        }
        print(f"   ✅ MAE: {results['Random Forest']['mae']:.2f}s | R²: {results['Random Forest']['r2']:.3f}\n")

        # 2. Gradient Boosting
        print("2️⃣ Training Gradient Boosting...")
        gb_model = GradientBoostingRegressor(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.1,
            random_state=42
        )
        gb_model.fit(X_train, y_train)
        gb_pred = gb_model.predict(X_test)

        results['Gradient Boosting'] = {
            'model': gb_model,
            'predictions': gb_pred,
            'mae': mean_absolute_error(y_test, gb_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, gb_pred)),
            'r2': r2_score(y_test, gb_pred)
        }
        print(f"   ✅ MAE: {results['Gradient Boosting']['mae']:.2f}s | R²: {results['Gradient Boosting']['r2']:.3f}\n")

        # 3. XGBoost (industry standard) - if available
        try:
            import xgboost as xgb
            print("3️⃣ Training XGBoost (Industry Standard)...")
            xgb_model = xgb.XGBRegressor(
                n_estimators=150,
                max_depth=8,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                verbosity=0  # Suppress warnings
            )
            xgb_model.fit(X_train, y_train)
            xgb_pred = xgb_model.predict(X_test)

            results['XGBoost'] = {
                'model': xgb_model,
                'predictions': xgb_pred,
                'mae': mean_absolute_error(y_test, xgb_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, xgb_pred)),
                'r2': r2_score(y_test, xgb_pred)
            }
            print(f"   ✅ MAE: {results['XGBoost']['mae']:.2f}s | R²: {results['XGBoost']['r2']:.3f}\n")
        except ImportError:
            print("3️⃣ XGBoost not available (skipping)")
            print("   Install with: pip install xgboost\n")

        # Store models
        self.models = results

        # Determine best model
        best_model_name = min(results.keys(), key=lambda k: results[k]['mae'])
        self.best_model_name = best_model_name

        print(f"🏆 Best Model: {best_model_name} (MAE: {results[best_model_name]['mae']:.2f}s)\n")

        return results

    def get_feature_importance(self, model_name='XGBoost'):
        """
        Get feature importance from trained model.

        Parameters:
        -----------
        model_name : str
            Name of the model

        Returns:
        --------
        DataFrame : Feature importance
        """
        if model_name not in self.models:
            return None

        model = self.models[model_name]['model']

        # Get feature importance
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
        else:
            return None

        # Create DataFrame
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)

        return importance_df

    def predict_travel_times(self, edges_with_features, model_name=None):
        """
        Predict travel times for all edges using trained model.

        Parameters:
        -----------
        edges_with_features : DataFrame
            Edges with extracted features
        model_name : str
            Model to use (default: best model)

        Returns:
        --------
        array : Predicted travel times
        """
        if model_name is None:
            model_name = self.best_model_name

        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not trained")

        model = self.models[model_name]['model']

        # Prepare features
        numerical_features = [
            'length', 'speed_kph', 'lanes',
            'is_bridge', 'is_tunnel', 'is_oneway',
            'speed_length_ratio', 'capacity_score',
            'congestion_factor', 'importance_score',
            'turn_penalty', 'intersection_complexity'
        ]

        categorical_features = ['road_category', 'length_category', 'speed_category']

        # Encode categorical features
        edges_ml = edges_with_features.copy()
        for cat_feature in categorical_features:
            if cat_feature in self.label_encoders:
                edges_ml[f'{cat_feature}_encoded'] = self.label_encoders[cat_feature].transform(
                    edges_ml[cat_feature]
                )

        # Prepare X
        feature_columns = numerical_features + [f'{cat}_encoded' for cat in categorical_features]
        X = edges_ml[feature_columns].fillna(0)

        # Predict
        predictions = model.predict(X)

        return predictions

    def create_comparison_dataframe(self, y_test):
        """
        Create comparison DataFrame for all models.

        Parameters:
        -----------
        y_test : array
            True values

        Returns:
        --------
        DataFrame : Model comparison
        """
        comparison_data = []

        for model_name, results in self.models.items():
            comparison_data.append({
                'Model': model_name,
                'MAE (seconds)': results['mae'],
                'RMSE (seconds)': results['rmse'],
                'R² Score': results['r2'],
                'Accuracy (%)': results['r2'] * 100
            })

        comparison_df = pd.DataFrame(comparison_data)
        comparison_df = comparison_df.sort_values('MAE (seconds)')

        return comparison_df
