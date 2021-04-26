# UoM COMP90054 Contest Project
# Table of contents
1. [Home and Introduction]()
2. [Design Choices (Offense/Defense)](Design-Choices)

    2.1 [Approach One - A Star](AI-Method-1)

    2.2 [Approach Two - MiniMax](AI-Method-2)

    2.3 [Approach Three - MCT](AI-Method-3)
3. [Evolution and Experiments](Evolution)
4. [Conclusions and Reflections](Conclusions-and-Reflections)

# Intro
The goal of this project is to develop an autonomous Pacman agent team to play the [Pacman Capture the Flag Contest](http://ai.berkeley.edu/contest.html). 

3 AI related techniques have been used in the final submission: 
1. Heuristic Search Algorithms - A Star 
2. Monte Carlo Tree Search 
3. Game Theoretic Methods - MiniMax.

A star is the core algorithm for this project, its performance has been further enhanced by using it injunction with Decision Tree. 
MiniMax achieved decent results and time limits has being implemented to overcome its tendency of being too slow and avoids timeout.
MCT is also able to work around the time limit by interrupt before timeout and yield current best path found. This project also explored a reinforcement learning technique - DQN. However it is exluded from submission due to performance issue.
See table of contents for details on each approach.

# Youtube presentation

[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/bnMl0d-RcPQ/0.jpg)](https://www.youtube.com/watch?v=bnMl0d-RcPQ)

## Team name
```determined-seals ```

## Team Members

List here the full name, email, and student number for each member of the team:

* Student 1's Full Name - Student email - UoM Student number
* Student 2's Full Name - Student email - UoM Student number
* Jiayu Li - jiayul3@student.unimelb.edu.au - 713551
* Xin Wei Ding - xind1@student.unimelb.edu.au - 758966


# Usage
Run final agent as blue team against baseline red team
```bash
python capture.py -b myTeam -r baselineTeam
```
