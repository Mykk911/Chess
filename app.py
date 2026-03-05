import math
import random
from dataclasses import dataclass

import chess
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

UNICODE_PIECES = {
    "P": "♙",
    "N": "♘",
    "B": "♗",
    "R": "♖",
    "Q": "♕",
    "K": "♔",
    "p": "♟",
    "n": "♞",
    "b": "♝",
    "r": "♜",
    "q": "♛",
    "k": "♚",
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

state = {
    "board": chess.Board(),
    "human_color": chess.WHITE,
    "level": 1000,
}


def evaluate_board(board: chess.Board) -> int:
    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0

    score = 0
    for piece_type, value in PIECE_VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value

    current_turn = board.turn
    board.turn = chess.WHITE
    white_moves = board.legal_moves.count()
    board.turn = chess.BLACK
    black_moves = board.legal_moves.count()
    board.turn = current_turn

    return score + (white_moves - black_moves) * 2


def minimax(board: chess.Board, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
    if depth == 0 or board.is_game_over(claim_draw=True):
        return evaluate_board(board)

    if maximizing:
        best = -math.inf
        for move in board.legal_moves:
            board.push(move)
            best = max(best, minimax(board, depth - 1, alpha, beta, False))
            board.pop()
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return int(best)

    best = math.inf
    for move in board.legal_moves:
        board.push(move)
        best = min(best, minimax(board, depth - 1, alpha, beta, True))
        board.pop()
        beta = min(beta, best)
        if beta <= alpha:
            break
    return int(best)


def choose_bot_move(board: chess.Board, level_key: int) -> chess.Move:
    level = LEVELS[level_key]
    legal = list(board.legal_moves)
    maximizing = board.turn == chess.WHITE

    scored_moves: list[tuple[chess.Move, int]] = []
    for move in legal:
        board.push(move)
        score = minimax(board, level.depth - 1, -math.inf, math.inf, not maximizing)
        board.pop()
        score += random.randint(-level.noise_cp, level.noise_cp)
        scored_moves.append((move, score))

    scored_moves.sort(key=lambda item: item[1], reverse=maximizing)

    if random.random() < level.blunder_chance:
        return random.choice(scored_moves[: min(5, len(scored_moves))])[0]
    return scored_moves[0][0]


def board_payload(board: chess.Board) -> dict:
    squares = []
    for rank in range(7, -1, -1):
        row = []
        for file_idx in range(8):
            sq = chess.square(file_idx, rank)
            piece = board.piece_at(sq)
            row.append(
                {
                    "square": chess.square_name(sq),
                    "piece": piece.symbol() if piece else None,
                    "unicode": UNICODE_PIECES.get(piece.symbol()) if piece else "",
                }
            )
        squares.append(row)

    outcome = board.outcome(claim_draw=True)
    return {
        "board": squares,
        "turn": "white" if board.turn == chess.WHITE else "black",
        "fen": board.fen(),
        "game_over": board.is_game_over(claim_draw=True),
        "result": board.result(claim_draw=True) if board.is_game_over(claim_draw=True) else None,
        "winner": None if not outcome or outcome.winner is None else ("white" if outcome.winner else "black"),
        "legal_moves": [m.uci() for m in board.legal_moves],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/new_game")
def new_game():
    data = request.get_json(silent=True) or {}
    color = data.get("color", "white")
    level = int(data.get("level", 1000))
    if level not in LEVELS:
        level = 1000

    state["board"] = chess.Board()
    state["human_color"] = chess.WHITE if color == "white" else chess.BLACK
    state["level"] = level

    if state["human_color"] == chess.BLACK:
        bot_move = choose_bot_move(state["board"], state["level"])
        state["board"].push(bot_move)

    payload = board_payload(state["board"])
    payload["last_bot_move"] = None
    return jsonify(payload)


@app.get("/api/state")
def get_state():
    return jsonify(board_payload(state["board"]))


@app.post("/api/move")
def player_move():
    data = request.get_json(silent=True) or {}
    move_uci = data.get("move", "")
    board: chess.Board = state["board"]

    if board.is_game_over(claim_draw=True):
        return jsonify({"error": "Игра уже окончена."}), 400

    if board.turn != state["human_color"]:
        return jsonify({"error": "Сейчас ход бота."}), 400

    try:
        move = chess.Move.from_uci(move_uci)
    except ValueError:
        return jsonify({"error": "Неверный формат хода."}), 400

    if move not in board.legal_moves:
        return jsonify({"error": "Нелегальный ход."}), 400

    board.push(move)
    bot_uci = None

    if not board.is_game_over(claim_draw=True):
        bot_move = choose_bot_move(board, state["level"])
        bot_uci = bot_move.uci()
        board.push(bot_move)

    payload = board_payload(board)
    payload["last_bot_move"] = bot_uci
    return jsonify(payload)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
