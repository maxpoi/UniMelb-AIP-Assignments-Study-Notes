import sys
import util
from game import Actions
from capture import SIGHT_RANGE, SONAR_NOISE_RANGE, noisyDistance
import distanceCalculator
import math

"""
For observing opponents positions
By using
1. position when distance <= 5
2. food got eaten
3. noisy distance
"""

EPSILON = sys.float_info.epsilon

class PositionEstimator():
  # __instance__ = None
  red = None
  blue = None
  
  def __init__(self, gameState, agent, forRed):
    """
    Constructor.
    """
    if forRed and PositionEstimator.red is None:
      self.width = gameState.data.layout.width
      self.height = gameState.data.layout.height

      self.walls = gameState.getWalls()
      self.walkablePositions = self.getWalkablePositions()
      self.distancer = distanceCalculator.Distancer(gameState.data.layout)

      self.numPlayers = gameState.getNumAgents()
      self.team = agent.getTeam(gameState) # assume only 1 teammate, also assume smaller index will be created first
      self.opponents = agent.getOpponents(gameState) # do we need to store this? since we are passing agent into update

      ######################
      # book keeping facts #
      ######################  
      self.isPacman = [False for i in range(self.numPlayers)]
      self.isScared = [0 for i in range(self.numPlayers)]
      self.lastSeenPos = [gameState.getInitialAgentPosition(i) for i in range(self.numPlayers)]
      self.lastCarrying = [0 for i in range(self.numPlayers)]
      self.lastScore = [0, 0]
      self.updateBookKeepingFacts(gameState)
      # self.updateBookKeepingFacts(gameState)
      # self.noisyProb = gameState.getDistanceProb(0, gameState.getAgentDistances()[agent.index])

      self.estimations = self.getInitialEstimations(gameState)
      self.prevDefending = PositionEstimator.getAllDefendingItems(gameState, agent)
      self.lastUpdatePlayer = agent.index
      PositionEstimator.red = self

    elif not forRed and PositionEstimator.blue is None:
      self.width = gameState.data.layout.width
      self.height = gameState.data.layout.height

      self.walls = gameState.getWalls()
      self.walkablePositions = self.getWalkablePositions()
      self.distancer = distanceCalculator.Distancer(gameState.data.layout)

      self.numPlayers = gameState.getNumAgents()
      self.team = agent.getTeam(gameState) # assume only 1 teammate, also assume smaller index will be created first
      self.opponents = agent.getOpponents(gameState) # do we need to store this? since we are passing agent into update

      ######################
      # book keeping facts #
      ######################
      self.isPacman = [False for i in range(self.numPlayers)]
      self.isScared = [0 for i in range(self.numPlayers)]
      self.lastSeenPos = [gameState.getInitialAgentPosition(i) for i in range(self.numPlayers)]
      self.lastCarrying = [0 for i in range(self.numPlayers)]
      self.lastScore = [0, 0]
      self.updateBookKeepingFacts(gameState)
      # self.updateBookKeepingFacts(gameState)
      # self.noisyProb = gameState.getDistanceProb(0, gameState.getAgentDistances()[agent.index])

      self.estimations = self.getInitialEstimations(gameState)
      self.prevDefending = PositionEstimator.getAllDefendingItems(gameState, agent)
      self.lastUpdatePlayer = agent.index
      PositionEstimator.blue = self
  
  @staticmethod
  def get_instance(gameState, agent):
    """
    Static method to fetch the current instance.
    """
    if agent.red:
      if not PositionEstimator.red:
        PositionEstimator(gameState, agent, True)
      return PositionEstimator.red
    else:
      if not PositionEstimator.blue:
        PositionEstimator(gameState, agent, False)
      return PositionEstimator.blue

  def getInitialEstimations(self, gameState):
    # estimations = util.Counter()
    estimations = [None for i in range(gameState.getNumAgents())]
    for index in self.opponents:
      opponentEstimation = self.getOpponentInitialEstimation(gameState, index)
      estimations[index] = opponentEstimation
    return estimations

  def getOpponentInitialEstimation(self, gameState, opponentIndex):
    estimation = util.Counter()
    initialPosition = gameState.getInitialAgentPosition(opponentIndex)
    estimation[initialPosition] = 1.0

    # where opponent likely to go next
    # self.updateNeighboursEstimation(initialPosition, estimation)
    
    # estimation.normalize()
    return estimation
  
  # def resetEstimation(self, gameState, opponentIndex):
  #   newEstimation = self.getOpponentInitialEstimation(gameState, opponentIndex)
  #   self.estimations[opponentIndex] = newEstimation
    
  def getNeighbours(self, pos):
    return Actions.getLegalNeighbors(pos, self.walls)

  def getWalkablePositions(self):
    return [(x, y) for x in range(self.width) for y in range(self.height) if not self.walls[x][y]]
  
  def getAllEstimations(self):
    return self.estimations
  
  @staticmethod
  def getAllDefendingItems(gameState, agent):
    foods = agent.getFoodYouAreDefending(gameState).asList();
    capsules = agent.getCapsulesYouAreDefending(gameState)
    return foods + capsules

  def updateBookKeepingFacts(self, gameState):
    for i in range(gameState.getNumAgents()):
      state = gameState.getAgentState(i)
      self.isPacman[i] = state.isPacman
      self.isScared[i] = state.scaredTimer
      self.lastSeenPos[i] = gameState.getAgentPosition(i)
      self.lastCarrying[i] = state.numCarrying
      if gameState.isOnRedTeam(i):
        self.lastScore[i % 2] = gameState.getScore()
      else:
        self.lastScore[i % 2] = gameState.getScore() * -1

  def update(self, gameState, agent):
    """
    Food got eaten indicates an enemy pacman is there
    """

    # currently, we have the following foods and capsule
    currentDefending = PositionEstimator.getAllDefendingItems(gameState, agent)
    # find out foods and capsule ate by enemies
    changed = PositionEstimator.listDiff(self.prevDefending, currentDefending)
    self.prevDefending = currentDefending
    
    _wasPacman = self.isPacman[:]
    _wasScared = self.isScared[:]
    _lastSeenPos = self.lastSeenPos[:]
    _lastCarrying = self.lastCarrying[:]
    _lastScore = self.lastScore[:]
    # _lastRange = self.lastNoisyRange[:]
    self.updateBookKeepingFacts(gameState)

    _lastUpdatePlayer = self.lastUpdatePlayer
    self.lastUpdatePlayer = agent.index
    if _lastUpdatePlayer != self.lastUpdatePlayer:
      lastPlayerMoved = self.lastUpdatePlayer - 1
      if lastPlayerMoved < 0:
        lastPlayerMoved = self.numPlayers - 1
      opponents = [lastPlayerMoved]
    else:
      opponents = self.opponents

    determinedByFood = set()
    if len(changed) == 1:
      newEstimation = util.Counter()
      newEstimation[changed[0]] = 1

      for i in opponents:
        if gameState.getAgentState(i).numCarrying > _lastCarrying[i]:
          self.estimations[i] = newEstimation
          determinedByFood.add(i)
          # print("Enemy pacman {} at {}".format(i, changed[0]))
    elif len(changed) > 1:
      # This still have bugs
      # closest pos is not accurate if 2 agents are close
      for food in changed:
        newEstimation = util.Counter()
        newEstimation[food] = 1

        probs = dict.fromkeys(opponents, 0.0)
        for opponentIndex in opponents:
          opponentProb = self.estimations[opponentIndex][food]
          probs[opponentIndex] = opponentProb
        closest = max(probs, key=lambda k: probs[k])
        self.estimations[closest] = newEstimation
        # print("Enemy pacman {} at {}".format(closest, food))
    
    for opponentIndex in opponents:
      if opponentIndex in determinedByFood:
        continue 

      myPosition = self.lastSeenPos[agent.index]
      newEstimation = util.Counter()
      opponentPos = gameState.getAgentPosition(opponentIndex)
      noisyDistance = gameState.getAgentDistances()[opponentIndex]
      # opponentPos = self.lastSeenPos[opponentIndex]

      """
      if we can see opponent,
      then the belief is deterministic
      """
      if opponentPos is not None:
        newEstimation[opponentPos] = 1
        self.estimations[opponentIndex] = newEstimation
        continue
      
      """
      if it is destoried,
      then the belief is deterministic
      """
      wasPacman = _wasPacman[opponentIndex]
      wasScared = _wasScared[opponentIndex] > 1
      if (wasPacman and not self.isPacman[opponentIndex] and self.lastScore[opponentIndex % 2] == _lastScore[opponentIndex % 2]) or (wasScared and self.isScared[opponentIndex] <= 0):
        self.estimations[opponentIndex] = self.getOpponentInitialEstimation(gameState, opponentIndex)
        continue
      
      """
      if last time we saw the opponent, and cannot see it now; or last estimation is deterministic
      then it is likely that it will go to the position around its previous position,
      e.g, up, down, left, right, stop
      which cannot be seen from our current position.
      then update belifs with this stronger belief
      """
      lastPos = _lastSeenPos[opponentIndex]
      if lastPos != None:
        legalEstimations = set()
        neighbours = Actions.getLegalNeighbors(lastPos, self.walls)
        for n in neighbours:
          trueDistToMe = self.distancer.getDistance(myPosition, n)
          probToMe = gameState.getDistanceProb(trueDistToMe, noisyDistance)
          # prtobToMate = gameState.getDistanceProb(trueToMate, noisyDistance)
          if self.outOfSight(n) and probToMe > 0 and self.posInCorrectHalf(gameState, opponentIndex, n):
            legalEstimations.add(n)
        for pos in legalEstimations:
          newEstimation[pos] = 1.0 / len(legalEstimations)
        """
        if only 1 legal belief, then it is determinsitic
        but this actually will never happen, due to the fact an agent can STOP
        """
        if len(legalEstimations) == 1:
          # print("only 1 possible action? how so?")
          self.lastSeenPos[opponentIndex] = list(legalEstimations)[0]
        self.estimations[opponentIndex] = newEstimation
        continue;

      """
      no other deterministic info,
      can only update estimate beliefs.
      get beliefs based on noisy distances.
      """
      legalEstimationsByDist = set()
      for pos in self.walkablePositions:
        trueDistToMe = self.distancer.getDistance(myPosition, pos)
        probToMe = gameState.getDistanceProb(trueDistToMe, noisyDistance)
        # prtobToMate = gameState.getDistanceProb(trueToMate, noisyDistance)
        if self.outOfSight(pos) and probToMe > 0 and self.posInCorrectHalf(gameState, opponentIndex, pos):
          legalEstimationsByDist.add(pos)

      legalNeighboursOfEstimations = set()
      for oldPos, prob in self.estimations[opponentIndex].items():
        if prob == 0:
          continue
        neighbours = Actions.getLegalNeighbors(oldPos, self.walls)
        for n in neighbours:
          trueDistToMe = self.distancer.getDistance(myPosition, n)
          probToMe = gameState.getDistanceProb(trueDistToMe, noisyDistance)
          # prtobToMate = gameState.getDistanceProb(trueToMate, noisyDistance)
          if self.outOfSight(n) and probToMe > 0 and self.posInCorrectHalf(gameState, opponentIndex, n):
            legalNeighboursOfEstimations.add(n)
 
      legalEstimations = legalEstimationsByDist.intersection(legalNeighboursOfEstimations)

      """
      get beliefs based on previous beliefs
      1) we can just use the raw prob, which is 1.0 / number of all distinct neighbours of our previous estimations.
         ideally this should be better than just use dist estimations
      2) we can use previous prob + current prob for each neighbour of each previous estimation. 
         this is essentially extracting/highlighting the path of the opponet is walking.
      3) we can use previous prob * current prob
         this is essentially biased to the neighbours (new pos) of previous estimations
      """ 
      try:
        strongerProb = 1.0 / len(legalEstimations)
      except:
        strongerProb = 1.0 / len(legalEstimationsByDist) # should never happen

      for pos in legalEstimations:
        prevProbAtPos = self.estimations[opponentIndex][pos]
        newProb = strongerProb # or prevProbAtPos + strongerProb, but how to ensure that all belifs add up to 1?
        if math.isclose(prevProbAtPos, 0.0): # bc it is float comparison
          newEstimation[pos] = newProb
        else:
          newEstimation[pos] = newProb * prevProbAtPos
      """
      if only 1 legal estimation, then it is determinsitic
      but this actually will never happen, due to the fact an agent can STOP
      """
      if len(legalEstimations) == 1:
        self.lastSeenPos[opponentIndex] = list(legalEstimations)[0]
      # filtered_dict = {k: v for k, v in newEstimation.items() if v > 0.01}
      # print(len(filtered_dict.keys()))

      # newEstimation.normalize()
      self.estimations[opponentIndex] = newEstimation
  
  def posInCorrectHalf(self, gameState, agentIndex, pos):
    if gameState.isOnRedTeam(agentIndex):
      return self.isPacman[agentIndex] != gameState.isRed(pos)
    else:
      return self.isPacman[agentIndex] == gameState.isRed(pos)

  def outOfSight(self, pos):
    out = True
    for teammate in self.team:
      out = out and self.distancer.getDistance(self.lastSeenPos[teammate], pos) > SIGHT_RANGE
    return out

  def getWalls(self, gameState):
    return gameState.getWalls() if not hasattr(self, 'walls') else self.walls
  
  # def updateEstimation(self, index, newEstimation):
  #   self.estimations[index] = newEstimation
    
  def updateNeighboursEstimation(self, pos, estimation):
    # where opponent likely to go next
    neighbours = self.getNeighbours(pos)
    for neighbour in neighbours:
      estimation[neighbour] = 1 / len(neighbours)
  
  def getProbAtPos(self, index, pos):
    return self.estimations[index][pos]
  
  def getEstimation(self, index):
    return self.estimations[index]
  
  def getApproxPosition(self, index):
    probs = self.estimations[index]
    if len(probs) == 0:
      return None
    return max(probs, key=lambda k: probs[k])
  
  def getGhostPositions(self, ghostIndexes):
    positions = []
    for index in ghostIndexes:
      probs = self.estimations[index]
      positions.append(max(probs, key=lambda k: probs[k]))
    return positions
  
  @staticmethod
  def listDiff(prev, current):
    return list(set(prev) - set(current))