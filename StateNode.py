class StateNode:    
    def __init__(self, name):
        self.name = name
        self.transfers = {}

    def __repr__(self):
        s = "State: " + self.name
        s += "\nTransfers:"
        for key,value in self.transfers.items():
            s += "\n\t" + key + "->" + value.name
        s += '\n'
        return s

    def addTransfer(self, event, node):
        self.transfers[event] = node

    def Transfer(self, event):
        return self.transfers(event)