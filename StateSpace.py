import os
import random
import StateNode as sn
from graphviz import Digraph
import itertools
"""
This file contains the StateSpace class, which represents a state space.
It uses the StateNode class to represent nodes in the state space,
and a few methods for traversal, visualization, and validation.
"""
class StateSpace:    
    ECHR = 97 
    def __init__(self, size, states):
        self.size = size
        self.eventHistory = ''
        self.stateHistory = ''
        self.states = states
        self.currentState = self.states[0] if self.states else None

    def random_traverse(self, iterations):
        self.currentState = self.states[0] if self.states else None
        self.eventHistory = ''
        self.stateHistory = ''
        for i in range(0, iterations):
            if self.currentState is None:
                break
            self.stateHistory += self.currentState.name
            event = random.choice(list(self.currentState.transfers))
            self.eventHistory += str(event)
            self.currentState = self.currentState.transfers[event]
        self.currentState = self.states[0] if self.states else None
        return self.eventHistory


    def visualize(self, filename='state_space', location='Graphs'):
        dot = Digraph(comment='State Space Diagram', format='png')
        dot.attr(rankdir='LR')  # Left to right layout
        dot.attr('node', shape='circle', style='filled', fillcolor='lightblue')
        
        for state in self.states:
            dot.node(state.name, state.name)
        
        for state in self.states:
            for event, target_state in state.transfers.items():
                dot.edge(state.name, target_state.name, label=event)
        
        dot.render(f"{location}/{filename}", cleanup=True)
        print(f"State space diagram saved as '{location}/{filename}.png'")

    def save_to_file(self, filename):
        import json
        # Create the directory if it doesn't exist
        os.makedirs('Saves', exist_ok=True) 
        data = []
        for state in self.states:
            transfers = {event: target.name for event, target in state.transfers.items()}
            data.append({
                'name': state.name,
                'transfers': transfers
            })
        with open(f"Saves/{filename}.json", 'w') as f:
            json.dump(data, f, indent=4)
    
    def string_traverse(self, event_sequence):
        stateHistory = ''
        self.currentState = self.states[0]
        for event in event_sequence:
            if event in self.currentState.transfers:
                stateHistory += self.currentState.name                
                self.currentState = self.currentState.transfers[event]

        return stateHistory
    
    def valid_language(self, event_sequence):
        self.currentState = self.states[0]
        for event in event_sequence:
            if event not in self.currentState.transfers:
                return False
            else:
                self.currentState = self.currentState.Transfer(event)
        return True

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
        if self.size == 0:
            return True
        
        # Check if the state spaces are structurally identical (graph isomorphism)
        # regardless of state names, but require state zero to match exactly.
        for perm in itertools.permutations(other.states):
            if perm[0] is not other.states[0]:
                continue
            mapping = dict(zip(self.states, perm))
            match = True
            for self_state, other_state in mapping.items():
                # Map self's targets to other's corresponding states
                self_transfers_mapped = {}
                for event, target in self_state.transfers.items():
                    self_transfers_mapped[event] = mapping[target]
                if self_transfers_mapped != other_state.transfers:
                    match = False
                    break
            if match:
                return True
        return False

    def similarity_score(self, other):
        """
        Compute a similarity score between 0 and 1 based on structural similarity.
        1 means identical, 0 means completely different.
        """
        if not isinstance(other, StateSpace):
            return 0.0
        if self.size != other.size:
            return 0.0
        if self.size == 0:
            return 1.0
        
        max_score = 0.0
        total_transitions = sum(len(state.transfers) for state in self.states)
        if total_transitions == 0:
            return 1.0 if self.states[0] is other.states[0] else 0.0
        
        for perm in itertools.permutations(other.states):
            if perm[0] is not other.states[0]:
                continue
            mapping = dict(zip(self.states, perm))
            matching_transitions = 0
            for self_state, other_state in mapping.items():
                # Map self's targets to other's corresponding states
                self_transfers_mapped = {}
                for event, target in self_state.transfers.items():
                    self_transfers_mapped[event] = mapping[target]
                # Count matching transitions
                for event, target in self_transfers_mapped.items():
                    if event in other_state.transfers and other_state.transfers[event] == target:
                        matching_transitions += 1
            score = matching_transitions / total_transitions
            if score > max_score:
                max_score = score
        return max_score
