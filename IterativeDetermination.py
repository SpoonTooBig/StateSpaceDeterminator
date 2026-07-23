import StateNode as sn
import StateSpace as ss
import StateSpaceFactory as ssf
from enum import Enum
import argparse
import itertools


class RefinementStrategy(Enum):
    GREEDY = 'greedy'

def analyze_forks_single_event(state_space):
    """
    Traverse the provided safe space and collect every pair of events
    that can occur sequentially.

    Returns a list of tuples like [("a", "a"), ("a", "b"), ("b", "c")].
    """
    sequential_pairs = []
    seen_states = set()

    def dfs(state):
        if state.name in seen_states:
            return
        seen_states.add(state.name)

        for first_event, next_state in state.transfers.items():
            for second_event in next_state.transfers.keys():
                pair = (first_event, second_event)
                if pair not in sequential_pairs:
                    sequential_pairs.append(pair)
            dfs(next_state)

    if state_space and state_space.states:
        dfs(state_space.states[0])

    return sequential_pairs


def analyze_forks_multi_event(state_space):
    """
    Analyze forks in a state space using depth-first search.
    A fork is a state with more than one outgoing transition (multiple events).
    Returns a list of dicts with: event_string (path to fork), depth (# of forks before this), visited_states, history (parent forks)
    """
    forks = []
    visited = set()
    
    def dfs(state, event_string, fork_depth, visited_states, history):
        """Recursively explore state space, tracking event path, fork depth, and parent fork history."""
        if state.name in visited:
            return
        visited.add(state.name)
        visited_states.append(state.name)
        
        # Check if this state is a fork
        if len(state.transfers) > 1:
            forks.append({
                'event_string': event_string,
                'depth': fork_depth,
                'visited_states': visited_states.copy(),
                'history': history.copy()
            })
            # Reset visited_states and increment fork depth for recursion
            new_fork_depth = fork_depth + 1
            new_event_string = ''
            new_visited_states = []
            new_history = history + [event_string]  # Add current fork to history
        else:
            new_fork_depth = fork_depth
            new_event_string = event_string
            new_visited_states = visited_states.copy()
            new_history = history
            
        # Continue DFS to all successor states
        for event in sorted(state.transfers.keys()):
            target_state = state.transfers[event]
            # Each branch gets its own copy of visited_states and history
            branch_visited_states = new_visited_states.copy()
            dfs(target_state, new_event_string + event, new_fork_depth, branch_visited_states, new_history)
    
    dfs(state_space.states[0], '', 0, [], [])
    return forks

def test_to_depth(reduced_event_strings, test_space, depth):
    """
    Test if the `test_space` can reproduce the same event sequences as `source_space`
    up to a given depth. Returns True if they match, False otherwise.
    """

    for string in reduced_event_strings:
        if not test_space.valid_language(string):  # Ensure the test space can traverse this string
            return False
    return True

def print_forks_analysis(forks):
    """Print fork analysis data in a human-readable format, sorted by depth."""
    if not forks:
        print("No forks found in state space.")
        return
    
    # Group forks by depth
    forks_by_depth = {}
    for fork in forks:
        depth = fork['depth']
        if depth not in forks_by_depth:
            forks_by_depth[depth] = []
        forks_by_depth[depth].append(fork)
    
    print("Fork Analysis Report (Sorted by Depth)")
    print("=" * 50)
    
    fork_num = 1
    for depth in sorted(forks_by_depth.keys()):
        forks_at_depth = forks_by_depth[depth]
        print(f"\nDEPTH {depth} - {len(forks_at_depth)} fork(s)")
        print("-" * 50)
        
        for fork in forks_at_depth:
            event_string = fork['event_string'] if fork['event_string'] else '(root)'
            visited = ' → '.join(fork['visited_states'])
            history = ' → '.join(fork['history']) if fork['history'] else '(none)'
            print(f"Fork #{fork_num}")
            print(f"  Event Path: {event_string}")
            print(f"  Visited States: {visited}")
            print(f"  Parent Fork History: {history}")
            print()
            fork_num += 1
    
    # Summary
    total_forks = len(forks)
    max_depth = max(forks_by_depth.keys())
    distribution = [len(forks_by_depth[d]) for d in sorted(forks_by_depth.keys())]
    
    print("Summary:")
    print("────────")
    print(f"Total forks: {total_forks}")
    print(f"Distribution by depth: {distribution}")
    print(f"Max depth: {max_depth}")


def get_all_event_strings_from_tree(det_state_space):
    """
    Collect every completed root-to-leaf event string in the deterministic
    state-space tree.

    Returns a list of full-length strings such as ['ab', 'ac', 'b'].
    """
    if not det_state_space or not det_state_space.states:
        return []

    event_strings = []
    visited_states = set()

    def dfs(state, prefix):
        if state.name in visited_states:
            return
        visited_states.add(state.name)

        if not state.transfers:
            if prefix:
                event_strings.append(prefix)
            return

        for event in sorted(state.transfers.keys()):
            dfs(state.transfers[event], prefix + event)

    dfs(det_state_space.states[0], '')
    return event_strings


def generate_state_spaces_from_event_pairs(event_pairs, num_states, source_space_event_strings):
    """
    Generate every possible deterministic StateSpace with `num_states` states
    that can realize the provided sequential event pairs.

    Each pair is interpreted as two events that can occur in sequence, e.g.
    ("a", "b") means there is some state S where transition "a" leads to
    state T and state T has a transition "b".

    Unlike the previous implementation, each state may now have any number of
    outgoing transitions between one and the size of the event alphabet, and
    the event subset for each state can be any combination of the available
    events.

    Returns a list of `ss.StateSpace` instances.
    """
    if num_states <= 0:
        return []

    alphabet = sorted({event for pair in event_pairs for event in pair})
    if not alphabet:
        return []

    state_spaces = []
    state_indices = list(range(num_states))

    def build_state_patterns(state_idx):
        patterns = []
        for transition_count in range(1, len(alphabet) + 1):
            for selected_events in itertools.combinations(alphabet, transition_count):
                for targets in itertools.product(state_indices, repeat=transition_count):
                    if any(target_idx == state_idx for target_idx in targets):
                        continue
                    transition_map = {
                        event: target_idx for event, target_idx in zip(selected_events, targets)
                    }
                    patterns.append(transition_map)
        return patterns

    state_patterns = [build_state_patterns(state_idx) for state_idx in state_indices]

    def build_state_space_from_transition_maps(transition_maps):
        needed_states = max(1, len(transition_maps))
        for transition_map in transition_maps:
            for target_idx in transition_map.values():
                needed_states = max(needed_states, target_idx + 1)

        state_nodes = [sn.StateNode(str(i)) for i in range(needed_states)]
        for node_idx, transition_map in enumerate(transition_maps):
            for event, target_idx in transition_map.items():
                state_nodes[node_idx].AddTransfer(event, state_nodes[target_idx])
        return ss.StateSpace(len(state_nodes), state_nodes)

    depth_event_strings = {}

    def recurse(state_idx, transition_maps, states, depth):
        if state_idx == num_states:
            state_nodes = build_state_space_from_transition_maps(transition_maps).states
            valid = True
            for first_event, second_event in event_pairs:
                pair_found = False
                for state in state_nodes:
                    if first_event not in state.transfers:
                        continue
                    intermediate = state.transfers[first_event]
                    if second_event in intermediate.transfers:
                        pair_found = True
                        break
                if not pair_found:
                    valid = False
                    break

            if valid:
                state_spaces.append(build_state_space_from_transition_maps(transition_maps))
            return

        unique_event_strings = {}
        if depth not in depth_event_strings.keys():
            for string in source_space_event_strings:
                unique_event_strings[string[:depth]] = True
            depth_event_strings[depth] = unique_event_strings.keys()

        for transition_map in state_patterns[state_idx]:
            candidate_transition_maps = transition_maps + [transition_map]
            partial_space = build_state_space_from_transition_maps(candidate_transition_maps)

            if test_to_depth(depth_event_strings[depth], partial_space, depth):
                recurse(state_idx + 1, candidate_transition_maps, states, depth + 1)

    recurse(0, [], [], 0)
    return state_spaces


def make_greedy_space_deterministic(source_space, max_depth=3):
    """
    Build a deterministic 'greedy' safe space from `source_space`.

    Starting at the initial node of `source_space`, attempt events 'a', 'b',
    ... up to the number of states in `source_space`. For each event that
    exists on the current source node, add a corresponding transition and
    new node to the constructed safe space. Recurse into the discovered
    target in `source_space` and continue exploration up to `max_depth`.

    This produces a deterministic tree-like safe space (no merging of
    target nodes) where each discovered valid transition from the source
    is included.

    Parameters:
    - source_space: an instance of `ss.StateSpace` to inspect (read-only).
    - max_depth: maximum depth to explore (non-negative integer).

    Returns a new `ss.StateSpace` instance representing the greedy safe space.
    """
    # Determine alphabet size: use number of states in source_space (clamped to 26)
    max_events = min(max(0, source_space.size), 26)
    events = [chr(ord('a') + i) for i in range(max_events)]

    # Create zero/start node for the new safe space
    name_counter = 0
    zero = sn.StateNode(str(name_counter))
    name_counter += 1
    states = [zero]

    def dfs(src_node, safe_prev, depth):
        nonlocal name_counter
        if depth <= 0:
            return
        for event in events:
            # If the source node has this event, follow it and add to safe space
            if event in src_node.transfers:
                target_src = src_node.transfers[event]
                # Create a fresh node in the safe space for this discovery
                new_node = sn.StateNode(str(name_counter))
                name_counter += 1
                states.append(new_node)
                safe_prev.AddTransfer(event, new_node)
                # Recurse on the source-space target with decreased depth
                dfs(target_src, new_node, depth - 1)

    dfs(source_space.states[0], zero, max_depth)
    return ss.StateSpace(len(states), states)

def language_compare(source_space, state_space):
    valid = True
    for i in range(0, 10):
        source_path = source_space.random_traverse(100)
        state_path = state_space.random_traverse(100)
        # if not state_space.valid_language(source_path):
        #     return False
        if source_space.valid_language(state_path):
            if state_space.valid_language(source_path):
                return True
    return False

def main():
    parser = argparse.ArgumentParser(description='Iterative state-space reconstruction demo')
    parser.add_argument('--max-iterations', type=int, default=20, help='Maximum number of refinement iterations (default: 20)')
    parser.add_argument('--strategy', type=str, default='greedy', choices=['greedy'], help='Refinement strategy to use (default: greedy)')
    parser.add_argument('--from-save', type=str, default='', help='Load a saved safe space from a file. No value means randomized source space.')
    args = parser.parse_args()
    
    strategy = RefinementStrategy.GREEDY if args.strategy == 'greedy' else RefinementStrategy.GREEDY
    if args.from_save:
        source_space = ssf.StateSpaceFactory.load_from_file(args.from_save)
    else:
        source_space = ssf.StateSpaceFactory.create_random(3)
        source_space.save_to_file('source_space')
    
    source_space.visualize(filename='source_space', location='Graphs')
       
    # safe_space = run_iterative_refinement(source_space, strategy=strategy, max_iterations=args.max_iterations)
    # safe_space.save_to_file('iterative_safe_space')

    safe_space = make_greedy_space_deterministic(source_space, 15)
    safe_space.save_to_file('deterministic_safe_space')

    # safe_space.visualize(filename='deterministic_safe_space', location='Graphs')

    # Analyze the forks in the safe space
    event_pairs = analyze_forks_single_event(safe_space)
    print(event_pairs)
    state_spaces_3 = generate_state_spaces_from_event_pairs(event_pairs, 3, get_all_event_strings_from_tree(safe_space))
    print("Number of generated state spaces:", len(state_spaces_3))


    valid_count = 0
    for i, state_space in enumerate(state_spaces_3):
        if language_compare(source_space, state_space):
            print(f"State space {i} is valid in 3 state model")
            state_space.visualize(filename=f'ValidatedSpace_3_{valid_count}', location='Graphs')
            valid_count += 1
    print(f"Validated {valid_count} state spaces in 3 state model")

    state_spaces_4 = generate_state_spaces_from_event_pairs(event_pairs, 4, get_all_event_strings_from_tree(safe_space))
    print("Number of generated state spaces:", len(state_spaces_4))

    print ('~'*40)

    valid_count = 0
    for i, state_space in enumerate(state_spaces_4):
        if language_compare(source_space, state_space):
            print(f"State space {i} is valid in 4 state model")
            state_space.visualize(filename=f'ValidatedSpace_4_{valid_count}', location='Graphs')
            valid_count += 1
    print(f"Validated {valid_count} state spaces in 4 state model")
if __name__ == "__main__":
    main()