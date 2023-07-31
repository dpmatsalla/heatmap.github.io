// Put this all into a function, like in gspeed
// then execute the function from the main html, like in gstrava

// set global styles in CSS
const style = document.createElement('style');
style.innerHTML = `
    .speedpopup {
        text-align:center;
        color:Black;
        background:White;
        font-size: 24px;
        font-weight: bold;
        padding: 0px;
        opacity: 0.5;
    }`;
document.head.appendChild(style);

//center map
var lastlat, lastlng;
if ("geolocation" in navigator) {
  navigator.geolocation.getCurrentPosition(
    function (position) {
        lastlat = position.coords.latitude;
        lastlng = position.coords.longitude;
        map123.setView([lastlat, lastlng], 13);
    },
    function (error) {
      alert("Unable to retrieve your location. " + error.message);
    }
  );
} else {
  alert("Geolocation is not available in this browser.");
}

// create blue Accuracy bubble
var accuracyCircle = L.circle([0,0],{
    stroke: false,
    color: 'cadetblue',
    fillOpacity: 0.2
}).addTo(fg123);

//create wide orange compass arrow
var compassArrow = L.polyline([], {
    color: 'orange',
    weight: 25,
    opacity: 0.30,
}).addTo(fg123);

// initiate trail
var trail = L.polyline([], {
    color: 'cadetblue',
    weight: 5,
}).addTo(fg123);
//trail.addLatLng([lastlat, lastlng]);

// Create a marker for user's location
var marker = L.marker([0,0],{}).addTo(fg123);

// create info popup on marker
var popup = L.popup({
    className: "speedpopup",
    direction:"bottom"
});
//Click event listener to marker
marker.on('click', function() {
    marker.bindPopup(popup).openPopup();
});

//create speed tooltip
var speedtt = L.tooltip();
marker.bindTooltip(speedtt, {
    className: "speedpopup",
    permanent: true,
    direction:"bottom",
    opacity: 0.5,
    offset: [0, 10],
}).openTooltip();

//create distance control
var distControl = L.control({ position:"bottomright" });
distControl.onAdd = function (map123) {
    var container = L.DomUtil.create('div', 'speedpopup');
    container.innerHTML = "";
    return container;
}
distControl.addTo(map123);
startTime = Date.now();

//Event handler for layer control change event
map123.on('overlayadd overlayremove', function(event) {
    if (event.layer === fg123) {
        if (event.type === "overlayadd") {
            map123.addControl(distControl);
        } else {
            map123.removeControl(distControl);
        }
    }
});

// Function to handle location updates
var follow_me = false;
function handleLocationUpdate(position) {
    let lat = position.coords.latitude;
    let lng = position.coords.longitude;
    let speed = position.coords.speed*3.6 || 0;
    let direction = position.coords.heading || 0;
    let accuracy = position.coords.accuracy || 0;
    var compass = null;
    var zoomLevel = map123.getZoom();

    // Update marker rotation for device orientation
    if (window.DeviceOrientationEvent) {
        window.addEventListener('deviceorientationabsolute', function(event) {
            if (event.alpha !== null) {
                //change marker orientation
                compass = -(event.alpha + event.beta * event.gamma / 90);
                compass -= Math.floor(compass / 360) * 360;
                var compassLength = 50/111320 / Math.pow(2,zoomLevel-17);
                compassArrow.setLatLngs([
                    [lat,lng],
                    [lat + compassLength*Math.cos(compass*Math.PI/180),
                     lng + compassLength*Math.sin(compass*Math.PI/180)]
                ]);
            } else { compassArrow.setLatLngs([[0,0],[0,0]]); }

            // populate contents of popup (whether open or not)
            var popupText = '('+lat+','+lng +
                ')<br>Accuracy = ' + accuracy.toFixed(1) +
                'm<br>Direction = ' + direction.toFixed(0) + 'º';
            if (event.alpha !== null) {
                popupText += '<br>Orientation = ' + compass.toFixed(0) + 'º';
            }
            popup.setContent(popupText);
        });
    } else { compassArrow.setLatLngs([[0,0],[0,0]]); }

    //update marker position, map panning, accuracy bubble
    var size = 36;  // &#9651; &#8710;
    var div_icon = L.divIcon({
        "className": "empty",
        "html":"<div style='transform: rotate("+direction+"deg);'> \
            <img src='arrow.png' width="+size+" height="+size+"></div>",
        "iconAnchor": [size/2, size/2],
        "iconSize": [size, size]
    });
    marker.setIcon(div_icon);
    marker.setLatLng([lat, lng]);
    if (follow_me) { map123.panTo([lat,lng]); }
    accuracyCircle.setLatLng([lat, lng]);
    accuracyCircle.setRadius(accuracy);

    //write speed in tooltip
    if (speed > 1) {
        speedtt.setContent(speed.toFixed(1) + ' km/h');
    } else {
        speedtt.setContent(' ');
    }

    //if position changed more than 3 m, add position to trail polyline
    if (((lat-lastlat)*111320)**2 + ((lng-lastlng)*111320)**2 > 9) {
        trail.addLatLng([lat, lng]);
        lastlat = lat;
        lastlng = lng;
    }

    //if featuregroup123 is selected then update distance and avg speed
    if (map123.hasLayer(fg123)) {
        var meters = 0;
        var latLngs = trail.getLatLngs();
        for (var i = 1; i < latLngs.length; i++) {
            meters += latLngs[i - 1].distanceTo(latLngs[i]);
        }
        var seconds = Math.floor((Date.now() - startTime) / 1000);
        avgSpd = meters/seconds*3.6;
        distControl.getContainer().innerHTML = "Dist = " + meters.toFixed(0) +
            " m<br>Avg= " + avgSpd.toFixed(1) + " km/h";
    }
}

// Function to handle location errors
function handleLocationError(error) {
    console.log('Error: ' + error.message);
}

// Continually watch for the user's location updates
var watchID = navigator.geolocation.watchPosition(handleLocationUpdate, handleLocationError, { enableHighAccuracy: true });

// Add a map scale, lower left corner
L.control.scale().addTo(map123);

// Create the follow_me centerControl
var centerControl = L.control({ position: 'topleft' });
centerControl.onAdd = function(map123) {
    var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
    container.innerHTML = '<a style="width:40px;height:40px;text-align:center;cursor:pointer"><img src="arrow.png" alt="Follow Me" width="30" height="30" style="padding-top:5px;filter: grayscale(100%) brightness(150%);"></a>';

    container.onclick = function() {
        follow_me = !follow_me;
        if (follow_me) {
            map123.locate({ setView: true, maxZoom: 16 });
            container.innerHTML = '<a style="width:40px;height:40px;text-align:center;cursor:pointer"><img src="arrow.png" alt="Unfollow" width="30" height="30" style="padding-top:5px;"></a>';
        } else {
            container.innerHTML = '<a style="width:40px;height:40px;text-align:center;cursor:pointer"><img src="arrow.png" alt="Follow Me" width="30" height="30" style="padding-top:5px;filter: grayscale(100%);"></a>';
        }
    }
    return container;
}
centerControl.addTo(map123);
