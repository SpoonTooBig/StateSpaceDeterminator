import StateNode
import StateSpace as s

def main():
    # Your program logic goes here
    x = s.StateSpace(3)
    print(x)
    x.traverse(10)

if __name__ == "__main__":
    main()