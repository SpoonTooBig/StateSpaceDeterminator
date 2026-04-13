import random
import StateNode as sn

class StateSpace:    
    ECHR = 65 # Character code for 'A', useful for event naming logic
    def __init__(self, size):
        self.states = []
        self.eventHistory = ''
        self.stateHistory = ''
        self.currentState = None
        self.size = size

        allStates = list(range(0,size))

        for i in range(0, size):
            stateName = str(i)
            node = sn.StateNode(stateName)
            self.states.append(node)

        allEvents = list((chr(i) for i in range(ord(chr(self.ECHR)), ord(chr(self.ECHR + size)))))
        for i in range(0, size):
            randEvents = random.sample(allEvents, size)
            transfers = dict(zip(randEvents, self.states))
            self.states[i].transfers = transfers

        self.currentState = self.states[0]

    def traverse(self, iterations):
        for i in range(0, iterations):
            self.stateHistory += self.currentState.name
            event = chr(self.ECHR + random.randint(0,self.size-1))
            self.eventHistory += str(event)
            self.currentState = self.currentState.transfers[event]

        print(self.eventHistory)
        print(self.stateHistory)


    def __repr__(self):
        s = ''
        for state in self.states:
            s += repr(state)
        return s