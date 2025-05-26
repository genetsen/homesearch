# NYC Commuter Home Finder

A Python tool to find homes for sale within walking distance of public transit stops with direct routes to New York City. Perfect for commuters looking for convenient access to NYC from New Jersey.

## 🎯 What This Does

This project helps you find residential properties that are:
- **For sale** in the current market
- **Within walking distance** (0.5 miles) of major transit stops
- **Connected by direct routes** to NYC (rail and express bus)
- **Focused on premium transit hubs** like Hoboken, Journal Square, Newark Penn Station {TODO: this needs to be updated to focused on stops with express service to NYC}

## 📊 Key Results

From the latest analysis:
- **81 unique properties** found within walking distance of NYC transit
- **4 major transit hubs** with nearby properties:
  - **Journal Square Transportation Center** - 46 properties (median price: $724,500)
  - **Hoboken** - 25 properties (median price: $800,000)  
  - **Newark Penn Station** - 6 properties (median price: $654,900)
  - **Hoboken Terminal** - 4 properties (median price: $537,000)

## 🚉 Transit Stops Covered

### Rail Stations (NJ Transit & PATH)
- **Hoboken** - Major hub with PATH to 33rd St, World Trade Center
- **Newark Penn Station** - NJ Transit & Amtrak to Penn Station NYC
- **Secaucus Junction** - Transfer hub for multiple train lines
- **New York Penn Station** - Direct access to Manhattan

### Major Bus Hubs  
- **Journal Square Transportation Center** - Multiple bus routes to NYC
- **Port Authority Bus Terminal** - Direct bus access to Midtown Manhattan
- **Hoboken Terminal** - Bus and ferry connections

## 🏠 Sample Properties Found

**Closest to Transit:**
1. **282 Magnolia Ave, Jersey City** - 0.18 miles from Journal Square - $430,000 (2br/1ba)
2. **551 Pavonia Ave, Jersey City** - 0.19 miles from Journal Square - $1,500,000 (6br/2ba)  
3. **123 Washington St, Hoboken** - 0.26 miles from Hoboken Station - $545,000 (1br/1ba)

## 🛠 Setup & Installation

### Prerequisites
```bash
pip install homeharvest geopy pandas numpy
```

### Files Needed
- `nj_transit_direct_to_nyc_[timestamp].csv` - Transit stop data (included)
- `nyc_commuter_homes.py` - Main analysis script

### Usage
```bash
python nyc_commuter_homes.py
```

## 📁 Output Files

The script generates:
- `nyc_commuter_homes_[timestamp].csv` - Complete property data with transit distances
- Terminal output with summary statistics and top properties

## 🔧 Customization

### Adjust Search Radius
```python
search_radius = 0.5  # Change to 0.25 for stricter walking distance or 1.0 for wider search
```

### Add More Transit Stops
Edit the `get_priority_stations()` function to include additional stations.

### Change Search Timeframe  
```python
past_days=60  # Change to search different time periods
```

## 📈 Analysis Features

- **Distance calculation** using geospatial coordinates
- **Duplicate removal** to avoid counting same property multiple times
- **Price analysis** with median prices by transit stop
- **Walking distance filtering** (default 0.5 miles)

## 🎯 Best Commuter Areas Found

1. **Journal Square, Jersey City** - Best value with most options
2. **Hoboken** - Premium location, higher prices, excellent transit
3. **Newark** - More affordable options, good rail connections

## 🚀 Future Enhancements

- Add ferry connections (Hoboken, Weehawken)
- Include commute time estimates  
- Add school district ratings
- Property price trend analysis
- Interactive map visualization

## 📝 Data Sources

- **Property Data**: HomeHarvest (Realtor.com scraping)
- **Transit Data**: NJ Transit GTFS feeds
- **Distance Calculations**: Geopy (geodesic distance)

## ⚠️ Notes

- Property data is current as of scan date
- Walking distances are straight-line calculations
- Transit schedules and routes can change
- Prices and availability subject to market conditions

---

**Built for NYC commuters seeking the perfect balance of convenience and value! 🏠🚊🗽**
