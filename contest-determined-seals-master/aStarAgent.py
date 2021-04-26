import sys
sys.path.append('teams/determined-seals/')

from captureAgents import CaptureAgent
import random, time, util, math
from game import Directions, Actions, Grid
import game

from positionEstimator import PositionEstimator
from searchProblems import HuTongSearchProblem
import features

DEFENSIVE = 0
OFFENSIVE = 1
offensiveAgents = []
defensiveAgents = []

posEstOn = True

TOTAL_ROUNDS = 300
oppoLastObservedPoses = [None, None]
oppoLastObservedRound = [-1, -1]

class AStarAgent(CaptureAgent):

  def registerInitialState(self, gameState):
    CaptureAgent.registerInitialState(self, gameState)
    # Initialise position estimator is it's enabled
    if posEstOn:
      self.posEst = PositionEstimator.get_instance(gameState, self)
    self.gameState = gameState

    # Layout specifications
    self.width = gameState.data.layout.width
    self.height = gameState.data.layout.height
    # Layout analysis
    self.teamSideBorder = self.getTeamSideBorder(gameState)
    self.opponentSideBorder = self.getOpponentSideBorder(gameState)
    self.staticCellHeuristics = self.getStaticCellHeuristics(gameState)
    self.totalFood = len(self.getFood(gameState).asList())

    # Track information
    self.round = 0
    self.roundsRemaining = TOTAL_ROUNDS
    self.opponentPrevStates = [None, None]
    # self.repeatMove = 0
    # self.ignoredAction = None

    # Assign agent mode
    if self.index <= 1: # 0 or 1
      self.agentMode = OFFENSIVE
      offensiveAgents.append(self)
    else: # 2 or 3
      self.agentMode = DEFENSIVE
      defensiveAgents.append(self)

  def chooseAction(self, gameState):
    # input("Next action")
    # print("=================================================================================")
    self.time = time.time() # Record start time
    # Updates
    self.gameState = gameState
    self.round += 1
    self.roundsRemaining = TOTAL_ROUNDS - self.round
    # self.ignoredAction = None
    
    # Position estimation
    if posEstOn:
      self.posEst.update(gameState, self)
    self.updateOppoApproxPoses(gameState)

    # Choose action
    action = 'Stop'
    if self.agentMode == OFFENSIVE:
      action = self.offensiveChooseAction(gameState)
    else:
      action =  self.defensiveChooseAction(gameState)

    # Records
    oppoIndices = self.getOpponents(gameState)
    self.opponentPrevStates[0] = gameState.getAgentState(oppoIndices[0])
    self.opponentPrevStates[1] = gameState.getAgentState(oppoIndices[1])
    ## print(self.opponentPrevStates)

    return action

  ##########################################
  # Offensive and defensive choose actions #
  ##########################################

  def offensiveChooseAction(self, gameState):
    
    # The offensive agent exchange mode with defensive agent if it's in a better a position to achieve defensive agent's goal
    # Situation 1: when defensive agent needs to chase an invader. Exchange mode if all following conditions are true:
    #   - there's invader and invader position observable,
    #   - this agent is not scared,
    #   - less than CHASE_INVADER_DISTANCE (in maze distance) away from the invader, and
    #   - closer to the invader than the defensive agent is.
    if self.countOpponentsInvading(gameState) > 0:
      if gameState.getAgentState(self.index).scaredTimer == 0:
        dist, oppoPos = self.getClosestInvaderToSelf(gameState)
        if oppoPos != None: # opponent position observable
          selfPos = gameState.getAgentPosition(self.index)
          distSelfOppo = self.getMazeDistance(selfPos, oppoPos)
          teammateIndex = self.getTeammateIndex(self.index)
          distTeammateOppo = self.getMazeDistance(gameState.getAgentPosition(teammateIndex), oppoPos)
          if distSelfOppo <= features.CHASE_INVADER_DISTANCE and distSelfOppo < distTeammateOppo:
            # print("++ o_agent "+str(self.index)+" wants to switch mode with d_agent "+str(teammateIndex))
            self.setAgentMode(DEFENSIVE)
            defensiveAgents[0].setAgentMode(OFFENSIVE)
            # print("==== o_agent index now is: "+str(offensiveAgents[0].index))
            # print("==== d_agent index now is: "+str(defensiveAgents[0].index))
            return self.defensiveChooseAction(gameState)
    # Situation 2: when defensive agent needs to defend an opponent from entering the border. Exchange mode if all following conditions are true:
    #   - there's no invader and there's opponent ghost with observable position,
    #   - this agent is not scared, and
    #   - closer to the target border cell than the defensive agent is.
    else: # No invader
      dist, cell, oppo = self.getClosestTeamBorderCellToOpponent(gameState)
      if oppo != None and cell != None: 
        selfPos = gameState.getAgentPosition(self.index)
        distSelfCell = self.getMazeDistance(selfPos, cell)
        teammateIndex = self.getTeammateIndex(self.index)
        distTeammateCell = self.getMazeDistance(gameState.getAgentPosition(teammateIndex), cell)
        if distSelfCell < distTeammateCell:
          # print("++ o_agent "+str(self.index)+" wants to switch mode with d_agent "+str(teammateIndex))
          self.setAgentMode(DEFENSIVE)
          defensiveAgents[0].setAgentMode(OFFENSIVE)
          # print("==== o_agent index now is: "+str(offensiveAgents[0].index))
          # print("==== d_agent index now is: "+str(defensiveAgents[0].index))
          return self.defensiveChooseAction(gameState)

    # Avoid repeated movements (e.g. moving back and forth) when attack
    # Detect two-step repeated movement (e.g. East -> West -> East -> West)
    # reverseDir = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    # prevDir = None
    # if self.getPreviousObservation():
    #   prevDir = self.getPreviousObservation().getAgentState(self.index).configuration.direction
    # if prevDir == reverseDir:
    #   self.repeatMove += 1
    # else:
    #   self.repeatMove = 0
    # if self.repeatMove >= features.REPEAT_MOVE_THRESHOLD:
    #   self.ignoredAction = reverseDir
    # Detect agent not moving (Stop -> Stop -> Stop)

    # Otherwise, continue being offensive
    selfPos = gameState.getAgentPosition(self.index)
    if self.isOnOpponentSide(selfPos):
      # print("++ o_agent "+str(self.index)+" is on opponent side")

      numCarrying = gameState.getAgentState(self.index).numCarrying
      numReturned = gameState.getAgentState(self.index).numReturned
      homeFoodLeft = len(self.getFoodYouAreDefending(gameState).asList())
      timeRequired = self.getClosestDistanceToHome(gameState)[0] + features.TIME_TO_GO_HOME_OFFSET

      # Go home immediately if:
      #   - We're winning
      #   - The opponent has collected enough food to win
      #   - We're carrying food but remaining time may not be enough to go home
      if numCarrying + numReturned >= self.totalFood - 2 or homeFoodLeft <= 2 or (numCarrying > 0 and timeRequired >= self.roundsRemaining):
        # print("++++ o_agent {} has {} carrying and {} returned food, that's enough food, going home".format(str(self.index), str(numCarrying), str(numReturned)))
        actions = self.aStarSearch(gameState, self.goHomeHeuristic, self.isAtHome)
        if actions == None or len(actions) == 0:
          # print("++++++ o_agent trying to go home: No action found")
          actions = gameState.getLegalActions(self.index)
          return random.choice(actions)
        return actions[0]

      # If the agent is carrying food and is close to home, go home
      if numCarrying > 0 and self.getClosestDistanceToHome(gameState)[0] <= features.GO_HOME_DISTANCE:
        # If opponents are scared #TODO: for needed amount of time
        if self.getOpponentMaxScaredTimer(gameState) < features.SAFE_OPPO_SCARED_FOR_MORE_FOOD:
          # print("++++ o_agent "+str(self.index)+" is close to home, going home")
          actions = self.aStarSearch(gameState, self.goHomeHeuristic, self.isAtHome)
          if actions == None or len(actions) == 0:
            # print("++++++ o_agent trying to go home: No action found")
            actions = gameState.getLegalActions(self.index)
            return random.choice(actions)
          return actions[0]

      # If the agent is too close to a not-scared opponent, go home or eat a capsule
      if self.getOpponentMaxScaredTimer(gameState) == 0:
        opponentPoses = self.getOpponentApproxPoses(gameState)
        for pos in opponentPoses:
          if self.getMazeDistance(selfPos, pos) <= features.DANGER_DISTANCE:
            # print("++++ o_agent "+str(self.index)+" is too close to an opponent at "+str(pos)+"!")
            actions = self.aStarSearch(gameState, self.goSafeHeuristic, self.isSafe)
            if actions == None or len(actions) == 0:
              # print("++++++ o_agent trying to go home or eat capsule: No action found")
              actions = gameState.getLegalActions(self.index)
              return random.choice(actions)
            return actions[0]

    # For all other cases, go to the next closest food
    # print("++ o_agent "+str(self.index)+" looking for next available food")
    actions = self.aStarSearch(gameState, self.findFoodHeuristic, self.isAtCapsuleOrFood)
    if actions == None or len(actions) == 0:
      # print("++ o_agent trying to eat food: No action found")
      actions = gameState.getLegalActions(self.index)
      return random.choice(actions)
    return actions[0]

  def defensiveChooseAction(self, gameState):

    # If there're invaders on team's side
    if self.countOpponentsInvading(gameState) > 0:
      # print("-- d_agent "+str(self.index)+" detected opponents invading")
      dist, oppoPos = self.getClosestInvaderToSelf(gameState)
      if oppoPos != None:
        # print("---- d_agent "+str(self.index)+" detected pacman at cell "+str(oppoPos))
        # If opponent pacman can be detected and I'm not scared, set goal to pacman position
        if gameState.getAgentState(self.index).scaredTimer == 0: #<= features.SAFE_TEAM_SCARED_TIMER: 
          actions = self.aStarGoalSearch(gameState, self.getCellHeuristics, oppoPos)
          if actions == None or len(actions) == 0:
            # print("------ d_agent "+str(self.index)+" chasing pacman at cell "+str(oppoPos)+": No action found")
            return 'Stop'
          return actions[0]

        # If opponent pacman can be detected but I'm scared, we have two strategies
        else:
          # Strategy A: Follow it while keeping a distance
          # It the distance from the agent to pacman is just right, stay put
          # if dist == features.DISTANCE_TO_INVADER_WHEN_SCARED: 
          #   return Directions.STOP
          # else:
          #   # Get all successors positions and their distance to the opponent pacman
          #   selfPos = gameState.getAgentPosition(self.index)
          #   availableActions = self.getAvailableActions(selfPos)
          #   oppoDistances = []
          #   for action in availableActions:
          #     succPos = self.getSuccessor(selfPos, action)
          #     distance = self.getMazeDistance(succPos, oppoPos)
          #     # Set distance to 0 if the successor got killed by opponent pacman
          #     if distance > features.DISTANCE_TO_INVADER_WHEN_SCARED + 3:
          #       distance = 0
          #     oppoDistances.append(distance)
          #   # If agent is far away from the pacman, go towards it
          #   if dist > features.DISTANCE_TO_INVADER_WHEN_SCARED:
          #     minValue = min(oppoDistances)
          #     bestActions = [a for a, v in zip(availableActions, oppoDistances) if v == minValue]
          #     return random.choice(bestActions)
          #   # If agent is too close to opponent pacman, go away from it
          #   if dist < features.DISTANCE_TO_INVADER_WHEN_SCARED: 
          #     maxValue = max(oppoDistances)
          #     bestActions = [a for a, v in zip(availableActions, oppoDistances) if v == maxValue]
          #     return random.choice(bestActions)

          # Strategy B: Set goal to the border cell that has the shortest maze distance to defending food
          minDist, cell, food = self.getClosestTeamBorderCellToDefendingFood(gameState)
          # print("---- d_agent "+str(self.index)+" is scared. Going to "+str(cell)+" to defend border")
          actions = self.aStarGoalSearch(gameState, self.getCellHeuristics, cell)
          if actions == None or len(actions) == 0:
            # print("------ d_agent "+str(self.index)+" moving to border cell "+str(cell)+": No action found")
            return 'Stop'
          return actions[0]
          
        
      # If opponent pacman cannot be detected, set goal to the border cell that has the shortest maze distance to defending food
      else:
        minDist, cell, food = self.getClosestTeamBorderCellToDefendingFood(gameState)
        # print("---- d_agent "+str(self.index)+" detected no pacman nearby. Going to "+str(cell)+" to defend border")
        actions = self.aStarGoalSearch(gameState, self.getCellHeuristics, cell)
        if actions == None or len(actions) == 0:
          # print("------ d_agent "+str(self.index)+" moving to border cell "+str(cell)+": No action found")
          return 'Stop'
        return actions[0]

    else: # No opponent invading
      # print("-- d_agent "+str(self.index)+" did not detect opponents invading")
      # If opponent position can be detected, set goal to the border cell that is closest to ghost
      minDist, cell, oppo = self.getClosestTeamBorderCellToOpponent(gameState)
      if oppo != None: 
        # print("---- d_agent "+str(self.index)+" detected opponent ghost nearby. Going to "+str(cell)+" to defend border")
        actions = self.aStarGoalSearch(gameState, self.getCellHeuristics, cell)
        if actions == None or len(actions) == 0:
          # print("------ d_agent "+str(self.index)+" moving to border cell "+str(cell)+": No action found")
          return 'Stop'
        return actions[0]
      # If opponent position cannot be detected, set goal to the closest border cell to me except for the one that I'm currently on
      else:
        dist, cell = self.getCoordOfAnotherClosestTeamBorderCell(gameState)
        # print("---- d_agent "+str(self.index)+" detected no opponent ghost nearby. Going to "+str(cell)+" to defend border")
        actions = self.aStarGoalSearch(gameState, self.getCellHeuristics, cell)
        if actions == None or len(actions) == 0:
          # print("------ d_agent "+str(self.index)+" moving to border cell "+str(cell)+": No action found")
          return 'Stop'
        return actions[0]

    # Default action for testing purpose
    # print("!!!! Defensive agent "+str(self.index)+" using default action")
    return 'Stop'

  ##################
  # Helper methods #
  ##################

  def getClosestDistAndCell(self, fromPos, toPoses):
    minDist = 999999
    bestPos = None
    for pos in toPoses:
      if fromPos != None and pos != None:
        dist = self.getMazeDistance(fromPos, pos)
        if dist < minDist:
          minDist = dist
          bestPos = pos
    return minDist, bestPos

  def getClosestDistanceToHome(self, gameState):
    """ Get the shortest distance from current position to home """
    selfPos = gameState.getAgentPosition(self.index)
    return self.getClosestTeamBorderCellToCoord(selfPos)

  def getClosestFood(self, gameState):
    """ Get the closest food to agent position """
    selfPos = gameState.getAgentPosition(self.index)
    foodList = self.getFood(gameState).asList()
    return self.getClosestDistAndCell(selfPos, foodList)

  def getClosestTeamBorderCellToDefendingFood(self, gameState):
    minDist = 999999
    bestCell = None
    bestFood = None
    dFoodList = self.getFoodYouAreDefending(gameState).asList()
    for food in dFoodList:
      dist, cell = self.getClosestTeamBorderCellToCoord(food)
      if dist < minDist:
        minDist = dist
        bestCell = cell
        bestFood = food
    return minDist, bestCell, bestFood

  def getClosestTeamBorderCellToCoord(self, coord):
    """ Get the closest border cell on team side to a coordinate """
    return self.getClosestDistAndCell(coord, self.teamSideBorder)

  def getClosestTeamBorderCellToOpponent(self, gameState):
    """ Get the closest border cell on team side to any opponent """
    minDist = 999999
    bestOppo = None
    bestCell = None
    oppoPoses = self.getOpponentApproxPoses(gameState)
    if len(oppoPoses) != 0:
      for oppoPos in oppoPoses:
        dist, cell = self.getClosestTeamBorderCellToCoord(oppoPos)
        if dist < minDist:
          minDist = dist
          bestOppo = oppoPos
          bestCell = cell
    return minDist, bestCell, bestOppo
  
  def getClosestOpponentToSelf(self, gameState):
    minDist = 999999
    oppoPos = None
    oppoPoses = self.getOpponentApproxPoses(gameState)
    for pos in oppoPoses:
      dist = self.getMazeDistance(gameState.getAgentPosition(self.index), pos)
      if dist < minDist:
        minDist = dist
        oppoPos = pos
    return minDist, oppoPos

  def getClosestInvaderToSelf(self, gameState):
    minDist = 999999
    oppoPos = None
    oppoPoses = self.getOpponentApproxPoses(gameState)
    for pos in oppoPoses:
      if self.isOnTeamSide(pos):
        dist = self.getMazeDistance(gameState.getAgentPosition(self.index), pos)
        if dist < minDist:
          minDist = dist
          oppoPos = pos
    return minDist, oppoPos

  def getCoordOfAnotherClosestTeamBorderCell(self, gameState):
    selfPos = gameState.getAgentPosition(self.index)
    borderCells = self.teamSideBorder[:]
    if selfPos in borderCells:
      borderCells.remove(selfPos)
    return self.getClosestDistAndCell(selfPos, borderCells)

  def countOpponentsInvading(self, gameState):
    """ Count the number of opponents that are invading """
    opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    invaders = [a for a in opponents if a.isPacman]
    return len(invaders)
    # opponentIndices = self.getOpponents(gameState)
    # opponentInvading = 0
    # if gameState.getAgentPosition(opponentIndices[0]) != None and self.isOnTeamSide(gameState.getAgentPosition(opponentIndices[0])):
    #   opponentInvading += 1
    # if gameState.getAgentPosition(opponentIndices[1]) != None and self.isOnTeamSide(gameState.getAgentPosition(opponentIndices[1])):
    #   opponentInvading += 1
    # return opponentInvading

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

  def getOpponentApproxPos(self, gameState, index):
    if index <= 1: # 0 or 1
      if self.round - oppoLastObservedRound[0] <= features.ROUNDS_POS_EST_STALE:
        return oppoLastObservedPoses[0]
    else: # 2 or 3
      if self.round - oppoLastObservedRound[1] <= features.ROUNDS_POS_EST_STALE:
        return oppoLastObservedPoses[1]
    return None

  def getTeamSideBorder(self, gameState):
    if self.red: # left
      return [(self.width//2-1, i) for i in range(self.height) if not gameState.hasWall(self.width//2-1, i)]
    else: # right
      return [(self.width//2, i) for i in range(self.height) if not gameState.hasWall(self.width//2, i)]

  def getOpponentSideBorder(self, gameState):
    if self.red: # left
      return [(self.width//2, i) for i in range(self.height) if not gameState.hasWall(self.width//2, i)]
    else: # right
      return [(self.width//2-1, i) for i in range(self.height) if not gameState.hasWall(self.width//2-1, i)]

  def isOnTeamSide(self, coord):
    if self.red: #left
      return coord[0] <= self.width//2-1
    else: #right
      return coord[0] >= self.width//2

  def isOnOpponentSide(self, coord):
    return not self.isOnTeamSide(coord)

  def getTeammateIndex(self, index):
    if index == 0: return 2
    elif index == 2: return 0
    elif index == 1: return 3
    elif index == 3: return 1
    else: return -1

  def setAgentMode(self, mode):
    if mode == OFFENSIVE:
      self.agentMode = OFFENSIVE
      offensiveAgents.append(self)
      defensiveAgents.remove(self)
      # print("== agent "+str(self.index)+" switched to offensive mode")
    else:
      self.agentMode = DEFENSIVE
      offensiveAgents.remove(self)
      defensiveAgents.append(self)
      # print("== agent "+str(self.index)+" switched to defensive mode")

  def getOpponentMaxScaredTimer(self, gameState):
    oppoIndices = self.getOpponents(gameState)
    st0 = gameState.getAgentState(oppoIndices[0]).scaredTimer
    st1 = gameState.getAgentState(oppoIndices[1]).scaredTimer
    return max(st0, st1)

  def getOpponentScaredTimer(self, gameState, index):
    return gameState.getAgentState(index).scaredTimer

  def getLastLostFood(self):
    if self.round <= 1:
      return []
    prevFood = self.getFoodYouAreDefending(self.getPreviousObservation()).asList()
    currFood = self.getFoodYouAreDefending(self.getCurrentObservation()).asList()
    return list(set(prevFood) - set(currFood))

  ########################
  # Heuristics functions #
  ########################

  def getCellHeuristics(self, agentPosition):
    x, y = agentPosition
    h = self.staticCellHeuristics[x][y] # base h
    if self.isOnOpponentSide((x,y)):
      oppoIndices = self.getOpponents(self.gameState)
      for oppoI in oppoIndices:
        oPos = self.getOpponentApproxPos(self.gameState, oppoI)
        # If the opponent is not None and is not scared or turning not scared
        if oPos != None and self.getOpponentScaredTimer(self.gameState, oppoI) <= features.SAFE_OPPO_SCARED_TIMER:
          dist = self.getMazeDistance(oPos, (x, y))
          if dist <= features.DANGER_DISTANCE:
            h += features.DANGER_H / (dist+1) # Increase h if opponent is within danger distance
    return h

  def findFoodHeuristic(self, agentPosition):
    if self.isAtFoodCell(agentPosition):
      return 0
    return self.getCellHeuristics(agentPosition)

  def goSafeHeuristic(self, agentPosition):
    if self.isSafe(agentPosition):
      return 0
    return self.getCellHeuristics(agentPosition)

  def goHomeHeuristic(self, agentPosition):
    if self.isAtHome(agentPosition):
      return 0
    return self.getCellHeuristics(agentPosition)

  ##########
  # isGoal #
  ##########
  
  def isAtFoodCell(self, agentPosition):
    foodList = self.getFood(self.gameState).asList()
    return agentPosition in foodList

  def isAtCapsuleCell(self, agentPosition):
    capsules = self.getCapsules(self.gameState)
    return agentPosition in capsules

  def isAtCapsuleOrFood(self, agentPosition):
    return self.isAtFoodCell(agentPosition) or self.isAtCapsuleCell(agentPosition)

  def isSafe(self, agentPosition):
    return self.isAtHome(agentPosition) or self.isAtCapsuleCell(agentPosition)

  def isAtHome(self, agentPosition):
    return self.isOnTeamSide(agentPosition)

  ######
  # A* #
  ######

  def aStarSearch(self, gameState, heuristic, isGoalState):
    pq = util.PriorityQueue()
    visited = {} # Visited state : total cost
    # Node:
    STATE = 0     # [0]: current state (position)
    ACTIONS = 1   # [1]: actions required to get to this node from root
    COST = 2      # [2]: cost from previous state to this node
    COST_SUM = 3  # [3]: total cost from root to this node
    # Push root node to queue
    startState = gameState.getAgentPosition(self.index)
    pq.push((startState, [], 0, 0), 0 + heuristic(startState))
    # Search
    while not pq.isEmpty():
      # return no action if timeout
      if time.time() - self.time >= 0.95:
        # print("A* TIMEOUT! Returning None")
        return None
      currNode = pq.pop()
      # If the state is not visited or the new visit has better total cost, explore or reopen node
      if currNode[STATE] not in visited.keys() or currNode[COST_SUM] < visited[currNode[STATE]]:
        if isGoalState(currNode[STATE]): # Check goal state
          return currNode[ACTIONS]
        else: # add node to open list if goal is not reached:
          actions = self.getAvailableActions(currNode[STATE])
          for action in actions:
            if action != 'Stop':
              successorState = self.getSuccessor(currNode[STATE], action)
              pq.push((successorState,                 # state
                      currNode[ACTIONS] + [action],    # actions
                      1,                               # cost
                      currNode[COST_SUM] + 1),         # total cost
                      currNode[COST_SUM] + 1 + heuristic(successorState)) # g(s)+h(s)
        visited[currNode[STATE]] = currNode[COST_SUM]
    return None

  def getAvailableActions(self, coord):
    actions = []
    x, y = coord
    if y+1 < self.height and not self.gameState.hasWall(x, y+1):
      actions.append('North')
    if y-1 >= 0 and not self.gameState.hasWall(x, y-1):
      actions.append('South')
    if x+1 < self.width and not self.gameState.hasWall(x+1, y):
      actions.append('East')
    if x-1 >= 0 and not self.gameState.hasWall(x-1, y):
      actions.append('West')
    actions.append('Stop')
    return actions

  def getSuccessor(self, coord, action):
    x, y = coord
    if action == 'North':
      return (x, y+1)
    elif action == 'South':
      return (x, y-1)
    elif action == 'East':
      return (x+1, y)
    elif action == 'West':
      return (x-1, y)
    else:
      return (x, y)

  def aStarGoalSearch(self, gameState, heuristic, goalCoord):
    pq = util.PriorityQueue()
    visited = {} # Visited state : total cost
    # Node:
    STATE = 0     # [0]: current position
    ACTIONS = 1   # [1]: actions required to get to this node from root
    COST = 2      # [2]: cost from previous state to this node
    COST_SUM = 3  # [3]: total cost from root to this node
    # Push root node to queue
    startState = gameState.getAgentPosition(self.index)
    pq.push((startState, [], 0, 0), 0 + heuristic(startState))
    # Search
    while not pq.isEmpty():
      # return no action if timeout
      if time.time() - self.time >= 0.95:
        # print("A* TIMEOUT! Returning None")
        return None
      currNode = pq.pop()
      # If the state is not visited or the new visit has better total cost, explore or reopen node
      if currNode[STATE] not in visited.keys() or currNode[COST_SUM] < visited[currNode[STATE]]:
        if currNode[STATE] == goalCoord: # Check goal state
          return currNode[ACTIONS]
        else: # add node to open list if goal is not reached:
          actions = self.getAvailableActions(currNode[STATE])
          for action in actions:
            if action != 'Stop':
              successorState = self.getSuccessor(currNode[STATE], action)
              newNode = (successorState,                # state
                        currNode[ACTIONS] + [action],   # actions
                        1,                              # cost
                        currNode[COST_SUM] + 1)         # total cost
              priority = currNode[COST_SUM] + 1 + heuristic(successorState)  # g(s)+h(s)
              pq.push(newNode, priority)
        visited[currNode[STATE]] = currNode[COST_SUM]
    return None

  ############################
  # Initialisation functions #
  ############################

  def getStaticCellHeuristics(self, gameState):
    # print("Initialise staticCellHeuristics")
    staticMapH = [[1 for i in range(self.height)] for j in range(self.width)]
    # Assign h=999999 to walls and h=1 to all reachable cells
    for x in range(self.width):
      for y in range(self.height):
        if gameState.hasWall(x, y):
          staticMapH[x][y] = 999999
    return staticMapH