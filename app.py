from flask import Flask, request
from ParkingSim import ParkingLot, getData

app = Flask(__name__)

numPermVehicles = 3
numTempVehicles = 5
numActiveVehicles = 50
spawnPercentage = 0.2
reservePercentage = 0.1
reservationHoldingTime = 15

parkingSim = ParkingLot(numPermVehicles, numTempVehicles, numActiveVehicles, spawnPercentage, reservePercentage, reservationHoldingTime)

@app.route('/step')
def index():
  parkingSim.step()
  data = getData(parkingSim)

  return data


@app.route('/reset')
def resetModel():
  global parkingSim
  parkingSim = ParkingLot(numPermVehicles, numTempVehicles, numActiveVehicles, spawnPercentage, reservePercentage, reservationHoldingTime)
  return "OK"

@app.route('/change', methods=['POST'])
def changeModel():
  global numPermVehicles, numTempVehicles, numActiveVehicles, spawnPercentage, reservePercentage, reservationHoldingTime
  numPermVehicles = int(request.form['numPermVehicles'])
  numTempVehicles = int(request.form['numTempVehicles'])
  numActiveVehicles = int(request.form['numActiveVehicles'])
  spawnPercentage = float(request.form['spawnPercentage'])
  reservePercentage = float(request.form['reservePercentage'])
  reservationHoldingTime = int(request.form['reservationHoldingTime'])

  global parkingSim
  parkingSim = ParkingLot(numPermVehicles, numTempVehicles, numActiveVehicles, spawnPercentage, reservePercentage, reservationHoldingTime)
  return "OK"


app.run()