from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation

from IPython.display import HTML
from random import random
from random import choice
from random import randrange
import numpy as np
import uuid

# --------------------------- Información en JSON ---------------------------
def getData(model):
  # Regresa información de los agentes para formar el JSON.
  data = {
      "vehicleAgents": [],
      "lightAgents": []
  }

  lightAgents = []
  vehicleAgents = []

  # Obtiene el ID, la posición y el estatus de cada agente en la lista
  for agent in model.scheduler.agents:
    vehicleAgentData = {}
    lightAgentData = {}

    if isinstance(agent, VehicleAgent):
      if agent.pos != None:
        (x, y) = agent.pos
        vehicleAgentData["index"] = agent.unique_id
        vehicleAgentData["x"] = y
        vehicleAgentData["z"] = x
        vehicleAgents.append(vehicleAgentData)
    elif isinstance(agent, LightAgent):
      lightAgentData["index"] = agent.unique_id
      lightAgentData["status"] = agent.status
      lightAgents.append(lightAgentData)

  data["vehicleAgents"] = vehicleAgents
  data["lightAgents"] = lightAgents

  return data

# ----------------------------- Agente Vehículo -----------------------------
class VehicleAgent(Agent):
  '''
  Agente inteligente vehículo que se estaciona por un determinado tiempo.
  Recibe como entrada el estado de movimiento, duración de tiempo estacionado,
  target de luz más cercana, y si tiene una reservación hecha.
  '''
  def __init__(self, unique_id, model, isParked, parkedTime, lightTarget, hasReservation):
    super().__init__(unique_id, model)
    # Indica si el vehículo está llegando y buscando un espacio de estacionamiento
    self.isParking = False
    # Indica si el vehículo está estacionado
    self.isParked = isParked
    # Indica si el vehículo está saliendo de su espacio de estacionamiento
    self.isLeaving = False
    # Cantidad de tiempo (steps) que el vehículo permanece estacionado
    self.parkedTime = parkedTime
    # Luz indicadora en el espacio al que se quiere mover
    self.lightTarget = lightTarget
    # Salida a la que se quiere mover
    self.exitTarget = None
    # Indica si el vehículo inicia con reservación
    self.hasReservation = hasReservation

  def getTarget(self):
    '''
    Si el vehículo todavía no tiene objetivo o si se ocupó en un step anterior:
    Calcula nuevo target, buscando el espacio libre más cercano.
    '''
    minDistance = float('inf')
    (i, j) = self.pos
    foundTarget = False

    # Revisa todos los cajones de estacionamiento
    for (tI, tJ) in self.model.parkingSpaces:
      # Obtiene la luz indicadora del cajón
      agents = self.model.grid.get_cell_list_contents([(tI, tJ)])
      for agent in agents:
        if isinstance(agent, LightAgent) and agent.status == 0:
          # Obtiene las coordenadas de entrada al cajón libre más cercano
          distance = abs(i - agent.entryPoint[0]) + abs(j - agent.entryPoint[1])
          if (distance < minDistance):
            minDistance = distance
            self.lightTarget = agent
            foundTarget = True

    # Si ya no quedan espacios disponibles, se sale del estacionamiento
    if not foundTarget:
      self.lightTarget = None
      self.getExit()

  def getExit(self):
    '''
    Obtiene el target de la salida más cercana al vehículo.
    '''
    (x, y) = self.pos
    width = self.model.width
    height = self.model.height

    # Obtiene la salida en el segundo cuadrante
    if x <= height // 2 and y <= width // 2:
      self.exitTarget = (0, 0)
    # Obtiene la salida en el primer cuadrante
    elif x <= height // 2 and y >= width // 2:
      self.exitTarget = (1, 14)
    # Obtiene la salida en el cuarto cuadrante
    elif x >= height // 2 and y >= width // 2:
      self.exitTarget = (13, 14)
    # Obtiene la salida en el tercer cuadrante
    elif x >= height // 2 and y <= width // 2:
      self.exitTarget = (12, 0)

  def move(self):
    '''
    Mueve el vehículo a la siguiente posición hacia su target, siguiendo las
    indicaciones de los carriles de estacionamiento.
    '''
    # Si el vehículo está estacionado
    if self.isParked:
      # Disminuye el tiempo restante estacionado
      self.parkedTime -= 1
      movedOut = False

      # Si ya terminó su tiempo estacionado
      if (self.parkedTime == 0):
        (x, y) = self.pos

        # Obtiene el agente luz en su celda
        agents = self.model.grid.get_cell_list_contents([self.pos])
        lightAgent = None
        for agent in agents:
          if isinstance(agent, LightAgent):
            lightAgent = agent
        # Si está en una fila par, se mueve hacia arriba para salir del cajón
        if x % 2 == 0:
          # Revisa que otro vehículo no esté obstruyendo su salida
          if self.isClear((x - 1, y)):
            lightAgent.status = 0
            self.model.grid.move_agent(self, (x - 1, y))
            movedOut = True
        # Si está en una fila impar, se mueve hacia abajo para salir del cajón
        else:
          # Revisa que otro vehículo no esté obstruyendo su salida
          if self.isClear((x + 1, y)):
            lightAgent.status = 0
            self.model.grid.move_agent(self, (x + 1, y))
            movedOut = True

        # Si pudo salirse del cajón de estacionamiento
        if movedOut:
          # Comienza el proceso de salir del estacionamiento
          self.isParked = False
          self.isLeaving = True
          self.lightTarget = None
          self.getExit()
        else:
          # Pausa su tiempo estacionado
          self.parkedTime += 1

    else:
      # Obtiene el agente direccional de la celda
      agents = self.model.grid.get_cell_list_contents([self.pos])
      dirAgent = None

      for agent in agents:
        if isinstance(agent, DirectionAgent):
          dirAgent = agent

      (x, y) = self.pos
      # Si tiene target de salida, se dirige hacia la salida
      if self.exitTarget != None:
        self.getExit()
        (tX, tY) = self.exitTarget
      # Si tiene target de luz, se dirige al espacio de estacionamiento
      else:
        (tX, tY) = self.lightTarget.entryPoint

      # Moverse a la única dirección posible
      if dirAgent.count == 1:
        if dirAgent.canGoUp and self.isClear((x - 1, y)): self.model.grid.move_agent(self, (x - 1, y))
        elif dirAgent.canGoRight and self.isClear((x, y + 1)): self.model.grid.move_agent(self, (x, y + 1))
        elif dirAgent.canGoDown and self.isClear((x + 1, y)): self.model.grid.move_agent(self, (x + 1, y))
        elif dirAgent.canGoLeft and self.isClear((x, y - 1)): self.model.grid.move_agent(self, (x, y - 1))
      # Tiene más de una dirección posible
      else:
        nextPos = (x, y)

        # X: ROWS || Y: COLUMNS
        if x > tX + 1 or x < tX - 1:
          # Se posiciona en el renglón del target
          if x < tX and dirAgent.canGoDown: nextPos = (x + 1, y)
          elif x > tX and dirAgent.canGoUp: nextPos = (x - 1, y)
          # Si no alcanza el renglon, redirigirse a otra dirección
          elif dirAgent.canGoUp: nextPos = (x - 1, y)
          elif dirAgent.canGoDown: nextPos = (x + 1, y)
        else:
          # Se posiciona en la columna del target
          if y < tY and dirAgent.canGoRight and (y + 1 < self.model.grid.width):
            nextPos = (x, y + 1)
          elif y > tY and dirAgent.canGoLeft and (y - 1 >= 0):
            nextPos = (x, y - 1)
          # Si no alcanza la columna, redirigirse a otra dirección
          elif dirAgent.canGoUp: nextPos = (x - 1, y)
          elif dirAgent.canGoRight: nextPos = (x, y + 1)
          elif dirAgent.canGoDown: nextPos = (x + 1, y)
          elif dirAgent.canGoLeft: nextPos = (x, y - 1)

        if self.isClear(nextPos):
          self.model.grid.move_agent(self, nextPos)

      (x, y) = self.pos
      # Si se está dirigiendo hacia un cajón de estacionamiento
      if self.exitTarget == None:
        # Si ya está a 1 o 2 espacios, se estaciona en el espacio
        if y == tY and (x <= tX + 1 and x >= tX - 1):
          self.isParking = True
          self.lightTarget.status = 2

  def isClear(self, nextPos):
    '''
    Revisa que la próxima posición no esté ocupada por un vehículo.
    '''
    agents = self.model.grid.get_cell_list_contents([nextPos])
    for agent in agents:
      if isinstance(agent, VehicleAgent):
        return False
    return True

  def park(self):
    '''
    Cambia el estado del vehículo a estacionado y detiene su movimiento.
    '''
    (x, y) = self.pos
    (tX, tY) = self.lightTarget.pos

    if (x < tX) and self.isClear((x + 1, y)):
      self.model.grid.move_agent(self, (x + 1, y))
    elif (x > tX) and self.isClear((x - 1, y)):
      self.model.grid.move_agent(self, (x - 1, y))
    if (x == tX):
      self.isParked = True
      self.isParking = False

  def step(self):
    '''
    Estados:
    0 --> Inicializado en una fila de vehículos a colocar
    1 --> Colocado en el tablero
    2 --> Dirigiendo a un espacio de estacionamiento
    3 --> Estacionando en el espacio
    4 --> Estacionado
    5 --> Saliendo del espacio de estacionamiento
    6 --> Saliendo del tablero

    Transiciones:
    0 --> 1: Sale de la fila de vehículos a colocar
    1 --> 2: Busca espacio más cercano o reservación
    2 --> 3: Se mueve a la posición del entry point
    3 --> 4: Se mueve a la posición del cajón
    4 --> 5: Termina el tiempo estacionado
    5 --> 6: Busca salida más cercana
    2 --> 5: No encuentra lugar de estacionamiento
    '''
    # Si es un vehículo con movimiento y ya está instanciado
    if (self.pos != None and self.parkedTime != -1):
      # Si está buscando un lugar de estacionamiento
      if not self.isParking and not self.isLeaving:
        if not self.hasReservation:
          self.getTarget()
        self.move()
      # Si se está estacionando
      elif self.isParking:
        self.park()
      # Si se está saliendo del cajón de estacionamiento
      elif self.isLeaving:
        self.move()

      # Si ya llegó a la salida, elimina el agente
      if self.pos == self.exitTarget:
        self.model.grid.remove_agent(self)
        del self
        return

# -------------------------------- Agente Luz --------------------------------
class LightAgent(Agent):
  '''
  Agente inteligente luz que indica el estado de disponibilidad del cajón de estacionamiento.
  '''
  def __init__(self, unique_id, model, status):
    super().__init__(unique_id, model)
    # Indica el estado de disponibilidad del cajón
    self.status = status
    # Coordenadas de entrada al cajón de estacionamiento
    self.entryPoint = (0, 0)
    # Cantidad de tiempo que es reservado el espacio
    self.reservedTime = -1
    # Agente del vehículo que realiza la reservación
    self.reservationHolder = None

  def step(self):
    '''
    Estados:
    0 --> Espacio disponible (Verde)
    1 --> Espacio reservado (Amarillo)
    2 --> Espacio ocupado (Rojo)

    Transiciones:
    0 --> 1: Un vehículo reserva el espacio
    1 --> 2: Un vehículo se estaciona en el espacio
    0 --> 2: Un vehículo se estaciona en el espacio
    2 --> 0: El vehículo estacionado sale del espacio
    1 --> 0: El tiempo de reservación se acaba
    '''
    # Si está reservado el espacio
    if self.status == 1:
      # Disminuye el tiempo restante reservado
      self.reservedTime -= 1
      # Cuando el tiempo se acaba, libera el espacio
      if self.reservedTime == 0:
        self.status = 0
        self.reservationHolder.hasReservation = False

    # Si un vehículo está ocupando el espacio, el estado marca ocupado
    agents = self.model.grid.get_cell_list_contents([self.pos])
    for agent in agents:
      if isinstance(agent, VehicleAgent):
        self.status = 2

class DirectionAgent(Agent):
  '''
  Agente estático de direccionamiento. Sirve como guía para las direcciones a las
  que se puede mover el agente vehículo dependiendo del sentido del carril.
  '''
  def __init__(self, unique_id, model, canGoUp, canGoRight, canGoDown, canGoLeft):
    super().__init__(unique_id, model)
    count = 0
    self.canGoUp = canGoUp
    self.canGoRight = canGoRight
    self.canGoDown = canGoDown
    self.canGoLeft = canGoLeft
    # Cantidad de direcciones posibles que puede tener la celda
    self.count = sum([canGoUp, canGoRight, canGoDown, canGoLeft])

# -------------------------- Modelo Estacionamiento --------------------------
class ParkingLot(Model):
  '''
  Modelo estacionamiento de tamaño 15 x 14 que contiene agentes de vehículos y
  luces indicadoras. Recibe como entrada la cantidad de vehículos estacionados a
  instanciar, los vehículos temporalmente estacionados, los vehículos que estarán
  en movimiento durante la simulación, el porcentaje de spawn aleatorio, el porcentaje
  de reservaciones aleatorias, y el tiempo de reservación.

  Posibles estados de inicio para agente vehículo:
    -> Inicia en un espacio ya estacionado, con un tiempo de espera (random) y
      después del tiempo se va
      -> Espacio marcado como ocupado -> Luz Roja
    -> Inicia en un espacio ya estacionado, pero nunca se mueve
      -> Espacio marcado como ocupado -> Luz Roja
    -> Inicia en una de las cuatro entradas (random)
      -> Busca el espacio más cercano
      -> Reserva un espacio y se dirige a su reservación
  '''
  def __init__(self, numPermVehicles, numTempVehicles, numActiveVehicles, spawnPercentage, reservePercentage, reservationHoldingTime):
    super().__init__()
    self.width = 15
    self.height = 14
    self.scheduler = SimultaneousActivation(self)
    self.grid = MultiGrid(self.height, self.width, False)
    # Contador de vehículos a activar durante la simulación
    self.numActiveVehicles = numActiveVehicles
    # Porcentaje de creación aleatoria de vehículos
    self.spawnPercentage = spawnPercentage
    # Porcentaje de reservación de espacios
    self.reservePercentage = reservePercentage
    # Tiempo que dura una reservación
    self.reservationHoldingTime = reservationHoldingTime
    # Lista de TODOS los cajones de estacionamiento
    self.parkingSpaces = []
    # Lista de los cajones de estacionamiento reservados
    self.reservedSpaces = []
    # Lista de vehículos en fila para ser posicionados
    self.vehicleQueue = []

    # Crear agentes de luces indicadoras en cada cajón de estacionamiento
    idLights = 0
    numRow = [2, 3, 6, 7, 10, 11]

    for i in numRow:
      for j in range(2, 13, 1):
        if (j != 7):
          light = LightAgent(str(idLights) + "-Light", self, 0)
          idLights += 1
          # Por todas las luces pares, su entrada es arriba
          if (i % 2 == 0):
            light.entryPoint = (i - 1, j)
          # Por todas las luces impares, su entrada es abajo
          else:
            light.entryPoint = (i + 1, j)
          self.scheduler.add(light)
          self.grid.place_agent(light, (i, j))
          self.parkingSpaces.append((i, j))

    # Crea árboles en el centro del estacionamiento
    self.treesList = []
    for i in numRow:
      self.treesList.append((i, 7))

    # Crea agentes direccionales para indicar el sentido de los carriles
    idDirections = 0

    for i in range(self.height):
      for j in range(self.width):
        # Direcciones posibles que puede tener una celda
        canGoUp = False
        canGoRight = False
        canGoDown = False
        canGoLeft = False

        if ((j == 1) or (j == 14)) and (i != 0):
          canGoUp = True
        if (((i == 5) or (i == 9)) and (j != 14)) or ((i == 1) or (i == 13)):
          canGoRight = True
        if ((j == 0) or (j == 13)) and (i != 13):
          canGoDown = True
        if (((i == 4) or (i == 8)) and (j != 0)) or ((i == 0) or (i == 12)):
          canGoLeft = True

        direction = DirectionAgent(str(idDirections) + "-Direction", self, canGoUp, canGoRight, canGoDown, canGoLeft)
        idDirections += 1
        self.grid.place_agent(direction, (i, j))

    # Limita la cantidad de vehículos dada al número de espacios
    if numPermVehicles + numTempVehicles > len(self.parkingSpaces):
      numPermVehicles = len(self.parkingSpaces)
      numTempVehicles = 0

    # Crea y coloca vehículos permanentes
    self.placeParkedVehicles(numPermVehicles, -1)

    # Crea y coloca vehículos temporales
    self.placeParkedVehicles(numTempVehicles, 0)

    # Crea primeros vehículos en movimiento y los agrega a la fila
    spawnCount = min(4, numActiveVehicles)
    for i in range(spawnCount):
      # isParked, parkedTime, lightTarget
      vehicle = VehicleAgent(str(uuid.uuid4()), self, False, randrange(5, 50, 5), None, False)
      self.scheduler.add(vehicle)
      self.vehicleQueue.append(vehicle)

  def placeParkedVehicles(self, numVehicles, parkedTime):
    '''
    Coloca los vehículos estacionados al inicio de la simulación en espacios aleatorios.
    '''
    for i in range(numVehicles):
      # Genera un tiempo aleatorio para los vehículos estacionados temporalmente
      if parkedTime != -1:
        parkedTime = randrange(5, 50, 2)
      # Escoge una posición aleatoria en el estacionamiento
      pos = choice(self.parkingSpaces)
      # Si la posición está ocupada por otro vehículo o reservada, escoge una nueva
      while (pos in self.reservedSpaces):
        pos = choice(self.parkingSpaces)
      # Agrega el vehículo al modelo y al tablero
      vehicle = VehicleAgent(str(uuid.uuid4()), self, True, parkedTime, None, False)
      self.scheduler.add(vehicle)
      self.grid.place_agent(vehicle, pos)
      self.reservedSpaces.append(pos)

  def spawnVehicles(self):
    '''
    Genera y coloca vehículos en movimiento en las 4 entradas del estacionamiento
    durante la simulación, con un porcentaje de spawn aleatorio.
    '''
    # Lista de coordenadas de puntos de entrada
    spawnPoints = [(1,0), (13,0), (0,14), (12,14)]

    for pos in spawnPoints:
      # Mientras existan vehículos en la fila, por cada entrada calcula el % random
      if random() < self.spawnPercentage and len(self.vehicleQueue) > 0:
        # Coloca el vehículo en la entrada y lo elimina de la fila
        self.grid.place_agent(self.vehicleQueue.pop(), pos)
        self.numActiveVehicles -= 1
        # Mientras existan vehículos por crear, sigue agregando a la fila
        if self.numActiveVehicles > len(self.vehicleQueue):
          vehicle = VehicleAgent(str(uuid.uuid4()), self, False, randrange(5, 50, 2), None, False)

          # Decisión de reservación de espacio
          if random() < self.reservePercentage:
            lightFound = False
            i = 0
            # Escoge un espacio aleatoriamente para reservar
            while (i < 60 and not lightFound):
              pos = choice(self.parkingSpaces)
              agents = self.grid.get_cell_list_contents([pos])

              for agent in agents:
                if isinstance(agent, LightAgent) and not lightFound:
                  # Si la luz está disponible
                  if agent.status == 0:
                    # Cambia el estado de la luz a reservado
                    agent.status = 1
                    vehicle.lightTarget = agent
                    vehicle.hasReservation = True
                    lightFound = True
                    agent.reservedTime = self.reservationHoldingTime
                    agent.reservationHolder = vehicle
              i += 1

          self.scheduler.add(vehicle)
          self.vehicleQueue.append(vehicle)

  def step(self):
    '''
    Avanza una iteración en el modelo.
    '''
    self.scheduler.step()
    # Mientras existan vehículos en la fila por agregar al tablero
    if len(self.vehicleQueue) <= 4 and len(self.vehicleQueue) > 0:
      self.spawnVehicles()