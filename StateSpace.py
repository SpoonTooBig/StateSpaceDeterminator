import random
import StateNode as sn

class StateSpace:    
    def __init__(self, size):
        self.states = []
        self.eventHistory = ''
        self.stateHistory = ''
        self.currentState = ''

        allEvents = list((chr(i) for i in range(ord(chr(65)), ord(chr(65 + size)))))
        allStates = list(range(0,size))

        for i in range(0, size):
            stateName = str(i)

            randstates = random.sample(allStates, size)
            transfers = dict(zip(allEvents, randstates))
            
            node = sn.StateNode(stateName, transfers)
            self.states.append(node)

        self.currentState = self.states[0]



    def __repr__(self):
        s = ''
        for state in self.states:
            s += state.__repr__()
        return s

def main():
    # Your program logic goes here
    x = StateSpace(3)
    print(x)

if __name__ == "__main__":
    main()