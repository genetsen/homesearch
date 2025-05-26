#!/usr/bin/env python3
"""
NYC Commuter Home Finder
Find homes for sale within walking distance of transit stops with direct routes to NYC.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import time
import os
from typing import List, Tuple, Optional

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
    print(f"Loaded {len(transit_data)} transit stops")
    return transit_data

def get_priority_stations() -> List[str]:
    """Get list of high-priority transit stations for NYC commuting."""
    return [
        'HOBOKEN',
        'NEW YORK PENN STATION', 
        'NEWARK PENN STATION',
        'FRANK R LAUTENBERG SECAUCUS LOWER LEVEL',
        'FRANK R LAUTENBERG SECAUCUS UPPER LEVEL',
        'PORT AUTHORITY BUS TERMINAL',
        'JOURNAL SQUARE TRANSPORTATION CENTER',
        'SECAUCUS JUNCTION BUS PLAZA',
        'HOBOKEN TERMINAL'
    ]

def filter_priority_stops(transit_data: pd.DataFrame) -> pd.DataFrame:
    """Filter to only high-priority transit stops for NYC commuting."""
    priority_stations = get_priority_stations()
    
    # Filter for priority rail stations
    priority_rail = transit_data[
        (transit_data['source'] == 'rail') & 
        (transit_data['stop_name'].isin(priority_stations))
    ].copy()
    
    # Filter for major bus hubs (Port Authority, Journal Square, Secaucus Junction)
    major_bus_hubs = transit_data[
        (transit_data['source'] == 'bus') & 
        (transit_data['stop_name'].isin(priority_stations))
    ].copy()
    
    # Combine and remove duplicates
    priority_stops = pd.concat([priority_rail, major_bus_hubs], ignore_index=True)
    priority_stops = priority_stops.drop_duplicates(subset=['stop_name', 'stop_lat', 'stop_lon'])
    
    print(f"Selected {len(priority_stops)} priority transit stops:")
    for _, stop in priority_stops.iterrows():
        print(f"  - {stop['stop_name']} ({stop['source']})")
    
    return priority_stops

def search_properties_near_stop(stop_data: pd.Series, search_radius_miles: float = 0.5) -> pd.DataFrame:
    """Search for properties near a specific transit stop."""
    stop_name = stop_data['stop_name']
    stop_lat = stop_data['stop_lat']
    stop_lon = stop_data['stop_lon']
    
    print(f"\nSearching for properties near {stop_name}...")
    
    # Determine search location based on stop
    if 'HOBOKEN' in stop_name.upper():
        search_location = "Hoboken, NJ"
    elif 'NEWARK' in stop_name.upper():
        search_location = "Newark, NJ"
    elif 'SECAUCUS' in stop_name.upper():
        search_location = "Secaucus, NJ"
    elif 'JOURNAL SQUARE' in stop_name.upper():
        search_location = "Jersey City, NJ"
    elif 'PORT AUTHORITY' in stop_name.upper():
        search_location = "Weehawken, NJ"  # Close to Port Authority
    else:
        # For other stops, try to infer from coordinates
        if stop_lat > 40.7 and stop_lon > -74.1:
            search_location = "Jersey City, NJ"
        elif stop_lat > 40.6 and stop_lon > -74.2:
            search_location = "Newark, NJ"  
        else:
            search_location = "New Jersey"
    
    try:
        # Search for properties
        properties = scrape_property(
            location=search_location,
            listing_type="for_sale",
            past_days=60  # Increased to get more results
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
                
                print(f"  Found {len(walking_distance)} properties within {search_radius_miles} miles of {stop_name}")
                return walking_distance
            else:
                print(f"  No properties within {search_radius_miles} miles of {stop_name}")
                return pd.DataFrame()
        else:
            print(f"  Properties missing latitude/longitude data")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"  Error searching near {stop_name}: {str(e)}")
        return pd.DataFrame()

def main():
    """Main function to find homes near NYC transit."""
    print("🏠 NYC Commuter Home Finder")
    print("=" * 50)
    
    try:
        # Load transit data
        transit_data = load_transit_data()
        
        # Filter to priority stops
        priority_stops = filter_priority_stops(transit_data)
        
        if priority_stops.empty:
            print("No priority transit stops found!")
            return
        
        # Search for properties near each priority stop
        all_properties = []
        search_radius = 0.5  # Half mile walking distance
        
        for idx, stop in priority_stops.iterrows():
            try:
                properties = search_properties_near_stop(stop, search_radius)
                if not properties.empty:
                    all_properties.append(properties)
                
                # Add delay to avoid overwhelming the API
                time.sleep(2)
                
            except Exception as e:
                print(f"Error processing {stop['stop_name']}: {str(e)}")
                continue
        
        # Combine all results
        if all_properties:
            combined_properties = pd.concat(all_properties, ignore_index=True)
            
            # Remove duplicates (same property near multiple stops)
            if 'property_url' in combined_properties.columns:
                combined_properties = combined_properties.drop_duplicates(subset=['property_url'])
            elif 'street' in combined_properties.columns:
                combined_properties = combined_properties.drop_duplicates(subset=['street', 'city'])
            
            # Sort by distance to transit
            combined_properties = combined_properties.sort_values('distance_miles')
            
            print(f"\n🎉 Found {len(combined_properties)} unique properties within walking distance of NYC transit!")
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"nyc_commuter_homes_{timestamp}.csv"
            combined_properties.to_csv(output_filename, index=False)
            
            print(f"📊 Results saved to: {output_filename}")
            
            # Display summary
            print("\n📈 Summary by Transit Stop:")
            summary = combined_properties.groupby('transit_stop').agg({
                'distance_miles': ['count', 'mean', 'min'],
                'list_price': 'median' if 'list_price' in combined_properties.columns else 'size'
            }).round(2)
            print(summary)
            
            # Show top 10 closest properties
            print(f"\n🏆 Top 10 Properties Closest to Transit:")
            
            # Create a clean address field
            combined_properties['full_address'] = combined_properties['street'].astype(str) + ', ' + combined_properties['city'].astype(str) + ', ' + combined_properties['state'].astype(str)
            
            display_cols = ['full_address', 'transit_stop', 'distance_miles']
            if 'list_price' in combined_properties.columns:
                display_cols.append('list_price')
            if 'beds' in combined_properties.columns:
                display_cols.append('beds')
            if 'full_baths' in combined_properties.columns:
                display_cols.append('full_baths')
                
            print(combined_properties[display_cols].head(10).to_string(index=False))
            
        else:
            print("\n❌ No properties found within walking distance of priority transit stops.")
            print("Consider:")
            print("  - Increasing search radius")
            print("  - Expanding to more transit stops")
            print("  - Checking different time periods")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
