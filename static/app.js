const boardEl = document.getElementById('board');
const statusEl = document.getElementById('status');
const hintEl = document.getElementById('hint');
const newGameBtn = document.getElementById('new-game');
const levelEl = document.getElementById('level');
const colorEl = document.getElementById('color');

let currentState = null;
let selectedSquare = null;

function isHumanTurn() {
  if (!currentState) return false;
  return currentState.turn === colorEl.value;
}

function legalTargetsFrom(square) {
  if (!currentState) return [];
  return currentState.legal_moves
    .filter((m) => m.startsWith(square))
    .map((m) => m.slice(2, 4));
}

function renderBoard() {
  boardEl.innerHTML = '';
  if (!currentState) return;

  const legalTargets = selectedSquare ? legalTargetsFrom(selectedSquare) : [];

  currentState.board.forEach((row, rowIdx) => {
    row.forEach((cell, colIdx) => {
      const square = document.createElement('button');
      square.className = 'square';
      const dark = (rowIdx + colIdx) % 2 === 1;
      square.classList.add(dark ? 'dark' : 'light');
      square.dataset.square = cell.square;
      square.textContent = cell.unicode || '';

      if (selectedSquare === cell.square) {
        square.classList.add('selected');
      }
      if (legalTargets.includes(cell.square)) {
        square.classList.add('legal');
      }

      square.addEventListener('click', onSquareClick);
      boardEl.appendChild(square);
    });
  });
}

function updateStatus(lastBotMove = null) {
  if (!currentState) return;

  if (currentState.game_over) {
    if (currentState.winner) {
      statusEl.textContent = `Игра окончена (${currentState.result}). Победили: ${currentState.winner === 'white' ? 'Белые' : 'Чёрные'}`;
    } else {
      statusEl.textContent = `Игра окончена (${currentState.result}). Ничья`;
    }
    hintEl.textContent = 'Нажми "Новая игра", чтобы начать заново.';
    return;
  }

  const turnText = currentState.turn === 'white' ? 'Белых' : 'Чёрных';
  statusEl.textContent = `Ход ${turnText}.`;

  if (lastBotMove) {
    hintEl.textContent = `Бот сыграл: ${lastBotMove}. Твой ход.`;
  } else if (isHumanTurn()) {
    hintEl.textContent = 'Кликни по своей фигуре, затем по клетке назначения.';
  } else {
    hintEl.textContent = 'Бот думает...';
  }
}

async function fetchState() {
  const res = await fetch('/api/state');
  currentState = await res.json();
  selectedSquare = null;
  renderBoard();
  updateStatus();
}

async function startNewGame() {
  const res = await fetch('/api/new_game', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      level: Number(levelEl.value),
      color: colorEl.value,
    }),
  });

  currentState = await res.json();
  selectedSquare = null;
  renderBoard();
  updateStatus(currentState.last_bot_move);
}

async function makeMove(from, to) {
  let move = `${from}${to}`;

  const fromRow = Number(from[1]);
  if ((fromRow === 7 && to[1] === '8') || (fromRow === 2 && to[1] === '1')) {
    move += 'q';
  }

  const res = await fetch('/api/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ move }),
  });

  const data = await res.json();

  if (!res.ok) {
    hintEl.textContent = data.error || 'Ошибка хода';
    return;
  }

  currentState = data;
  selectedSquare = null;
  renderBoard();
  updateStatus(data.last_bot_move);
}

function onSquareClick(event) {
  if (!currentState || currentState.game_over || !isHumanTurn()) return;

  const clicked = event.currentTarget.dataset.square;
  const cell = currentState.board.flat().find((x) => x.square === clicked);
  const piece = cell?.piece;

  if (!selectedSquare) {
    if (!piece) return;
    const isWhitePiece = piece === piece.toUpperCase();
    const humanWhite = colorEl.value === 'white';

    if ((humanWhite && !isWhitePiece) || (!humanWhite && isWhitePiece)) {
      hintEl.textContent = 'Это не твоя фигура.';
      return;
    }

    selectedSquare = clicked;
    renderBoard();
    return;
  }

  if (selectedSquare === clicked) {
    selectedSquare = null;
    renderBoard();
    return;
  }

  makeMove(selectedSquare, clicked);
}

newGameBtn.addEventListener('click', startNewGame);
fetchState();
