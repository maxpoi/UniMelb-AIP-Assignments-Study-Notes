# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
from capture import SIGHT_RANGE
import random, time, util
from game import Directions, Actions, Grid
import game
import distanceCalculator
from positionEstimator import PositionEstimator
from searchProblems import FoodSearchProblem, PathSearchProblem, HuTongSearchProblem
import math
#################
# Team creation #
#################

# strategies
ATTACK = 0
RETURN = 1
DEFEND = 2
CHASE = 3
CAP = 4
DECOY = 5
PATROL = 6

TIMEOUT = -1
FOUND = 1

#######################
# Heursitic functions #
#######################
def nullHeuristic(pos=None, problem=None):
  return 0

def createTeam(firstIndex, secondIndex, isRed,
               first = 'MiniMaxAgent', second = 'MiniMaxAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class DummyAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)
    '''
    Your initialization code goes here, if you need any.
    '''

  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    '''
    You should change this in your own agent.
    '''
    return random.choice(actions)

class MiniMaxAgent(CaptureAgent):

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''
    # self.stateValue = {}
    self.start = time.time()
    self.gameLen = gameState.data.timeleft
    self.weightsAscending = self.getWeightsAscending()
    self.weightsDescending = self.getWeightsDescending()
    self.manhattanDistancer = distanceCalculator.Distancer(gameState.data.layout)

    self.numPlayers = gameState.getNumAgents()
    self.seenOpponents = None

    width = gameState.data.layout.width
    height = gameState.data.layout.height

    self.strategy = ATTACK
    self.limited = True
    self.neverAttack = False
    self.forcedExit = None
    self.turnLeft = int(gameState.data.timeleft / 4)

    ##############################################################
    #                  Special Grid Information                  #
    ##############################################################
    self.teamIndex = self.index % 2
    self.guardingPts = [
                        [(width//2-1-3, i) for i in range(height) if not gameState.hasWall(width//2-1-3, i)], # red
                        [(width//2+3, i) for i in range(height) if not gameState.hasWall(width//2+3, i)] # blue
                       ]

    self.middlePts = [
                      [(width//2-1, i) for i in range(height) if not gameState.hasWall(width//2-1, i)], # red
                      [(width//2, i) for i in range(height) if not gameState.hasWall(width//2, i)] # blue
                     ]

    self.opponentEntryPts = [
                              [(width//2+2, i) for i in range(height) if not gameState.hasWall(width//2+2, i)], # red
                              [(width//2-1-2, i) for i in range(height) if not gameState.hasWall(width//2-1-2, i)] # blue
                            ]
    
    self.hutongs = self.findHuTongs(gameState.getWalls()) # [[(x, y)]]
    self.hutongsPos = self.getAllHuTongsPos() # set of (x, y)
    self.deepHuTongs = self.getDeepHuTongs() # depth > 3, set of (x, y)

    # self.requiredFood = len(self.getFoodList(gameState, self.index)) - 1 # min(5, int(len(self.getFood(gameState).asList())/4))
    # TODO

    # 2, record the closest food to enemy, this is highly likly to be their next goal
    # this is kind of like goal recognition
    # self.estimateEntryPts = []

    # 3, add an agent that go to the capsule half of grid, then went to the estimation pts of ghosts, attract them to attack him, while the other one is eating the other half of the pts, make sure the bate agent should eat food first
    # self.upperHalfFood = [food for food in self.getFood(gameState).asList() if food[1] >= gameState.data.layout.height / 2]
    # self.lowerHalfFood = [food for food in self.getFood(gameState).asList() if food[1] < gameState.data.layout.height / 2]

    if self.index < 2: # assume only 4 players, and 2 for each team
      self.teammate = self.index + 2
    else:
      self.teammate = self.index - 2

    self.foodPathAction = None
    path, actions, status = self.getPathEatAllFood(gameState, self.index, 15//2)
    if status == FOUND:
      self.foodPathAction = path, actions

    # self.lastAction = Directions.STOP
    

    #########################################
    # They are the values for current state #
    #########################################
    # self.guardingPoint = [random.Random().choice(self.guardingPoints) for i in range(self.numPlayers)]
    # self.lastAction = [None for i in range(self.numPlayers)]
    # self.lastSeenInvaders = [[] for i in range(self.numPlayers)]
    # self.wasPacman = [False for i in range(self.numPlayers)]
    # self.wasScared = [False for i in range(self.numPlayers)]

    PositionEstimator.get_instance(gameState, self)
    # test usage
    print((time.time() - self.start))
    # if self.foodPathAction != None:
    #   self.debugDraw(self.foodPathAction[0], [1,0,0])
    # for hutong in self.hutongs:
    #   self.debugDraw(hutong, [0,1,0])
    # input()

  def chooseAction(self, gameState):
    # test usage
    # self.debugClear()
    # self.debugDraw(self.guardingPts[self.teamIndex], [1,1,1], False)
    # self.debugDraw(self.middlePts[self.teamIndex], [1,1,1], False)
    # self.debugDraw(self.opponentEntryPts[self.teamIndex], [1,1,1], False)
    self.start = time.time()
    PositionEstimator.get_instance(gameState, self).update(gameState, self)
    self.seenOpponents = [(i, gameState.getAgentPosition(i)) for i in self.getOpponents(gameState) if gameState.getAgentPosition(i) != None]
    self.turnLeft = int(gameState.data.timeleft / 4)
    
    # beliefs = PositionEstimator.get_instance(gameState, self).getAllEstimations()
    
    # self.displayDistributionsOverPositions(belief)
    feasibleActions = gameState.getLegalActions(self.index)
    ###########################################################
    #                     Update Strategy                     #
    ###########################################################
    isPacman = gameState.getAgentState(self.index).isPacman
    myPos = gameState.getAgentPosition(self.index)
    myState = gameState.getAgentState(self.index)
    numInvaders = len(self.getInvaders(gameState))

    notScaredGhostsICanSee = self.getGhostsICanSee(gameState, maze=False, excludeScared=True)
    opponentsICanSee = self.getOpponentsICanSee(gameState, maze=False, excludeScared=True)
    numFoodLeft = len(self.getFoodList(gameState, self.index))
    if numFoodLeft == 0 and self.limited and numInvaders == 2:
      self.limited = False
      numFoodLeft = len(self.getFoodList(gameState, self.index))
    ############################################
    # Swicth Strategy between ATTACK OR DEFEND #
    ############################################

    # ATTACK
    if self.strategy == ATTACK:
      # if self.limited:
      #   if numFoodLeft == 0:
      #     # print("因为都吃完了，回家")
      #     self.strategy = RETURN
      # else:
      #   if numFoodLeft == 2:
      #     self.strategy = RETURN
      if numFoodLeft == 0:
        # print("因为都吃完了，回家")
        self.strategy = RETURN
      if isPacman and len(notScaredGhostsICanSee) > 0: # _range =3?
        distToMe = min([self.getMazeDistance(myPos, pos) for i, pos in notScaredGhostsICanSee])
        if distToMe < 6:
          # print("因为看到了ghost，回家")
          self.strategy = RETURN
      # TODO
      # 加入如果游戏即将结束，则直接回家
    elif self.strategy == RETURN:
      if self.isGoalState(gameState):
        self.strategy = DEFEND
        # print("因为到家了，开始defend")
      if gameState.getAgentPosition(self.index)[0] == gameState.getInitialAgentPosition(self.index)[0]:
        self.strategy = ATTACK
        # print("回家路上被吃了，重新开始吃")
      if numFoodLeft > 0 and len(notScaredGhostsICanSee) == 0:
        if not self.neverAttack:
          self.strategy = ATTACK
        # print("之前看到了敌人开始回家，但是因为他们都scared了，重新开始吃")

    # DEFEND
    if self.strategy == DEFEND:
      # print("开始defend")
      if numInvaders > 0:
        if gameState.getAgentState(self.teammate).isPacman:
          self.strategy = PATROL
          # print("但是有invader，并且只有自己在家，所以巡逻")
        else:
          if self.index < 2:
            self.strategy == CHASE
            # print("但是有invader，而且两个人都在家，因为这个index较小，所以去追")
          else:
            self.strategy == PATROL
            # print("但是有invader，而且两个人都在家，因为这个index较大，所以巡逻")
      elif numFoodLeft > 0:
        # TODO 
        # redirect root from a different exiting point
        if not self.neverAttack:
          self.strategy = ATTACK
        # print("没有invader，但是我还没吃完food，所以重新开始吃")
      else:
        self.strategy = PATROL
        # print("没什么特殊情况，巡逻吧")

    ##############################################
    # Swicth Strategy based on special situation #
    ##############################################

    # eat enemy whenever is possible
    if not isPacman and self.strategy != DEFEND:
      if gameState.getAgentState(self.teammate).isPacman and numInvaders > 0:
        self.strategy = DEFEND
      elif len(self.getPacmenICanSee(gameState, maze=False)) > 0:
        # print("看到入侵者，开始chase")
        self.strategy == CHASE
      else:
        seen = self.getOpponentsICanSee(gameState, maze=False)
        atEntry = False
        if len(seen) > 0:
          for i, pos in seen:
            if self.red:
              atEntry = atEntry or pos[0] <= self.opponentEntryPts[self.teamIndex][0][0]
            else:
              atEntry = atEntry or pos[0] >= self.opponentEntryPts[self.teamIndex][0][0]
          if atEntry:
            self.strategy = DEFEND
            # print("本来是有事的，但是看到有人要进来了，开始defend")
    
    if isPacman and self.strategy == ATTACK:
      minDistHome = min([self.getMazeDistance(myPos, pos) for pos in self.middlePts[self.teamIndex]])
      if self.turnLeft < minDistHome + 3:
        # print("因为要没时间了，直接回家")
        self.strategy == RETURN
        self.neverAttack = True

    if self.strategy != ATTACK:
      self.foodPathAction = None
    if self.foodPathAction != None:
      if len(self.foodPathAction[0]) == 0:
        self.foodPathAction = None
    
    if self.forcedExit != None:
      if not isPacman:
        self.forcedExit = None

    # print(self.index, " 的strategy是：", self.strategy)
    #################################################################
    #                     Search & Choose Action                    #
    #################################################################

    if len(opponentsICanSee) > 0:
      # print("看见对手，开始minimax")
      self.foodPathAction = None
      avaliablePlayers = [self.index] + [i for i, pos in opponentsICanSee]
      _, action = self.miniMax(gameState, -9999999, 9999999, 8, 0, avaliablePlayers)

      # _states = [(gameState.generateSuccessor(self.index, a), a) for a in feasibleActions]
      # _val = self.evaluate(gameState.generateSuccessor(self.index, action), self.index, False)
      # for s, a in _states:
      #   print(s)
      #   print(a, self.evaluate(s, self.index, False))
      # print("这个state的value是：", self.evaluate(gameState, self.index, False))
      # print("选择了 ", action, "，对应的value是 ", _val)
      # input()
      
    elif self.strategy == ATTACK:
      # print("没看见对手，用a*")
      if self.foodPathAction == None:
        path, actions, status = self.getPathEatAllFood(gameState, self.index, _maxTime=1)
        # print("没有path，现找，然后a*结果是：", status)
        if status == FOUND:
          # print("找到了，path是用红色的画出来的")
          self.foodPathAction = path, actions
      # elif self.foodPathAction[-1] == TIMEOUT:
      #   path, actions, status = self.getPathEatAllFood(gameState, self.index, _maxTime=1)
      #   if status == FOUND:
      #     try:
      #       i = path.index(myPos) + 1
      #       self.foodPathAction = path[i:], actions[i:], status
      #       self.debugDraw(path[i:], [0,0,1], True)
      #     except:
      #       # should never happen
      #       action = random.choice(feasibleActions)
      #       self.foodPathAction = None
      #       return action
          action = self.foodPathAction[1].pop(0)
          self.foodPathAction[0].pop(0)
          # self.debugDraw(self.foodPathAction[0], [1,0,0])
        else:
          # print("没找到，只取第一个")
          action = actions[0]

      else:
        # print("有path，直接用第一个，path是用绿色的画出来的")
        action = self.foodPathAction[1].pop(0)
        self.foodPathAction[0].pop(0)
        # self.debugDraw(self.foodPathAction[0], [0,1,0])

    elif self.strategy == RETURN:
      # print("回家的path，蓝色的")
      path, actions, _ = self.getReturnPath(gameState, self.index, _maxTime=1)
      action = actions[0]
      # self.debugDraw(path, [0,0,1])

    elif self.strategy == PATROL:
      # print("巡逻的path是用蓝色的画出来的")
      path, actions, _ = self.getPatrolPath(gameState, self.index, _maxTime=1)
      if len(path) == 0:
        action = random.choice(feasibleActions)
      else:
        action = actions[0]
      # self.debugDraw(path, [0,0,1], True)

    else:
      # print("用的不该用的a*")
      # choose action by astar
      action = self.aStarSearch(gameState)

    if action not in feasibleActions:
      action = random.choice(feasibleActions)

    # if (time.time() - self.start) > 1:
    #       print((time.time() - self.start))
    # input()
    return action

  ######################################################
  #                MiniMax Simulation                  #
  ######################################################
  
  def miniMax(self, gameState, alpha, beta, depth, playerIndex, allPlayers):
    if playerIndex == len(allPlayers):
      playerIndex = 0
    player = allPlayers[playerIndex]
    
    removed = gameState.getAgentPosition(player)[0] == gameState.getInitialAgentPosition(player)[0]
    _players = allPlayers[:]
    if removed:
      _players.remove(player)
    if depth == 0 or removed or len(_players) == 1 or gameState.isOver():
      return self.evaluate(gameState, self.index, False), None

    actions = self.getSortedActions(gameState, player)
    _action = actions[0]
    if player == self.index:
      _max = -9999999
      for action in actions:
        succ = gameState.generateSuccessor(player, action)
        val, _ = self.miniMax(succ, alpha, beta, depth-1, playerIndex+1, _players)

        if _max < val:
          _max = val
          _action = action

        alpha = max(alpha, val)
        if beta <= alpha:
          return _max, action
      return _max, _action
    else:
      _min = 9999999
      for action in actions:
        succ = gameState.generateSuccessor(player, action)
        val, _ = self.miniMax(succ, alpha, beta, depth-1, playerIndex+1, _players)

        if _min > val:
          _min = val
          _action = action

        beta = min(beta, val)
        if beta <= alpha:
          return _min, action
      return _min, _action

  ###################################################
  #                Blind A* Search                  #
  ###################################################

  def aStarSearch(self, gameState):
    """Search the node that has the lowest combined cost and heuristic first."""
    "*** YOUR CODE HERE ***"
    myPQ = util.PriorityQueue()
    
    startNode = (gameState, Directions.STOP, 0, [])
    myPQ.push(startNode, self.evaluate(gameState, self.index))
    visited = set()
    best_g = dict()
    while not myPQ.isEmpty():
      node = myPQ.pop()
      state, action, cost, path = node
      if (not state in visited) or cost < best_g.get(state):
        visited.add(state)
        best_g[state]=cost

        if self.isGoalState(state) or self.timeUp(1):
          # path = path + [(state, action)]
          # actions = [action[1] for action in path]
          # del actions[0]
          # print(path)
          if len(path) > 0:
            return path[0][1]
          return random.choice(self.getSortedActions(state, self.index))
        for action in self.getSortedActions(state, self.index):
          succ = state.generateSuccessor(self.index, action)
          newNode = (succ, action, cost + 1, path + [(node, action)])
          myPQ.push(newNode, self.evaluate(succ, self.index))
  
  def isGoalState(self, gameState):
    if self.strategy == ATTACK:
      # return len(self.getFood(gameState).asList()) <= 2
      return len(self.getFoodList(gameState, self.index)) == 0
    elif self.strategy == RETURN:
      # beenEaten = self.getMazeDistance(gameState.getInitialAgentPosition(self.index), gameState.getAgentPosition(self.index)) < 2
      return gameState.getAgentPosition(self.index)[0] == self.middlePts[self.teamIndex][0][0]
    elif self.strategy == DEFEND:
      return len(self.getInvaders(gameState)) == 0
    elif self.strategy == CHASE:
      return len(self.getInvaders(gameState)) == 0
    elif self.strategy == PATROL:
      return True

 
  ##########################################################################
  #                   Feature extractions (no team work)                   #
  ##########################################################################
  
  def getAttackingFeatures(self, gameState, agentIndex):
    features = util.Counter()
    myState = gameState.getAgentState(agentIndex)
    myPos = gameState.getAgentPosition(agentIndex)
    foodList = self.getFoodList(gameState, agentIndex)

    features['numFood'] = len(foodList)
    if myState.isPacman:
      features['isPacman'] = 1
    # else:
    #   features['isPacman'] = -1

    if len(foodList) > 0: # This should always be True,  but better safe than sorry
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['minDistToFood'] = minDistance
    
    ghosts = self.getGhostsICanSee(gameState, maze=False, excludeScared=True)
    if len(ghosts) > 0:
      features['distToGhosts'] = min([self.getMazeDistance(myPos, pos) for i, pos in ghosts])
      if myPos in self.hutongsPos:
        features['inHuTong'] = 1
    return features 

  def getReturningFeatures(self, gameState, agentIndex):
    features = util.Counter()
    myState = gameState.getAgentState(agentIndex)
    myPos = gameState.getAgentPosition(agentIndex)
    
    if not myState.isPacman:
      features['isGhost'] = 1000
    # else:
    #   features['isGhost'] = -1

    ghosts = self.getGhostsICanSee(gameState, maze=False, excludeScared=True)
    if len(ghosts) > 0:
      features['distToGhosts'] = min([self.getMazeDistance(myPos, pos) for i, pos in ghosts])
      if myPos in self.hutongsPos:
        features['inHuTong'] = 1
    
    features['homeDist'], _ = self.getExitPt(gameState)
    # features['distToCapsule'] = min([self.getMazeDistance(myPos, pos) for pos in self.getCapsules(gameState)])
    
    return features

  def getDefendingFeatures(self, gameState, agentIndex):
    features = util.Counter()
    myState = gameState.getAgentState(agentIndex)
    myPos = gameState.getAgentPosition(agentIndex)

    if not myState.isPacman:
      features['isGhost'] = 1000
    # else:
    #   features['isGhost'] = -1   

    # features['numFoodToDefend'] = len(self.getFoodYouAreDefending(gameState).asList())

    invaders = self.getPacmenICanSee(gameState, maze=False)
    features['numInvaders'] = len(self.getInvaders(gameState))
    if len(invaders) > 0:
      # if myState.scaredTimer > 0:
      #   features['minDistToInvaders'] = min([self.getMazeDistance(myPos, pos) for i, pos in invaders]) * -1
      # else:
      minDist, minPos = min([(self.getMazeDistance(myPos, pos), pos) for i, pos in invaders])
      features['minDistToInvaders'] = minDist
      if myPos[1] == minPos[1]:
        features['sameY'] = 1
      
    #   features['minDistInvadersBackHome'] = min([self.getMazeDistance(self.guardingPt, pos) for i, pos in invaders])
      # features['midDistToNextFood'] = min([min([self.getMazeDistance(food, pos) for food in self.getFood(gameState).asList()]) for i, pos in invaders])
    else:
      if len(self.seenOpponents) == 0:
        guardingPt = self.getClosestGuardingPoint(gameState, self.guessOpponentsY(gameState))
      else:
        x, y = min([(self.getMazeDistance(myPos, pos), pos) for i, pos in self.seenOpponents])[1]
        guardingPt = self.getClosestGuardingPoint(gameState, y)

      features['distToGuardingPoint'] = self.getMazeDistance(myPos, guardingPt)
      # features['distToGuardingPoint'] = min([self.getMazeDistance(myPos, pos) for pos in self.guardingPts[self.index % 2]])

    return features

  def getPatrolFeatures(self, gameState, agentIndex):
    features = util.Counter()
    myState = gameState.getAgentState(agentIndex)
    myPos = gameState.getAgentPosition(agentIndex)

    if not myState.isPacman:
      features['isGhost'] = 1000
    
    if len(self.seenOpponents) == 0:
      guardingPt = self.getClosestGuardingPoint(gameState, self.guessOpponentsY(gameState))
    else:
      x, y = min([(self.getMazeDistance(myPos, pos), pos) for i, pos in self.seenOpponents])[1]
      guardingPt = self.getClosestGuardingPoint(gameState, y)

    features['distToGuardingPoint'] = self.getMazeDistance(myPos, guardingPt)
    
    return features

  def getDefaultFeatures(self, gameState, agengIndex):
    features = util.Counter()
    myPos = gameState.getAgentPosition(agengIndex)

    '''
    Keep me alive
    ''' 
    if myPos == gameState.getInitialAgentPosition(agengIndex):
      features['getEaten'] = 1

    # '''
    # Take any change to destroy an invader
    # '''
    # for i in self.getOpponents(gameState):
    #   if gameState.getAgentPosition(i) != None and gameState.getAgentPosition(i) == gameState.getInitialAgentPosition(i):
    #     self.debugDraw([myPos], [0,1,0])
    #     features['eatEnemy'] = 1

    '''
    Better not standing still or repeat it self
    '''
    # but how to keep track of last action when doing simulation?
    # if self.lastAction == Directions.STOP:
    #   features['stop'] = 1
    # elif Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction] == self.lastAction: 
    #   features['reverse'] = 1

    '''
    Basic game rule
    '''
    # features['numInvaders'] = len(invaders)
    features['score'] = self.getScore(gameState)
    if gameState.isOver():
      if self.getScore(gameState) == 0:
        features['tie'] = 1
      elif self.getScore(gameState) > 0:
        features['win'] = 1
      else:
        features['lose'] = 1

    return features
  
  def evaluate(self, gameState, agengIndex, forGoal=True):
    """
    Computes a linear combination of features and feature weights
    """
    if forGoal:
      weights = self.weightsDescending
    else:
      weights = self.weightsAscending

    defualtValue = self.getDefaultFeatures(gameState, agengIndex) * weights
    if self.strategy == ATTACK:
      return defualtValue + self.getAttackingFeatures(gameState, agengIndex) * weights
    elif self.strategy == RETURN:
      return defualtValue + self.getReturningFeatures(gameState, agengIndex) * weights
    elif self.strategy == DEFEND:
      return defualtValue + self.getDefendingFeatures(gameState, agengIndex) * weights
    elif self.strategy == CHASE:
      return defualtValue + self.getDefendingFeatures(gameState, agengIndex) * weights
    elif self.strategy == PATROL:
      return defualtValue + self.getPatrolFeatures(gameState, agengIndex) * weights
    else:
      return defualtValue

  ###################################################################
  #                   Feature extractions as Team                   #
  ###################################################################

  def getAttackingTeamFeature(self, gameState):
    return None

  # def updateStateVal(self, index, gameState):
    #   seenOpponents = [i for i in self.getOpponents(gameState) if gameState.getAgentPosition(i) != None]
    #   self.seenOpponents = seenOpponents

    #   myPos = gameState.getAgentPosition(index)
    #   isRed = gameState.isOnRedTeam(index)
    #   if isRed:
    #     enemies = gameState.getBlueTeamIndices()
    #   else:
    #     enemies = gameState.getRedTeamIndices()
    #   invaders = [i for i in enemies if gameState.getAgentState(i).isPacman]
      
    #   seenInvaders = [self.getMazeDistance(myPos, gameState.getAgentPosition(i)) for i in invaders if gameState.getAgentPosition(i) != None]
    #   if len(seenInvaders) > 0:
    #     self.lastSeenInvaders[index] = [gameState.getAgentPosition(i) for i in invaders if gameState.getAgentPosition(i) != None]
    #   if len(invaders) == 0:
    #     self.lastSeenInvaders[index] = []
    #   if myPos in self.lastSeenInvaders[index]:
    #     self.lastSeenInvaders[index].remove(myPos)

  def getWeightsDescending(self):
    """
    reward: negative
    punishment: positive
    """
    return util.Counter({
            'numFood': 100,            # main feature that determines the value of a state
            'minDistToFood': 1,        # secondary feature which controls the choice of actions 
            'isPacman': -10,           # instant reward/punishment if it is reach/undo

            'minDistToGhost': -1,    # this has to out range midDIstToFood and homeDist
            'inHuTong': 1000,
            # 'beenChased': 1000,

            'homeDist': 5,             # secondary feature which controls the choice of ations
            'isGhost': -1,             # instant reward/punishment if it is reach/undo
            # 'numCarrying': -100,       # main feature that determines the value of a state

            # 'numPowerToEat': -100,   # num is max at 2, so use large weights to increase its influence
            # 'minDistToPower': -2,

            'numInvaders': 1000,       # main feature which determines the value of a state
            'minDistToInvaders': 5,    # dist can increase or decrease, as long as we get the distination
            'sameY': -100,
            'midDistToNextFood': -1,
            'myScaredTime': 500,       # instant punishment
            'numFoodToDefend': -10,     # num is max at 20, so use large weights to increase its influence
            'distToFoodToDefend': 1,
            'distToGuardingPoint': 1,

            'minDistToEntry': -5,
            'minDistToExit': -5,

            'getEaten': 9999,         # instant punishment
            
            # 'enemyScaredTime': -500,    # instant reward
            # 'eatEnemy': -2000,          # instant reward

            # 'numReturned': -100,        # fixed instant reward
            'score': -1000,             # fixed instant reward
            'win': -9999,               # instant punishment
            'lose': 9999,             # instant punishment
            'tie': -100,

            'stop': 100,
            'reverse': 200
            })
  
  def getWeightsAscending(self):
    _weights = self.getWeightsDescending()
    weights = util.Counter()
    for key, value in _weights.items():
      weights[key] = value * -1
    return weights
  
  ################################################################
  #                Some useful helper functions                  #
  ################################################################
  def timeUp(self, _max):
    duration = time.time() - self.start
    return _max - duration < 0.2

  def getOpponentsICanSee(self, gameState, maze=True, _range=SIGHT_RANGE, excludeScared=True):
    '''
    param: 
          maze: boolean
                True -> use maze distance, 
                False -> use Manhattan distance
          _range: int, 0 - SIGHT_RANGE
                  SIGHT_RANGE -> specify the range of sight range, default with game setting
          includeScared: boolean
                         True -> include scared enemies
                         False -> exclude ...

    return: [(agent index, agent position)]
    '''

    myPos = gameState.getAgentPosition(self.index)
    if maze:
      if excludeScared:
        return [(i, pos) for i, pos in self.seenOpponents if self.getMazeDistance(myPos, pos) <= _range and gameState.getAgentState(i).scaredTimer < 6]
      else:
        return [(i, pos) for i, pos in self.seenOpponents if self.getMazeDistance(myPos, pos) <= _range]
    else:
      if excludeScared:
        return [(i, pos) for i, pos in self.seenOpponents if self.manhattanDistancer.getDistance(myPos, pos) <= _range and gameState.getAgentState(i).scaredTimer < 6]
      else:
        return [(i, pos) for i, pos in self.seenOpponents if self.manhattanDistancer.getDistance(myPos, pos) <= _range]

  def getGhostsICanSee(self, gameState, maze=True, _range=SIGHT_RANGE, excludeScared=True):
    return [(i, pos) for i, pos in self.getOpponentsICanSee(gameState, maze, _range, excludeScared) if not gameState.getAgentState(i).isPacman]

  def getPacmenICanSee(self, gameState, maze=True, _range=SIGHT_RANGE, excludeScared=True):
    return [(i, pos) for i, pos in self.getOpponentsICanSee(gameState, maze, _range, excludeScared) if gameState.getAgentState(i).isPacman]
  
  def getOpponentsInSight(self, gameState, maze=True, _range=SIGHT_RANGE, excludeScared=True):
    # beliefs = PositionEstimator.get_instance(gameState, self).getAllEstimations()
    # seen = []
    # for i in self.getOpponents(gameState):
    #   _maxKey = beliefs[i].argMax()
    #   if math.isclose(beliefs[i][_maxKey], 1.0):
    #     seen.append((i, _maxKey))
    myPos = gameState.getAgentPosition(self.index)
    if maze:
      if excludeScared:
        return [(i, pos) for i, pos in self.seenOpponents if gameState.getAgentState(i).scaredTimer < 6]
      else:
        return [(i, pos) for i, pos in self.seenOpponents]
    else:
      if excludeScared:
        return [(i, pos) for i, pos in self.seenOpponents if gameState.getAgentState(i).scaredTimer < 6]
      else:
        return [(i, pos) for i, pos in self.seenOpponents]
    # return [(i, gameState.getAgentPosition(i)) for i in self.getOpponents(gameState) if gameState.getAgentPosition(i) != None]

  def getGhostsInSight(self, gameState, maze=True, _range=SIGHT_RANGE, excludeScared=True):
    return [i for i in self.getOpponentsInSight(gameState, maze, _range, excludeScared) if not gameState.getAgentState(i[0]).isPacman]
    # return [i for i in self.seenOpponents if not gameState.getAgentState(i[0]).isPacman]

  def getPacmenInSight(self, gameState, maze=True, _range=SIGHT_RANGE, excludeScared=True):
    return [i for i in self.getOpponentsInSight(gameState, maze, _range, excludeScared) if gameState.getAgentState(i[0]).isPacman]
    # return [i for i in self.seenOpponents if gameState.getAgentState(i[0]).isPacman]
 
  # def getClosestFoodToEnemy(self):
    #   # should I return a list of 4 players?
    #   # or should I return a pos for a player?
    #   return None

  def getInvaders(self, gameState):
    return [i for i in self.getOpponents(gameState) if gameState.getAgentState(i).isPacman]

  # def beenChased(self, gameState, opponents):
    #   chased = False
    #   for i, pos in opponents:
    #     chased = chased or self.beenChasedBy(gameState, i)
    #   return chased

  # def beenChasedBy(self, gameState, opponentIndex):
    #   myPos = gameState.getAgentPosition(self.index)
    #   currPos = gameState.getAgentPosition(opponentIndex)
    #   lastPos = self.getPreviousObservation().getAgentPosition(opponentIndex)
    #   # lastDirection = self.getPreviousObservation().getAgentState(opponentIndex).getDirection()
    #   if lastPos != None:
    #     lastDist = self.getMazeDistance(myPos, lastPos)
    #     return self.getMazeDistance(myPos, currPos) <= lastDist
      
    #   currDirection = gameState.getAgentState(opponentIndex).getDirection()
    #   if myPos[0] < currPos[0]:
    #     comeToMe = currDirection == Directions.WEST
    #   elif myPos[0] > currPos[0]:
    #     comeToMe = currDirection == Directions.EAST

    #   if myPos[1] < currPos[1]:
    #     comeToMe = currDirection == Directions.WEST
    #   elif myPos[1] > currPos[1]:
    #     comeToMe = currDirection == Directions.NORTH
    #   return comeToMe      

  def getSortedActions(self, gameState, index):
    actions = set(gameState.getLegalActions(index))
    state = gameState.getAgentState(index)

    if index == self.index:
      if gameState.isOnRedTeam(index):
        goRight = self.strategy == ATTACK
      else:
        goRight = self.strategy == RETURN
    else:
      goRight = state.isPacman != gameState.isOnRedTeam(index)  

    # seenEnemy = self.getClosetEnemy(gameState, True)
    # if self.isDefending and seenEnemy != None:
    #   if gameState.getAgentState(self.index).isPacman: # we are been attacked, move away is better
         
    if goRight:
      mySortedActions = [Directions.EAST, Directions.NORTH, Directions.SOUTH, Directions.WEST] # , Directions.STOP
    else:
      mySortedActions = [Directions.WEST, Directions.SOUTH, Directions.NORTH, Directions.EAST] # , Directions.STOP

    return [i for i in mySortedActions if i in actions]

  # def getFilteredActions(self, gameState, index):
  #   agentState = state.getAgentState(index)
  #   conf = agentState.configuration
  #   walls =gameState.getWalls()
  #   use grid
  #   def getPossibleActions(config, walls):
  #       possible = []
  #       x, y = config.pos
  #       x_int, y_int = int(x + 0.5), int(y + 0.5)

  #       # In between grid points, all agents must continue straight
  #       if (abs(x - x_int) + abs(y - y_int)  > Actions.TOLERANCE):
  #           return [config.getDirection()]

  #       for dir, vec in Actions._directionsAsList:
  #           dx, dy = vec
  #           next_y = y_int + dy
  #           next_x = x_int + dx
  #           if not walls[next_x][next_y]: possible.append(dir)

  #       return possible

  def quarterGrid(self, grid, agentIndex, red=True, excludeDeepFoods=True):
    halfway = grid.width // 2
    halfHeight = grid.height // 2
    quarterGrid = Grid(grid.width, grid.height, False)

    if red:
      _xrange = range(halfway)
    else:
      _xrange = range(halfway, grid.width)
    
    if excludeDeepFoods:
      if agentIndex < 2:    
        yrange = range(halfHeight)
      else:       
        yrange = range(halfHeight, grid.height)
    else:
      yrange = range(grid.height)

    for y in yrange:
      for x in _xrange:
        if grid[x][y]:
          if excludeDeepFoods:
            if (x, y) not in self.deepHuTongs: 
              quarterGrid[x][y] = True
          else:
            quarterGrid[x][y] = True

    return quarterGrid

  def getFoodGrid(self, gameState, agentIndex):
    numInvaders = len(self.getInvaders(gameState))
    foodGrid = self.quarterGrid(
                              self.getFood(gameState), 
                              agentIndex, 
                              not gameState.isOnRedTeam(agentIndex),
                              self.limited
                              # numInvaders < 2
                            )
    
    if not self.limited:
      foodList = foodGrid.asList()
      if gameState.isOnRedTeam(agentIndex):
        foodGrid[foodList[-1][0]][foodList[-1][1]] = False
        foodGrid[foodList[-2][0]][foodList[-2][1]] = False
      else:
        foodGrid[foodList[0][0]][foodList[0][1]] = False
        foodGrid[foodList[1][0]][foodList[1][1]] = False

    # if not self.limited:
    #   foodGrid = self.quarterGrid(
    #                           self.getFood(gameState), 
    #                           agentIndex, 
    #                           not gameState.isOnRedTeam(agentIndex),
    #                           False
    #                           # numInvaders < 2
    #                         )
    return foodGrid

  def getFoodList(self, gameState, agentIndex):
    # TODO
    # disable constraints if losing

    # if len(foodList) == 0 and self.getScore(gameState) < 0:
    #   foodList = self.getFood(gameState).asList()

    # unreachables = set([food for food in foodList if food in self.deepHuTongs])
    # foodList = list(set(foodList).difference(unreachables))
    return self.getFoodGrid(gameState, agentIndex).asList()

  def guessOpponentsY(self, gameState):
    beliefs = PositionEstimator.get_instance(gameState, self).getAllEstimations()
    count = util.Counter()
    for i in self.getOpponents(gameState):
      for key, value in beliefs[i].items():
        if not math.isclose(value, 0.0):
          count[key[1]] += 1
    return count.argMax()

  def getClosestGuardingPoint(self, gameState, y):
    if y == None:
      # should never happen
      # beliefs = PositionEstimator.get_instance(gameState, self).getAllEstimations()
      # self.debugDraw(beliefs[0], [1,0,0])
      # self.debugDraw(beliefs[2], [0,1,0])
      # input()
      return random.choice(self.guardingPts[self.teamIndex])

    count = util.Counter()
    for i in self.guardingPts[self.teamIndex]:
      count[i] = abs(i[1] - y) * -1
    return count.argMax()

  def getExitPt(self, gameState):
    myPos = gameState.getAgentPosition(self.index)
    if self.forcedExit != None:
      return self.getMazeDistance(myPos, self.forcedExit), self.forcedExit

    _, minExit = min([(self.getMazeDistance(myPos, pos), pos) for pos in self.middlePts[self.teamIndex]])

    ghosts = self.getGhostsICanSee(gameState, maze=False)
    if len(ghosts) > 0:
      if gameState.isOnRedTeam(self.index):
        ghostInFrontMe = [(i, pos) for i, pos in ghosts if pos[0] < myPos[0]]
      else:
        ghostInFrontMe = [(i, pos) for i, pos in ghosts if pos[0] > myPos[0]]

      if len(ghostInFrontMe) > 0:
        _, minGhost = min([(self.getMazeDistance(myPos, pos), pos) for i, pos in ghostInFrontMe])
        _, minExit = max([(self.getMazeDistance(minGhost, pos), pos) for pos in self.middlePts[self.teamIndex]])
        self.forcedExit = minExit
 
    return _, minExit

  ########################################################
  # Use General A Star Search to find some special paths #
  ########################################################
  def aStarSearchGeneral(self, problem, _maxTime, heuristic=nullHeuristic):
    '''
    return: [(x, y)], [actions]
    '''
    myPQ = util.PriorityQueue()
    startState = problem.getStartState()
    startNode = (startState, '', 0, [])
    myPQ.push(startNode, heuristic(startState, problem))
    visited = set()
    best_g = dict()
    while not myPQ.isEmpty():
      node = myPQ.pop()
      state, action, cost, path = node
      if (not state in visited) or cost < best_g.get(state):
        visited.add(state)
        best_g[state]=cost

        if self.timeUp(_maxTime):
          path = path + [(state, action)]
          actions = problem.retrieveActions(path)
          path = problem.retrievePath(path)
          return path, actions, TIMEOUT

        if problem.isGoalState(state): #  or self.timeUp(_maxTime)
          path = path + [(state, action)]
          actions = problem.retrieveActions(path)
          path = problem.retrievePath(path)
          return path, actions, FOUND

        for succ in problem.getSuccessors(state):
          succState, succAction = succ
          newNode = (succState, succAction, cost + 1, path + [(state, action)])
          myPQ.push(newNode, heuristic(succState, problem)+cost+1)
          
  def getPathEatAllFood(self, gameState, agentIndex, _maxTime):
    def minDistToGoalHeuristic(state, problem):
      return self.getMazeDistance(state, problem.goal)
    
    def allfoodHeuristic(state, problem):
        myPos, foodGrid = state
        foodList = foodGrid.asList()
        if len(foodList) == 0:
          return 0
        #   return min([self.getMazeDistance(myPos, pos) for pos in problem.middlePts])
        return max([self.getMazeDistance(myPos, food) for food in foodList])

    myPos = gameState.getAgentPosition(agentIndex)
    foodGrid = self.getFoodGrid(gameState, self.index)
    walls = gameState.getWalls()
    minDist, minFood = min([(self.getMazeDistance(myPos, food), food) for food in foodGrid.asList()])

    problem = PathSearchProblem(myPos, minFood, walls)
    minPath, minActions, _ = self.aStarSearchGeneral(problem, _maxTime=_maxTime, heuristic=minDistToGoalHeuristic)
    foodGrid[minFood[0]][minFood[1]] = False

    problem = FoodSearchProblem(minFood, foodGrid, walls, self.middlePts[agentIndex % 2])
    foodPath, foodActions, _ = self.aStarSearchGeneral(problem, _maxTime=_maxTime, heuristic=allfoodHeuristic)
    return minPath + foodPath, minActions + foodActions, _

  def getReturnPath(self, gameState, agentIndex, _maxTime):
    def minDistToGoalHeuristic(state, problem):
      return self.getMazeDistance(state, problem.goal)

    myPos = gameState.getAgentPosition(agentIndex)
    walls = gameState.getWalls()
    _, exitPt = self.getExitPt(gameState)

    problem = PathSearchProblem(myPos, exitPt, walls)
    minPath, minActions, _ = self.aStarSearchGeneral(problem, _maxTime=_maxTime, heuristic=minDistToGoalHeuristic)

    return minPath, minActions, _

  def getPatrolPath(self, gameState, agentIndex, _maxTime):
    def minDistToGoalHeuristic(state, problem):
      return self.getMazeDistance(state, problem.goal)
    
    myPos = gameState.getAgentPosition(agentIndex)
    walls = gameState.getWalls()
    if len(self.seenOpponents) == 0:
      goalPos = self.getClosestGuardingPoint(gameState, self.guessOpponentsY(gameState))
    else:
      x, y = min([(self.getMazeDistance(myPos, pos), pos) for i, pos in self.seenOpponents])[1]
      goalPos = self.getClosestGuardingPoint(gameState, y)
    
    problem = PathSearchProblem(myPos, goalPos, walls)
    minPath, minActions, _ = self.aStarSearchGeneral(problem, _maxTime=_maxTime, heuristic=minDistToGoalHeuristic)

    return minPath, minActions, _
    
  def findHuTongs(self, walls):
    hutongs = []

    _walls = walls.deepCopy()
    _last = _walls.deepCopy()
    emptyPos = _walls.asList(False)
    for pos in emptyPos:
      if len(Actions.getLegalNeighbors(pos, _walls)) == 2: # should work fine if change to == 2
        problem = HuTongSearchProblem(pos, _walls)
        path, actions, _ = self.aStarSearchGeneral(problem, _maxTime=15)
        hutongs.append(path)
    for hutong in hutongs:
      for x, y in hutong:
        _walls[x][y] = True

    i=0
    while _last != _walls or i>5:
      i += 1
      _last = _walls.deepCopy()
      emptyPos = _walls.asList(False)
      for pos in emptyPos:
        if len(Actions.getLegalNeighbors(pos, _walls)) == 2: # should work fine if change to == 2
          problem = HuTongSearchProblem(pos, _walls)
          path, actions, _ = self.aStarSearchGeneral(problem, _maxTime=15)
          hutongs.append(path)
      for hutong in hutongs:
        for x, y in hutong:
          _walls[x][y] = True
    
    return hutongs
  
  def getAllHuTongsPos(self):
    pos = set()
    for hutong in self.hutongs:
      pos.update(hutong)
    return pos

  def getDeepHuTongs(self):
    hutongs = set()
    for hutong in self.hutongs:
      if len(hutong) > 3:
        hutongs.update(hutong)
    return hutongs