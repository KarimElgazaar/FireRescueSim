import pygame
import random
from enum import Enum
from collections import namedtuple
import numpy as np

pygame.init()
font = pygame.font.Font('arial.ttf', 20)

class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

Position = namedtuple('Position', 'x, y')

WHITE = (255, 255, 255)
RED = (200,0,0)
BLUE1 = (0, 0, 255)
BLUE2 = (0, 100, 255)
BLACK = (0,0,0)
GREY = (150, 150, 150)
ORANGE = (255, 165, 0)
BLOCK_SIZE = 20
SPEED = 40

class FireRescueSimulation:

    def __init__(self, w=640, h=480):
        self.w = w
        self.h = h
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Fire Rescue Simulation')
        self.clock = pygame.time.Clock()
        self.walls=[]
        self.fires = []
        self.reset()

    def reset(self):
        self.Direction = Direction.RIGHT
        self.hero = Position(20, self.h - 2*BLOCK_SIZE) 
        self.rescuers = [self.hero]
        self.score = 0
        self.victim = None
        self.victim_count = 0
        self._place_victim()
        self.init_fires()
        self.create_walls_and_rooms()
        self.frame_iteration = 1

    def _place_victim(self):
        if self.victim_count == 0:
            x = random.randint(1, (self.w - 2*BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
            y = random.randint(1, (self.h - 2*BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
            self.victim = Position(x, y)
            self.victim_count += 1
        elif self.victim_count == 1:
            self.victim = Position(20, self.h - BLOCK_SIZE*2)  
            self.victim_count += 1
        else:
            self.victim = None  

    def create_walls_and_rooms(self):
        self.walls = [
            pygame.Rect(0, 0, self.w, BLOCK_SIZE),
            pygame.Rect(0, 0, BLOCK_SIZE, self.h),
            pygame.Rect(self.w - BLOCK_SIZE, 0, BLOCK_SIZE, self.h),
            pygame.Rect(0, self.h - BLOCK_SIZE, self.w, BLOCK_SIZE),
        ]


    def init_fires(self):
        self.fires = []
        num_clusters = 3
        cluster_size = 5
        for _ in range(num_clusters):
            cx = random.randint(1, (self.w - 2 * BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
            cy = random.randint(1, (self.h - 2 * BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
            for _ in range(cluster_size):
                fx = cx + random.choice([-1, 0, 1]) * BLOCK_SIZE
                fy = cy + random.choice([-1, 0, 1]) * BLOCK_SIZE
                fire_rect = pygame.Rect(fx, fy, BLOCK_SIZE, BLOCK_SIZE)
                self.fires.append(fire_rect)

    def spread_fire(self):
        new_fires = []
        for fire in self.fires:
            possible_spreads = [Position(fire.x + BLOCK_SIZE, fire.y), Position(fire.x - BLOCK_SIZE, fire.y),
                                Position(fire.x, fire.y + BLOCK_SIZE), Position(fire.x, fire.y - BLOCK_SIZE)]
            for pos in possible_spreads:
                if 0 <= pos.x < self.w and 0 <= pos.y < self.h and not any(fire.x == pos.x and fire.y == pos.y for fire in self.fires):
                    new_fires.append(pygame.Rect(pos.x, pos.y, BLOCK_SIZE, BLOCK_SIZE))
        self.fires.extend(new_fires)

    def play_step(self, action):
        self.frame_iteration += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        if self.frame_iteration % 150 == 0:
            self.spread_fire()
        self._move(action)
        self.rescuers.insert(0, self.hero)
        
        reward = 0
        game_over = False
        if self.is_collision() or self.frame_iteration > 200*len(self.rescuers):
            game_over = True
            if self.victim_count == 2:
                reward = 10-self.frame_iteration/50
            reward = -10-self.frame_iteration/50
            return reward, game_over, self.score,self.frame_iteration

        if self.hero == self.victim:
            self.score += 1
            reward = 10-self.frame_iteration/50
            if self.victim_count < 2:
                self._place_victim()
            else:
                game_over = True  
                reward=20-self.frame_iteration/50
        else:
            self.rescuers.pop()
        for fire in self.fires:
            if pygame.Rect(self.victim.x, self.victim.y, BLOCK_SIZE, BLOCK_SIZE).colliderect(fire) and self.victim_count==1:
                self._place_victim()
            elif pygame.Rect(self.victim.x, self.victim.y, BLOCK_SIZE, BLOCK_SIZE).colliderect(fire) and self.victim_count==2:
                game_over =True
                reward= 0
        
        self._update_ui()
        self.clock.tick(SPEED)
        return reward, game_over, self.score, self.frame_iteration

    def is_collision(self, pt=None):
        if pt is None:
            pt = self.hero
        if pt.x > self.w - BLOCK_SIZE*2 or pt.x < 20 or pt.y > self.h - BLOCK_SIZE*2 or pt.y < 20:
            return True
        if pt in self.rescuers[1:]:
            return True
        for fire in self.fires:
            if pygame.Rect(pt.x, pt.y, BLOCK_SIZE, BLOCK_SIZE).colliderect(fire):
                return True
        return False

    def _update_ui(self):
        self.display.fill(WHITE)
        for fire in self.fires:
            pygame.draw.rect(self.display, ORANGE, fire)
        for pt in self.rescuers:
            pygame.draw.rect(self.display, BLACK, pygame.Rect(pt.x, pt.y, BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(self.display, BLUE1, pygame.Rect(pt.x+4, pt.y+4, 12, 12))
        if self.victim:
            pygame.draw.rect(self.display, RED, pygame.Rect(self.victim.x, self.victim.y, BLOCK_SIZE, BLOCK_SIZE))
        for wall in self.walls:
            pygame.draw.rect(self.display, GREY, wall)
        # pygame.draw.rect(self.display, RED, self.starting_Position)
        text = font.render("Score: " + str(self.score), True, WHITE)
        self.display.blit(text, [0, 0])
        pygame.display.flip()

    def _move(self, action):
        clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
        idx = clock_wise.index(self.Direction)
        if np.array_equal(action, [1, 0, 0]):
            new_dir = clock_wise[idx]
        elif np.array_equal(action, [0, 1, 0]):
            next_idx = (idx + 1) % 4
            new_dir = clock_wise[next_idx]
        else:
            next_idx = (idx - 1) % 4
            new_dir = clock_wise[next_idx]
        self.Direction = new_dir
        x = self.hero.x
        y = self.hero.y
        if self.Direction == Direction.RIGHT:
            x += BLOCK_SIZE
        elif self.Direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif self.Direction == Direction.DOWN:
            y += BLOCK_SIZE
        elif self.Direction == Direction.UP:
            y -= BLOCK_SIZE
        self.hero = Position(x, y)
