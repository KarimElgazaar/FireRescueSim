import torch
import random
import numpy as np
from collections import deque
from game import FireRescueSimulation, Direction, Position
from model import Linear_QNet, QTrainer
from helper import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:
    def __init__(self):
        self.n_games = 0
        self.epsilon = 0
        self.gamma = 0.9
        self.memory = deque(maxlen=MAX_MEMORY)
        self.model = Linear_QNet(11, 256, 3)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def get_state(self, game):
        hero = game.rescuers[0]
        Position_l = Position(hero.x - 20, hero.y)
        Position_r = Position(hero.x + 20, hero.y)
        Position_u = Position(hero.x, hero.y - 20)
        Position_d = Position(hero.x, hero.y + 20)
        
        dir_l = game.Direction == Direction.LEFT
        dir_r = game.Direction == Direction.RIGHT
        dir_u = game.Direction == Direction.UP
        dir_d = game.Direction == Direction.DOWN

        state = [
            (dir_r and game.is_collision(Position_r)) or 
            (dir_l and game.is_collision(Position_l)) or 
            (dir_u and game.is_collision(Position_u)) or 
            (dir_d and game.is_collision(Position_d)),

            (dir_u and game.is_collision(Position_r)) or 
            (dir_d and game.is_collision(Position_l)) or 
            (dir_l and game.is_collision(Position_u)) or 
            (dir_r and game.is_collision(Position_d)),

            (dir_d and game.is_collision(Position_r)) or 
            (dir_u and game.is_collision(Position_l)) or 
            (dir_r and game.is_collision(Position_u)) or 
            (dir_l and game.is_collision(Position_d)),
            
            dir_l,
            dir_r,
            dir_u,
            dir_d,
            
            game.victim.x < game.hero.x,
            game.victim.x > game.hero.x,
            game.victim.y < game.hero.y,
            game.victim.y > game.hero.y
        ]

        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) 

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
        

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        self.epsilon = 80 - self.n_games
        final_move = [0, 0, 0]
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move

def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record_mean = 0
    agent = Agent()
    game = FireRescueSimulation()
    while True:
        state_old = agent.get_state(game)
        final_move = agent.get_action(state_old)
        reward, done, score, _ = game.play_step(final_move)
        state_new = agent.get_state(game)
        agent.train_short_memory(state_old, final_move, reward, state_new, done)
        agent.remember(state_old, final_move, reward, state_new, done)
        if done:
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()
            total_score += score
            mean_score = total_score / agent.n_games
            if mean_score > record_mean:
                record_mean = mean_score
                agent.model.save()
            print('Game', agent.n_games, 'Score', score, 'Mean Score:', mean_score, 'Record Mean:', record_mean)
            plot_scores.append(score)
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)

if __name__ == '__main__':
    train()
