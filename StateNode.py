"""
Simple class to represent a state node in a state space.
"""
class StateNode:    
    def __init__(self, name, transfers=None):
        self.name = name
        self.transfers = transfers.copy() if transfers else {}

    def __repr__(self):
        s = "State: " + self.name
        s += "\nTransfers:"
        for key,value in self.transfers.items():
            s += "\n\t" + key + "->" + value.name
        s += '\n'
        return s
        
    def AddTransfer(self, event, node):
        self.transfers[event] = node
        return

    def Transfer(self, event):
        return self.transfers[event]