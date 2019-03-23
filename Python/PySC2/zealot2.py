# https://itnext.io/build-a-zerg-bot-with-pysc2-2-0-295375d2f58e

from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app 
import random

class P_Agent(base_agent.BaseAgent):
    def __init__(self):
        super(P_Agent, self).__init__()
        self.attack_coordinates = None


    def get_units_by_type(self, obs, unit_type):
        return [unit for unit in obs.observation.feature_units if unit.unit_type == unit_type]
    
    def unit_type_is_selected(self, obs, unit_type):
       if (len(obs.observation.single_select) > 0 and obs.observation.single_select[0].unit_type == unit_type):
           return True
  
       if (len(obs.observation.multi_select) > 0 and obs.observation.multi_select[0].unit_type == unit_type):
           return True
 
       return False
    
    def step(self, obs):
        super(P_Agent, self).step(obs)

        if obs.first():
            player_y, player_x = (obs.observation.feature_minimap.player_relative == features.PlayerRelative.SELF).nonzero()

            xmean = player_x.mean()
            ymean = player_y.mean()

            if xmean <= 31 and ymean <= 31:
                self.attack_coordinates = (49, 49)
            else:
                self.attack_coordinates = (12, 16)

        gateway = self.get_units_by_type(obs, units.Protoss.Gateway)
        pylon = self.get_units_by_type(obs, units.Protoss.Pylon)
        zealots = self.get_units_by_type(obs, units.Protoss.Zealot)

        if len(zealots) > 4:
            if self.unit_type_is_selected(obs, units.Protoss.Zealot):
                if (actions.FUNCTIONS.Attack_minimap.id):
                    return actions.FUNCTIONS.Attack_minimap("now", self.attack_coordinates)

            if (actions.FUNCTIONS.select_army.id in obs.observation.available_actions):
                return actions.FUNCTIONS.select_army("select")

        if len(pylon) == 0:
            if self.unit_type_is_selected(obs, units.Protoss.Probe):
                if (actions.FUNCTIONS.Build_Pylon_screen.id in obs.observation.available_actions):
                    x = random.randint(0, 83)
                    y = random.randint(0, 83)

                    return actions.FUNCTIONS.Build_Pylon_screen("now", (x, y))
        
        if len(gateway) == 0:
            if self.unit_type_is_selected(obs, units.Protoss.Probe):
                if (actions.FUNCTIONS.Build_Gateway_screen.id in obs.observation.available_actions):
                    x = random.randint(0, 83)
                    y = random.randint(0, 83)

                    return actions.FUNCTIONS.Build_Gateway_screen("now", (x, y))

        if len(gateway) == 1:
            if self.unit_type_is_selected(obs, units.Protoss.Gateway):
                if (actions.FUNCTIONS.Train_Zealot_quick.id in obs.observation.available_actions):
                    return actions.FUNCTIONS.Train_Zealot_quick("now")
            else:
                return actions.FUNCTIONS.select_point("select_all_type", (gateway[0].x, gateway[0].y))

        probes = self.get_units_by_type(obs, units.Protoss.Probe)
        if len(probes) > 0:
            probe = random.choice(probes)
            return actions.FUNCTIONS.select_point("select_all_type", (probe.x, probe.y))

          
        return actions.FUNCTIONS.no_op()

    
def main(unused_arg):
    agent = P_Agent()
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
