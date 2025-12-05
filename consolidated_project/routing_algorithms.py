import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Any
import time


class RouteOptimizer:

    def __init__(self, graph):
        self.graph = graph
        self.results_cache = {}

    def dijkstra_shortest_path(self, origin, destination, weight='length'):
        start_time = time.time()

        try:
            route = nx.shortest_path(self.graph, origin, destination, weight=weight)

            length = sum(self._get_edge_attribute(route, 'length'))
            travel_time = sum(self._get_edge_attribute(route, 'travel_time'))

            computation_time = time.time() - start_time

            if weight == 'length':
                algo_name = 'Dijkstra (Distance)'
            elif weight == 'travel_time':
                algo_name = 'Dijkstra (Time)'
            elif weight == 'ml_travel_time':
                algo_name = 'Dijkstra (ML-Optimized)'
            else:
                algo_name = f'Dijkstra ({weight})'

            return {
                'route': route,
                'length_m': length,
                'time_s': travel_time,
                'computation_time': computation_time,
                'algorithm': algo_name,
                'nodes_explored': len(route)
            }
        except nx.NetworkXNoPath:
            return None

    def find_k_shortest_paths(self, origin, destination, k=3, weight='length'):
        try:
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
        attributes = []
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            edge_data = self.graph[u][v][0]
            attributes.append(edge_data.get(attribute, 0))
        return attributes

    def calculate_route_quality_metrics(self, route):
        edges = self._get_edge_attribute(route, 'highway')
        speeds = self._get_edge_attribute(route, 'speed_kph')
        lengths = self._get_edge_attribute(route, 'length')

        total_length = sum(lengths)
        avg_speed = np.mean(speeds) if speeds else 0
        speed_variance = np.var(speeds) if speeds else 0

        num_turns = len(route) - 1

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
        turns_per_km = num_turns / (total_length / 1000) if total_length > 0 else 0
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
    attributes = []
    for i in range(len(route) - 1):
        u, v = route[i], route[i + 1]
        edge_data = G[u][v][0]
        attributes.append(edge_data.get(attribute, 0))
    return attributes
