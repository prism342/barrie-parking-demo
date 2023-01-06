let graphicsLayer = null

let add_polygon = null

let current_page = "dashboard"

dataServerAddress = "http://34.130.118.110:8001"

const xhr = new XMLHttpRequest()

function get_default_date_range(){
    var today = new Date();
    var start_date = new Date();

    // past year
    start_date.setYear(start_date.getFullYear() - 1);

    //past month
    //start_date.setMonth(start_date.getMonth() - 1);

    return [date_to_str(start_date), date_to_str(today)]
}

function date_to_str(date){
    var dd = String(date.getDate()).padStart(2, '0');
    var mm = String(date.getMonth() + 1).padStart(2, '0'); //January is 0!
    var yyyy = date.getFullYear();

    today = yyyy + '-' + mm + '-' + dd;
    
    return today;
}


function get_data_by_dates(start_date, end_date){
    revenue_by_space = document.getElementById("toggleRevenuePerSpace").checked

    if(!revenue_by_space){
        xhr.open("GET", dataServerAddress + "/get_gis_revenue_data?start_date=" + start_date + "&end_date=" + end_date)}
    else{
        xhr.open("GET", dataServerAddress + "/get_gis_revenue_per_space_data?start_date=" + start_date + "&end_date=" + end_date)}
        
    xhr.send()

    xhr.onload = function() {
        if (xhr.status === 200) {
          //parse JSON datax`x
          data = JSON.parse(xhr.responseText)
          color_revenue_range = data["color_revenue_range"]
          revenue_data = data["data"]

          document.getElementById("revenue_range_left").textContent = "" + color_revenue_range[0] + "$";
          document.getElementById("revenue_range_right").textContent = "≥ " + color_revenue_range[1] + "$";

          revenue_data.forEach((e)=>{
            add_polygon(e["name"], e["description"], e["rings"], e["color"]);
          })
          
        } else if (xhr.status === 404) {
          console.log("No records found")
        }
      }
}

const onUpdateData = ()=>{
    start_date = document.getElementById("start_date").value
    end_date = document.getElementById("end_date").value
    
    graphicsLayer.removeAll();
    get_data_by_dates(start_date, end_date);
}

const onSelectDate = onUpdateData;

const onToggleRevenuePerSpace = onUpdateData;

const onSwitchPage = ()=>{
    if (current_page == "dashboard"){
        document.getElementById("dashboard").style.display = "none";
        document.getElementById("gisvisual").style.display = "inline-block";
        document.getElementById("switch_page").textContent = "Show Dashboard";
        current_page = "gisvisual";
    }
    else{
        document.getElementById("dashboard").style.display = "inline-block";
        document.getElementById("gisvisual").style.display = "none";
        document.getElementById("switch_page").textContent = "Show GIS Visual";
        current_page = "dashboard";
    }
}

require([
    "esri/config",
    "esri/Map",
    "esri/views/MapView",

    "esri/Graphic",
    "esri/layers/GraphicsLayer"

], function(esriConfig, Map, MapView, Graphic, GraphicsLayer) {

    esriConfig.apiKey = "AAPK424c44c9f9c242f1bf364e89c097a7fdY5NOuVpBjhGMGKUrT4n63dRwQ6sB71ypNpsSDYw48scHIVbh_VtiMgPKjdDM0BF8";

    // create map and set map center
    const map = new Map({
        basemap: "arcgis-topographic" //Basemap layer service
    });

    const view = new MapView({
        map: map,
        center: [-79.687013, 44.385862], //Barrie: Longitude, latitude
        zoom: 15,
        container: "viewDiv"
    });

    graphicsLayer = new GraphicsLayer();
    map.add(graphicsLayer);


    // add a polygon to graphicsLayer
    add_polygon = (name, discription, rings, color) => {
        const polygon = {
            type: "polygon",
            rings: rings
        };

        const simpleFillSymbol = {
            type: "simple-fill",
            color: color, 
            style: "solid",
            outline: {  // autocasts as new SimpleLineSymbol()
                color: color,
                width: 1
            }
        };

        const popupTemplate = {
            title: "{Name}",
            content: "{Description}"
        }
        const attributes = {
            Name: name,
            Description: discription
        }

        const polygonGraphic = new Graphic({
            geometry: polygon,
            symbol: simpleFillSymbol,

            attributes: attributes,
            popupTemplate: popupTemplate

        });

        graphicsLayer.add(polygonGraphic);
    }

    add_polygon = add_polygon;

    view.on("pointer-move", (event) => {

        view.hitTest(event).then(function(response) {
            var filtered_graphics = response.results.filter((result) => {
                return result.graphic.layer === graphicsLayer;
            })
            if (filtered_graphics.length) {

                var graphic = filtered_graphics[0].graphic;

                if (typeof view.poppedup === undefined || view.poppedup !== graphic) {
                    view.popup.open({
                        location: graphic.geometry.centroid,
                        features: [graphic]
                    });
                    view.poppedup = graphic;
                } else {
                    //already popped up
                }
            } else {
                if (typeof view.poppedup !== undefined || graphic.poppedup !== null) {
                    view.popup.close();
                    view.poppedup = null
                }
            }
        });
    });

    date_range = get_default_date_range();
    console.log(date_range);

    document.getElementById("start_date").value = date_range[0];
    document.getElementById("end_date").value = date_range[1];
    get_data_by_dates(date_range[0], date_range[1]);
});




