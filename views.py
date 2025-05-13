from flask import render_template
#from models import Modelo sin crear
from run import app

@app.route('/')
def index():
    return render_template('index.html')
