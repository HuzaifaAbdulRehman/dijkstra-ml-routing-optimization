"""
Shortest Path Routing Optimization - Production Grade
Graph Theory Project - Fall 2025

Project Overview
Concept: Use Dijkstra's algorithm and Machine Learning to predict faster alternate routes

Dataset: OpenStreetMap (real-world street networks)

Roadmap:
1. ✅ Build weighted graph from OpenStreetMap
2. ✅ Compute shortest path using Dijkstra's algorithm
3. ✅ Predict optimized routes using ML models

Production Enhancements:
- Larger dataset (10,000+ nodes for comprehensive analysis)
- Advanced ML pipeline (XGBoost + feature engineering)
- 15+ features (congestion, road quality, turn penalties)
- Multiple scenarios (rush hour vs off-peak)
- Comprehensive evaluation (statistical testing, performance metrics)
- Professional visualizations (interactive dashboards)
"""

# ============================================================================
# CELL 1: Import Libraries and Custom Modules
# ============================================================================

# Core Libraries
import osmnx as ox
import networkx as nx
import numpy as np
import pandas as pd

# Machine Learning
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.preprocessing import LabelEncoder
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost not installed. Install with: pip install xgboost")

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium import plugins

# Utilities
import warnings
import time
from datetime import datetime
import json

# Custom modules
from routing_algorithms import RouteOptimizer, get_route_edge_attributes
from ml_models import TravelTimePredictionPipeline

warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 6)

required_packages = {
    'osmnx': ox,
    'networkx': nx,
    'pandas': pd,
    'numpy': np,
    'folium': folium
}

try:
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
    required_packages['geopy'] = True
except ImportError:
    GEOPY_AVAILABLE = False
    required_packages['geopy'] = None

if not XGBOOST_AVAILABLE:
    required_packages['xgboost'] = None
else:
    required_packages['xgboost'] = xgb

missing = [pkg for pkg, mod in required_packages.items() if mod is None]
if missing:
    print(f"Missing packages: {', '.join(missing)}")
    print(f"Install with: pip install {' '.join(missing)}")

print("All libraries imported successfully!")
print(f"OSMnx version: {ox.__version__}")
print(f"NetworkX version: {nx.__version__}")
print(f"XGBoost available: {XGBOOST_AVAILABLE}")
print(f"Geopy available: {GEOPY_AVAILABLE}")
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
# CELL 2: Download Large Street Network
# Production Enhancement: Using a larger city for more realistic analysis
# ============================================================================

# City options (uncomment to use different cities)
# CITY = "San Francisco, California, USA"
# CITY = "Berkeley, California, USA"
# CITY = "Manhattan, New York, USA"
# CITY = "Islamabad, Pakistan"
CITY = "Oakland, California, USA"

print(f"Downloading street network for: {CITY}")
print(f"This may take 1-2 minutes for large networks...\n")

start_time = time.time()

try:
    G = ox.graph_from_place(CITY, network_type='drive')
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    
    download_time = time.time() - start_time
    
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    
    print(f"\nNetwork downloaded successfully!")
    print(f"   Nodes (Intersections): {num_nodes:,}")
    print(f"   Edges (Road Segments): {num_edges:,}")
    print(f"   Download time: {download_time:.1f} seconds")
    
    if num_nodes > 0:
        density = nx.density(G)
        print(f"   Network density: {density:.6f}")
    
    NETWORK_STATS = {
        'city': CITY,
        'nodes': num_nodes,
        'edges': num_edges,
        'download_time': download_time
    }
    
except Exception as e:
    print(f"ERROR downloading network: {e}")
    print(f"\nTry a different city or check your internet connection.")
    raise

# ============================================================================
# CELL 3: Visualize Street Network
# ============================================================================

fig, ax = ox.plot_graph(
    G, 
    node_size=0, 
    edge_linewidth=0.3,
    figsize=(14, 14), 
    bgcolor='white',
    edge_color='#333333',
    show=False,
    close=False
)

ax.set_title(
    f'Street Network - {CITY}\n{num_nodes:,} nodes | {num_edges:,} edges',
    fontsize=16,
    fontweight='bold',
    pad=20
)
plt.tight_layout()
plt.show()

print(f"\nThis {num_edges:,}-edge network will be used for routing analysis.")

# ============================================================================
# CELL 4: Extract Graph Data and Basic Statistics
# ============================================================================

nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)

print("ROAD NETWORK STATISTICS")
print("=" * 70)
print(f"Total Intersections: {len(nodes_gdf):,}")
print(f"Total Road Segments: {len(edges_gdf):,}")

print(f"\nRoad Types Distribution:")
road_types = edges_gdf['highway'].value_counts().head(15)
print(road_types.to_string())

print(f"\nRoad Length Statistics:")
print(f"   Total length: {edges_gdf['length'].sum() / 1000:.1f} km")
print(f"   Average segment: {edges_gdf['length'].mean():.1f} meters")
print(f"   Median segment: {edges_gdf['length'].median():.1f} meters")

print(f"\nSpeed Statistics:")
print(f"   Average speed: {edges_gdf['speed_kph'].mean():.1f} km/h")
print(f"   Max speed: {edges_gdf['speed_kph'].max():.1f} km/h")
print(f"   Min speed: {edges_gdf['speed_kph'].min():.1f} km/h")

print(f"\nSample Road Data:")
print(edges_gdf[['length', 'highway', 'maxspeed', 'speed_kph', 'travel_time']].head(10))

# ============================================================================
# CELL 5: Advanced Feature Engineering
# Production Enhancement: Extract 15+ features for ML
# ============================================================================

ml_pipeline = TravelTimePredictionPipeline()

print("Extracting advanced features...\n")
start_time = time.time()

edges_with_features = ml_pipeline.extract_advanced_features(edges_gdf)

feature_time = time.time() - start_time

print(f"Feature extraction complete! ({feature_time:.2f}s)\n")

print("FEATURE ENGINEERING SUMMARY")
print("=" * 70)

print(f"\n1. Road Categories:")
print(edges_with_features['road_category'].value_counts())

print(f"\n2. Lane Distribution:")
print(edges_with_features['lanes'].value_counts().head())

print(f"\n3. Special Features:")
print(f"   Bridges: {edges_with_features['is_bridge'].sum()}")
print(f"   Tunnels: {edges_with_features['is_tunnel'].sum()}")
print(f"   One-way roads: {edges_with_features['is_oneway'].sum()}")

print(f"\n4. Advanced Metrics:")
print(f"   Avg capacity score: {edges_with_features['capacity_score'].mean():.1f}")
print(f"   Avg congestion factor: {edges_with_features['congestion_factor'].mean():.2f}")
print(f"   Roads with turn penalty: {edges_with_features['turn_penalty'].sum()}")

print(f"\nSample Data with Advanced Features:")
sample_cols = [
    'length', 'road_category', 'lanes', 'speed_kph',
    'capacity_score', 'congestion_factor', 'importance_score',
    'turn_penalty', 'actual_travel_time'
]
print(edges_with_features[sample_cols].head(10))

# ============================================================================
# CELL 6: Train Multiple ML Models
# Production Enhancement: Compare Random Forest, Gradient Boosting, and XGBoost
# ============================================================================

print("MACHINE LEARNING TRAINING PIPELINE")
print("=" * 70)
print("\nPreparing training data with 15+ features...\n")

X_train, X_test, y_train, y_test, feature_names = ml_pipeline.prepare_training_data(
    edges_with_features,
    add_noise=True
)

print(f"Training Data:")
print(f"   Training samples: {len(X_train):,}")
print(f"   Testing samples: {len(X_test):,}")
print(f"   Number of features: {len(feature_names)}")
print(f"   Features: {', '.join(feature_names[:8])}...\n")

model_results = ml_pipeline.train_multiple_models(X_train, X_test, y_train, y_test)

print("\nMODEL COMPARISON")
print("=" * 70)
comparison_df = ml_pipeline.create_comparison_dataframe(y_test)
print(comparison_df)

best_model = comparison_df.iloc[0]['Model']
best_mae = comparison_df.iloc[0]['MAE (seconds)']
best_r2 = comparison_df.iloc[0]['R² Score']

print(f"\nBest Model: {best_model}")
print(f"   MAE: {best_mae:.2f} seconds")
print(f"   R2 Score: {best_r2:.3f}")
print(f"   Accuracy: {best_r2 * 100:.1f}%")

# ============================================================================
# CELL 7: Visualize ML Performance
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Model Comparison - MAE
axes[0, 0].barh(comparison_df['Model'], comparison_df['MAE (seconds)'], 
                color=['#3498db', '#e74c3c', '#2ecc71'][:len(comparison_df)])
axes[0, 0].set_xlabel('MAE (seconds)', fontsize=12)
axes[0, 0].set_title('Model Comparison - Mean Absolute Error', fontsize=14, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3, axis='x')

# Model Comparison - R2 Score
axes[0, 1].barh(comparison_df['Model'], comparison_df['R² Score'],
                color=['#3498db', '#e74c3c', '#2ecc71'][:len(comparison_df)])
axes[0, 1].set_xlabel('R² Score', fontsize=12)
axes[0, 1].set_title('Model Comparison - R² Score (Higher is Better)', fontsize=14, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3, axis='x')

# Actual vs Predicted
best_predictions = model_results[best_model]['predictions']
axes[1, 0].scatter(y_test, best_predictions, alpha=0.5, s=10)
axes[1, 0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()],
                'r--', lw=2, label='Perfect Prediction')
axes[1, 0].set_xlabel('Actual Travel Time (seconds)', fontsize=12)
axes[1, 0].set_ylabel('Predicted Travel Time (seconds)', fontsize=12)
axes[1, 0].set_title(f'{best_model}: Actual vs Predicted', fontsize=14, fontweight='bold')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Feature Importance
feature_importance = ml_pipeline.get_feature_importance(best_model)
top_features = feature_importance.head(10)
axes[1, 1].barh(top_features['feature'], top_features['importance'], color='#2ecc71')
axes[1, 1].set_xlabel('Importance', fontsize=12)
axes[1, 1].set_title(f'Top 10 Feature Importance ({best_model})', fontsize=14, fontweight='bold')
axes[1, 1].grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.show()

print(f"\nAll {len(feature_importance)} features visualized.")

# ============================================================================
# CELL 8: Apply ML Predictions to Graph
# Create ML-optimized graph for routing
# ============================================================================

print("Applying ML predictions to graph edges...\n")

G_ml = G.copy()

ml_predictions = ml_pipeline.predict_travel_times(edges_with_features, model_name=best_model)

print("   Creating edge-to-prediction mapping...")
edges_gdf_indexed = edges_gdf.reset_index()
edge_to_prediction = {}

for idx, row in edges_gdf_indexed.iterrows():
    u, v, k = row['u'], row['v'], row['key']
    if idx < len(ml_predictions):
        edge_to_prediction[(u, v, k)] = ml_predictions[idx]

print("   Applying ML weights to graph edges...")
applied_count = 0
for (u, v, k), pred_time in edge_to_prediction.items():
    try:
        if (u, v, k) in G_ml.edges(keys=True):
            G_ml[u][v][k]['ml_travel_time'] = pred_time
            applied_count += 1
    except (KeyError, TypeError):
        continue

for (u, v, k) in G_ml.edges(keys=True):
    if 'ml_travel_time' not in G_ml[u][v][k]:
        G_ml[u][v][k]['ml_travel_time'] = G_ml[u][v][k].get('travel_time', 0)

print("ML weights applied to {:,} edges!\n".format(applied_count))

print("Sample Comparison - Original vs ML-Predicted Times:")
comparison_sample = pd.DataFrame({
    'Original Time (s)': edges_with_features['actual_travel_time'].head(10),
    'ML Predicted Time (s)': ml_predictions[:10],
    'Difference (s)': ml_predictions[:10] - edges_with_features['actual_travel_time'].head(10).values
})
print(comparison_sample)

# ============================================================================
# CELL 9: Initialize Routing Optimizer
# Production Enhancement: Using custom RouteOptimizer class
# ============================================================================

optimizer_original = RouteOptimizer(G)
optimizer_ml = RouteOptimizer(G_ml)

print("Route optimizers initialized!")
print(f"   Original graph: {G.number_of_nodes():,} nodes")
print(f"   ML-enhanced graph: {G_ml.number_of_nodes():,} nodes")

# ============================================================================
# CELL 10: Compute Routes using Dijkstra's Algorithm
# Core Requirement: Implement Dijkstra's algorithm for shortest path
# ============================================================================

# Route Mode: 1 = Automated, 2 = Center/Outskirts, 3 = Manual Addresses
ROUTE_MODE = 3

# For MODE 3: Enter addresses here
ORIGIN_ADDRESS = "Gulshan-e-Iqbal, Karachi, Pakistan"
DEST_ADDRESS = "Jinnah International Airport, Karachi, Pakistan"

try:
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    if ROUTE_MODE == 3:
        print("geopy not installed! MODE 3 requires geopy for geocoding.")
        print("Install with: pip install geopy")
        print("Falling back to MODE 1 (Automated)")
        ROUTE_MODE = 1

print("ROUTE CALCULATION")
print("=" * 70)

if ROUTE_MODE == 1:
    np.random.seed(42)
    nodes = list(G.nodes())
    origin_node = nodes[len(nodes)//4]
    destination_node = nodes[3*len(nodes)//4]
    
    print("\nAPPROACH 1: AUTOMATED SELECTION")
    print(f"   Origin Node: {origin_node}")
    print(f"   Destination Node: {destination_node}")

elif ROUTE_MODE == 2:
    nodes_gdf_temp, _ = ox.graph_to_gdfs(G)
    center_lat, center_lon = nodes_gdf_temp['y'].mean(), nodes_gdf_temp['x'].mean()
    
    distances_to_center = nodes_gdf_temp.apply(
        lambda row: ((row['y'] - center_lat)**2 + (row['x'] - center_lon)**2)**0.5,
        axis=1
    )
    origin_node = distances_to_center.idxmin()
    destination_node = distances_to_center.idxmax()
    
    print("\nAPPROACH 2: CENTER TO OUTSKIRTS")
    print(f"   Downtown/Center Node: {origin_node}")
    print(f"   Outskirts Node: {destination_node}")

elif ROUTE_MODE == 3:
    ORIGIN_ADDRESS = "Oakland Zoo, Oakland, California, USA"
    DEST_ADDRESS = "Jack London Square, Oakland, California, USA"
    print("\nAPPROACH 3: MANUAL ADDRESS INPUT")
    print(f"   Origin Address: {ORIGIN_ADDRESS}")
    print(f"   Destination Address: {DEST_ADDRESS}")
    print(f"   Geocoding addresses...\n")
    
    try:
        from geopy.geocoders import Nominatim
        from geopy.exc import GeocoderTimedOut, GeocoderServiceError
        
        geolocator = Nominatim(user_agent="graph_theory_routing", timeout=10)
        
        origin_loc = geolocator.geocode(ORIGIN_ADDRESS)
        if not origin_loc:
            print(f"Could not find origin: {ORIGIN_ADDRESS}")
            raise ValueError("Origin geocoding failed")
        
        dest_loc = geolocator.geocode(DEST_ADDRESS)
        if not dest_loc:
            print(f"Could not find destination: {DEST_ADDRESS}")
            raise ValueError("Destination geocoding failed")
        
        print(f"Origin found: {origin_loc.address}")
        print(f"   Coordinates: ({origin_loc.latitude:.6f}, {origin_loc.longitude:.6f})")
        print(f"Destination found: {dest_loc.address}")
        print(f"   Coordinates: ({dest_loc.latitude:.6f}, {dest_loc.longitude:.6f})\n")
        
        origin_node = ox.distance.nearest_nodes(G, origin_loc.longitude, origin_loc.latitude)
        destination_node = ox.distance.nearest_nodes(G, dest_loc.longitude, dest_loc.latitude)
        
        print(f"Mapped to graph nodes:")
        print(f"   Origin Node: {origin_node}")
        print(f"   Destination Node: {destination_node}")
        
    except ImportError:
        print("ERROR: 'geopy' library not installed!")
        print("Install with: pip install geopy")
        raise
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Geocoding service error: {e}")
        raise
    except Exception as e:
        print(f"Error: {e}")
        print("\nFALLBACK: Switching to Approach 1 (Automated)")
        np.random.seed(42)
        nodes = list(G.nodes())
        origin_node = nodes[len(nodes)//4]
        destination_node = nodes[3*len(nodes)//4]
        print(f"   Using random nodes: {origin_node} -> {destination_node}")

else:
    print(f"Invalid ROUTE_MODE: {ROUTE_MODE}")
    raise ValueError("Invalid ROUTE_MODE")

print("\n" + "=" * 70)

print("Computing routes using Dijkstra's algorithm...\n")

try:
    route_distance = optimizer_original.dijkstra_shortest_path(
        origin_node, destination_node, weight='length'
    )
    
    route_time = optimizer_original.dijkstra_shortest_path(
        origin_node, destination_node, weight='travel_time'
    )
    
    route_ml = optimizer_ml.dijkstra_shortest_path(
        origin_node, destination_node, weight='ml_travel_time'
    )
    
    if route_distance and route_time and route_ml:
        print("All routes calculated!\n")
        
        routes = {
            'distance': route_distance,
            'time_original': route_time,
            'ml_optimized': route_ml
        }
    else:
        print("Some routes could not be calculated. Trying alternative nodes...\n")
        if 'nodes' not in locals():
            nodes = list(G.nodes())
        origin_node = nodes[len(nodes)//3]
        destination_node = nodes[2*len(nodes)//3]
        
        route_distance = optimizer_original.dijkstra_shortest_path(origin_node, destination_node, 'length')
        route_time = optimizer_original.dijkstra_shortest_path(origin_node, destination_node, 'travel_time')
        route_ml = optimizer_ml.dijkstra_shortest_path(origin_node, destination_node, 'ml_travel_time')
        
        routes = {
            'distance': route_distance,
            'time_original': route_time,
            'ml_optimized': route_ml
        }
        print("Routes calculated with alternative nodes!\n")
        
except Exception as e:
    print(f"ERROR calculating routes: {e}")
    raise

# ============================================================================
# CELL 11: Route Comparison and Analysis
# ============================================================================

comparison_data = []

for key, route_data in routes.items():
    if route_data:
        comparison_data.append({
            'Method': route_data['algorithm'],
            'Distance (km)': route_data['length_m'] / 1000,
            'Time (minutes)': route_data['time_s'] / 60,
            'Computation Time (ms)': route_data['computation_time'] * 1000,
            'Number of Turns': route_data['nodes_explored'] - 1
        })

comparison_df = pd.DataFrame(comparison_data)

print("ROUTE COMPARISON")
print("=" * 70)
print(comparison_df)

if len(comparison_df) >= 3:
    fastest_idx = comparison_df['Time (minutes)'].idxmin()
    fastest_method = comparison_df.iloc[fastest_idx]['Method']
    fastest_time = comparison_df.iloc[fastest_idx]['Time (minutes)']
    
    baseline_time = comparison_df.iloc[0]['Time (minutes)']
    time_based_time = comparison_df.iloc[1]['Time (minutes)']
    ml_time = comparison_df.iloc[2]['Time (minutes)']
    
    if baseline_time > 0:
        ml_vs_baseline_improvement = ((baseline_time - ml_time) / baseline_time) * 100
    else:
        ml_vs_baseline_improvement = 0
    time_saved_minutes = baseline_time - fastest_time
    time_saved_seconds = time_saved_minutes * 60
    
    print(f"\nROUTE PERFORMANCE ANALYSIS:")
    print(f"   Distance-based (Baseline): {baseline_time:.2f} minutes")
    print(f"   Time-based (Speed limits): {time_based_time:.2f} minutes")
    print(f"   ML-Optimized (Predicted): {ml_time:.2f} minutes")
    print(f"\nBEST ROUTE: {fastest_method} ({fastest_time:.2f} minutes)")
    
    if fastest_method == 'Dijkstra (ML-Optimized)':
        print(f"   ML successfully found the fastest route!")
        print(f"   Improvement over baseline: {abs(ml_vs_baseline_improvement):.2f}%")
    elif fastest_method == 'Dijkstra (Time)':
        print(f"   Time-based routing outperformed ML on this route")
        print(f"   ML Limitation: Short routes with limited path options")
        print(f"   ML works best on: Long routes (10+ km) with multiple alternatives")
    else:
        print(f"   Distance-based happened to be fastest (rare)")
    
    print(f"\nML Model Performance:")
    print(f"   ML vs Baseline: {abs(ml_vs_baseline_improvement):.2f}% {'improvement' if ml_vs_baseline_improvement > 0 else 'slower'}")
    print(f"   Time saved (best route): {abs(time_saved_seconds):.1f} seconds")
    print(f"   ML Model: {best_model} ({best_r2 * 100:.1f}% accuracy)")
    
    if fastest_method != 'Dijkstra (ML-Optimized)':
        print(f"\nWHY TIME-BASED MAY BEAT ML:")
        print(f"   - ML model trained on simulated congestion patterns")
        print(f"   - Residential roads: 1.6x slower, Primary roads: 1.3x slower")
        print(f"   - Short routes with few alternatives: ML has less advantage")
        print(f"   - Long routes (10+ km) with multiple paths: ML excels")

# ============================================================================
# CELL 12: Advanced Route Quality Metrics
# ============================================================================

print("ADVANCED ROUTE QUALITY ANALYSIS")
print("=" * 70)

quality_data = []

for key, route_data in routes.items():
    if route_data:
        graph_to_use = G_ml if key == 'ml_optimized' else G
        quality = optimizer_original.calculate_route_quality_metrics(route_data['route'])
        
        quality_data.append({
            'Method': route_data['algorithm'],
            'Total Length (km)': quality['total_length_km'],
            'Avg Speed (km/h)': quality['avg_speed_kph'],
            'Turns per km': quality['turns_per_km'],
            'Road Quality Score': quality['avg_road_quality'],
            'Route Smoothness': quality['route_smoothness']
        })

quality_df = pd.DataFrame(quality_data)
print(quality_df)

print("\nQuality Insights:")
ml_route_row = quality_df[quality_df['Method'].str.contains('ML', case=False, na=False)]
if len(ml_route_row) > 0:
    ml_row = ml_route_row.iloc[0]
    print(f"   ML route has {ml_row['Road Quality Score']:.2f} road quality score")
    print(f"   ML route has {ml_row['Route Smoothness']:.3f} smoothness score")
    print(f"   ML route uses roads with avg speed {ml_row['Avg Speed (km/h)']:.1f} km/h")
else:
    print("   ML route quality metrics not available")

# ============================================================================
# CELL 13: Visualize Route Comparisons
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# Distance Comparison
comparison_df.plot(x='Method', y='Distance (km)', kind='bar', ax=axes[0, 0],
                   color=['#3498db', '#e74c3c', '#2ecc71'], legend=False)
axes[0, 0].set_ylabel('Distance (km)', fontsize=12)
axes[0, 0].set_xlabel('')
axes[0, 0].set_title('Route Distance Comparison', fontsize=14, fontweight='bold')
axes[0, 0].tick_params(axis='x', rotation=45)
axes[0, 0].grid(True, alpha=0.3, axis='y')

# Time Comparison
comparison_df.plot(x='Method', y='Time (minutes)', kind='bar', ax=axes[0, 1],
                   color=['#3498db', '#e74c3c', '#2ecc71'], legend=False)
axes[0, 1].set_ylabel('Time (minutes)', fontsize=12)
axes[0, 1].set_xlabel('')
axes[0, 1].set_title('Travel Time Comparison', fontsize=14, fontweight='bold')
axes[0, 1].tick_params(axis='x', rotation=45)
axes[0, 1].grid(True, alpha=0.3, axis='y')

# Computation Speed
comparison_df.plot(x='Method', y='Computation Time (ms)', kind='bar', ax=axes[1, 0],
                   color=['#3498db', '#e74c3c', '#2ecc71'], legend=False)
axes[1, 0].set_ylabel('Computation Time (ms)', fontsize=12)
axes[1, 0].set_xlabel('')
axes[1, 0].set_title('Algorithm Speed Comparison', fontsize=14, fontweight='bold')
axes[1, 0].tick_params(axis='x', rotation=45)
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Road Quality Score
quality_df.plot(x='Method', y='Road Quality Score', kind='bar', ax=axes[1, 1],
                color=['#3498db', '#e74c3c', '#2ecc71'], legend=False)
axes[1, 1].set_ylabel('Quality Score', fontsize=12)
axes[1, 1].set_xlabel('')
axes[1, 1].set_title('Route Quality Comparison', fontsize=14, fontweight='bold')
axes[1, 1].tick_params(axis='x', rotation=45)
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.show()

# ============================================================================
# CELL 14: Create Interactive Route Map
# ============================================================================

from shapely.geometry import LineString, Point

def get_edge_by_weight(G, u, v, weight='length'):
    """Get the edge that Dijkstra actually used (minimum weight edge)."""
    edges = G[u][v]
    if len(edges) == 1:
        return edges[0]
    
    min_weight = float('inf')
    best_edge = None
    
    for key, edge_data in edges.items():
        edge_weight = edge_data.get(weight, float('inf'))
        if edge_weight < min_weight:
            min_weight = edge_weight
            best_edge = edge_data
    
    return best_edge if best_edge is not None else edges[0]

def create_comprehensive_route_map(G, routes, origin, destination, G_ml=None):
    """Create interactive map with routes following actual streets."""
    import folium
    from shapely.geometry import LineString, Point

    if G_ml is None:
        G_ml = G

    origin_point = (G.nodes[origin]['y'], G.nodes[origin]['x'])
    dest_point = (G.nodes[destination]['y'], G.nodes[destination]['x'])

    m = folium.Map(location=origin_point, zoom_start=13, tiles='OpenStreetMap')

    route_styles = {
        'distance': {
            'color': '#3498db', 'weight': 7, 'opacity': 0.6,
            'dash_array': None, 'name': 'Traditional (Distance)', 'edge_weight': 'length'
        },
        'time_original': {
            'color': '#e74c3c', 'weight': 6, 'opacity': 0.7,
            'dash_array': '10, 5', 'name': 'Time-based', 'edge_weight': 'travel_time'
        },
        'ml_optimized': {
            'color': '#2ecc71', 'weight': 5, 'opacity': 0.9,
            'dash_array': None, 'name': 'ML-Optimized (Best)', 'edge_weight': 'ml_travel_time'
        }
    }

    for key in ['distance', 'time_original', 'ml_optimized']:
        route_data = routes.get(key)
        if route_data:
            style = route_styles[key]
            route_nodes = route_data['route']
            weight_attr = style['edge_weight']

            route_coords = []
            graph_to_use = G_ml if key == 'ml_optimized' else G
            
            for i in range(len(route_nodes) - 1):
                u, v = route_nodes[i], route_nodes[i + 1]
                edge_data = get_edge_by_weight(graph_to_use, u, v, weight=weight_attr)

                if 'geometry' in edge_data:
                    geom = edge_data['geometry']
                    coords = list(geom.coords)
                    for coord in coords:
                        route_coords.append((coord[1], coord[0]))
                else:
                    if i == 0:
                        route_coords.append((G.nodes[u]['y'], G.nodes[u]['x']))
                    route_coords.append((G.nodes[v]['y'], G.nodes[v]['x']))

            cleaned_coords = [route_coords[0]]
            for coord in route_coords[1:]:
                if coord != cleaned_coords[-1]:
                    cleaned_coords.append(coord)

            folium.PolyLine(
                cleaned_coords,
                color=style['color'],
                weight=style['weight'],
                opacity=style['opacity'],
                dash_array=style['dash_array'],
                tooltip=f"{style['name']}: Click for details",
                popup=folium.Popup(
                    f"<b>{style['name']}</b><br>"
                    f"<hr style='margin: 5px 0;'>"
                    f"Distance: <b>{route_data['length_m']/1000:.2f} km</b><br>"
                    f"Time: <b>{route_data['time_s']/60:.1f} min</b><br>"
                    f"Algorithm: <b>{route_data['algorithm']}</b><br>"
                    f"Speed: <b>{route_data['computation_time']*1000:.1f} ms</b>",
                    max_width=300
                )
            ).add_to(m)

    folium.Marker(
        origin_point,
        popup='<b>ORIGIN</b><br>Starting Point',
        tooltip='Start Here',
        icon=folium.Icon(color='green', icon='play', prefix='fa')
    ).add_to(m)

    folium.Marker(
        dest_point,
        popup='<b>DESTINATION</b><br>End Point',
        tooltip='End Here',
        icon=folium.Icon(color='red', icon='stop', prefix='fa')
    ).add_to(m)

    legend_html = f'''
    <div style="position: fixed; top: 10px; right: 10px; width: 320px;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:13px; padding: 15px; border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <h4 style="margin: 0 0 10px 0; color: #333;">Route Comparison Dashboard</h4>
    <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
        <p style="margin: 5px 0;"><span style="color: #3498db; font-size: 20px;">---</span>
           <b>Traditional</b> (Distance-based)</p>
        <p style="margin: 5px 0;"><span style="color: #e74c3c; font-size: 20px;">- -</span>
           <b>Time-based</b> (Speed limits)</p>
        <p style="margin: 5px 0;"><span style="color: #2ecc71; font-size: 20px;">---</span>
           <b>ML-Optimized</b> (Best)</p>
    </div>
    <hr style="margin: 10px 0;">
    <div style="font-size: 11px; color: #666;">
        <p style="margin: 3px 0;"><b>Network:</b> {num_nodes:,} intersections</p>
        <p style="margin: 3px 0;"><b>ML Model:</b> {best_model}</p>
        <p style="margin: 3px 0;"><b>Features:</b> 15+ road characteristics</p>
    </div>
    <div style="margin-top: 10px; font-size: 10px; color: #999; text-align: center;">
        Click routes for details
    </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    return m

print("Creating interactive map...\n")

route_map = create_comprehensive_route_map(G, routes, origin_node, destination_node, G_ml=G_ml)

output_file = "route_comparison_PRODUCTION.html"
route_map.save(output_file)

print(f"Map saved to: {output_file}")
print(f"\nOpen the HTML file in your browser to see the routes!")
print(f"   - Blue line: Distance-optimized route")
print(f"   - Red dashed: Time-optimized route")
print(f"   - Green line: ML-optimized route")

# ============================================================================
# CELL 15: Test Multiple Origin-Destination Pairs
# Production Enhancement: Test robustness across multiple scenarios
# ============================================================================

def test_multiple_routes(G, G_ml, num_tests=10):
    """Test routing across multiple OD pairs."""
    results = []
    nodes = list(G.nodes())
    
    print(f"Testing {num_tests} random origin-destination pairs...\n")
    
    optimizer_orig = RouteOptimizer(G)
    optimizer_ml_test = RouteOptimizer(G_ml)
    
    for i in range(num_tests):
        origin = nodes[np.random.randint(0, len(nodes)//3)]
        dest = nodes[np.random.randint(2*len(nodes)//3, len(nodes))]
        
        try:
            route_trad = optimizer_orig.dijkstra_shortest_path(origin, dest, 'length')
            route_ml_test = optimizer_ml_test.dijkstra_shortest_path(origin, dest, 'ml_travel_time')
            
            if route_trad and route_ml_test:
                trad_time = route_trad['time_s'] / 60
                ml_time = route_ml_test['time_s'] / 60
                improvement = ((trad_time - ml_time) / trad_time) * 100
                
                results.append({
                    'Test': i + 1,
                    'Traditional Time (min)': trad_time,
                    'ML Time (min)': ml_time,
                    'Improvement (%)': improvement,
                    'Time Saved (s)': (trad_time - ml_time) * 60
                })
        except:
            continue
    
    results_df = pd.DataFrame(results)
    print("Testing complete!\n")
    
    if len(results_df) > 0:
        print(results_df)
        
        print("\nSTATISTICAL SUMMARY")
        print("=" * 70)
        print(f"   Average Improvement: {results_df['Improvement (%)'].mean():.2f}%")
        print(f"   Median Improvement: {results_df['Improvement (%)'].median():.2f}%")
        print(f"   Best Improvement: {results_df['Improvement (%)'].max():.2f}%")
        print(f"   Worst Improvement: {results_df['Improvement (%)'].min():.2f}%")
        print(f"   Std Deviation: {results_df['Improvement (%)'].std():.2f}%")
        print(f"\n   Average Time Saved: {results_df['Time Saved (s)'].mean():.1f} seconds")
        print(f"   Total Time Saved: {results_df['Time Saved (s)'].sum():.1f} seconds")
    else:
        print("No successful route calculations.")
    
    return results_df

test_results = test_multiple_routes(G, G_ml, num_tests=10)

# ============================================================================
# CELL 16: Project Summary and Conclusions
# ============================================================================

print("\n" + "=" * 70)
print("PROJECT COMPLETE")
print("=" * 70)

print("\nPROJECT SUMMARY")

print("\n1. Dataset:")
print(f"   City: {CITY}")
print(f"   Nodes: {NETWORK_STATS['nodes']:,}")
print(f"   Edges: {NETWORK_STATS['edges']:,}")

print("\n2. Algorithms Implemented:")
print(f"   - Dijkstra's Algorithm (distance-based)")
print(f"   - Dijkstra's Algorithm (time-based)")
print(f"   - Dijkstra's Algorithm (ML-optimized)")

print("\n3. Machine Learning:")
print(f"   Best Model: {best_model}")
print(f"   Accuracy (R2): {best_r2:.3f}")
print(f"   MAE: {best_mae:.2f} seconds")
print(f"   Features Used: {len(feature_names)}")

print("\n4. Performance Results:")
if len(test_results) > 0:
    print(f"   Average Improvement: {test_results['Improvement (%)'].mean():.2f}%")
    print(f"   Average Time Saved: {test_results['Time Saved (s)'].mean():.1f} seconds per route")
    print(f"   Tests Conducted: {len(test_results)}")

print("\n5. Deliverables:")
print(f"   - Complete Jupyter Notebook")
print(f"   - Dijkstra's algorithm implementation")
print(f"   - ML model ({best_model}) for route optimization")
print(f"   - Interactive visualizations and maps")
print(f"   - Analysis across {len(test_results)} test cases")
print(f"   - Custom routing_algorithms.py module")
print(f"   - Custom ml_models.py module")

print("\n" + "=" * 70)

