# https://chatbotslife.com/building-a-basic-pysc2-agent-b109cde1477c
'''
TO DO:
Add vespene gas prior to core + mine the gas
Trian stalkers
Attack
'''
from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features

build_pylon = actions.FUNCTIONS.Build_Pylon_screen.id
build_gateway = actions.FUNCTIONS.Build_Gateway_screen.id
build_cybernetics_core = actions.FUNCTIONS.Build_CyberneticsCore_screen.id
noop = actions.FUNCTIONS.no_op.id
select_point = actions.FUNCTIONS.select_point.id


player_rel = features.SCREEN_FEATURES.player_relative.index
unit_type = features.SCREEN_FEATURES.unit_type.index

nexus = 59
probe = 84
stalker = 74

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
    cybernetics_core_built = False

    def step(self, obs):
        super(Simple, self).step(obs)

        if spawn_loc is False:
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
            if build_gateway in obs.observation["available_actions"]:
                ut = obs.observation["screen"][unit_type]
                uy, ux = (unit_type == nexus).nonzero()
                target = self.rel_base(int(ux.mean()), 20, int(uy.mean()), 0)
                self.gateway_built = True
                return actions.FunctionCall(build_gateway, [not_queued, target])
        elif not self.cybernetics_core_built:
            if build_cybernetics_core in obs.observation["available_actions"]:
                ut = obs.observation["screen"][unit_type]
                uy, ux = (unit_type == nexus).nonzero()
                target = self.rel_base(int(ux.mean()), 0, int(uy.mean()), 30)
                self.built_cybernetics_core = True
                return acations.FunctionCall(build_cybernetics_core, [not_queued, target])
        

        return actions.FunctionCall(noop, [])
    
    def rel_base(self, x, dx, y, dy) {
        if not self.spawn_loc:
            return [x - dx, y - dy]
        return [x + dx, y + dy]
    }


        
