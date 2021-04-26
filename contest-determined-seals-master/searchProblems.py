from game import Directions, Actions

class FoodSearchProblem:
    """
    copy from Assignment 1
    This is used to find the shortest path to eat all foods via A*
    """
    def __init__(self, pos, foodGrid, walls, middlePts):
        self.start = (pos, foodGrid)
        self.walls = walls
        self.middlePts = middlePts

    def getStartState(self):
        return self.start

    def isGoalState(self, state):
        return state[1].count() == 0
        # return state[1].count() == 0 and state[0][0] == self.middlePts[0][0]

    def getSuccessors(self, state):
        "Returns successor states, the actions they require, and a cost of 1."
        successors = []
        x,y = state[0]
        x_int, y_int = int(x + 0.5), int(y + 0.5)
        for _dir, vec in Actions._directionsAsList:
            dx, dy = vec
            next_x = x_int + dx
            if next_x < 0 or next_x == self.walls.width: continue
            next_y = y_int + dy
            if next_y < 0 or next_y == self.walls.height: continue
            if not self.walls[next_x][next_y]: 
                nextFood = state[1].copy()
                nextFood[next_x][next_y] = False
                successors.append(
                                    (
                                        ((next_x, next_y), nextFood),
                                        _dir
                                    )
                                )
        return successors
    
    def retrievePath(self, path):
        _path = [state[0] for state, action in path]
        del _path[0]
        return _path

    def retrieveActions(self, path):
        _actions = [action for state, action in path]
        del _actions[0]
        return _actions

class PathSearchProblem:
    """
    Given start position and end position, 
    find shortest path between them
    """
    def __init__(self, pos, goal, walls):
        self.start = pos
        self.walls = walls
        self.goal = goal

    def getStartState(self):
        return self.start

    def isGoalState(self, state):
        return state == self.goal
        # return state[1].count() == 0 and state[0][0] == self.middlePts[0][0]

    def getSuccessors(self, state):
        "Returns successor states, the actions they require, and a cost of 1."
        successors = []
        x,y = state
        x_int, y_int = int(x + 0.5), int(y + 0.5)
        for _dir, vec in Actions._directionsAsList:
            dx, dy = vec
            next_x = x_int + dx
            if next_x < 0 or next_x == self.walls.width: continue
            next_y = y_int + dy
            if next_y < 0 or next_y == self.walls.height: continue
            if not self.walls[next_x][next_y]: 
                successors.append((
                                    (next_x, next_y),
                                     _dir
                                ))
        return successors
    
    def retrievePath(self, path):
        _path = [state for state, action in path]
        del _path[0]
        return _path

    def retrieveActions(self, path):
        _actions = [action for state, action in path]
        del _actions[0]
        return _actions

class HuTongSearchProblem:
    """
    This is used to find all hutongs via A*
    """
    def __init__(self, pos, walls):
        self.start = pos
        self.walls = walls

    def getStartState(self):
        return self.start

    def isGoalState(self, state):
        return len(Actions.getLegalNeighbors(state, self.walls)) > 3

    def getSuccessors(self, state):
        "Returns successor states, the actions they require, and a cost of 1."
        successors = []
        x,y = state
        x_int, y_int = int(x + 0.5), int(y + 0.5)
        for _dir, vec in Actions._directionsAsList:
            dx, dy = vec
            next_x = x_int + dx
            if next_x < 0 or next_x == self.walls.width: continue
            next_y = y_int + dy
            if next_y < 0 or next_y == self.walls.height: continue
            if not self.walls[next_x][next_y]: 
                successors.append(((next_x, next_y), _dir))
        return successors

    def retrievePath(self, path):
        path.pop()
        return [state for state, action in path]
    
    def retrieveActions(self, path):
        return None