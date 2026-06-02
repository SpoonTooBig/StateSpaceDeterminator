import StateNode as sn
import StateSpace as ss
import StateSpaceFactory as ssf
from enum import Enum
import argparse


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


def analyze_forks(state_space):
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

def reconstruct_state_space_from_forks(forks):
    # Find max depth to initialize forks_by_depth as a list
    max_depth = max([fork['depth'] for fork in forks]) if forks else 0
    forks_by_depth = [[] for _ in range(max_depth + 1)]
    
    # Populate forks_by_depth with event_strings at each depth
    for fork in forks:
        depth = fork['depth']
        event_string = fork['event_string']
        forks_by_depth[depth].append(event_string)
    
    print("\n=== Forks by Depth ===")
    for depth, event_strings in enumerate(forks_by_depth):
        if event_strings:
            print(f"Depth {depth}: {event_strings}")

    print(f"\n {forks_by_depth}")
    

def run_iterative_refinement(strategy=RefinementStrategy.GREEDY, max_iterations=20):
    print('Iterative state-space reconstruction demo')
    print(f'Using refinement strategy: {strategy.value}')
    print(f'Max iterations: {max_iterations}')
    source_space = build_random_source_state_space(size=3)
    source_space.visualize(filename='source_space', location='Iterations')
    initial_iterations = 20
    source_space.traverse(initial_iterations)
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
        source_space.traverse(initial_iterations)
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
        safe_space = ssf.StateSpaceFactory.load_from_file(args.from_save)
    else:
        safe_space = run_iterative_refinement(strategy=strategy, max_iterations=args.max_iterations)
        safe_space.save_to_file('iterative_safe_space')

    # Analyze the forks in the safe space
    forks = analyze_forks(safe_space)
    print_forks_analysis(forks)
    reconstruct_state_space_from_forks(forks)

if __name__ == "__main__":
    main()