import StateNode as sn
import StateSpace as ss
import StateSpaceFactory as ssf
from enum import Enum
import argparse
import itertools


class RefinementStrategy(Enum):
    GREEDY = 'greedy'


def build_random_source_state_space(size=6):
    return ssf.StateSpaceFactory.create_random(size)


def reconstruct_from_history(event_history):
    # Build a minimal deterministic path that reproduces the event string.
    states = [sn.StateNode(str(i)) for i in range(len(event_history) + 1)]
    for idx, event in enumerate(event_history):
        states[idx].AddTransfer(event, states[idx + 1])
    return ss.StateSpace(len(states), states)


def refine_safe_space_greedy(safe_space, event_history):
    current = safe_space.states[0]
    for idx, event in enumerate(event_history):
        if event in current.transfers:
            current = current.transfers[event]
            continue

        # Create new suffix states for the remainder of this trace.
        remainder = event_history[idx:]
        new_states = [sn.StateNode(str(len(safe_space.states) + i)) for i in range(len(remainder))]
        current.AddTransfer(remainder[0], new_states[0])
        for sub_idx, next_event in enumerate(remainder[1:], start=1):
            new_states[sub_idx - 1].AddTransfer(next_event, new_states[sub_idx])
        safe_space.states.extend(new_states)
        safe_space.size = len(safe_space.states)
        return safe_space

    return safe_space


def can_reproduce_history(state_space, event_history):
    output = state_space.string_traverse(event_history)
    return len(output) == len(event_history)

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

def extract_loops_from_forks(forks):
    # Find max depth to initialize forks_by_depth as a list
    max_depth = max([fork['depth'] for fork in forks]) if forks else 0
    forks_by_depth = [[] for _ in range(max_depth + 1)]
    
    # Populate forks_by_depth with event_strings at each depth
    for fork in forks:
        depth = fork['depth']
        event_string = fork['event_string']
        history = fork['history']
        forks_by_depth[depth].append((event_string, history))
    
    print("\n=== Forks by Depth ===")
    for depth, event_strings in enumerate(forks_by_depth):
        if event_strings:
            print(f"Depth {depth}: {event_strings}")

    # Build occurrences of full histories and event-strings
    occurrences_by_event = {}
    occurrences_by_full = {}
    all_full_histories = []

    for depth_list in forks_by_depth:
        for event_string, history in depth_list:
            # history is a list of parent fork event_strings (strings)
            full_history = "".join(history + [event_string])
            all_full_histories.append(full_history)

            occurrences_by_full[full_history] = occurrences_by_full.get(full_history, 0) + 1

            if event_string not in occurrences_by_event:
                occurrences_by_event[event_string] = []
            occurrences_by_event[event_string].append(full_history)

    # Loops: strings that either repeat (same full history seen >1) or are length 2 (two characters)
    loops = []
    for fh, count in occurrences_by_full.items():
        if count > 1 or len(fh) == 2:
            loops.append(fh)

    # Unresolved: full histories seen once and longer than 2
    unresolved_loops = [fh for fh, count in occurrences_by_full.items() if count == 1 and len(fh) > 2]

    def trim_history(full_history, known_loops):
        """Remove any known loop substrings from the left of full_history until nothing left or no change."""
        cur = full_history
        changed = True
        while changed and cur:
            changed = False
            for loop in known_loops:
                if cur.startswith(loop):
                    cur = cur[len(loop):]
                    changed = True
                    break
        return cur

    # Attempt to resolve unresolved_loops by trimming known loops
    resolved = []
    for fh in list(unresolved_loops):
        trimmed = trim_history(fh, loops)
        if not trimmed:
            # fully explained by known loops
            resolved.append(fh)
            unresolved_loops.remove(fh)

    # Add resolved ones to loops as well
    for r in resolved:
        if r not in loops:
            loops.append(r)

    print("\nDetected loops:", loops)
    if unresolved_loops:
        print("Unresolved candidate loops:", unresolved_loops)

    return loops


def create_state_space_from_loops(loops):
    """
    Create a StateSpace from a list of loop strings.
    - `loops` is a list of strings, each string is a sequence of events (characters).
    - Creates a single zero/start state and one branch per loop.
    - For each loop, one new state is created per event; the last event's transition returns to the zero state.

    Returns a new `ss.StateSpace` instance.
    """
    # Create zero state (numeric naming starting at 0)
    name_counter = 0
    zero = sn.StateNode(str(name_counter))
    name_counter += 1
    states = [zero]

    for loop in loops:
        if not loop:
            continue
        # start each loop from the zero state
        prev = zero
        # create nodes only for non-final events to avoid stranded nodes
        for j, event in enumerate(loop):
            # If this event already exists on the current state, reuse the
            # existing target instead of overwriting it. This preserves any
            # previously-created branches that start with the same event.
            if event in prev.transfers:
                # follow the existing branch
                prev = prev.transfers[event]
                continue

            if j < len(loop) - 1:
                node_name = str(name_counter)
                new_node = sn.StateNode(node_name)
                states.append(new_node)
                name_counter += 1
                prev.AddTransfer(event, new_node)
                prev = new_node
            else:
                # final event transitions back to zero
                prev.AddTransfer(event, zero)

    return ss.StateSpace(len(states), states)


def create_state_space_from_forks_prefix_merge(loops_or_forks):
    """
    Build a state space from loop data using prefix-merging.

    Accepts either:
    - `loops_or_forks` as a list of loop strings (each string is a sequence of events),
    - OR `loops_or_forks` as a list of fork tuples `(event_string, history_list)`
        where `history_list` is a list of event-strings leading up to the fork.

    The function converts fork tuples into full loop strings by concatenating
    `history_list + [event_string]` and then builds nodes for each prefix.
    The empty prefix is the zero/start node. Shared prefixes are merged.
    The final event of each loop transitions back to the zero node.

    This function is non-destructive: if a transfer already exists it will
    not be overwritten.
    """
    name_counter = 0
    zero = sn.StateNode(str(name_counter))
    name_counter += 1
    states = [zero]

    prefix_map = {"": zero}

    # Normalize input: support fork dicts, fork tuples, or loop strings
    normalized_loops = []
    for item in loops_or_forks:
        if not item:
            continue
        # fork dict: {'event_string': ..., 'history': [...]}
        if isinstance(item, dict) and 'event_string' in item and 'history' in item:
            event_string = item['event_string']
            history = item['history']
            if not isinstance(history, (list, tuple)):
                history = list(history)
            full = "".join(list(history) + [event_string])
            normalized_loops.append(full)
            continue
        # fork tuple: (event_string, history_list)
        if isinstance(item, (list, tuple)) and len(item) == 2:
            event_string, history = item
            if not isinstance(history, (list, tuple)):
                history = list(history)
            full = "".join(list(history) + [event_string])
            normalized_loops.append(full)
            continue
        # otherwise assume it's already a loop string
        normalized_loops.append(str(item))
    for loop in normalized_loops:
        if not loop:
            continue
        cur = ""
        for i, event in enumerate(loop):
            nxt = cur + event
            # If final event, ensure it points to zero (loop closure)
            if i == len(loop) - 1:
                src = prefix_map[cur]
                if event not in src.transfers:
                    src.AddTransfer(event, zero)
                # done with this loop
                break

            # Ensure node exists for nxt prefix
            if nxt not in prefix_map:
                node = sn.StateNode(str(name_counter))
                name_counter += 1
                states.append(node)
                prefix_map[nxt] = node

            # Add transfer if missing
            src = prefix_map[cur]
            dst = prefix_map[nxt]
            if event not in src.transfers:
                src.AddTransfer(event, dst)

            cur = nxt

    return ss.StateSpace(len(states), states)

def forks_to_safe_space(forks):

    def get_full_history(fork):
        return fork['history'] + [fork['event_string']]
    
    simplified_forks = []
    possible_transitions = []
    for fork in forks:
        event = fork['event_string']
        history = fork['history']
        depth = fork['depth']
        full_history = get_full_history(fork)
        print(full_history)
        simple_fork = (event, history)
        simplified_forks.append((event, history))

        for i in range(len(full_history)):
            if i == 0:
                continue
            transition = (full_history[i-1], full_history[i])
            if transition not in possible_transitions:
                possible_transitions.append(transition)
    print(possible_transitions)   


def count_possible_state_spaces(event_pairs, num_states):
    """
    Compute the number of deterministic state spaces with `num_states` states
    that satisfy the no-self-loop constraint and use the events present in
    `event_pairs`.

    This is the total number of possible transition assignments before any
    sequential-pair filtering is applied.
    """
    if num_states <= 0:
        return 0

    alphabet = sorted({event for pair in event_pairs for event in pair})
    if not alphabet:
        return 0

    choices_per_transition = num_states - 1
    total_transitions = num_states * len(alphabet)
    return choices_per_transition ** total_transitions


def generate_state_spaces_from_event_pairs(event_pairs, num_states):
    """
    Generate every possible deterministic StateSpace with `num_states` states
    that can realize the provided sequential event pairs.

    Each pair is interpreted as two events that can occur in sequence, e.g.
    ("a", "b") means there is some state S where transition "a" leads to
    state T and state T has a transition "b".

    Returns a list of `ss.StateSpace` instances.
    """
    if num_states <= 0:
        return []

    alphabet = sorted({event for pair in event_pairs for event in pair})
    if not alphabet:
        return []

    state_spaces = []
    state_indices = range(num_states)
    transition_positions = num_states * len(alphabet)

    for assignment in itertools.product(state_indices, repeat=transition_positions):
        if any(target_idx == state_idx for state_idx in state_indices for target_idx in [assignment[state_idx * len(alphabet) + event_idx] for event_idx in range(len(alphabet))]):
            continue

        # Build states for this assignment
        states = [sn.StateNode(str(i)) for i in state_indices]
        for state_idx in state_indices:
            for event_idx, event in enumerate(alphabet):
                target_idx = assignment[state_idx * len(alphabet) + event_idx]
                states[state_idx].AddTransfer(event, states[target_idx])

        valid = True
        for first_event, second_event in event_pairs:
            pair_found = False
            for state in states:
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
            state_spaces.append(ss.StateSpace(len(states), states))

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

def run_iterative_refinement(source_space, strategy=RefinementStrategy.GREEDY, max_iterations=20):
    print('Iterative state-space reconstruction demo')
    print(f'Using refinement strategy: {strategy.value}')
    print(f'Max iterations: {max_iterations}')
    source_space.visualize(filename='source_space', location='Iterations')
    initial_iterations = 20
    source_space.random_traverse(initial_iterations)
    event_history = source_space.eventHistory
    print('Initial trace length:', len(event_history))
    print('Initial event history:', event_history)

    safe_space = reconstruct_from_history(event_history)
    safe_space.visualize(filename=f'safe_space_0', location='Iterations')

    print('Initial safe space reconstructed with', safe_space.size, 'states.')

    stable_rounds = 0
    for round_num in range(1, max_iterations + 1):
        print('\nRound', round_num)
        source_space.eventHistory = ''
        source_space.stateHistory = ''
        source_space.currentState = source_space.states[0]
        source_space.random_traverse(initial_iterations)
        event_history = source_space.eventHistory
        print('Observed event history:', event_history)

        can_reproduce = can_reproduce_history(safe_space, event_history)
        if can_reproduce:
            print('Safe space already reproduces this trace exactly.')
            stable_rounds += 1
        else:
            print('Mismatch detected. Refining safe space...')
            if strategy == RefinementStrategy.GREEDY:
                safe_space = refine_safe_space_greedy(safe_space, event_history)
            print('Safe space updated to', safe_space.size, 'states.')
            safe_space.visualize(filename=f'safe_space_{round_num}', location='Iterations')
            stable_rounds = 0

        if stable_rounds >= 3:
            print('Safe space has reproduced three consecutive traces exactly; stopping.')
            return safe_space
        
    return safe_space

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
        source_space = build_random_source_state_space(size=3)
        source_space.save_to_file('source_space')
    
    source_space.visualize(filename='source_space', location='Graphs')
       
    # safe_space = run_iterative_refinement(source_space, strategy=strategy, max_iterations=args.max_iterations)
    # safe_space.save_to_file('iterative_safe_space')

    safe_space = make_greedy_space_deterministic(source_space, 10)
    safe_space.save_to_file('deterministic_safe_space')
    safe_space.visualize(filename='deterministic_safe_space', location='Graphs')

    # Analyze the forks in the safe space
    event_pairs = analyze_forks_single_event(safe_space)
    print(event_pairs)
    state_spaces = generate_state_spaces_from_event_pairs(event_pairs, 3)
    for i, state_space in enumerate(state_spaces):
        state_space.visualize(filename=f'generated_space_{i}', location='Graphs')

if __name__ == "__main__":
    main()