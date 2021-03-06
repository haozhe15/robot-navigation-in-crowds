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
robot_radius = 30
robot_velocity = 200
obs_radius = 30

class GameClass:
    def __init__(self, draw_screen, display_path, fps):
        # Physics conditions.
        self.space = pymunk.Space()
        self.space.gravity = pymunk.Vec2d(0., 0.)
        self.draw_screen = draw_screen 
        self.display_path = display_path
        self.fps = fps

        # Exit the game
        self.exit = 0

        # Record num of steps
        self.num_steps = 0

        # Record whether the robot hit something
        self.hit = 0

        # Add borders in the space
        self.add_borders()

        # Add the robot in the space.
        self.add_robot(100, 100)

        # Add some obstacles in the space
        # For now, the obstacles have fixed position
        self.num_obstacles = 10
        self.add_obstacles(False) # if True, obstacles are randomly spanned in the space

        # Add the goal in the space
        self.add_goal(width - 100, height-100)
        self.reach_goal = 0
        
        # Track the path of the robot
        self.path_holder = []
        # Draw stuffs on the screen
        self.draw_options = pymunk.pygame_util.DrawOptions(screen)

    def add_borders(self):
        self.borders = [
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
                (1, 1), (width, 1), 5)
            # pymunk.Segment(
            #     self.space.static_body,
            #     (width/2., 1), (width/2., height*0.75), 5)
        ]
        for b in self.borders:
            b.friction = 1.
            b.group = 1
            b.collision_type = 1
            b.color = THECOLORS['brown']
            b.elasticity = 1
        self.space.add(self.borders)

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
        self.robot_shape.collision_type = 2
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

            # self.obstacles.append(self.add_obstacle(600,450))

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
        self.goal_shape.collision_type = 2
        self.goal_shape.elasticity = 0
        self.space.add(self.goal, self.goal_shape)

    # Keep robot velocity at a static value
    def constant_velocity(self,body, gravity, damping, dt):
        body.velocity = body.velocity.normalized() * robot_velocity

    def get_sensor_data(self):
        readings = list([-100]*self.num_obstacles)
        for i, o in enumerate(self.obstacles):
            distance = self.robot_body.position.get_distance(o.body.position)
            readings[i] = distance - robot_radius - obs_radius
        return readings

    def check_hit_obstacle(self):
        for o_shape in self.obstacles:
            if self.robot_shape.shapes_collide(o_shape).points:
                print("Hit an obstacle!")
                return True
        return False

    def check_hit_wall(self):
        for b in self.borders:
            if self.robot_shape.shapes_collide(b).points:
                print("Hit the wall!")
                return True
        return False

    def check_reach_goal(self):
        if self.robot_shape.shapes_collide(self.goal_shape).points:
            print("reach goal!")
            return True
        else:
            return False

    def get_reward(self,readings):
        reward = -self.num_steps/self.fps
        
        if self.check_hit_obstacle():
            reward -=50
            self.hit = 1
        else:
            self.hit = 0
            
        if self.check_hit_wall():
            reward -=50
            self.hit = 1
        else:
            self.hit = 0

        if self.check_reach_goal():
            reward += 10000
            self.reach_goal = 1
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
                self.robot_body.velocity = self.robot_body.velocity.rotated_degrees(-45)
            elif event.type == KEYDOWN and event.key == K_LEFT:
                self.robot_body.velocity = self.robot_body.velocity.rotated_degrees(45)

        # Use given action
        if action == 0: # Turn right
            self.robot_body.velocity = self.robot_body.velocity.rotated_degrees(-5)
        elif action == 1: # Turn left
            self.robot_body.velocity = self.robot_body.velocity.rotated_degrees(5)

        # Exit the game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # sys.exit(0)
                self.exit = 1
            elif event.type == pygame.KEYDOWN and (event.key in [pygame.K_ESCAPE, pygame.K_q]):
                # sys.exit(0)
                self.exit = 1

        # Stop if reach the goal
        if self.check_reach_goal():
            self.robot_body.velocity = 0,0
            self.reach_goal = 1
            self.exit = 1
            
        # Get the current state of the robot
        position = np.array(self.robot_body.position)
        angle = np.array(self.robot_body.angle)
        readings = self.get_sensor_data()
        # state = np.array(readings).reshape((self.num_obstacles,))
        state = np.hstack((position,angle))
        reward = self.get_reward(readings)
        
        # if self.hit or self.reach_goal:
        #     print("action: %d, reward: %f, reach goal? %d" % (action, reward,self.reach_goal))
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



if __name__ == "__main__":

    game_class = GameClass(draw_screen = True, display_path = True, fps = 30)
    
    # Game loop
    while game_class.exit == 0:
            reward, state = game_class.frame_step(random.randint(0, 2))
        # reward, state = game_class.frame_step(2)
    pygame.display.quit()
    pygame.quit()

#test
