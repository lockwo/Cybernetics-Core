# This is from a tutorial, see newer version for updated information
# Whoops, outdated version, this code might be useless

from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features

build_pylon = actions.FUNCTIONS.Build_Pylon_screen.id
build_gateway = actions.FUNCTIONS.Build_Gateway_screen.id
build_zealot = actions.FUNCTIONS.Train_Zealot_quick.id
rally = actions.FUNCTIONS.Rally_Units_minimap.id
select_army = actions.FUNCTIONS.select_army.id
attack_minimap = actions.FUNCTIONS.Attack_minimap.id


noop = actions.FUNCTIONS.no_op.id
select_point = actions.FUNCTIONS.select_point.id

player_rel = features.SCREEN_FEATURES.player_relative.index
unit_type = features.SCREEN_FEATURES.unit_type.index

nexus = 59
probe = 84
zealot = 73
gateway = 62

supply_used = 3
supply_max = 4
player_self = 1
not_queued = [0]
queued = [1]


class Simple(base_agent.BaseAgent):
    # Only Works for 2 Player Mpas?
    spawn_loc = False

    # Build Order
    pylon_built = False
    probe_selected = False
    gateway_built = False
    zealot_built = False
    gateway_selected = False
    gateway_rallied = False
    army_selected = False
    army_rallied = False
    def step(self, obs):
        super(Simple, self).step(obs)

        if self.spawn_loc is False:
            player_y, player_x = (obs.observation["minimap"][player_rel] == player_self).nonzero()
            self.spawn_loc = player_y.mean() <= 31
        
        if not self.pylon_built:
            if not self.probe_selected:
                ut = obs.observation["screen"][unit_type]
                uy, ux = (ut == probe).nonzero()
                target = [ux[0], uy[1]]
                self.probe_selected = True
                return actions.FunctionCall(select_point, [not_queued, target])
            elif build_pylon in obs.observation["available_actions"]:
                ut = obs.observation["screen"][unit_type]
                uy, ux = (unit_type == nexus).nonzero()
                target = self.rel_base(int(ux.mean()), 0, int(uy.mean()), 20)
                self.pylon_built = True
                return actions.FunctionCall(build_pylon, [not_queued, target])
        elif not self.gateway_built:
            if not self.probe_selected:
                ut = obs.observation["screen"][unit_type]
                uy, ux = (ut == probe).nonzero()
                target = [ux[0], uy[1]]
                self.probe_selected = True
                return actions.FunctionCall(select_point, [not_queued, target])
            elif build_gateway in obs.observation["available_actions"]:
                ut = obs.observation["screen"][unit_type]
                uy, ux = (unit_type == nexus).nonzero()
                target = self.rel_base(int(ux.mean()), 20, int(uy.mean()), 0)
                self.gateway_built = True
                return actions.FunctionCall(build_gateway, [not_queued, target])
        elif not self.gateway_rallied:
            if not self.gateway_selected:
                ut = obs.observation["screen"][unit_type]
                uy, ux = (unit_type == gateway).nonzero()
                if uy.any():
                    target = [int(ux.mean()), int(uy.mean())]
                    self.gateway_selected = True
                    return actions.FunctionCall(select_point, [not_queued, target])
            else: 
                self.gateway_rallied = True
                if self.spawn_loc == True:
                    return actions.FunctionCall(rally, [not_queued, [29,21]])
                return actions.FunctionCall(rally, [not_queued, [26,46]])
        elif obs.observation["player"][supply_used] < obs.observation["player"][supply_max] and build_zealot in obs.observation["available_actions"]:
            return actions.FunctionCall(build_zealot, [queued])
        elif not self.army_rallied:
            if not self.army_selected:
                if select_army in obs.observation["available_actions"]:
                    self.army_selected = True
                    self.gateway_selected = False
                    return actions.FunctionCall(select_army, [not_queued])
                elif attack_minimap in obs.observation["available_actions"]:
                    self.army_rallied = True
                    self.army_selected = False
                    if self.spawn_loc:
                        return actions.FunctionCall(attack_minimap, [not_queued, [39, 45]])
                    return actions.FunctionCall(attack_minimap, [not_queued, [21,24]])
        return actions.FunctionCall(noop, [])
    
    def rel_base(self, x, dx, y, dy): 
        if not self.spawn_loc:
            return [x - dx, y - dy]
        return [x + dx, y + dy]
    


        
