import StateNode
import StateSpace as s
import StateSpaceFactory as ssf

def main():
    ss = ssf.StateSpaceFactory.create_random(3)
    # print(ss)
    # ss.traverse(100)
    # print(ss.eventHistory)
    # print(ss.stateHistory)
    ss.visualize('state_space_generated')

    ss.save_to_file('state_space.json')

    loaded_ss1 = ssf.StateSpaceFactory.load_from_file('state_space.json')
    loaded_ss1.visualize('state_space_loaded')

    # loaded_ss2 = ssf.StateSpaceFactory.load_from_file('state_space.json')

    print(loaded_ss1 == ss)  # Should print True
if __name__ == "__main__":
    main()