class StateNode:    
    def __init__(self, name, transfers):
        self.name = name
        self.transfers = transfers
    def __repr__(self):
        s = "State: " + self.name
        s += "\nTransfers:"
        for key,value in self.transfers.items():
            s += "\n\t" + key + "->" + str(value)
        s += '\n'
        return s

    def Transfer(self, event):
        return self.transfers(event)