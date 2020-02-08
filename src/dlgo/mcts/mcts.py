"""
Monte Carlo tree search
"""
from __future__ import annotations
import math
import random
import copy
import zmq

from typing import Dict, List, Optional, Tuple, cast
from dlgo.agent.base import Agent
from dlgo.agent.helpers import is_point_an_eye
from dlgo.agent.random_bot import FastRandomAgent
from dlgo.goboard import GameState, Move, Board
from dlgo.gotypes import Player


class MCTSNode:
    def __init__(self, game_state: GameState, parent: MCTSNode = None, last_move: Move = None):
        self.game_state = game_state
        self.parent = parent
        self.last_move = last_move
        self.win_counts: Dict[Player, int] = {
            Player.black: 0,
            Player.white: 0,
        }
        self.num_rollouts: int = 0
        self.children: List[MCTSNode] = []
        b: Board = game_state.board
        p: Player = game_state.next_player
        moves: List[Move] = game_state.legal_moves()
        self.unvisited_moves: List[Move] = [m for m in moves if not (m.point and is_point_an_eye(b, m.point, p))]

    def add_random_child(self) -> MCTSNode:
        index = random.randint(0, len(self.unvisited_moves) - 1)
        new_move = self.unvisited_moves.pop(index)
        new_game_state = self.game_state.apply_move(new_move)
        new_node = MCTSNode(new_game_state, self, new_move)
        self.children.append(new_node)
        return new_node

    def increment_win(self, winner):
        self.win_counts[winner] += 1
        self.num_rollouts += 1

    def can_add_child(self) -> bool:
        return len(self.unvisited_moves) > 0

    def is_terminal(self) -> bool:
        return self.game_state.is_over()

    def winning_frac(self, player) -> float:
        return self.win_counts[player] / self.num_rollouts  # watch out for division by 0


class MCTSAgent(Agent):
    def __init__(self, num_rounds: int, temperature: float, parallel_rollouts: bool = False):
        """
        temperature: around 1.5
                    Hotter (greater) means search what seems to be bad moves a bit more.
                    Cooler means search what seems to be good moves a bit deeper.
        """
        super().__init__()
        self.num_rounds = num_rounds
        self.temperature = temperature
        self.parallel_rollouts = parallel_rollouts

        if self.parallel_rollouts:
            self.context = zmq.Context()
            #  Socket to talk to server
            print("Connecting to sim_games parallel games server...")
            self.socket = self.context.socket(zmq.REQ)
            self.socket.connect("tcp://localhost:5555")

    def select_move(self, game_state) -> Move:
        root: MCTSNode = MCTSNode(game_state)

        for i in range(self.num_rounds):
            node = root
            while (not node.can_add_child()) and (not node.is_terminal()):
                node = self.select_child(node)

            # Add a new child node into the tree.
            if node.can_add_child():
                node = node.add_random_child()

            # Simulate a random game from this node.
            if self.parallel_rollouts:
                winners = self.simulate_parallel_random_games(node.game_state)
            else:
                winners = [self.simulate_random_game(node.game_state)]

            # Propagate scores back up the tree.
            tmp_node: Optional[MCTSNode] = node
            while tmp_node is not None:
                for winner in winners:
                    tmp_node.increment_win(winner)
                tmp_node = tmp_node.parent

        scored_moves: List[Tuple[float, Move, int]] = [
            (child.winning_frac(game_state.next_player), cast(Move, child.last_move), child.num_rollouts)
            for child in root.children
        ]
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        for s, m, n in scored_moves[:10]:
            print('%s - %.3f (%d)' % (m, s, n))

        print('Select move %s with win pct %.3f' % (scored_moves[0][1], scored_moves[0][0]))
        print_mc_tree_info(root)
        return scored_moves[0][1]

    def select_child(self, node: MCTSNode) -> MCTSNode:
        """Select a child according to the upper confidence bound for
        trees (UCT) metric.
        """
        total_rollouts: int = sum(child.num_rollouts for child in node.children)
        log_rollouts: float = math.log(total_rollouts)

        best_score = -1.0
        best_child = None

        for child in node.children:
            # Calculate the UCT score.
            win_percentage = child.winning_frac(node.game_state.next_player)
            exploration_factor = math.sqrt(log_rollouts / child.num_rollouts)
            uct_score = win_percentage + self.temperature * exploration_factor
            # Check if this is the largest we've seen so far.
            if uct_score > best_score:
                best_score = uct_score
                best_child = child
        return cast(MCTSNode, best_child)

    @staticmethod
    def simulate_random_game(game: GameState) -> Player:
        bots = {
            Player.black: FastRandomAgent(),
            Player.white: FastRandomAgent(),
        }
        while not game.is_over():
            bot_move = bots[game.next_player].select_move(game)
            game = game.apply_move(bot_move)
        return cast(Player, game.winner())

    def simulate_parallel_random_games(self, game: GameState) -> List[Player]:
        game_with_nomore_than_one_parent = game
        parent = game.previous_state
        if parent is not None:
            board = copy.deepcopy(parent.board)
            parent_copy = GameState(board, parent.next_player, None, parent.last_move)
            game_with_nomore_than_one_parent.previous_state = parent_copy
        self.socket.send_pyobj(game_with_nomore_than_one_parent)
        results: List[Player] = self.socket.recv_pyobj()
        return results


# Helper functions to print MCTS tree info
def _depth_from_to(node_descendent: MCTSNode, node_ancestor: Optional[MCTSNode]) -> int:
    ret = 0
    while node_descendent != node_ancestor:
        node_descendent = cast(MCTSNode, node_descendent.parent)
        ret += 1
    return ret


def _find_tree_deepest_node(node: MCTSNode) -> MCTSNode:
    ret = node
    children: List[MCTSNode] = [c for c in node.children if c.last_move and not c.last_move.is_resign]
    if len(children) > 0:
        depth = 0
        for c in children:
            n: MCTSNode = _find_tree_deepest_node(c)
            current_depth = _depth_from_to(n, node)
            if current_depth > depth:
                depth = current_depth
                ret = n
    return ret


def _find_tree_shallowest_node(node: MCTSNode) -> MCTSNode:
    ret = node
    children: List[MCTSNode] = [c for c in node.children if c.last_move and not c.last_move.is_resign]
    if len(children) > 0:
        depth = 10000
        for c in children:
            n: MCTSNode = _find_tree_shallowest_node(c)
            current_depth = _depth_from_to(n, node)
            if current_depth < depth:
                depth = current_depth
                ret = n
    return ret


def print_mc_tree_info(root: MCTSNode) -> None:
    candidates: List[MCTSNode] = [c for c in root.children if c.last_move and not c.last_move.is_resign]
    candidate_count: int = len(candidates)
    strongest: MCTSNode = max(candidates, key=lambda c: c.winning_frac(root.game_state.next_player))
    weakest: MCTSNode = min(candidates, key=lambda c: c.winning_frac(root.game_state.next_player))
    strongest_deepest_depth: int = _depth_from_to(_find_tree_deepest_node(strongest), root)
    weakest_deepest_depth: int = _depth_from_to(_find_tree_deepest_node(weakest), root)
    shalowest_depth: int = _depth_from_to(_find_tree_shallowest_node(root), root)
    print('# candidate moves: {}'.format(candidate_count))
    print('strongest move, deepest MCTS depth: {}'.format(strongest_deepest_depth))
    print('weakest move, deepest MCTS depth: {}'.format(weakest_deepest_depth))
    print('shallowest MCTS depth: {}'.format(shalowest_depth))
