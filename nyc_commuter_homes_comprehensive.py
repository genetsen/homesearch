#!/usr/bin/env python3
"""
NYC Commuter Home Finder - Comprehensive Version
Find homes for sale within walking distance of ALL transit stops with direct routes to NYC.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import time
import os
from typing import List, Tuple, Optional
import math

# Uncomment to install: pip install homeharvest geopy
from homeharvest import scrape_property
from geopy.distance import geodesic

def load_transit_data() -> pd.DataFrame:
    """Load the pre-processed transit data with NYC connections."""
    csv_files = [f for f in os.listdir('.') if f.startswith('nj_transit_direct_to_nyc_') and f.endswith('.csv')]
    if not csv_files:
        raise FileNotFoundError("No transit data file found. Make sure nj_transit_direct_to_nyc_*.csv exists.")
    
    # Use the most recent file
    latest_file = sorted(csv_files)[-1]
    print(f"Loading transit data from: {latest_file}")
    
    transit_data = pd.read_csv(latest_file)
    print(f"Loaded {len(transit_data)} transit stops with NYC connections")
    return transit_data

def cluster_nearby_stops(transit_data: pd.DataFrame, cluster_radius_miles: float = 0.3) -> pd.DataFrame:
    """
    Cluster nearby transit stops to avoid searching the same area multiple times.
    Returns representative stops for each cluster.
    """
    print("Clustering nearby transit stops to optimize search...")
    
    # Create clusters of nearby stops
    transit_data = transit_data.copy()
    transit_data['cluster_id'] = -1
    transit_data['is_representative'] = False
    
    cluster_id = 0
    
    for idx, stop in transit_data.iterrows():
        if transit_data.loc[idx, 'cluster_id'] != -1:
            continue  # Already assigned to a cluster
            
        # Find all stops within cluster radius
        distances = transit_data.apply(
            lambda row: geodesic((stop['stop_lat'], stop['stop_lon']), 
                               (row['stop_lat'], row['stop_lon'])).miles,
            axis=1
        )
        
        nearby_stops = transit_data[distances <= cluster_radius_miles].index
        
        # Assign cluster ID
        transit_data.loc[nearby_stops, 'cluster_id'] = cluster_id
        
        # Choose representative stop (preferring rail over bus, then by importance)
        cluster_stops = transit_data.loc[nearby_stops]
        
        # Priority: rail first, then major bus hubs
        rail_stops = cluster_stops[cluster_stops['source'] == 'rail']
        if not rail_stops.empty:
            representative_idx = rail_stops.index[0]
        else:
            # Choose bus stop with most central location or important name
            representative_idx = cluster_stops.index[0]
            
        transit_data.loc[representative_idx, 'is_representative'] = True
        cluster_id += 1
    
    representatives = transit_data[transit_data['is_representative']].copy()
    
    print(f"Created {len(representatives)} representative stops from {len(transit_data)} total stops")
    return representatives

def infer_search_location(stop_data: pd.Series) -> str:
    """Infer the best search location based on stop coordinates and name."""
    stop_name = stop_data['stop_name'].upper()
    stop_lat = stop_data['stop_lat']
    stop_lon = stop_data['stop_lon']
    
    # Known locations by name
    if 'HOBOKEN' in stop_name:
        return "Hoboken, NJ"
    elif 'NEWARK' in stop_name and 'PENN' in stop_name:
        return "Newark, NJ"
    elif 'SECAUCUS' in stop_name:
        return "Secaucus, NJ"
    elif 'JOURNAL SQUARE' in stop_name:
        return "Jersey City, NJ"
    elif 'PORT AUTHORITY' in stop_name:
        # Search near the Port Authority Bus Terminal in Manhattan
        return "New York, NY"
    elif 'JERSEY CITY' in stop_name:
        return "Jersey City, NJ"
    elif 'WEEHAWKEN' in stop_name:
        return "Weehawken, NJ"
    elif 'UNION CITY' in stop_name:
        return "Union City, NJ"
    elif 'NORTH BERGEN' in stop_name:
        return "North Bergen, NJ"
    elif 'ELIZABETH' in stop_name:
        return "Elizabeth, NJ"
    elif 'BAYONNE' in stop_name:
        return "Bayonne, NJ"
    
    # Infer by coordinates (approximate boundaries)
    if 40.73 <= stop_lat <= 40.76 and -74.04 <= stop_lon <= -74.02:
        return "Hoboken, NJ"
    elif 40.73 <= stop_lat <= 40.76 and -74.08 <= stop_lon <= -74.05:
        return "Jersey City, NJ"  
    elif 40.73 <= stop_lat <= 40.74 and -74.17 <= stop_lon <= -74.15:
        return "Newark, NJ"
    elif 40.75 <= stop_lat <= 40.78 and -74.08 <= stop_lon <= -74.06:
        return "Secaucus, NJ"
    elif stop_lat >= 40.80:
        return "North Bergen, NJ"
    elif stop_lat <= 40.70 and stop_lon >= -74.10:
        return "Bayonne, NJ"
    elif stop_lat <= 40.70:
        return "Elizabeth, NJ"
    else:
        return "Jersey City, NJ"  # Default fallback

def search_properties_near_stop(stop_data: pd.Series, search_radius_miles: float = 0.5) -> pd.DataFrame:
    """Search for properties near a specific transit stop."""
    stop_name = stop_data['stop_name']
    stop_lat = stop_data['stop_lat']
    stop_lon = stop_data['stop_lon']
    
    search_location = infer_search_location(stop_data)
    
    print(f"Searching for properties near {stop_name} in {search_location}...")
    
    try:
        # Search for properties
        properties = scrape_property(
            location=search_location,
            listing_type="for_sale",
            past_days=60
        )
        
        if properties.empty:
            print(f"  No properties found in {search_location}")
            return pd.DataFrame()
        
        print(f"  Found {len(properties)} properties in {search_location}")
        
        # Filter properties within walking distance
        if 'latitude' in properties.columns and 'longitude' in properties.columns:
            # Remove properties without coordinates
            properties = properties.dropna(subset=['latitude', 'longitude'])
            
            if properties.empty:
                print(f"  No properties with coordinates found")
                return pd.DataFrame()
            
            # Calculate distance to transit stop
            properties['distance_miles'] = properties.apply(
                lambda row: geodesic((stop_lat, stop_lon), (row['latitude'], row['longitude'])).miles,
                axis=1
            )
            
            # Filter to walking distance
            walking_distance = properties[properties['distance_miles'] <= search_radius_miles].copy()
            
            if not walking_distance.empty:
                # Add transit stop information
                walking_distance['transit_stop'] = stop_name
                walking_distance['transit_type'] = stop_data['source']
                walking_distance['stop_lat'] = stop_lat
                walking_distance['stop_lon'] = stop_lon
                walking_distance['search_location'] = search_location
                
                print(f"  Found {len(walking_distance)} properties within {search_radius_miles} miles")
                return walking_distance
            else:
                print(f"  No properties within {search_radius_miles} miles")
                return pd.DataFrame()
        else:
            print(f"  Properties missing latitude/longitude data")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"  Error searching near {stop_name}: {str(e)}")
        return pd.DataFrame()

def main():
    """Main function to find homes near ALL NYC transit stops."""
    print("🏠 NYC Commuter Home Finder - COMPREHENSIVE SEARCH")
    print("=" * 60)
    
    try:
        # Load transit data
        transit_data = load_transit_data()
        
        # Cluster nearby stops to avoid redundant searches
        representative_stops = cluster_nearby_stops(transit_data, cluster_radius_miles=0.3)
        
        print(f"\nSearching properties near {len(representative_stops)} representative transit stops...")
        print("This may take a while - searching comprehensively across NJ!")
        
        # Search for properties near each representative stop
        all_properties = []
        search_radius = 0.5  # Half mile walking distance
        
        for idx, (stop_idx, stop) in enumerate(representative_stops.iterrows()):
            print(f"\n[{idx+1}/{len(representative_stops)}]", end=" ")
            
            try:
                properties = search_properties_near_stop(stop, search_radius)
                if not properties.empty:
                    all_properties.append(properties)
                
                # Add delay to avoid overwhelming the API
                time.sleep(3)  # Increased delay for comprehensive search
                
            except Exception as e:
                print(f"Error processing {stop['stop_name']}: {str(e)}")
                continue
        
        # Combine all results
        if all_properties:
            combined_properties = pd.concat(all_properties, ignore_index=True)
            
            # Remove duplicates (same property near multiple stops)
            print(f"\nRemoving duplicates from {len(combined_properties)} total property records...")
            
            if 'property_url' in combined_properties.columns:
                combined_properties = combined_properties.drop_duplicates(subset=['property_url'])
            elif 'street' in combined_properties.columns:
                combined_properties = combined_properties.drop_duplicates(subset=['street', 'city'])
            
            # Sort by distance to transit
            combined_properties = combined_properties.sort_values('distance_miles')
            
            print(f"\n🎉 Found {len(combined_properties)} unique properties within walking distance of NYC transit!")
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"nyc_commuter_homes_comprehensive_{timestamp}.csv"
            combined_properties.to_csv(output_filename, index=False)
            
            print(f"📊 Results saved to: {output_filename}")
            
            # Enhanced analytics
            print("\n📈 Comprehensive Summary:")
            print(f"Total unique properties: {len(combined_properties)}")
            print(f"Transit stops with nearby properties: {combined_properties['transit_stop'].nunique()}")
            print(f"Cities covered: {combined_properties['city'].nunique()}")
            
            if 'list_price' in combined_properties.columns:
                print(f"Price range: ${combined_properties['list_price'].min():,.0f} - ${combined_properties['list_price'].max():,.0f}")
                print(f"Median price: ${combined_properties['list_price'].median():,.0f}")
            
            # Summary by city
            print("\n📍 Properties by City:")
            city_summary = combined_properties.groupby('city').agg({
                'distance_miles': ['count', 'mean'],
                'list_price': 'median' if 'list_price' in combined_properties.columns else 'size'
            }).round(2)
            print(city_summary)
            
            # Summary by transit type
            print("\n🚉 Properties by Transit Type:")
            transit_summary = combined_properties.groupby('transit_type').agg({
                'distance_miles': ['count', 'mean'],
                'list_price': 'median' if 'list_price' in combined_properties.columns else 'size'
            }).round(2)
            print(transit_summary)
            
            # Top 15 closest properties
            print(f"\n🏆 Top 15 Properties Closest to Transit:")
            
            # Create a clean address field
            combined_properties['full_address'] = combined_properties['street'].astype(str) + ', ' + combined_properties['city'].astype(str) + ', ' + combined_properties['state'].astype(str)
            
            display_cols = ['full_address', 'transit_stop', 'distance_miles']
            if 'list_price' in combined_properties.columns:
                display_cols.append('list_price')
            if 'beds' in combined_properties.columns:
                display_cols.append('beds')
            if 'full_baths' in combined_properties.columns:
                display_cols.append('full_baths')
                
            print(combined_properties[display_cols].head(15).to_string(index=False))
            
            # Best value analysis
            if 'list_price' in combined_properties.columns and 'sqft' in combined_properties.columns:
                print(f"\n💰 Best Value Properties (price per sqft):")
                valid_sqft = combined_properties[combined_properties['sqft'].notna() & (combined_properties['sqft'] > 0)].copy()
                if not valid_sqft.empty:
                    valid_sqft['price_per_sqft_calc'] = valid_sqft['list_price'] / valid_sqft['sqft']
                    best_value = valid_sqft.nsmallest(10, 'price_per_sqft_calc')
                    value_cols = ['full_address', 'list_price', 'sqft', 'price_per_sqft_calc', 'distance_miles', 'transit_stop']
                    print(best_value[value_cols].to_string(index=False))
            
        else:
            print("\n❌ No properties found within walking distance of any transit stops.")
            print("Consider:")
            print("  - Increasing search radius")
            print("  - Checking different time periods")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
