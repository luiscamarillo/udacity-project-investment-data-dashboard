from myapp import app
import json, plotly
from flask import render_template
from wrangling_scripts.wrangle_data import create_charts

@app.route('/')
@app.route('/index')
def index():

    figures, values_dict = create_charts()

    # plot ids for the html id tag
    ids = [f'figure-{i}' for i, _ in enumerate(figures)]

    # Convert the plotly figures to JSON for javascript in html template
    figuresJSON = json.dumps(figures, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html',
                           ids=ids,
                           figuresJSON=figuresJSON,
                           values_dict=values_dict)