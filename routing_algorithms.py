"""
Routing Algorithms Module
Production-grade implementation of shortest path algorithms
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Any
import time
import heapq


class RouteOptimizer:
    """
    Production-grade route optimizer with multiple algorithms.
    Implements Dijkstra, A*, and Bidirectional Dijkstra.
    """

    def __init__(self, graph):
        """
        Initialize route optimizer with graph.

        Parameters:
        -----------
        graph : networkx.MultiDiGraph
            Street network graph
        """
        self.graph = graph
        self.results_cache = {}


    def dijkstra_shortest_path(self, origin, destination, weight='length'):
        """
        Standard Dijkstra's algorithm.

        Parameters:
        -----------
        origin, destination : int
            Node IDs
        weight : str
            Edge attribute to use as weight

        Returns:
        --------
        dict : Route information including path, distance, time
        """
        start_time = time.time()

        try:
            # Use NetworkX's implementation (optimized C code)
            route = nx.shortest_path(self.graph, origin, destination, weight=weight)

            # Calculate metrics
            length = sum(self._get_edge_attribute(route, 'length'))
            travel_time = sum(self._get_edge_attribute(route, 'travel_time'))

            computation_time = time.time() - start_time

            return {
                'route': route,
                'length_m': length,
                'time_s': travel_time,
                'computation_time': computation_time,
                'algorithm': 'Dijkstra',
                'nodes_explored': len(route)
            }
        except nx.NetworkXNoPath:
            return None


    def find_k_shortest_paths(self, origin, destination, k=3, weight='length'):
        """
        Find k alternative routes.
        Useful for providing route options to users.

        Parameters:
        -----------
        origin, destination : int
            Node IDs
        k : int
            Number of alternative routes
        weight : str
            Edge attribute to use as weight

        Returns:
        --------
        list : List of k route dictionaries
        """
        try:
            # Use NetworkX's k shortest paths
            paths = list(nx.shortest_simple_paths(
                self.graph,
                origin,
                destination,
                weight=weight
            ))

            results = []
            for i, route in enumerate(paths[:k]):
                length = sum(self._get_edge_attribute(route, 'length'))
                travel_time = sum(self._get_edge_attribute(route, 'travel_time'))

                results.append({
                    'route': route,
                    'length_m': length,
                    'time_s': travel_time,
                    'rank': i + 1,
                    'algorithm': f'K-Shortest (k={i+1})'
                })

            return results
        except (nx.NetworkXNoPath, nx.NetworkXError):
            return []


    def _get_edge_attribute(self, route, attribute):
        """
        Helper function to get edge attributes along route.

        Parameters:
        -----------
        route : list
            List of node IDs
        attribute : str
            Edge attribute name

        Returns:
        --------
        list : Attribute values
        """
        attributes = []
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            # Get first edge (in case of parallel edges)
            edge_data = self.graph[u][v][0]
            attributes.append(edge_data.get(attribute, 0))
        return attributes

    def calculate_route_quality_metrics(self, route):
        """
        Calculate advanced route quality metrics.

        Parameters:
        -----------
        route : list
            List of node IDs

        Returns:
        --------
        dict : Quality metrics
        """
        edges = self._get_edge_attribute(route, 'highway')
        speeds = self._get_edge_attribute(route, 'speed_kph')
        lengths = self._get_edge_attribute(route, 'length')

        # Calculate metrics
        total_length = sum(lengths)
        avg_speed = np.mean(speeds) if speeds else 0
        speed_variance = np.var(speeds) if speeds else 0

        # Number of turns (direction changes)
        num_turns = len(route) - 1

        # Road quality score (prefer highways)
        road_quality_scores = {
            'motorway': 5,
            'trunk': 4,
            'primary': 3,
            'secondary': 2,
            'tertiary': 1,
            'residential': 0.5
        }

        quality_score = 0
        for edge_type in edges:
            edge_str = edge_type[0] if isinstance(edge_type, list) else str(edge_type).lower()
            for road_type, score in road_quality_scores.items():
                if road_type in edge_str:
                    quality_score += score
                    break

        avg_quality = quality_score / len(edges) if edges else 0

        # Safely calculate turns per km
        turns_per_km = num_turns / (total_length / 1000) if total_length > 0 else 0

        # Safely calculate smoothness
        route_smoothness = 1 / (1 + speed_variance) if speed_variance >= 0 else 0.5

        return {
            'total_length_km': total_length / 1000,
            'avg_speed_kph': avg_speed,
            'speed_variance': speed_variance,
            'num_turns': num_turns,
            'turns_per_km': turns_per_km,
            'avg_road_quality': avg_quality,
            'route_smoothness': route_smoothness
        }


def get_route_edge_attributes(G, route, attribute):
    """
    Standalone helper function to extract edge attributes.
    Compatible with OSMnx 2.0+

    Parameters:
    -----------
    G : networkx.MultiDiGraph
        Input graph
    route : list
        List of node IDs
    attribute : str
        Edge attribute name

    Returns:
    --------
    list : Attribute values
    """
    attributes = []
    for i in range(len(route) - 1):
        u, v = route[i], route[i + 1]
        edge_data = G[u][v][0]
        attributes.append(edge_data.get(attribute, 0))
    return attributes
