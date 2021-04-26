import sys
sys.path.append('teams/determined-seals/')

from captureAgents import CaptureAgent
import random, time, util, math
from game import Directions
import game

from positionEstimator import PositionEstimator

DEFENSIVE = 0
OFFENSIVE = 1

posEstOn = True

TOTAL_ROUNDS = 300
oppoLastObservedPoses = [None, None]
oppoLastObservedRound = [-1, -1]

class ValueIterationAgent(CaptureAgent):

  def registerInitialState(self, gameState):
    CaptureAgent.registerInitialState(self, gameState)
    # Initialise position estimator is it's enabled
    if posEstOn:
      self.posEst = PositionEstimator.get_instance(gameState, self)
    self.gameState = gameState

    self.width = gameState.data.layout.width
    self.height = gameState.data.layout.height
    if self.red:
      self.teamSideBorderX = int(gameState.getWalls().width / 2 - 1)
    else:
      self.teamSideBorderX = int(gameState.getWalls().width / 2)

    # Track information
    self.round = 0
    self.roundsRemaining = TOTAL_ROUNDS
    self.opponentPrevStates = [None, None]

    # Assign agent mode
    if self.index <= 1: # 0 or 1
      self.agentMode = OFFENSIVE
    else: # 2 or 3
      self.agentMode = DEFENSIVE

  def chooseAction(self, gameState):
    # Updates
    self.gameState = gameState
    self.round += 1
    self.roundsRemaining = TOTAL_ROUNDS - self.round
    if posEstOn:
      self.posEst.update(gameState, self)
    self.updateOppoApproxPoses(gameState)

    # Choose action
    action = self.valueIteration(gameState)

    # Records
    oppoIndices = self.getOpponents(gameState)
    self.opponentPrevStates[0] = gameState.getAgentState(oppoIndices[0])
    self.opponentPrevStates[1] = gameState.getAgentState(oppoIndices[1])

    if action == None:
      action = gameState.getLegalActions(self.index)
      return random.choice(action)
    return action

  def updateOppoApproxPoses(self, gameState):
    global oppoLastObservedPoses
    global oppoLastObservedRound
    oppoIndices = self.getOpponents(gameState)
    # If position estimator is enabled, get estimated position
    if posEstOn: 
      approxPos0 = self.posEst.getApproxPosition(oppoIndices[0])
      if approxPos0 != None:
        oppoLastObservedPoses[0] = approxPos0
        oppoLastObservedRound[0] = self.round
      approxPos1 = self.posEst.getApproxPosition(oppoIndices[1])
      if approxPos1 != None:
        oppoLastObservedPoses[1] = approxPos1
        oppoLastObservedRound[1] = self.round
    # If position estimator is disabled, get position from gameState
    else: 
      approxPos0 = gameState.getAgentPosition(oppoIndices[0])
      if approxPos0 != None:
        oppoLastObservedPoses[0] = approxPos0
        oppoLastObservedRound[0] = self.round
      approxPos1 = gameState.getAgentPosition(oppoIndices[1])
      if approxPos1 != None:
        oppoLastObservedPoses[1] = approxPos1
        oppoLastObservedRound[1] = self.round
      # Get more accurate position if there's lost food in the previous round
      lastLostFood = self.getLastLostFood()
      oppoIndices = self.getOpponents(gameState)
      if len(lastLostFood) == 2:
        # print("Found last lost food at "+str(lastLostFood))
        oppoLastObservedPoses[0] = lastLostFood[0]
        oppoLastObservedRound[0] = self.round
        oppoLastObservedPoses[1] = lastLostFood[1]
        oppoLastObservedRound[1] = self.round
      elif len(lastLostFood) == 1:
        # print("Found last lost food at "+str(lastLostFood))
        if self.opponentPrevStates[0].numCarrying - gameState.getAgentState(oppoIndices[0]).numCarrying == -1:
          oppoLastObservedPoses[0] = lastLostFood[0]
          oppoLastObservedRound[0] = self.round
        elif self.opponentPrevStates[1].numCarrying - gameState.getAgentState(oppoIndices[1]).numCarrying == -1:
          oppoLastObservedPoses[1] = lastLostFood[0]
          oppoLastObservedRound[1] = self.round
    # print("Agent "+str(self.index)+" in round "+str(self.round))
    # print("  observed positions: "+str(oppoLastObservedPoses))
    # print("  observed in rounds: "+str(oppoLastObservedRound))
    
  def getOpponentApproxPoses(self, gameState):
    approxPoses = []
    for i in range(0, 2):
      if oppoLastObservedPoses[i] != None:
        if posEstOn:
          approxPoses.append(oppoLastObservedPoses[i])
        else:
          if self.round - oppoLastObservedRound[i] <= features.ROUNDS_POS_EST_STALE:
            approxPoses.append(oppoLastObservedPoses[i])
    return approxPoses

  def getLastLostFood(self):
    if self.round <= 1:
      return []
    prevFood = self.getFoodYouAreDefending(self.getPreviousObservation()).asList()
    currFood = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()
    return list(set(prevFood) - set(currFood))

  def isOnTeamSide(self, coord):
    if self.red: #left
      return coord[0] <= self.width//2-1
    else: #right
      return coord[0] >= self.width//2

  def isOnOpponentSide(self, coord):
    return not self.isOnTeamSide(coord)
  
  ##################
  # Value Iteraion #
  ##################

  def offensiveInitValueGrid(self, gameState):
  
    #intial the value for the Grid
    foodGrid = self.getFood(gameState)
    wallGrid = gameState.getWalls()
    valueGrid = wallGrid.copy()
    for i in range(valueGrid.width):
      for j in range(valueGrid.height):
        valueGrid[i][j] = 0.0
        if wallGrid[i][j]:
          valueGrid[i][j] = None
        if foodGrid[i][j]:
          valueGrid[i][j] = 10.0
    for j in range(valueGrid.height):
      if valueGrid[self.teamSideBorderX][j] != None:
        valueGrid[self.teamSideBorderX][j] = 4.0 * gameState.getAgentState(self.index).numCarrying

    #give the rewards to the positions nearby the opponents
    opponentPositions = self.getOpponentApproxPoses(gameState)
    for opponentPosition in opponentPositions:
      for i in range(1, valueGrid.width - 1):
        for j in range(1, valueGrid.height -1):
          if abs(opponentPosition[0] - i) + abs(opponentPosition[1] - j) <= 5:
            if valueGrid[i][j] != None and self.isOnOpponentSide((i,j)):
              distance = self.getMazeDistance((i,j), opponentPosition)
              valueGrid[i][j] = -10.0 + distance

    return valueGrid

  def defensiveInitValueGrid(self, gameState):
    wallGrid = gameState.getWalls()
    valueGrid = wallGrid.copy()
    for i in range(valueGrid.width):
      for j in range(valueGrid.height):
        valueGrid[i][j] = 0.0
        if wallGrid[i][j]:
          valueGrid[i][j] = None

    opponentPositions = self.getOpponentApproxPoses(gameState)
    for opponentPosition in opponentPositions:
      (i,j) = opponentPosition
      if valueGrid[i][j] != None and self.isOnTeamSide((i,j)):
        valueGrid[i][j] = 20.0
    return valueGrid


  def valueIteration(self, gameState):
    if self.agentMode == OFFENSIVE:
      valueGrid = self.offensiveInitValueGrid(gameState)
    else:
      valueGrid = self.defensiveInitValueGrid(gameState)
    finalValueGrid = self.doValueIteration(gameState, valueGrid, True)

    (x,y) = gameState.getAgentPosition(self.index)
    maxVal = finalValueGrid[x][y]
    bestAction = 'Stop'
    #choose the best Action
    if finalValueGrid[x+1][y] != None and finalValueGrid[x+1][y] > maxVal:
      maxVal = finalValueGrid[x+1][y]
      bestAction = 'East'
    if finalValueGrid[x-1][y] != None and finalValueGrid[x-1][y] > maxVal:
      maxVal = finalValueGrid[x - 1][y]
      bestAction = 'West'
    if finalValueGrid[x][y+1] != None and finalValueGrid[x][y+1] > maxVal:
      maxVal = finalValueGrid[x][y+1]
      bestAction = 'North'
    if finalValueGrid[x][y-1] != None and finalValueGrid[x][y-1] > maxVal:
      maxVal = finalValueGrid[x][y-1]
      bestAction = 'South'

    return bestAction

  def doValueIteration(self, gameState, valueGrid, converage):
    #the value(s) will be converage to optimal value after many evaluations
    if not converage:
      return valueGrid
    else:
      flag = False
      newValueGrid = valueGrid.copy()
      foodGrid = self.getFood(gameState)
      for i in range(1, valueGrid.width - 1):
        for j in range(1, valueGrid.height - 1):
          if valueGrid[i][j] != None and not foodGrid[i][j] and valueGrid[i][j] >= 0.0:
              newValueGrid[i][j] = self.qFunction(valueGrid, i, j, 0.9)
              if newValueGrid[i][j] != valueGrid[i][j]:
                  flag = True
      return self.doValueIteration(gameState, newValueGrid, flag)

  def qFunction(self,valueGrid, x, y, gamma = 0.9):

    maxVal = valueGrid[x][y]

    if valueGrid[x - 1][y] != None:
      westVal = gamma * valueGrid[x - 1][y]
      if westVal > maxVal:
        maxVal = westVal
    if valueGrid[x + 1][y] != None:
      eastVal = gamma * valueGrid[x + 1][y]
      if eastVal > maxVal:
        maxVal = eastVal
    if valueGrid[x][y - 1] != None:
      southVal = gamma * valueGrid[x][y - 1]
      if southVal > maxVal:
        maxVal = southVal
    if valueGrid[x][y + 1] != None:
      northVal = gamma * valueGrid[x][y + 1]
      if northVal > maxVal:
        maxVal = northVal
    return maxVal
