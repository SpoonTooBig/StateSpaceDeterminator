import StateNode
import StateSpace as s
import StateSpaceFactory as ssf

def main():

    ss1 = ssf.StateSpaceFactory.load_from_file('Saves/ss1.json')
    ss1_2 = ssf.StateSpaceFactory.load_from_file('Saves/ss1.json')
    ss2 = ssf.StateSpaceFactory.load_from_file('Saves/ss2.json')

    ss1.traverse(100)

    ss1_2_states = ss1_2.string_traverse(ss1.eventHistory)
    ss2_states = ss2.string_traverse(ss1.eventHistory)

    print(f"Event String: {ss1.eventHistory}")

    print("SS1 State History: ", ss1.stateHistory)
    print("SS1_2 State History: ", ss1_2_states)
    print("SS2 State History: ", ss2_states)

    print(ss1_2_states == ss1.stateHistory)
    print(ss2_states == ss1.stateHistory)

    ss1_from_history = ssf.StateSpaceFactory.from_histories(ss1.eventHistory, ss1.stateHistory)
    print(ss1_from_history == ss1)

if __name__ == "__main__":
    main()