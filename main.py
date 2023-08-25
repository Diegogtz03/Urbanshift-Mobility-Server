import json
from flask import Flask, render_template

from CarPark import ParkingLot

app = Flask(__name__)

numVehicles = 10
parkingSim = ParkingLot(numVehicles)

@app.route('/')
def index():
    parkingSim.step()
    animation = parkingSim.generateAnim()
    data = parkingSim.getData()
    return render_template('index.html', animation=animation, data=data)

app.run()