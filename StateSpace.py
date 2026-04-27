import random
import StateNode as sn
from graphviz import Digraph
import itertools

class StateSpace:    
    ECHR = 97 # Character code for 'A', useful for event naming logic
    def __init__(self, size, states):
        self.size = size
        self.eventHistory = ''
        self.stateHistory = ''
        self.states = states
        self.currentState = self.states[0]

    def traverse(self, iterations):
        for i in range(0, iterations):
            self.stateHistory += self.currentState.name
            event = random.choice(list(self.currentState.transfers))
            self.eventHistory += str(event)
            self.currentState = self.currentState.transfers[event]


    def visualize(self, filename='state_space'):
        dot = Digraph(comment='State Space Diagram', format='png')
        dot.attr(rankdir='LR')  # Left to right layout
        dot.attr('node', shape='circle', style='filled', fillcolor='lightblue')
        
        for state in self.states:
            dot.node(state.name, state.name)
        
        for state in self.states:
            for event, target_state in state.transfers.items():
                dot.edge(state.name, target_state.name, label=event)
        
        dot.render(filename, cleanup=True)
        print(f"State space diagram saved as '{filename}.png'")

    def save_to_file(self, filename):
        import json
        data = []
        for state in self.states:
            transfers = {event: target.name for event, target in state.transfers.items()}
            data.append({
                'name': state.name,
                'transfers': transfers
            })
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def __repr__(self):
        s = ''
        for state in self.states:
            s += repr(state)
        return s
    
    def __eq__(self, other):
        if not isinstance(other, StateSpace):
            return NotImplemented
        if self.size != other.size:
            return False
        
        # Check if the state spaces are structurally identical (graph isomorphism)
        # regardless of state names
        for perm in itertools.permutations(other.states):
            mapping = dict(zip(self.states, perm))
            match = True
            for self_state, other_state in mapping.items():
                # Map self's targets to other's corresponding states
                self_transfers_mapped = {event: mapping[target] for event, target in self_state.transfers.items()}
                if self_transfers_mapped != other_state.transfers:
                    match = False
                    break
            if match:
                return True
        return False