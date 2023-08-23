import mesa
import numpy as np
from random import choice
import uuid
import time

# Agente Vehiculo
class VehicleAgent(mesa.Agent):
  def __init__(self, unique_id, model, parkedTime, target, smartSystem):
    super().__init__(unique_id, model)

    self.isParked = False
    self.parkedTime = parkedTime
    self.path = []
    self.target = target
    self.smartSystem = smartSystem

  def park(self):
    # isParked = true
    print(f"Soy el agente VEHICULO {self.unique_id} y me estoy estacionando")

  def move(self):
    # Mover a la siguiente posición en el arrgelo de path
    print(f"Soy el agente VEHICULO {self.unique_id} y me estoy moviendo, POS: {self.pos}")

  def step(self):
    if(not self.isParked):
      self.calcPath()
      self.move()
      self.park()
      self.smartSystem.reserveParkingSpot(self)

  def calcPath(self):
    if self.target == None or self.target.status == 2: #Si todavía no tiene objetivo o si se ocupó en un step anterior:
      # Calcular nuevo target, buscando el espacio más cercano
      # Calcular path de tiles que hay que seguir para ir al objetivo.
      self.path = [(0,1), (1,0), (2,0)]
      print(f"Soy el agente VEHICULO {self.unique_id} y estoy calculando la ruta")

# Agente Luz
class LightAgent(mesa.Agent):
  def __init__(self, unique_id, model, status):
    super().__init__(unique_id, model)
    '''
    STATUS:
    0 --> Espacio disponible (Verde)
    1 --> Espacio reservado (Amarillo)
    2 --> Espacio ocupado (Rojo)
    '''
    self.status = status

  def step(self):
    print(f"Soy el agente LUZ {self.unique_id} y mi estado es {self.status}")


# Agente Sistema Inteligente
class SmartSystem(mesa.Agent):
  def __init__(self, unique_id, model):
    super().__init__(unique_id, model)

    self.reservedSpaces = []

  def reserveParkingSpot(self, vehicle):
    # Buscar un espacio disponible, reservar el espacio, y retornar el espacio reservado
    # Buscar la luz en ese espacio y solicitar el cambio de color
    # cambiar el nuevo espacio
    new_target = (1, 2)
    vehicle.pos = new_target

  def step(self):
    print(f"Soy el sistema inteligente {self.unique_id}")


# Modelo
class ParkingLot(mesa.Model):
  def __init__(self, N, M, numVehicles):
    super().__init__()
    self.width = N
    self.height = M
    self.scheduler = mesa.time.SimultaneousActivation(self)
    self.grid = mesa.space.MultiGrid(N, M, False)

    grid_coords = list(self.grid.coord_iter())

    smartSystemAgent = SmartSystem(uuid.uuid4(), self)
    self.scheduler.add(smartSystemAgent)

    numLights = 10

    for i in range(numLights):
      _, pos = choice(grid_coords)
      light = LightAgent(uuid.uuid4(), self, 0)
      self.scheduler.add(light)
      self.grid.place_agent(light, pos)

    for i in range(numVehicles):
      _, pos = choice(grid_coords)
      vehicle = VehicleAgent(uuid.uuid4(), self, 5, None, smartSystemAgent)
      self.scheduler.add(vehicle)
      self.grid.place_agent(vehicle, pos)

  def step(self):
    self.scheduler.step()