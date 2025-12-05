# Dijkstra ML Routing Optimization

**AI-Enhanced Route Planning using Graph Theory & Machine Learning**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange.svg)](https://jupyter.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> A production-grade implementation combining Dijkstra's algorithm with Machine Learning to find optimal routes in real-world street networks. Achieves **90.4% prediction accuracy** with intelligent route optimization.

---

## Project Overview

This project demonstrates how **Graph Theory** and **Machine Learning** can work together to solve real-world routing problems. Using OpenStreetMap data from San Francisco, California, we implement three routing approaches:

1. **Distance-based Dijkstra** - Shortest physical path
2. **Time-based Dijkstra** - Fastest using speed limits
3. **ML-Optimized Dijkstra** - AI-predicted optimal route

### Key Features

- **Custom Dijkstra Implementation** - O((V+E)logV) complexity
- **Gradient Boosting ML Model** - 90.4% accuracy with 15 engineered features
- **Interactive Maps** - Routes follow actual streets (not straight lines)
- **Manual Location Input** - Geocoding support for any address
- **Production-Grade Architecture** - Modular, tested, documented

---

## Results

| Metric | Value |
|--------|-------|
| **ML Accuracy (R²)** | 90.4% |
| **Average Improvement** | 18.87% |
| **Average Time Saved** | 100.3 seconds/route |
| **Best Improvement** | 34.60% |
| **Network Size** | 10,011 nodes, 27,584 edges |

---

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/HuzaifaAbdulRehman/dijkstra-ml-routing-optimization.git
cd dijkstra-ml-routing-optimization

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Notebook

```bash
# Start Jupyter
jupyter notebook shortest_path_routing.ipynb

# Run all cells: Kernel -> Restart & Run All
```

### 3. Try Manual Route Finding

```python
# In Cell 20, set ROUTE_MODE = 3 and edit:
ORIGIN_ADDRESS = "Golden Gate Park, San Francisco, California, USA"
DEST_ADDRESS = "San Francisco International Airport, California, USA"
```

**Output:** Interactive map with 3 optimized routes + statistics

---

## Project Structure

```
dijkstra-ml-routing-optimization/
│
├── shortest_path_routing.ipynb      # Main Jupyter notebook
├── routing_algorithms.py            # Dijkstra implementation
├── ml_models.py                     # ML pipeline (Gradient Boosting, XGBoost)
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
│
├── Project_Report/                  # Project documentation
│   ├── Graph_Theory_Project_Report.pdf
│   ├── Graph_Theory_Project_Report.docx
│   └── GT_projects_list_fall25 (1).pdf
│
└── route_comparison_PRODUCTION.html # Interactive route visualization
```

---

## How It Works

### 1. Data Acquisition
- Downloads street network from **OpenStreetMap** (OSMnx)
- Extracts 10,011 nodes (intersections) + 27,584 edges (roads)

### 2. Feature Engineering (15 Features)
- **Base:** length, speed, lanes
- **Infrastructure:** bridges, tunnels, one-way roads
- **Computed:** capacity score, congestion factor, turn penalties
- **Quality:** road importance, smoothness score

### 3. Machine Learning
- Trains 3 models: Random Forest, Gradient Boosting, XGBoost
- Best model: **Gradient Boosting** (MAE: 1.54s, R²: 0.904)
- Applies ML predictions as edge weights

### 4. Routing Engine
- Implements **Dijkstra's Algorithm** with 3 weight variants
- Compares routes: distance vs time vs ML-optimized
- Generates interactive visualizations

---

## Algorithm Comparison

| Algorithm | Distance (km) | Time (min) | Computation (ms) |
|-----------|--------------|------------|------------------|
| **Distance-based** | 13.09 | 19.27 | 215.5 |
| **Time-based** | 13.91 | 14.75 | 162.2 |
| **ML-optimized** | 13.91 | 14.75 | 184.1 |

*ML successfully matches time-based performance while using predicted optimal weights.*

---

## Visualizations

### Interactive Map
- **Blue line:** Distance-optimized
- **Red dashed:** Time-optimized
- **Green line:** ML-optimized

**Key Innovation:** Routes follow actual street curves (using OSM geometry), not straight lines

### Charts & Graphs
- ML model comparison (MAE, R², RMSE)
- Feature importance analysis
- Route quality metrics
- Statistical summaries

---

## Technical Details

### Dijkstra's Algorithm
```
Time Complexity: O((V + E) log V)
Space Complexity: O(V + E)

Where:
- V = 10,011 nodes (intersections)
- E = 27,584 edges (road segments)
- Execution: 162-215 milliseconds
```

### ML Model Performance
```
Best Model: Gradient Boosting
R² Score: 0.904 (90.4% accuracy)
MAE: 1.54 seconds
RMSE: 2.48 seconds

Training Samples: 22,067 (80%)
Testing Samples: 5,517 (20%)
Features: 15
```

---

## Dependencies

```
osmnx>=1.6.0          # OpenStreetMap downloader
networkx>=3.1         # Graph algorithms
xgboost>=2.0.0        # ML model
scikit-learn>=1.3.0   # ML utilities
pandas>=2.0.0         # Data manipulation
numpy>=1.24.0         # Numerical computing
matplotlib>=3.7.0     # Plotting
seaborn>=0.12.0       # Statistical plots
folium>=0.14.0        # Interactive maps
geopy>=2.3.0          # Geocoding
```

---

## Limitations

**Current Constraints:**
- No real-time traffic (simulated congestion)
- Limited to downloaded city network
- No historical GPS trace data
- Internet required (OSMnx/Geopy)

**Future Enhancements:**
- Real-time traffic API integration
- Expand to larger networks (50K+ nodes)
- Multi-modal routing (walk + bus + car)

---

## Usage Examples

### Example 1: Change City
```python
# Works with any city!
CITY = "Manhattan, New York, USA"
# Re-run notebook from Cell 4
```

### Example 2: Manual Location Input
```python
# In Cell 20, set ROUTE_MODE = 3
ORIGIN_ADDRESS = "Your starting address"
DEST_ADDRESS = "Your destination address"
```

---

## Author

**Huzaifa Abdul Rehman**

- GitHub: [@HuzaifaAbdulRehman](https://github.com/HuzaifaAbdulRehman)
- Project: Graph Theory Fall 2025

---

## Acknowledgments

- **OpenStreetMap** - Real-world street data
- **OSMnx** - Python library for network analysis
- **Scikit-learn** - ML model implementation
- **Folium** - Interactive map visualizations

---

## License

MIT License - feel free to use for academic or commercial projects.
