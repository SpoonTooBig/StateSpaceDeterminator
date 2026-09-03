import StateSpace as ss
import StateNode as sn
import random

"""
This file is a factory for conveniently creating state spaces using a variety of methods.
"""
class StateSpaceFactory:
    @staticmethod
    def create_random(size):        
        ECHR = 97
        states = []
        currentState = None
        size = size

        allEvents = list((chr(i) for i in range(ord(chr(ECHR)), ord(chr(ECHR + size)))))

        for i in range(0, size):
            stateName = str(i)
            node = sn.StateNode(stateName)
            states.append(node)

        for state in states:
            # Build list of state transfers randomly for each node
            transferNum = random.randint(1, size-1)
            availableStates = [x for x in states if x.name != state.name]
            randStates = random.sample(availableStates, transferNum)
            randEvents = random.sample(allEvents, transferNum)
            transfers = dict(zip(randEvents, randStates))
            state.transfers = transfers

        return ss.StateSpace(size, states)


    @staticmethod
    def load_from_file(filename):
        import json
        with open(filename, 'r') as f:
            data = json.load(f)
        
        state_nodes = []
        # First, create nodes
        for item in data:
            node = sn.StateNode(item['name'])
            state_nodes.append(node)
        
        # Then, set transfers
        name_to_node = {node.name: node for node in state_nodes}
        for item, node in zip(data, state_nodes):
            for event, target_name in item['transfers'].items():
                node.AddTransfer(event, name_to_node[target_name])
        
        return ss.StateSpace(len(state_nodes), state_nodes)
    
    @staticmethod
    def from_histories(event_history, state_history):
        zero_state = sn.StateNode('0')
        nodes = {'0': zero_state}
        for i in range(1, len(event_history)):
            current_state_str = state_history[i]
            prev_state_str = state_history[i-1]
            event_to_reach_current = event_history[i-1]

            # Check if the state already exists, if not create it    
            if current_state_str not in nodes:
                nodes[current_state_str] = sn.StateNode(current_state_str)

            nodes[prev_state_str].AddTransfer(event_to_reach_current, nodes[current_state_str])    
        
        return ss.StateSpace(len(nodes), list(nodes.values()))


