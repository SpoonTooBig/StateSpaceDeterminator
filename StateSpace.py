import random
import StateNode as sn
from graphviz import Digraph

class StateSpace:    
    ECHR = 97 # Character code for 'A', useful for event naming logic
    def __init__(self, size):
        self.states = []
        self.eventHistory = ''
        self.stateHistory = ''
        self.currentState = None
        self.size = size

        allEvents = list((chr(i) for i in range(ord(chr(self.ECHR)), ord(chr(self.ECHR + size)))))

        for i in range(0, size):
            stateName = str(i)
            node = sn.StateNode(stateName)
            self.states.append(node)

        for state in self.states:
            # Build list of state transfers randomly for each node
            transferNum = random.randint(1, size-1)
            availableStates = [x for x in self.states if x.name != state.name]
            randStates = random.sample(availableStates, transferNum)
            randEvents = random.sample(allEvents, transferNum)
            transfers = dict(zip(randEvents, randStates))
            state.transfers = transfers

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

    def __repr__(self):
        s = ''
        for state in self.states:
            s += repr(state)
        return s