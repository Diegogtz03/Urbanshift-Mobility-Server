from flask import Flask
from ParkingSim import ParkingLot

app = Flask(__name__)

n = 10
m = 10
numVehicles = 10
steps = 2

parkingSim = ParkingLot(n, m, numVehicles)

@app.route('/api/request_step')
def index():
  parkingSim.step()
  return "I'm Alive!!"

app.run()