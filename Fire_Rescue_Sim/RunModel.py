import torch
import numpy as np
from game import FireRescueSimulation, Direction, Position
from model import Linear_QNet

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:

    def __init__(self, file_name):
        self.model = Linear_QNet(11, 256, 3)
        self.model.load_state_dict(torch.load(file_name))
        self.model.eval()


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
            # Danger straight
            (dir_r and game.is_collision(Position_r)) or 
            (dir_l and game.is_collision(Position_l)) or 
            (dir_u and game.is_collision(Position_u)) or 
            (dir_d and game.is_collision(Position_d)),

            # Danger right
            (dir_u and game.is_collision(Position_r)) or 
            (dir_d and game.is_collision(Position_l)) or 
            (dir_l and game.is_collision(Position_u)) or 
            (dir_r and game.is_collision(Position_d)),

            # Danger left
            (dir_d and game.is_collision(Position_r)) or 
            (dir_u and game.is_collision(Position_l)) or 
            (dir_r and game.is_collision(Position_u)) or 
            (dir_l and game.is_collision(Position_d)),
            
            # Move Direction
            dir_l,
            dir_r,
            dir_u,
            dir_d,
            
            # victim location 
            game.victim.x < game.hero.x,  # victim left
            game.victim.x > game.hero.x,  # victim right
            game.victim.y < game.hero.y,  # victim up
            game.victim.y > game.hero.y  # victim down
            ]

        return np.array(state, dtype=int)

    def get_action(self, state):
        state0 = torch.tensor(state, dtype=torch.float)
        prediction = self.model(state0)
        move = torch.argmax(prediction).item()
        final_move = [0,0,0]
        final_move[move] = 1
        return final_move


def run():
    agent = Agent('model/model.pth')  
    game = FireRescueSimulation()
    rewards = []
    ngames=0
    while True:
        state_old = agent.get_state(game)
        final_move = agent.get_action(state_old)
        reward, done, _, _ = game.play_step(final_move)
        if done:
            rewards.append(reward)
            game.reset()
            ngames += 1
            if reward > 0:
                print(f'Simulation {ngames}: Rescue successful!')
            else:
                print(f'Simulation {ngames}: Rescue failed.')


if __name__ == '__main__':
    run()
