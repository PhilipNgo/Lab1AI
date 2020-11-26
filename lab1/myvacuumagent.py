import queue
#import sys
from lab1.liuvacuum import *

# sys.setrecursionlimit(500)
# Students:
# Philip Ngo - phing272, Emma Segolsson - emmse713

DEBUG_OPT_DENSEWORLDMAP = False

AGENT_STATE_UNKNOWN = 0
AGENT_STATE_WALL = 1
AGENT_STATE_CLEAR = 2
AGENT_STATE_DIRT = 3
AGENT_STATE_HOME = 4

AGENT_DIRECTION_NORTH = 0
AGENT_DIRECTION_EAST = 1
AGENT_DIRECTION_SOUTH = 2
AGENT_DIRECTION_WEST = 3


def direction_to_string(cdr):
    cdr %= 4
    return "NORTH" if cdr == AGENT_DIRECTION_NORTH else\
        "EAST" if cdr == AGENT_DIRECTION_EAST else\
        "SOUTH" if cdr == AGENT_DIRECTION_SOUTH else\
        "WEST"  # if dir == AGENT_DIRECTION_WEST


"""
Internal state of a vacuum agent
"""


class MyAgentState:

    def __init__(self, width, height):

        # Initialize perceived world state
        self.world = [[AGENT_STATE_UNKNOWN for _ in range(
            height)] for _ in range(width)]
        self.world[1][1] = AGENT_STATE_HOME

        # Agent internal state
        self.last_action = ACTION_NOP
        self.direction = AGENT_DIRECTION_EAST
        self.pos_x = 1
        self.pos_y = 1

        # Metadata
        self.world_width = width
        self.world_height = height

        # Check when its time to go home
        self.going_home = False

        # Check if recursion is too high
        self.stopped = False

        # Queue and visited
        self.visited = []
        self.queue = []
        self.path = []

    """
    Update perceived agent location
    """

    def update_position(self, bump):
        if not bump and self.last_action == ACTION_FORWARD:
            if self.direction == AGENT_DIRECTION_EAST:
                self.pos_x += 1
            elif self.direction == AGENT_DIRECTION_SOUTH:
                self.pos_y += 1
            elif self.direction == AGENT_DIRECTION_WEST:
                self.pos_x -= 1
            elif self.direction == AGENT_DIRECTION_NORTH:
                self.pos_y -= 1

    """
    Update perceived or inferred information about a part of the world
    """

    def update_world(self, x, y, info):
        self.world[x][y] = info

    """
    Dumps a map of the world as the agent knows it
    """

    def print_world_debug(self):
        for y in range(self.world_height):
            for x in range(self.world_width):
                if self.world[x][y] == AGENT_STATE_UNKNOWN:
                    print("?" if DEBUG_OPT_DENSEWORLDMAP else " ? ", end="")
                elif self.world[x][y] == AGENT_STATE_WALL:
                    print("#" if DEBUG_OPT_DENSEWORLDMAP else " # ", end="")
                elif self.world[x][y] == AGENT_STATE_CLEAR:
                    print("." if DEBUG_OPT_DENSEWORLDMAP else " . ", end="")
                elif self.world[x][y] == AGENT_STATE_DIRT:
                    print("D" if DEBUG_OPT_DENSEWORLDMAP else " D ", end="")
                elif self.world[x][y] == AGENT_STATE_HOME:
                    print("H" if DEBUG_OPT_DENSEWORLDMAP else " H ", end="")

            print()  # Newline
        print()  # Delimiter post-print


"""
Vacuum agent
"""


class MyVacuumAgent(Agent):

    def __init__(self, world_width, world_height, log):
        super().__init__(self.execute)
        self.initial_random_actions = 10
        self.iteration_counter = 2000
        self.state = MyAgentState(world_width, world_height)
        self.log = log

    def move_to_random_start_position(self, bump):
        action = random()

        self.initial_random_actions -= 1
        self.state.update_position(bump)

        if action < 0.1666666:   # 1/6 chance
            self.state.direction = (self.state.direction + 3) % 4
            self.state.last_action = ACTION_TURN_LEFT
            return ACTION_TURN_LEFT
        elif action < 0.3333333:  # 1/6 chance
            self.state.direction = (self.state.direction + 1) % 4
            self.state.last_action = ACTION_TURN_RIGHT
            return ACTION_TURN_RIGHT
        else:                    # 4/6 chance
            self.state.last_action = ACTION_FORWARD
            return ACTION_FORWARD

    def BFS(self, search_obj, queue=None, initial=None):

        if(queue.qsize() < 500):

            # Get data from queue
            current = queue.get()
            current_index = current[0]
            parent = current[1]
            current_x, current_y = current_index[0], current_index[1]

            element = self.state.world[current_x][current_y]

            # Check if its time to go home
            if(self.state.going_home):
                if(current_index == (1, 1)):
                    self.log("Find path home..")
                    self.state.path.append(current_index)
                    self.state.path.append(parent)

                    return parent

            # Check if unknown
            elif (element == AGENT_STATE_UNKNOWN):

                self.state.path.append(current_index)
                self.state.path.append(parent)
                return parent

            # Count if anything has been added to the queue
            counter = 0

            for n in range(current_x-1, current_x+2):
                for m in range(current_y-1, current_y+2):
                    if not (n == current_x and m == current_y) \
                            and not (n == current_x - 1 and m == current_y - 1) \
                            and not (n == current_x + 1 and m == current_y + 1) \
                            and not (n == current_x - 1 and m == current_y + 1) \
                            and not (n == current_x + 1 and m == current_y - 1) \
                            and n > -1 and m > -1 \
                            and n < self.state.world_width and m < self.state.world_height \
                            and self.state.world[n][m] != AGENT_STATE_WALL\
                            and (n, m) not in self.state.visited:
                        queue.put(((n, m), current_index))
                        counter += 1

            # Keep track of visited positions
            self.state.visited.append(current_index)

            # No path to next unknown and nothing added to queue. Time to go home.
            if(queue.qsize() == 0 and counter == 0):

                self.state.going_home = True
                self.state.path.clear()
                self.state.visited.clear()

            elif(queue.qsize() > 0):

                p = self.BFS(search_obj, queue, initial)

                if(self.state.going_home):
                    self.state.going_home = True

                elif(p == current_index and parent != current_index):
                    self.state.path.append(parent)
                    return parent
                else:
                    return p

        else:

            self.log("Recursion limit reached..")
            self.state.stopped = True

    def execute(self, percept):

        ###########################
        # DO NOT MODIFY THIS CODE #
        ###########################

        bump = percept.attributes["bump"]
        dirt = percept.attributes["dirt"]
        home = percept.attributes["home"]

        # Move agent to a randomly chosen initial position
        if self.initial_random_actions > 0:
            self.log("Moving to random start position ({} steps left)".format(
                self.initial_random_actions))
            return self.move_to_random_start_position(bump)

        # Finalize randomization by properly updating position (without subsequently changing it)
        elif self.initial_random_actions == 0:
            self.initial_random_actions -= 1
            self.state.update_position(bump)
            self.state.last_action = ACTION_SUCK
            self.log("Processing percepts after position randomization")
            return ACTION_SUCK

        ########################
        # START MODIFYING HERE #
        ########################

        # Track position of agent
        self.state.update_position(bump)

        # Max iterations for the agent
        if self.iteration_counter < 1:
            if self.iteration_counter == 0:
                self.iteration_counter -= 1
                self.log("Iteration counter is now 0. Halting!")
                self.log("Performance: {}".format(self.performance))
            return ACTION_NOP

        self.log("Position: ({}, {})\t\tDirection: {}".format(self.state.pos_x, self.state.pos_y,
                                                              direction_to_string(self.state.direction)))

        self.iteration_counter -= 1

        if bump:
            # Get an xy-offset pair based on where the agent is facing
            offset = [(0, -1), (1, 0), (0, 1),
                      (-1, 0)][self.state.direction]

            # Mark the tile at the offset from the agent as a wall (since the agent bumped into it)
            self.state.update_world(
                self.state.pos_x + offset[0], self.state.pos_y + offset[1], AGENT_STATE_WALL)

        # Update perceived state of current tile
        if dirt:
            self.state.update_world(
                self.state.pos_x, self.state.pos_y, AGENT_STATE_DIRT)
        else:
            self.state.update_world(
                self.state.pos_x, self.state.pos_y, AGENT_STATE_CLEAR)

        # Debug
        self.state.print_world_debug()

        # Decide action
        if dirt:
            self.log("DIRT -> choosing SUCK action!")
            self.state.last_action = ACTION_SUCK
            return ACTION_SUCK
        elif bump:
            if(self.state.direction == 3):
                self.state.direction = 0
            else:
                self.state.direction += 1

            self.state.last_action = ACTION_TURN_RIGHT
            return ACTION_TURN_RIGHT

        else:

            if(self.state.stopped == True):
                self.log("Recursion break")
                self.iteration_counter = 0
                self.state.last_action = ACTION_NOP
                return ACTION_NOP

            else:

                # Initiate queue
                start_queue = queue.Queue()
                current_pos = (self.state.pos_x, self.state.pos_y)
                start_queue.put((current_pos, current_pos))

                # Find unknown or home
                if(len(self.state.path) == 0):

                    self.state.visited.clear()
                    self.BFS(AGENT_STATE_UNKNOWN, start_queue, current_pos)

                    if(len(self.state.path) > 0):
                        self.state.path.pop()

                # Follow path given by BFS
                if(len(self.state.path) != 0):

                    go_to = self.state.path[-1]

                    if(self.state.pos_x > go_to[0]):
                        if(self.state.direction == AGENT_DIRECTION_WEST):

                            self.state.path.pop(-1)
                            #self.log(("Going forward"))
                            self.state.last_action = ACTION_FORWARD
                            return ACTION_FORWARD

                        else:

                            if(self.state.direction == AGENT_DIRECTION_NORTH):

                                if(self.state.direction == 0):
                                    self.state.direction = 3
                                else:
                                    self.state.direction -= 1

                                self.state.last_action = ACTION_TURN_LEFT
                                return ACTION_TURN_LEFT

                            else:

                                if(self.state.direction == 3):
                                    self.state.direction = 0
                                else:
                                    self.state.direction += 1

                                self.state.last_action = ACTION_TURN_RIGHT
                                return ACTION_TURN_RIGHT

                    elif(self.state.pos_x < go_to[0]):
                        if(self.state.direction == AGENT_DIRECTION_EAST):

                            self.state.path.pop(-1)
                            #self.log(("Going forward"))
                            self.state.last_action = ACTION_FORWARD
                            return ACTION_FORWARD
                        else:

                            if(self.state.direction == AGENT_DIRECTION_SOUTH):

                                if(self.state.direction == 0):
                                    self.state.direction = 3
                                else:
                                    self.state.direction -= 1

                                self.state.last_action = ACTION_TURN_LEFT
                                return ACTION_TURN_LEFT

                            else:
                                if(self.state.direction == 3):
                                    self.state.direction = 0
                                else:
                                    self.state.direction += 1

                                self.state.last_action = ACTION_TURN_RIGHT
                                return ACTION_TURN_RIGHT

                    elif(self.state.pos_y > go_to[1]):
                        if(self.state.direction == AGENT_DIRECTION_NORTH):

                            self.state.path.pop(-1)
                            #self.log(("Going forward"))
                            self.state.last_action = ACTION_FORWARD
                            return ACTION_FORWARD

                        else:

                            if(self.state.direction == AGENT_DIRECTION_EAST):

                                if(self.state.direction == 0):
                                    self.state.direction = 3
                                else:
                                    self.state.direction -= 1

                                self.state.last_action = ACTION_TURN_LEFT
                                return ACTION_TURN_LEFT

                            else:
                                if(self.state.direction == 3):
                                    self.state.direction = 0
                                else:
                                    self.state.direction += 1

                                self.state.last_action = ACTION_TURN_RIGHT
                                return ACTION_TURN_RIGHT

                    elif(self.state.pos_y < go_to[1]):
                        if(self.state.direction == AGENT_DIRECTION_SOUTH):

                            self.state.path.pop(-1)
                            #self.log(("Going forward"))
                            self.state.last_action = ACTION_FORWARD
                            return ACTION_FORWARD
                        else:

                            if(self.state.direction == AGENT_DIRECTION_WEST):

                                if(self.state.direction == 0):
                                    self.state.direction = 3
                                else:
                                    self.state.direction -= 1

                                self.state.last_action = ACTION_TURN_LEFT
                                return ACTION_TURN_LEFT
                            else:
                                if(self.state.direction == 3):
                                    self.state.direction = 0
                                else:
                                    self.state.direction += 1
                                #self.log(("Turning right towards SOUTH"))
                                self.state.last_action = ACTION_TURN_RIGHT
                                return ACTION_TURN_RIGHT

                    else:
                        self.log("You are at home..")
                        #self.log(("Path:", self.state.path))
                        self.state.path.pop()
                        self.iteration_counter = 0
                        self.state.last_action = ACTION_NOP
                        return ACTION_NOP
