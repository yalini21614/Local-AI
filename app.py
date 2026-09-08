import math
import urllib.parse
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="/static")

def get_location_name(lat, lon):
    """Get city or area name from lat, lon"""
    headers = {'User-Agent': 'LocalPlaceFinderBot/2.0 (contact@example.com)'}
    url = 'https://nominatim.openstreetmap.org/reverse'
    params = {'lat': lat, 'lon': lon, 'format': 'json', 'accept-language': 'en'}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=5)
        if r.status_code == 200:
            addr = r.json().get('address', {})
            area = (addr.get('suburb') or 
                    addr.get('town') or 
                    addr.get('city') or 
                    addr.get('county') or 
                    addr.get('state_district') or 
                    'your area')
            city = addr.get('city') or addr.get('town') or ''
            return area, city
    except Exception:
        pass
    return "nearby", ""

def search_osm(query, lat, lon):
    """Search OpenStreetMap Nominatim"""
    headers = {'User-Agent': 'LocalPlaceFinderBot/2.0 (contact@example.com)'}
    url = "https://nominatim.openstreetmap.org/search"
    
    # Try searching with bounding box first
    params = {
        'q': query,
        'format': 'json',
        'addressdetails': 1,
        'limit': 15,
        'viewbox': f"{lon-0.12},{lat+0.12},{lon+0.12},{lat-0.12}",
        'bounded': 1
    }
    data = []
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
    except Exception:
        pass
        
    # If no results, try broader search with area name
    if not data:
        area, city = get_location_name(lat, lon)
        search_term = f"{query} {city}".strip() if city else f"{query} {area}".strip()
        params = {
            'q': search_term,
            'format': 'json',
            'addressdetails': 1,
            'limit': 15
        }
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
        except Exception:
            pass

    results = []
    for item in data:
        try:
            item_lat = float(item['lat'])
            item_lon = float(item['lon'])
            R = 6371000
            dlat = math.radians(item_lat - lat)
            dlon = math.radians(item_lon - lon)
            a = (math.sin(dlat / 2) ** 2 + 
                 math.cos(math.radians(lat)) * math.cos(math.radians(item_lat)) * 
                 math.sin(dlon / 2) ** 2)
            dist = int(2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a)))
            
            disp = item.get('display_name', '')
            name = item.get('name') or disp.split(',')[0]
            gmaps = f"https://www.google.com/maps/search/?api=1&query={item_lat},{item_lon}"
            results.append({
                "name": name,
                "address": disp,
                "distance_m": dist,
                "lat": item_lat,
                "lon": item_lon,
                "google_maps_url": gmaps
            })
        except Exception:
            continue

    results.sort(key=lambda x: x['distance_m'])
    return results

@app.route('/')
def index():
    return send_from_directory('', 'index.html')

@app.route('/search', methods=['GET'])
def search():
    try:
        lat = float(request.args.get('lat', 9.9029))
        lon = float(request.args.get('lon', 78.0390))
        query = request.args.get('q', 'biryani').strip()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    area, city = get_location_name(lat, lon)
    results = search_osm(query, lat, lon)
    
    # Direct Google Maps query URL for instant 100% accurate fallback
    gmaps_search_query = f"{query} near {lat},{lon}"
    direct_gmaps_url = f"https://www.google.com/maps/search/{urllib.parse.quote(gmaps_search_query)}"

    return jsonify({
        "status": "success",
        "area": area,
        "city": city,
        "query": query,
        "direct_google_maps_url": direct_gmaps_url,
        "count": len(results),
        "results": results
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
