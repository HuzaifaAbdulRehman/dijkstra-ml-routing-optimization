"""
FIXED MAP VISUALIZATION - Routes Follow Actual Streets!

Replace the create_comprehensive_route_map function in Cell 14/28 with this version.
This uses actual road geometry instead of straight lines between nodes.
"""

def create_comprehensive_route_map(G, routes, origin, destination):
    """
    Create professional interactive map with routes following ACTUAL streets.

    FIX: Uses edge geometry from OSM data instead of straight lines between nodes.
    """
    import folium
    from shapely.geometry import LineString, Point

    # Get coordinates
    origin_point = (G.nodes[origin]['y'], G.nodes[origin]['x'])
    dest_point = (G.nodes[destination]['y'], G.nodes[destination]['x'])

    # Create map
    m = folium.Map(
        location=origin_point,
        zoom_start=13,
        tiles='OpenStreetMap'
    )

    # Route colors and styles
    route_styles = {
        'distance': {
            'color': '#3498db',      # Blue
            'weight': 7,
            'opacity': 0.6,
            'dash_array': None,
            'name': 'Traditional (Distance)'
        },
        'time_original': {
            'color': '#e74c3c',      # Red
            'weight': 6,
            'opacity': 0.7,
            'dash_array': '10, 5',   # Dashed
            'name': 'Time-based'
        },
        'ml_optimized': {
            'color': '#2ecc71',      # Green
            'weight': 5,
            'opacity': 0.9,
            'dash_array': None,
            'name': 'ML-Optimized (Best)'
        }
    }

    # Add routes with ACTUAL geometry
    for key in ['distance', 'time_original', 'ml_optimized']:
        route_data = routes.get(key)
        if route_data:
            style = route_styles[key]
            route_nodes = route_data['route']

            # ============================================================
            # FIX: Build route using ACTUAL edge geometry
            # ============================================================
            route_coords = []

            for i in range(len(route_nodes) - 1):
                u, v = route_nodes[i], route_nodes[i + 1]

                # Get edge data (first edge if multiple)
                edge_data = G[u][v][0]

                # Check if edge has geometry (curved roads)
                if 'geometry' in edge_data:
                    # Use actual road geometry
                    geom = edge_data['geometry']
                    # Extract coordinates from geometry
                    coords = list(geom.coords)
                    # Add as (lat, lon) - note the order!
                    for coord in coords:
                        route_coords.append((coord[1], coord[0]))  # (lat, lon)
                else:
                    # No geometry - use straight line between nodes
                    # (this happens for very short road segments)
                    if i == 0:  # Add start point
                        route_coords.append((G.nodes[u]['y'], G.nodes[u]['x']))
                    route_coords.append((G.nodes[v]['y'], G.nodes[v]['x']))

            # Remove duplicate consecutive points
            cleaned_coords = [route_coords[0]]
            for coord in route_coords[1:]:
                if coord != cleaned_coords[-1]:
                    cleaned_coords.append(coord)

            # ============================================================
            # Create polyline with ACTUAL road path
            # ============================================================
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

    # Add origin marker
    folium.Marker(
        origin_point,
        popup='<b>ORIGIN</b><br>Starting Point',
        tooltip='Start Here',
        icon=folium.Icon(color='green', icon='play', prefix='fa')
    ).add_to(m)

    # Add destination marker
    folium.Marker(
        dest_point,
        popup='<b>DESTINATION</b><br>End Point',
        tooltip='End Here',
        icon=folium.Icon(color='red', icon='stop', prefix='fa')
    ).add_to(m)

    # Enhanced legend
    legend_html = f'''
    <div style="position: fixed; top: 10px; right: 10px; width: 320px;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:13px; padding: 15px; border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">

    <h4 style="margin: 0 0 10px 0; color: #333;">
        🗺️ Route Comparison Dashboard
    </h4>

    <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
        <p style="margin: 5px 0;"><span style="color: #3498db; font-size: 20px;">━━━</span>
           <b>Traditional</b> (Distance-based)</p>
        <p style="margin: 5px 0;"><span style="color: #e74c3c; font-size: 20px;">╍╍╍</span>
           <b>Time-based</b> (Speed limits)</p>
        <p style="margin: 5px 0;"><span style="color: #2ecc71; font-size: 20px;">━━━</span>
           <b>ML-Optimized</b> (Best) ⭐</p>
    </div>

    <hr style="margin: 10px 0;">

    <div style="font-size: 11px; color: #666;">
        <p style="margin: 3px 0;"><b>Network:</b> {NETWORK_STATS['nodes']:,} intersections</p>
        <p style="margin: 3px 0;"><b>ML Model:</b> {best_model}</p>
        <p style="margin: 3px 0;"><b>Features:</b> 15+ road characteristics</p>
    </div>

    <hr style="margin: 10px 0;">

    <div style="font-size: 10px; background: #fff3cd; padding: 8px; border-radius: 4px;">
        ✅ <b>Routes now follow actual streets!</b>
        Lines follow real road geometry from OpenStreetMap.
    </div>

    <div style="margin-top: 10px; font-size: 10px; color: #999; text-align: center;">
        💡 Click routes for details
    </div>

    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


# ============================================================================
# HOW TO USE THIS FIX
# ============================================================================

"""
1. Copy this entire function
2. Go to Cell 14 (or Cell 28) in your notebook
3. Replace the old create_comprehensive_route_map function with this one
4. Re-run Cell 14 to regenerate the map
5. Routes will now follow actual streets perfectly!

WHAT CHANGED:
- Old code: Connected nodes with straight lines
- New code: Uses edge 'geometry' attribute from OSM
- Result: Routes follow actual curved roads

NOTE: Make sure to import at the top:
from shapely.geometry import LineString, Point
(This should already be available if osmnx is installed)
"""
