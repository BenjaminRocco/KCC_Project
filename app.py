from flask import Flask, render_template
from parser import get_florida_hurricanes, get_florida_hurricanes_spatial
import folium

app = Flask(__name__)

def generate_storm_map(storms_list):
    m = folium.Map(location=[27.7662, -82.6868], zoom_start=6, tiles="CartoDB positron")
    for storm in storms_list:
        popup_text = f"<strong>{storm['name']}</strong><br>Date: {storm['date']}<br>Max Wind: {storm['max_wind']} kts"
        pin_color = 'red' if storm['max_wind'] >= 115 else ('orange' if storm['max_wind'] >= 83 else 'green')
        folium.Marker(
            location=[storm['latitude'], storm['longitude']],
            popup=folium.Popup(popup_text, max_width=200),
            icon=folium.Icon(color=pin_color, icon='info-sign')
        ).add_to(m)
    return m._repr_html_()

@app.route('/')
def index():
    try:
        # 1. Gather indicator-validated sets
        storms_indicator = get_florida_hurricanes()
        map_indicator_html = generate_storm_map(storms_indicator)
        
        # 2. Gather geometry-calculated spatial sets (without indicator)
        storms_spatial = get_florida_hurricanes_spatial()
        map_spatial_html = generate_storm_map(storms_spatial)
        
        return render_template(
            'index.html', 
            storms_ind=storms_indicator, 
            map_ind_html=map_indicator_html,
            storms_spat=storms_spatial,
            map_spat_html=map_spatial_html,
            error=None
        )
    except Exception as e:
        return render_template('index.html', storms_ind=[], map_ind_html="", storms_spat=[], map_spat_html="", error=str(e))

if __name__ == '__main__':
    app.run(debug=True)