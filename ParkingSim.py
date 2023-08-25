from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
matplotlib.use("Agg")

from IPython.display import HTML
from random import choice
import numpy as np
import uuid
import time

def getGrid(model):
  '''
  Genera el tablero del modelo usado para animar la simulación.
  Para el colormap, utiliza códigos de celdas correspondientes a:
  0: Celda vacía
  1: Luz indicadora
  2: Vehículo
  '''
  # Genera la matriz de ceros
  grid = np.zeros((model.grid.width, model.grid.height))
  # Recorre todas las celdas del tablero y obtiene el código de cada celda
  for cell in model.grid.coord_iter():
    content, (x, y) = cell
    # Verifica el tipo de agente con isinstance
    for agent in content:
      if isinstance(agent, LightAgent):
        grid[x][y] = 1
      elif isinstance(agent, VehicleAgent):
        grid[x][y] = 2
  return grid

class VehicleAgent(Agent):
  '''
  Agente inteligente vehículo que se estaciona por un determinado tiempo.
  Recibe como entrada el estado de movimiento, tiempo a estacionar,
  arreglo del path, y destino.
  '''
  def __init__(self, unique_id, model, parkedTime, target):
    super().__init__(unique_id, model)
    self.isParked = False
    self.parkedTime = parkedTime
    self.path = []
    self.target = target

  def calcPath(self):
    '''
    Si todavía no tiene objetivo o si se ocupó en un step anterior:
    Calcular nuevo target, buscando el espacio más cercano.
    Calcular path de tiles que hay que seguir para ir al objetivo.
    '''
    if self.target == None or self.target.status == 2:
      self.path = [(0,1), (1,0), (2,0)]
      print(f"Soy el agente VEHICULO {self.unique_id} y estoy calculando la ruta")

  def move(self):
    '''
    Mueve el vehículo a la siguiente posición en el arreglo del path.
    '''
    print(f"Soy el agente VEHICULO {self.unique_id} y me estoy moviendo, POS: {self.pos}")

  def park(self):
    '''
    Cambia el estado del vehículo a estacionado y detiene su movimiento.
    '''
    # isParked = true
    print(f"Soy el agente VEHICULO {self.unique_id} y me estoy estacionando")

  def step(self):
    '''
    [Explicar lógica de máquina de estados]
    '''
    if not self.isParked:
      self.calcPath()
      self.move()
      self.park()
      self.model.reserveParkingSpot(self)

class LightAgent(Agent):
  '''
  Agente inteligente luz que indica el estado de disponibilidad del cajón de estacionamiento.
  '''
  def __init__(self, unique_id, model, status):
    super().__init__(unique_id, model)
    self.status = status

  def step(self):
    '''
    [Explicar lógica de máquina de estados]
    STATUS:
    0 --> Espacio disponible (Verde)
    1 --> Espacio reservado (Amarillo)
    2 --> Espacio ocupado (Rojo)
    '''
    print(f"Soy el agente LUZ {self.unique_id}, estado={self.status}, pos={self.pos}")

class ParkingLot(Model):
  '''
  Modelo estacionamiento de tamaño 25 x 50 que contiene agentes de vehículos y luces indicadoras.
  Recibe como entrada la cantidad de vehículos a instanciar.
  '''
  def __init__(self, numVehicles):
    super().__init__()
    self.width = 25
    self.height = 50
    self.scheduler = SimultaneousActivation(self)
    self.grid = MultiGrid(self.width, self.height, False)
    # Lista de todos los agentes en el modelo
    self.agentsList = []
    # Lista de los cajones de estacionamiento reservados
    self.reservedSpaces = []

    # Crea y coloca agentes de luces indicadoras en frente de cada cajón de estacionamiento
    yValues = [5, 11, 13, 19]
    for y in yValues:
      for x in range(5, 46, 4):
        if (x < 22) or (x > 28):
          light = LightAgent(str(uuid.uuid4()), self, 0)
          self.scheduler.add(light)
          self.grid.place_agent(light, (y, x))
          self.agentsList.append(light)

    # Crea la lista de coordenadas de los espacios de estacionamiento
    yValues = [6, 10, 14, 18]
    gridCoords = []
    for y in yValues:
      for x in range(5, 46, 4):
        if (x < 22) or (x > 28):
          gridCoords.append((y, x))
    
    # Limita la cantidad de vehículos dada al número de espacios
    if numVehicles > len(gridCoords):
      numVehicles = len(gridCoords)
    
    # Crea y coloca aleatoriamente un nuevo agente vehículo en un espacio
    for i in range(numVehicles):
      pos = choice(gridCoords)
      # Si el espacio está ocupado o reservado por otro vehículo, escoger otro
      while pos in self.reservedSpaces:
        pos = choice(gridCoords)
      vehicle = VehicleAgent(str(uuid.uuid4()), self, 5, None)
      self.scheduler.add(vehicle)
      self.grid.place_agent(vehicle, pos)
      self.agentsList.append(vehicle)
      self.reservedSpaces.append(pos)

    # Obtiene la información del modelo
    self.datacollector = DataCollector(model_reporters={"Grid": getGrid})

  def reserveParkingSpot(self, vehicle):
    '''
    Busca un espacio disponible, reserva el espacio, y retorna el espacio reservado.
    Busca la luz en ese espacio y solicita el cambio de color.
    Cambia el nuevo espacio.
    '''
    new_target = (1, 2)
    vehicle.pos = new_target

  def getData(self):
    '''
    Regresa información de los agentes para formar el JSON.
    '''
    data = {}
    # Obtiene el ID y la posición de cada agente en la lista
    for agent in self.agentsList:
      data[agent.unique_id] = agent.pos
    return data

  def generateAnim(self):
    '''
    Genera la animación del tablero en HTML con la información del modelo.
    '''
    # Obtiene el tablero con toda la información del modelo
    allGrid = self.datacollector.get_model_vars_dataframe()

    # Colormap de la animación
    cmapAgent = plt.cm.colors.ListedColormap(['white','blue','red'])
    bounds = [0, 1, 2, 3]
    norm = plt.cm.colors.BoundaryNorm(bounds, cmapAgent.N)

    # Crea los ejes para la figura
    fig, axs = plt.subplots()
    axs.set_xticks([])
    axs.set_yticks([])

    # Anima la información del tablero
    patch = plt.imshow(allGrid.iloc[0][0], cmap=cmapAgent, norm=norm)
    def animate(i):
      patch.set_data(allGrid.iloc[i][0])

    # Regresa la animación en formato HTML
    anim = animation.FuncAnimation(fig, animate, frames=len(allGrid))
    return HTML(anim.to_jshtml())

  def step(self):
    '''
    Avanza una iteración en el modelo.
    '''
    # Obtiene información del modelo y agrega al tablero
    self.datacollector.collect(self)
    self.scheduler.step()