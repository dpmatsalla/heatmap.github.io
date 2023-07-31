"""
To do
-on blank_map page, should we post the data and then plot it from Javascript side?  I.e. include another JS file into the folium map with the plot_map
-plot just the map & marker, have button for loading the data, then data appears
-customise colors?  have a button that leads to a settings page
-select either folium or googlemaps and make def in main.py
-show progress of download - by printing a number of activities loaded and refreshing the download page every 2 sec

https://www.strava.com/settings/api
200 requests every 15 minutes, 2,000 daily

To get token:
http://www.strava.com/oauth/authorize?client_id=108742&response_type=code&redirect_uri=https://stravaheatmap.pythonanywhere.com/callback&approval_prompt=force&scope=activity:read_all

help:
https://www.markhneedham.com/blog/2020/12/15/strava-authorization-error-missing-read-permission/
https://github.com/ndoornekamp/strava-plotter/blob/master/strava_connection.py
https://github.com/domoritz/leaflet-locatecontrol
http://leaflet-extras.github.io/leaflet-providers/preview/

response = [{'resource_state': 2,
'athlete': {'id': 22764388, 'resource_state': 1},
'name': 'Morning Run', 'distance': 6813.9, 'moving_time': 2283, 'elapsed_time': 2399, 'total_elevation_gain': 53.0,
'type': 'Run', 'sport_type': 'Run', 'workout_type': None, 'id': 9216259109,
'start_date': '2023-06-06T20:03:29Z', 'start_date_local': '2023-06-07T04:03:29Z', 'timezone': '(GMT+08:00) Australia/Perth',
'utc_offset': 28800.0, 'location_city': None, 'location_state': None, 'location_country': 'Australia',
'achievement_count': 0, 'kudos_count': 7, 'comment_count': 0, 'athlete_count': 1, 'photo_count': 0,
'map': {'id': 'a9216259109', 'summary_polyline': 'AAAAA', 'resource_state': 2},
'trainer': False, 'commute': False, 'manual': False, 'private': False, 'visibility': 'everyone', 'flagged': False, 'gear_id': None, 'start_latlng': [-31.949614053592086, 115.8565980847925], 'end_latlng': [-31.949797114357352, 115.85386633872986],
'average_speed': 2.985, 'max_speed': 6.268, 'average_cadence': 81.2, 'average_temp': 18, 'has_heartrate': True, 'average_heartrate': 142.2, 'max_heartrate': 157.0, 'heartrate_opt_out': False, 'display_hide_heartrate_option': True, 'elev_high': 33.6, 'elev_low': 12.2,
'upload_id': 9887592665, 'upload_id_str': '9887592665', 'external_id': 'garmin_ping_278174572396', 'from_accepted_tag': False, 'pr_count': 0, 'total_photo_count': 0, 'has_kudoed': False},
"""

from flask import Flask, redirect, request, render_template
import json
import requests
import polyline
import folium
#from folium import plugins
from branca.element import Element

app = Flask(__name__)

# Strava API credentials
CLIENT_ID = "108742"
CLIENT_SECRET = "ab3fdd70c8b66837005361fa7c17eb53ddf0cdf1"

# Endpoint URLs
AUTHORIZE_URL = 'https://www.strava.com/oauth/authorize'
REDIRECT_URI = 'https://stravaheatmap.pythonanywhere.com/callback'
TOKEN_URL = 'https://www.strava.com/oauth/token'
API_URL = 'https://www.strava.com/api/v3'

# Global variables to store access token and athlete ID
access_token = None
athlete_id = None
new_activities = 0
comments = []
refresh = False

# Flask route for initial authentication
@app.route('/')
def index():
    global refresh
    refresh = False
    return render_template('index.html')

@app.route('/authorize', methods=["POST"])
def authorize():
    auth_url = f"{AUTHORIZE_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&approval_prompt=auto&scope=activity:read_all"
    return redirect(auth_url)

#open JSON file and load data
def load_json(json_file):
    global comments
    try:
        with open("static/"+json_file, 'r') as file:
            data = json.load(file)
        comments.append(f"{json_file} loaded successfully.")
        return data
    except FileNotFoundError:
        comments.append(f"{json_file} not found, so will need to create one.")
    except json.JSONDecodeError:
        comments.append(f"Error: Failed to decode JSON from {json_file}.")
    except:
    	comments.append(f"Other error loading {json_file}.")
    return None

def save_json(data, json_file):
    global comments
    try:
        with open("static/"+json_file, 'w') as file:
            json.dump(data, file)
        comments.append(f"{json_file} saved.")
    except:
    	comments.append(f"Error saving {json_file}.")
    return

def get_token(code):
    global access_token, athlete_id, comments
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    }
    response = requests.post(TOKEN_URL, data=payload)
    if response.status_code == 200:
        access_token = response.json()['access_token']
        athlete_id = response.json()['athlete']['id']
        comments.append("Login successful!")
        return True
    else:
        comments.append("Login failed.")
        return False

# Make a request to get the authenticated user's activities
def get_page_data(per_page=100, page=1):
    global access_token, comments
    url = f"{API_URL}/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {'per_page': per_page, 'page': page}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        page_data = response.json()
        if page_data:
            return page_data
        else:
            return None
    else:
        comments.append("Failed to retrieve activities.")
        return None

#return all new records since data last saved in JSON -- last_activity_id
def update_data(last_activity_id):
    global comments, new_activities
    done = False
    new_data = list()
    page_num = 0
    while not done:
        page_num += 1
        page_data = get_page_data(page=page_num, per_page=10)
        if page_data == None:
            done = True
            break
        for page in page_data:
            if int(page["id"]) > int(last_activity_id):
                new_data.append(page)
            else:
                done = True
                break
    new_activities = len(new_data)
    comments.append(f"{new_activities} activities updated since activity {last_activity_id}.")
    return new_data

#replace all data independent of any JSON
def refresh_data():
    global comments, new_activities
    max_pages = 50
    data = list()
    for page_num in range(1, max_pages + 1):
        page_data = get_page_data(page=page_num)
        if page_data == None:
            break
        for page in page_data:
            data.append(page) #use extend instead?
    if data == []:
    	comments.append("No data available.")
    new_activities = len(data)
    comments.append(f"{new_activities} activities obtained.")
    return data

def get_comments(data):
    comments.append("")
    comments.append("Last Activities:")
    a = 1  #count of last activities to print
    for activity in data:
        coords = polyline.decode(activity["map"]["summary_polyline"])
        if coords:
            loc = coords[0]
        else:
        	loc = "()"
        comments.append(f"{a} {activity['id']} {activity['start_date'][:10]} {loc} {activity['distance']/1000:.1f} km {activity['type']}, elev={activity['total_elevation_gain']:.0f}m, {activity['name']}")
        a += 1
    return

def get_Strava_data():
    global access_token, athlete_id, refresh
    if not access_token or not athlete_id:
        return redirect('/')

    #if we're not refreshing the data, then get the JSON file if it exists
    if refresh:
        data = None
    else:
        data = load_json(str(athlete_id)+".json")

    if data:
        #Update Strava data
        data = update_data(data[0]["id"]) + data
    else:
    	#Either we're refreshing, or there's no JSON, so refresh the JSON
        data = refresh_data()

    get_comments(data)
    return data

#plot folium map
def plot_map():
    global comments

    #now setup the map centred on the last ride
    map = folium.Map(location=[-27.5,153], tiles='cartodbpositron', zoom_start=13)

    # add possible tiles
    folium.TileLayer('cartodbdark_matter').add_to(map)
    folium.TileLayer('openstreetmap').add_to(map)
    folium.TileLayer('http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        name='googleStreets',
        max_zoom=20,
        subdomains=['mt0','mt1','mt2','mt3'],
        attr='google Streets'
    ).add_to(map)
    folium.TileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        name='googleSatellite',
        max_zoom=20,
        subdomains=['mt0','mt1','mt2','mt3'],
        attr='google Satellite'
    ).add_to(map)
    folium.TileLayer('stamentoner').add_to(map)
    folium.TileLayer('stamenterrain').add_to(map)
    folium.TileLayer('white.png', name='White', attr='Custom Mosaic Tile').add_to(map)
    folium.TileLayer('black.png', name='Black', attr='Custom Mosaic Tile').add_to(map)

    comments.append("Map plotted.")
    return map

def plot_data(map, data):
    global comments

    # add decoded summary polylines
    t = 0  #count of unique types
    types = {}  #create dictionary of types and respective featuregroup
    featuregroup = []   #feature groups that contain the unique activity types
    for activity in data:
        type = activity["type"]
        coords = polyline.decode(activity["map"]["summary_polyline"])

        if coords:
            #extract unique activity types and create featuregroups for each one
            if type not in types:
            	types[type] = t
            	featuregroup.append(folium.FeatureGroup(name=type))
            	t += 1

            #find record in activities and determine colour
            if type in ('Ride', 'EBikeRide'): c = 'blue'
            elif type in ('RollerSki', 'InlineSkate', 'Skateboard'): c = 'darkblue'
            elif type in ('Run', 'Soccer'): c = 'darkred'
            elif type in ('Hike', 'Walk', 'Golf'): c = 'purple'
            elif type in ('Swim', 'Kayaking', 'Canoeing', 'Rowing', 'Canoe', 'StandUpPaddling', 'Surfing'): c = 'green'
            elif type in ('NordicSki', 'AlpineSki', 'IceSkate', 'Snowboard'): c = 'magenta'
            else: c = 'grey'

            folium.PolyLine(
                locations=coords,
                color=c,
                weight=1,
                opacity=1,
                popup=f"<a href='https://www.strava.com/activities/{activity['id']}' target='_blank'>{activity['id']}</a><br>{activity['start_date'][:10]}<br>{activity['distance']/1000:.1f} km {type}<br>'{activity['name']}'"
            ).add_to(featuregroup[types[type]])

    for type in types:
    	featuregroup[types[type]].add_to(map)

    comments.append(f"{len(types)} different activity types plotted.")
    return

def plot_marker(map):
    global comments

    #feature group that contains my position, accuracy bubble, speed, trails
    featureme = folium.FeatureGroup(name='My Location').add_to(map)

    #add all of the featuregroups to the map (must be done after populating the featuregroups
    folium.LayerControl(setview='always').add_to(map) #needs to go later after script?

    #Add some html to the header of the map file
    js = """
        <title>Strava Heatmap</title>
        <link rel="icon" type="image/x-icon" href="/static/logo.ico">
        <script>
            window.onbeforeunload = function() {
               return "Leave site?";
            }
        </script>
    """
    map.get_root().header.add_child(Element(js))

    #Add some JavaScript to the end of the map file
    map_id = map.get_name()                 #get the map name used in the folium script
    featureme_id = featureme.get_name()     #get the featuregroup name used in the folium script so that I can add position marker, etc against it
    map.get_root().render()                 #add JavaScript functions to the END of the script (by rendering first)

    #load the javascript, replace occurrences of the map_id and featuregroup then add it to the map file
    with open('static/speed.js', 'r') as file:
        js = file.read()
    js = js.replace("map123", map_id)
    js = js.replace("fg123", featureme_id)
    map.get_root().script.add_child(Element(js))

    comments.append("Marker plotted.")
    return

def save_map(map, map_file):
    global comments
    map.save("static/"+map_file)
    comments.append(f"{map_file} saved.")
    return


# Create a map without Strava Data
@app.route('/blank_map', methods=['POST'])
def blank_map():
    map = plot_map()
    plot_marker(map)
    save_map(map, "blank_map.html")
    return redirect("/static/blank_map.html")   #map._repr_html_()

# Flask route for callback URL after authentication
# populates the access_token and athlete_id
@app.route('/callback', methods=['GET', 'POST'])
def callback():
    global comments, athlete_id, refresh
    comments = []

    code = request.args.get('code')

    if code:
        #get a token
        if get_token(code):
            comments.append("Authorization token successfully obtained.")
        else:
            return "Failed authorization token"
    elif request.args.get('refresh'):
        refresh = True
        comments.append("Request made to refresh cache.")
    else:
        return "No args in callback."

    comments.append(f"refresh = {refresh}")
    return render_template('download.html',athlete_id=athlete_id, comments=comments)

#download screen
@app.route('/download', methods=['POST'])
def download():
    global comments, new_activities, athlete_id

    data = get_Strava_data()  #refresh all data
    send_comments = comments[0:11]+['...']

    #only if there are new activities do we need to update the map and JSON
    if new_activities > 0:
        map = plot_map()
        plot_data(map, data)
        plot_marker(map)
        save_map(map, str(athlete_id)+".html")
        save_json(data, str(athlete_id)+".json")

    return render_template('download_end.html',athlete_id=athlete_id, comments=send_comments)

#downloading and drawing done
@app.route('/download_end', methods=['POST'])
def download_end():
    global comments, new_activities, athlete_id

    if request.args.get('print'):  #this download has already been run once, and they pressed the print data button, so go to print screen
        send_comments = comments
    else:
        send_comments = comments[0:11]+['...']

    return render_template('download_end.html',athlete_id=athlete_id, comments=send_comments)

#download_end screen
@app.route('/goto_map', methods=['POST'])
def goto_map():
    global athlete_id
    return redirect("/static/"+str(athlete_id)+".html")   #map._repr_html_()

if __name__ == '__main__':
    app.run(debug=True)
