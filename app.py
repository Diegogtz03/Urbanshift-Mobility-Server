from flask import Flask, request
from ParkingSim import ParkingLot, getData

app = Flask(__name__)

numPermVehicles = 3
numTempVehicles = 5
numActiveVehicles = 50
spawnPercentage = 0.2
reservePercentage = 0.1
badAgentPercentage = 0
reservationHoldingTime = 15

parkingSim = ParkingLot(numPermVehicles, numTempVehicles, numActiveVehicles, spawnPercentage, reservePercentage, reservationHoldingTime, badAgentPercentage)

@app.route('/step')
def index():
  parkingSim.step()
  data = getData(parkingSim)

  return data


@app.route('/reset')
def resetModel():
  global parkingSim
  parkingSim = ParkingLot(numPermVehicles, numTempVehicles, numActiveVehicles, spawnPercentage, reservePercentage, reservationHoldingTime, badAgentPercentage)
  return "OK"

@app.route('/change', methods=['POST'])
def changeModel():
  global numPermVehicles, numTempVehicles, numActiveVehicles, spawnPercentage, reservePercentage, reservationHoldingTime
  numPermVehicles = int(request.form['numPermVehicles'])
  numTempVehicles = int(request.form['numTempVehicles'])
  numActiveVehicles = int(request.form['numActiveVehicles'])
  spawnPercentage = float(request.form['spawnPercentage'])
  reservePercentage = float(request.form['reservePercentage'])
  badAgentPercentage = float(request.form['badAgentPercentage'])
  reservationHoldingTime = int(request.form['reservationHoldingTime'])

  global parkingSim
  parkingSim = ParkingLot(numPermVehicles, numTempVehicles, numActiveVehicles, spawnPercentage, reservePercentage, reservationHoldingTime, badAgentPercentage)
  return "OK"


@app.route('/results')
def getResults():
  vehicleParkData = parkingSim.vehicleParkData
  reserveParkData = parkingSim.reserveParkData
  reservationsExpired = parkingSim.reservationsExpired

  if vehicleParkData:
    avgVehiclePark = sum(vehicleParkData) / len(vehicleParkData)
  else:
    avgVehiclePark = 0
  if reserveParkData:
    avgReservePark = sum(reserveParkData) / len(reserveParkData)
  else:
    avgReservePark = 0
  
  data = {
    "first": f'El promedio de steps que tardaron los vehiculos sin reservacion en estacionarse fue: {avgVehiclePark}',
    "second": f'El promedio de steps que tardaron los vehiculos con reservacion previa en estacionarse fue: {avgReservePark}',
    "third": f'La cantidad de reservaciones expiradas durante la simulacion fueron: {reservationsExpired}'
  }

  return data

app.run()