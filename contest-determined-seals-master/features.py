# Offensive features

# Danger zone (in maze distance) within which the agent needs to be careful 
# about an opponent when invading opponent's area
DANGER_DISTANCE = 3

# The amount of heuristics to add to the opponent's side cell that has an 
# opponent on it
DANGER_H = (DANGER_DISTANCE+1) * 90

# When agent is carrying food and is less than GO_HOME_DISTANCE maze distance 
# away from any border cell on the team's side, go home
GO_HOME_DISTANCE = 5

# When the scared timer is larger than SAFE_OPPO_SCARED_TIMER, agent can ignore
# the opponents
SAFE_OPPO_SCARED_TIMER = 5
SAFE_OPPO_SCARED_FOR_MORE_FOOD = 15

TIME_TO_GO_HOME_OFFSET = 10

# REPEAT_MOVE_THRESHOLD = 5

# Defensive features

# If the agent is within CHASE_DISTANCE maze distance away from an invader, 
# chase the invader
CHASE_INVADER_DISTANCE = 5

DEFEND_GHOST_DISTANCE = 5

SAFE_TEAM_SCARED_TIMER = 3

ROUNDS_POS_EST_STALE = 4

# Distance to follow invaders when scared
DISTANCE_TO_INVADER_WHEN_SCARED = 3