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

GAME_STATE = {
    "board": chess.Board(),
    "level": 1000,
    "human_color": chess.WHITE,
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

    turn = board.turn
    board.turn = chess.WHITE
    white_moves = board.legal_moves.count()
    board.turn = chess.BLACK
    black_moves = board.legal_moves.count()
    board.turn = turn

    return score + (white_moves - black_moves) * 2


def minimax(board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool) -> int:
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


def choose_bot_move(board: chess.Board, level: BotLevel) -> chess.Move:
    legal_moves = list(board.legal_moves)
    maximizing = board.turn == chess.WHITE
    scored: list[tuple[chess.Move, int]] = []

    for move in legal_moves:
        board.push(move)
        score = minimax(board, level.depth - 1, -math.inf, math.inf, not maximizing)
        board.pop()
        score += random.randint(-level.noise_cp, level.noise_cp)
        scored.append((move, score))

    scored.sort(key=lambda item: item[1], reverse=maximizing)

    if random.random() < level.blunder_chance:
        top_n = min(5, len(scored))
        return random.choice(scored[:top_n])[0]

    return scored[0][0]


def piece_symbol(piece: chess.Piece | None) -> str:
    if piece is None:
        return ""
    symbols = {
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
    return symbols[piece.symbol()]


def board_to_ui(board: chess.Board) -> list[list[dict[str, str]]]:
    rows = []
    for rank in range(7, -1, -1):
        line = []
        for file in range(8):
            sq = chess.square(file, rank)
            piece = board.piece_at(sq)
            line.append(
                {
                    "square": chess.square_name(sq),
                    "piece": piece_symbol(piece),
                    "color": "light" if (rank + file) % 2 == 0 else "dark",
                }
            )
        rows.append(line)
    return rows


def game_status(board: chess.Board) -> str:
    if board.is_checkmate():
        winner = "Белые" if board.turn == chess.BLACK else "Чёрные"
        return f"Мат. Победили: {winner}"
    if board.is_stalemate():
        return "Пат. Ничья"
    if board.is_insufficient_material():
        return "Ничья: недостаточно материала"
    if board.can_claim_draw():
        return "Можно заявить ничью"
    return f"Ход: {'Белые' if board.turn == chess.WHITE else 'Чёрные'}"


def serialize_state() -> dict:
    board = GAME_STATE["board"]
    return {
        "board": board_to_ui(board),
        "fen": board.fen(),
        "legal_moves": [m.uci() for m in board.legal_moves],
        "status": game_status(board),
        "game_over": board.is_game_over(claim_draw=True),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "human_color": "white" if GAME_STATE["human_color"] == chess.WHITE else "black",
        "level": GAME_STATE["level"],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state")
def state():
    return jsonify(serialize_state())


@app.route("/api/new-game", methods=["POST"])
def new_game():
    payload = request.get_json(silent=True) or {}
    level = int(payload.get("level", 1000))
    human_color = payload.get("human_color", "white")

    if level not in LEVELS:
        level = 1000

    GAME_STATE["board"] = chess.Board()
    GAME_STATE["level"] = level
    GAME_STATE["human_color"] = chess.WHITE if human_color == "white" else chess.BLACK

    if GAME_STATE["human_color"] == chess.BLACK:
        bot_move = choose_bot_move(GAME_STATE["board"], LEVELS[level])
        GAME_STATE["board"].push(bot_move)

    return jsonify(serialize_state())


@app.route("/api/move", methods=["POST"])
def move():
    payload = request.get_json(silent=True) or {}
    uci = str(payload.get("move", "")).strip().lower()
    board: chess.Board = GAME_STATE["board"]

    if board.is_game_over(claim_draw=True):
        return jsonify({"error": "Игра уже завершена", **serialize_state()}), 400

    if board.turn != GAME_STATE["human_color"]:
        return jsonify({"error": "Сейчас ход бота", **serialize_state()}), 400

    try:
        human_move = chess.Move.from_uci(uci)
    except ValueError:
        return jsonify({"error": "Неверный формат хода", **serialize_state()}), 400

    if human_move not in board.legal_moves:
        return jsonify({"error": "Нелегальный ход", **serialize_state()}), 400

    board.push(human_move)

    if not board.is_game_over(claim_draw=True):
        bot_move = choose_bot_move(board, LEVELS[GAME_STATE["level"]])
        board.push(bot_move)

    return jsonify(serialize_state())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
