import StateNode
import StateSpace as s

def main():
    ss = s.StateSpace(5)
    print(ss)
    ss.traverse(100)
    print(ss.eventHistory)
    print(ss.stateHistory)
    ss.visualize()

if __name__ == "__main__":
    main()