'''
The original ideas came from https://chatbotslife.com/building-a-smart-pysc2-agent-cdc269cb095d,
but that is an outdated version that is very different and for a different race, 
so this code is heavily adapted from that.
Also https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow
'''
import random
import math
import numpy as np
import pandas as pd
from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app 

act = ['nothing', 'build_pylon', 'build_gateway', 'select_army', 'attack', 'train_zealot', 'select_gateway', 'select_probe']


KILL_UNIT_REWARD = 0.3
KILL_BUILD_REWARD = 0.4
#ARMY_REWARD = 0.1
#The qtable is straight from Morvan but will be improved upon
class QLearningTable:
    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actions = actions  # a list
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation):
        self.check_state_exist(observation)
        # action selection
        if np.random.uniform() < self.epsilon:
            # choose best action
            state_action = self.q_table.loc[observation, :]
            # some actions may have the same value, randomly choose on in these actions
            action = np.random.choice(state_action[state_action == np.max(state_action)].index)
        else:
            # choose random action
            action = np.random.choice(self.actions)
        return action

    def learn(self, s, a, r, s_):
        self.check_state_exist(s_)
        self.check_state_exist(s)
        
        q_predict = self.q_table.ix[s, a]
        q_target = r + self.gamma * self.q_table.ix[s_, :].max()
        
        # update
        self.q_table.ix[s, a] += self.lr * (q_target - q_predict)

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            # append new state to q table
            self.q_table = self.q_table.append(
                pd.Series(
                    [0]*len(self.actions),
                    index=self.q_table.columns,
                    name=state,
                )
            )

class Q_Agent(base_agent.BaseAgent):
    def __init__(self):
        super(Q_Agent, self).__init__()
        self.prev_kill_unit = 0
        self.attack_coordinates = None
        self.prev_kill_built = 0
        self.prev_act = None
        self.prev_state = None
        #self.prev_army = None
        self.qlearn = QLearningTable(actions=list(range(len(act))))

    def get_units_by_type(self, obs, unit_type):
        return [unit for unit in obs.observation.feature_units if unit.unit_type == unit_type]
    
    def step(self, obs):
        super(Q_Agent, self).step(obs)

        if obs.first():
            player_y, player_x = (obs.observation.feature_minimap.player_relative == features.PlayerRelative.SELF).nonzero()

            xmean = player_x.mean()
            ymean = player_y.mean()

            if xmean <= 31 and ymean <= 31:
                self.attack_coordinates = (49, 49)
            else:
                self.attack_coordinates = (12, 16)


        pylon_count = len(self.get_units_by_type(obs, units.Protoss.Pylon))
        gateway_count = len(self.get_units_by_type(obs, units.Protoss.Gateway))
        zealot_count = len(self.get_units_by_type(obs, units.Protoss.Zealot))
        minerals = obs.observation['player'][1]
        supply_limit = obs.observation['player'][4]
        army_supply = obs.observation['player'][5]
        
        state = [
            pylon_count,
            gateway_count,
            zealot_count,
            minerals,
            supply_limit,
            army_supply
            ]
        ku = obs.observation['score_cumulative'][5]
        kb = obs.observation['score_cumulative'][6]
        #arm = obs.observation['player'][8]
        if self.prev_act is not None:
            reward = 0
            if ku > self.prev_kill_unit:
                #for i in range(int(ku - self.prev_kill_unit)):
                reward += KILL_UNIT_REWARD
            if kb > self.prev_kill_built:
                reward += KILL_BUILD_REWARD
            #if arm > self.prev_army:
            #    reward += ARMY_REWARD
             
            self.qlearn.learn(str(self.prev_state), self.prev_act, reward, str(state))
        
        
        rl_action = self.qlearn.choose_action(str(state))
        q_action = act[rl_action]
        self.prev_kill_unit = ku
        self.prev_kill_built = kb
        self.prev_act = rl_action
        self.prev_state = state
        print(q_action)
        if q_action == 'nothing':
            return actions.FUNCTIONS.no_op()
        elif q_action == 'attack':
            if (actions.FUNCTIONS.Attack_minimap.id in obs.observation.available_actions):
                return actions.FUNCTIONS.Attack_minimap("now", self.attack_coordinates)
            else:
                self.prev_act = 0
                return actions.FUNCTIONS.no_op()
        elif q_action == 'select_army':
            if (actions.FUNCTIONS.select_army.id in obs.observation.available_actions):
                return actions.FUNCTIONS.select_army("select")
            else:
                self.prev_act = 0
                return actions.FUNCTIONS.no_op()
        elif q_action == 'build_pylon':
            if (actions.FUNCTIONS.Build_Pylon_screen.id in obs.observation.available_actions):
                return actions.FUNCTIONS.Build_Pylon_screen("now", (random.randint(0, 83), random.randint(0, 83)))
            else:
                self.prev_act = 0
                return actions.FUNCTIONS.no_op()
        elif q_action == 'build_gateway':
            if (actions.FUNCTIONS.Build_Gateway_screen.id in obs.observation.available_actions):
                return actions.FUNCTIONS.Build_Gateway_screen("now", (random.randint(0, 83), random.randint(0, 83)))
            else:
                self.prev_act = 0
                return actions.FUNCTIONS.no_op()
        elif q_action == 'select_gateway':
            gateways = self.get_units_by_type(obs, units.Protoss.Gateway)
            if (actions.FUNCTIONS.select_point.id in obs.observation.available_actions) and len(gateways) > 0:
                gateway = random.choice(gateways)
                return actions.FUNCTIONS.select_point("select_all_type", (gateway.x, gateway.y))
            else:
                self.prev_act = 0
                return actions.FUNCTIONS.no_op()
        elif q_action == 'select_probe':
            probes = self.get_units_by_type(obs, units.Protoss.Probe)
            if (actions.FUNCTIONS.select_point.id in obs.observation.available_actions) and len(probes) > 0:
                probe = random.choice(probes)
                if probe.x > 0 and probe.y > 0 and probe.x < 84 and probe.y < 84:
                    return actions.FUNCTIONS.select_point("select_all_type", (probe.x, probe.y))
                else:
                    self.prev_act = 0
                    return actions.FUNCTIONS.no_op()                    
            else:
                self.prev_act = 0
                return actions.FUNCTIONS.no_op()
        elif q_action == 'train_zealot':
            if (actions.FUNCTIONS.Train_Zealot_quick.id in obs.observation.available_actions):
                return actions.FUNCTIONS.Train_Zealot_quick("now")
            else:
                self.prev_act = 0
                return actions.FUNCTIONS.no_op()

def main(unused_arg):
    agent = Q_Agent()
    try:
        while True:
            with sc2_env.SC2Env(
                map_name="AbyssalReef",
                players=[sc2_env.Agent(sc2_env.Race.protoss), sc2_env.Bot(sc2_env.Race.random, sc2_env.Difficulty.very_easy)],
                agent_interface_format=features.AgentInterfaceFormat(feature_dimensions=features.Dimensions(screen=84, minimap=64), use_feature_units=True),
                step_mul=8, #300 apm?
                game_steps_per_episode=0,
                visualize=True) as env:
                
                agent.setup(env.observation_spec(), env.action_spec())
        
                timesteps = env.reset()
                agent.reset()
        
                while True:
                    step_actions = [agent.step(timesteps[0])]
                    if timesteps[0].last():
                        break
                    timesteps = env.step(step_actions)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app.run(main)

