import math
import random
from dataclasses import dataclass

import chess

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


@dataclass(frozen=True)
class BotLevel:
    depth: int
    blunder_chance: float
    noise_cp: int


LEVELS: dict[int, BotLevel] = {
    100: BotLevel(depth=1, blunder_chance=0.60, noise_cp=220),
    500: BotLevel(depth=1, blunder_chance=0.35, noise_cp=140),
    1000: BotLevel(depth=2, blunder_chance=0.20, noise_cp=80),
    1500: BotLevel(depth=3, blunder_chance=0.10, noise_cp=40),
    2000: BotLevel(depth=4, blunder_chance=0.03, noise_cp=20),
}


def evaluate_board(board: chess.Board) -> int:
    """Positive = good for side to move's opponent? No: good for White."""
    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0

    score = 0
    for piece_type, value in PIECE_VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value

    # Simple mobility bonus.
    white_turn = board.turn
    board.turn = chess.WHITE
    white_moves = board.legal_moves.count()
    board.turn = chess.BLACK
    black_moves = board.legal_moves.count()
    board.turn = white_turn
    score += (white_moves - black_moves) * 2

    return score


def minimax(board: chess.Board, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
    if depth == 0 or board.is_game_over(claim_draw=True):
        return evaluate_board(board)

    if maximizing:
        value = -math.inf
        for move in board.legal_moves:
            board.push(move)
            value = max(value, minimax(board, depth - 1, alpha, beta, False))
            board.pop()
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return int(value)

    value = math.inf
    for move in board.legal_moves:
        board.push(move)
        value = min(value, minimax(board, depth - 1, alpha, beta, True))
        board.pop()
        beta = min(beta, value)
        if beta <= alpha:
            break
    return int(value)


def choose_bot_move(board: chess.Board, level: BotLevel) -> chess.Move:
    legal = list(board.legal_moves)
    if not legal:
        raise ValueError("No legal moves")

    move_scores: list[tuple[chess.Move, int]] = []

    maximizing = board.turn == chess.WHITE
    for move in legal:
        board.push(move)
        score = minimax(board, level.depth - 1, -math.inf, math.inf, not maximizing)
        board.pop()

        # Add configurable noise on lower levels.
        noise = random.randint(-level.noise_cp, level.noise_cp)
        move_scores.append((move, score + noise))

    move_scores.sort(key=lambda x: x[1], reverse=maximizing)

    # Simulate blunders by sampling from top-N instead of always best.
    if random.random() < level.blunder_chance:
        window = min(5, len(move_scores))
        candidates = move_scores[:window]
        return random.choice(candidates)[0]

    return move_scores[0][0]


def print_intro() -> None:
    print("=== Primitive Chess vs AI ===")
    print("Формат хода: e2e4, g1f3, e7e8q")
    print("Команды: help, moves, quit")


def ask_level() -> BotLevel:
    print("Доступные уровни ИИ: 100, 500, 1000, 1500, 2000")
    while True:
        raw = input("Выбери уровень ИИ: ").strip()
        if not raw.isdigit():
            print("Введите число из списка.")
            continue
        lvl = int(raw)
        if lvl in LEVELS:
            return LEVELS[lvl]
        print("Такого уровня нет.")


def ask_color() -> chess.Color:
    while True:
        raw = input("Играть за белых или чёрных? (w/b): ").strip().lower()
        if raw in {"w", "white", "б", "белые"}:
            return chess.WHITE
        if raw in {"b", "black", "ч", "черные", "чёрные"}:
            return chess.BLACK
        print("Введите w или b.")


def main() -> None:
    random.seed()
    print_intro()
    level = ask_level()
    human_color = ask_color()

    board = chess.Board()

    while not board.is_game_over(claim_draw=True):
        print("\n" + str(board))
        print(f"Ход: {'Белые' if board.turn == chess.WHITE else 'Чёрные'}")

        if board.turn == human_color:
            raw = input("Твой ход: ").strip().lower()
            if raw == "quit":
                print("Игра завершена пользователем.")
                return
            if raw == "help":
                print("Вводи ход в UCI, пример: e2e4")
                continue
            if raw == "moves":
                print("Легальные ходы:", " ".join(m.uci() for m in board.legal_moves))
                continue

            try:
                move = chess.Move.from_uci(raw)
            except ValueError:
                print("Неверный формат. Пример: e2e4")
                continue

            if move not in board.legal_moves:
                print("Нелегальный ход.")
                continue

            board.push(move)
        else:
            bot_move = choose_bot_move(board, level)
            print(f"Бот играет: {bot_move.uci()}")
            board.push(bot_move)

    print("\n" + str(board))
    print("\nИгра окончена:", board.result(claim_draw=True))
    outcome = board.outcome(claim_draw=True)
    if outcome is not None and outcome.winner is not None:
        print("Победили:", "Белые" if outcome.winner == chess.WHITE else "Чёрные")
    else:
        print("Ничья")


if __name__ == "__main__":
    main()
