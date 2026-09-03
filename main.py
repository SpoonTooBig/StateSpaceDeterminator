import StateNode
import StateSpace as s
import StateSpaceFactory as ssf
import IterativeDetermination as id

def main():
    """Interact with other files to randomly generate a state space and then reproduce it without observing its states."""
    print('loading state space')
    three_state_ss = ssf.StateSpaceFactory.create_random(3)
    three_state_ss.visualize(filename='three_state_ss')
    print('state space loaded')
    print('making greedy state space')
    deterministic_ss = id.make_greedy_space_deterministic(three_state_ss, 8)
    deterministic_ss.visualize(filename='deterministic_ss_3states')
    print('greedy state space genereated')
    print('getting event pairs')
    event_pairs = id.analyze_forks_single_event(deterministic_ss)
    print('event pairs generated')
    print('generating state spaces from event pairs')
    spaces = id.generate_state_spaces_from_event_pairs(event_pairs, 3, id.get_all_event_strings_from_tree(deterministic_ss))
    print('state spaces generated')
    print('Number of spaces generated: ', len(spaces))
    print('validating state spaces')
    validations = id.validate_spaces(spaces, three_state_ss)
    print(f"Number of validated spaces found: {validations}")
    

    # print('loading state space')
    # four_state_ss = ssf.StateSpaceFactory.load_from_file('Saves/four_state_ss.json')
    # print('state space loaded')
    # print('making greedy state space')
    # deterministic_ss = id.make_greedy_space_deterministic(four_state_ss, 7)
    # deterministic_ss.visualize(filename='deterministic_ss_4states')
    # print('greedy state space genereated')
    # print('getting event pairs')
    # event_pairs = id.analyze_forks_single_event(deterministic_ss)
    # print('event pairs generated')
    # print('generating state spaces from event pairs')
    # spaces = id.generate_state_spaces_from_event_pairs(event_pairs, 4, id.get_all_event_strings_from_tree(deterministic_ss))
    # print('state spaces generated')
    # print('Number of spaces generated: ', len(spaces))
    # print('validating state spaces')
    # validations = id.validate_spaces(spaces, four_state_ss)
    # print(f"Number of validated spaces found: {validations}")
if __name__ == "__main__":
    main()