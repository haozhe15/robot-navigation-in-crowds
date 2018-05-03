import sys, random
import math
import numpy as np

import pygame
from pygame.locals import *
from pygame.color import THECOLORS

import pymunk
from pymunk.vec2d import Vec2d
import pymunk.pygame_util

# PyGame init
width = 1200
height = 900
pygame.init()
screen = pygame.display.set_mode((width, height),RESIZABLE,32)
clock = pygame.time.Clock()

# Global variables
sensor_range = 100
robot_radius = 30
robot_velocity = 200
obs_radius = 30

# Collision types
COLLITYPE_ROBOT = 1
COLLITYPE_OBSTACLE = 2
COLLITYPE_WALL = 3
COLLITYPE_GOAL = 4

# Robot status
EXIT = -1
NORMAL = 0
REACH_GOAL = 1
HIT_OBSTACLE = 2
HIT_WALL = 3

class GameClass:
    def __init__(self, draw_screen, display_path, fps):
        # Physics conditions.
        self.space = pymunk.Space()
        self.space.gravity = pymunk.Vec2d(0., 0.)
        self.draw_screen = draw_screen 
        self.display_path = display_path
        self.fps = fps

        # Setup the status
        self.status = NORMAL

        collision_handle(self)        

        # Record num of steps
        self.num_steps = 0

        # Add borders in the space
        self.add_borders()

        # Add the robot in the space.
        self.add_robot(100, 100)

        # Add some obstacles in the space
        # For now, the obstacles have fixed position
        self.num_obstacles = 10
        self.add_obstacles(isRandom = False) # if True, obstacles are randomly spanned in the space

        # Add the goal in the space
        self.add_goal(width - 100, height-100)
        
        # Track the path of the robot
        self.path_holder = []
        # Draw stuffs on the screen
        self.draw_options = pymunk.pygame_util.DrawOptions(screen)

    
    

    def add_borders(self):
        borders = [
            pymunk.Segment(
                self.space.static_body,
                (0, 1), (0, height), 5),
            pymunk.Segment(
                self.space.static_body,
                (1, height), (width, height), 5),
            pymunk.Segment(
                self.space.static_body,
                (width - 1, height), (width - 1, 1), 5),
            pymunk.Segment(
                self.space.static_body,
                (1, 1), (width, 1), 5)  # ,
            # pymunk.Segment(
            #     self.space.static_body,
            #     (width/2., 1), (width/2., height*0.75), 5)
        ]
        for b in borders:
            b.friction = 1.
            b.group = 1
            b.collision_type = COLLITYPE_WALL
            b.color = THECOLORS['brown']
            b.elasticity = 1
        self.space.add(borders)

    def add_robot(self, x, y):
        """Add a circle robot at a given position"""
        mass = 1
        radius = robot_radius
        inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
        self.robot_body = pymunk.Body(mass, inertia)
        self.robot_body.position = x, y
        self.robot_body.velocity = random.choice([(1, 10), (-1, 10)])
        self.robot_body.velocity_func = self.constant_velocity

        self.robot_shape = pymunk.Circle(self.robot_body, radius, (0, 0))
        self.robot_shape.color = THECOLORS["orange"]
        self.robot_shape.elasticity = 1
        self.robot_shape.collision_type = COLLITYPE_ROBOT
        self.space.add(self.robot_body, self.robot_shape)

    def add_obstacle(self, x, y):
        """Add an obstacle at a given position"""
        # mass = 1
        radius = obs_radius
        # inertia = pymunk.moment_for_circle(mass, 0, radius, (0,0))
        # obs_body = pymunk.Body(mass, inertia)

        obs_body = pymunk.Body(body_type=pymunk.Body.STATIC)

        obs_body.position = x, y
        obs_shape = pymunk.Circle(obs_body, radius, (0, 0))
        obs_shape.color = THECOLORS["blue"]
        obs_shape.elasticity = 1
        obs_shape.collision_type = COLLITYPE_OBSTACLE
        self.space.add(obs_body, obs_shape)
        return obs_shape

    def add_obstacles(self,isRandom):
        self.obstacles = []
        if isRandom:
            for i in range(self.num_obstacles):
                self.obstacles.append(self.add_obstacle(random.randint(obs_radius, width - obs_radius),
                                                    random.randint(obs_radius, height - obs_radius)))
        else:
            self.obstacles.append(self.add_obstacle(390, 774))
            self.obstacles.append(self.add_obstacle(917, 349))
            self.obstacles.append(self.add_obstacle(660, 580))
            self.obstacles.append(self.add_obstacle(730, 344))
            self.obstacles.append(self.add_obstacle(712, 204))
            self.obstacles.append(self.add_obstacle(431, 516))
            self.obstacles.append(self.add_obstacle(1048, 199))
            self.obstacles.append(self.add_obstacle(1155, 689))
            self.obstacles.append(self.add_obstacle(660, 134))
            self.obstacles.append(self.add_obstacle(826, 589))

    def draw_path(self):
         # Update the path points and draw the path
        position = np.array(self.robot_body.position)
        position[1] = height-position[1]
        if len(self.path_holder)>1:
            notCollapes = np.linalg.norm(
                self.path_holder[-1]-self.path_holder[-2]) >= 0.1
            if notCollapes:
                self.path_holder.append(position)
            pygame.draw.aalines(
                screen, THECOLORS["red"], False, self.path_holder)
        else:
            self.path_holder.append(position)
            
    def add_goal(self, x, y):
        """Add the goal at a given position"""
        self.goal = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.goal.position = x, y
        self.goal_radius = 10
        self.goal_shape = pymunk.Circle(self.goal, self.goal_radius, (0, 0))
        self.goal_shape.color = THECOLORS["red"]
        self.goal_shape.collision_type = COLLITYPE_GOAL
        self.goal_shape.elasticity = 0
        self.space.add(self.goal, self.goal_shape)

    # Keep robot velocity at a static value
    def constant_velocity(self,body, gravity, damping, dt):
        body.velocity = body.velocity.normalized() * robot_velocity

    # def get_sensor_data(self):
    #     readings = list([-100]*self.num_obstacles)
    #     for i, o in enumerate(self.obstacles):
    #         distance = self.robot_body.position.get_distance(o.body.position)
    #         if distance <= sensor_range + obs_radius:
    #             readings[i] = distance - robot_radius - obs_radius
    #     return readings

    # def check_reach_goal(self):
    #     distance2goal = self.robot_body.position.get_distance(self.goal.position)
    #     if distance2goal <= (robot_radius + self.goal_radius + 5):
    #         screen.fill(THECOLORS["yellow"])
    #         self.reach_goal = 1
    #         return True
    #     else:
    #         return False

    # def get_reward_0(self,readings):
    #     reward = 0
    #     distance2goal = self.robot_body.position.get_distance(self.goal.position)
    #     if self.check_reach_goal():
    #         reward = 10000
    #     reward -= int(distance2goal/math.sqrt(width**2 + height**2) * 600)
    #     for reading in readings:
    #         if reading != -100: # the reading is valid
    #             reward += int(200/(sensor_range-robot_radius) * reading - 200)
    #     return reward

    # def get_reward_1(self,readings):
    #     # reward = -self.num_steps/self.fps
    #     reward = 0
    #     for reading in readings:
    #         if reading >= 0 and reading <=1:
    #             reward -=50
    #     if self.check_reach_goal():
    #         reward += 10000
    #     return reward
    
    def get_reward(self):
        reward = 0
        if self.status == HIT_OBSTACLE:
            reward -= 50
        elif self.status == HIT_WALL:
            reward -= 10
        elif self.status == REACH_GOAL:
            reward += 10000
        return reward

    def frame_step(self, action):
        # Update the screen and stuff every second
        self.update(self.fps)
        self.num_steps += 1

        # Align the robot's pointing angle to its velocity
        r_v = self.robot_body.velocity.get_length()
        r_vx = self.robot_body.velocity.x
        r_vy = self.robot_body.velocity.y
        if r_v != 0:
            if r_vx >= 0:
                self.robot_body.angle = math.asin(r_vy / r_v)
            else:
                self.robot_body.angle = math.pi - math.asin(r_vy / r_v)

        # Manually control the robot's action for debuging
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_RIGHT:
                self.robot_body.velocity = self.robot_body.velocity.rotated_degrees(-30)
            elif event.type == KEYDOWN and event.key == K_LEFT:
                self.robot_body.velocity = self.robot_body.velocity.rotated_degrees(30)

        # Use given action
        if action == 0: # Turn right
            self.robot_body.velocity = self.robot_body.velocity.rotated_degrees(-5)
        elif action == 1: # Turn left
            self.robot_body.velocity = self.robot_body.velocity.rotated_degrees(5)

        # Exit the game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # sys.exit(0)
                self.status = EXIT
            elif event.type == pygame.KEYDOWN and (event.key in [pygame.K_ESCAPE, pygame.K_q]):
                # sys.exit(0)
                self.status = EXIT

            
        # Get the current state of the robot
        position = np.array(self.robot_body.position)
        # velocity = self.robot_body.velocity
        # readings = self.get_sensor_data()
        # state = np.array(readings).reshape((self.num_obstacles,))
        state = position
        reward = self.get_reward()

        if reward != 0:
            print("action: %d, reward: %f, reach goal? %d" % (action, reward,self.reach_goal))
        return reward, state

    def update(self, fps):
        screen.fill(THECOLORS["white"])
        if self.display_path:
            self.draw_path()
        self.space.debug_draw(self.draw_options)
        self.space.step(1 / fps)
        if self.draw_screen:
            pygame.display.flip()
            clock.tick(fps)

# Define collision callback function, will be called when X touches Y
def reach_goal(arbiter, space, data):
    self.status = REACH_GOAL
    self.robot_body.velocity = 0,0 # Stop if reach the goal
    if self.draw_screen:
        print("you reach the goal!")

def exit_game(arbiter, space, data):
    self.status = EXIT  

def hit_obstacle(arbiter, space, data = GameClass):
    GameClass.status = HIT_OBSTACLE
    if GameClass.draw_screen:
        print("you hit an obstacle!")
    return True

def hit_wall(arbiter, space, data):
    self.status = HIT_WALL
    if self.draw_screen:
        print("you hit the wall!")
    return True

def normal(arbiter, space, data):
    self.status = NORMAL
    if self.draw_screen:
        print("Nothing happens.")

# Setup the collision callback function
def conllision_handle(gameObject):
    rg = gameObject.space.add_collision_handler(COLLITYPE_ROBOT, COLLITYPE_GOAL)
    rg.begin = reach_goal
    rg.post_solve = exit_game

    ro = gameObject.space.add_collision_handler(COLLITYPE_ROBOT, COLLITYPE_OBSTACLE)
    ro.begin = hit_obstacle
    ro.separate = normal

    rw = gameObject.space.add_collision_handler(COLLITYPE_ROBOT, COLLITYPE_WALL)
    rw.begin = hit_wall
    rw.separate = normal

if __name__ == "__main__":

    game_class = GameClass(draw_screen = True, display_path = True, fps = 60)
    
    # Game loop
    while game_class.status != EXIT:
        # randomly set the action every 100 steps
        # action = 2
        # if game_class.num_steps % 100 ==0:
        #     action = random.randint(0, 2)
        # else:
        #     action = 2
        # reward, state = game_class.frame_step(action)
        
        reward, state = game_class.frame_step(random.randint(0, 2))
        # reward, state = game_class.frame_step(2)
    pygame.display.quit()
    pygame.quit()

#test
