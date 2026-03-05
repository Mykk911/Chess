const boardEl = document.getElementById('board');
const statusEl = document.getElementById('status');
const errorEl = document.getElementById('error');
const levelEl = document.getElementById('level');
const humanColorEl = document.getElementById('humanColor');
const newGameBtn = document.getElementById('newGame');

let game = null;
let selectedSquare = null;

function clearSelection() {
  selectedSquare = null;
}

function getMovesFrom(square) {
  if (!game) return [];
  return game.legal_moves.filter((m) => m.startsWith(square)).map((m) => m.slice(2, 4));
}

function renderBoard() {
  boardEl.innerHTML = '';
  if (!game) return;

  const targets = selectedSquare ? getMovesFrom(selectedSquare) : [];

  for (const row of game.board) {
    for (const cell of row) {
      const sq = document.createElement('button');
      sq.className = `square ${cell.color}`;
      sq.dataset.square = cell.square;
      sq.textContent = cell.piece;

      if (selectedSquare === cell.square) sq.classList.add('selected');
      if (targets.includes(cell.square)) sq.classList.add('target');

      sq.addEventListener('click', () => onSquareClick(cell.square));
      boardEl.appendChild(sq);
    }
  }
}

async function fetchState() {
  const res = await fetch('/api/state');
  game = await res.json();
  statusEl.textContent = game.status;
  levelEl.value = String(game.level);
  humanColorEl.value = game.human_color;
  renderBoard();
}

async function sendMove(move) {
  const res = await fetch('/api/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ move }),
  });
  const data = await res.json();
  game = data;
  statusEl.textContent = game.status;
  errorEl.textContent = data.error || '';
  renderBoard();
}

function detectPromotion(from, to) {
  const piece = game.board.flat().find((s) => s.square === from)?.piece;
  if (!piece) return '';
  if (piece === '♙' && to.endsWith('8')) return 'q';
  if (piece === '♟' && to.endsWith('1')) return 'q';
  return '';
}

async function onSquareClick(square) {
  if (!game || game.game_over) return;
  if (game.turn !== game.human_color) {
    errorEl.textContent = 'Сейчас ход бота';
    return;
  }

  errorEl.textContent = '';

  if (!selectedSquare) {
    selectedSquare = square;
    renderBoard();
    return;
  }

  const moveBase = `${selectedSquare}${square}`;
  const promotion = detectPromotion(selectedSquare, square);
  const move = `${moveBase}${promotion}`;

  const legal = game.legal_moves.includes(move)
    ? move
    : game.legal_moves.includes(moveBase)
      ? moveBase
      : null;

  if (!legal) {
    selectedSquare = square;
    renderBoard();
    return;
  }

  clearSelection();
  await sendMove(legal);
}

newGameBtn.addEventListener('click', async () => {
  const res = await fetch('/api/new-game', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      level: Number(levelEl.value),
      human_color: humanColorEl.value,
    }),
  });

  game = await res.json();
  statusEl.textContent = game.status;
  errorEl.textContent = '';
  clearSelection();
  renderBoard();
});

fetchState();
