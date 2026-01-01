// CHANGE THIS AFTER DEPLOY
const WS_URL = "ws://10.17.38.163:8000/ws";

const statusEl = document.getElementById("status");
const gameEl = document.getElementById("game");
const resultEl = document.getElementById("result");

const clickBtn = document.getElementById("clickBtn");
const timerEl = document.getElementById("timer");
const youEl = document.getElementById("you");
const oppEl = document.getElementById("opponent");

let ws;
let timeLeft = 10;
let timerInterval = null;

// ---- WebSocket setup ----
function connect() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    statusEl.textContent = "Connected. Waiting for opponent…";
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    switch (msg.type) {
      case "waiting":
        statusEl.textContent = "Waiting for opponent…";
        break;

      case "start":
        startGame(msg.duration);
        break;

      case "score_update":
        youEl.textContent = msg.you;
        oppEl.textContent = msg.opponent;
        break;

      case "end":
        endGame(msg);
        break;
    }
  };

  ws.onclose = () => {
    statusEl.textContent = "Disconnected from server.";
    clickBtn.disabled = true;
  };
}

// ---- Game logic ----
function startGame(duration) {
  statusEl.textContent = "Game started!";
  gameEl.classList.remove("hidden");
  resultEl.classList.add("hidden");

  timeLeft = duration;
  timerEl.textContent = timeLeft;

  youEl.textContent = "0";
  oppEl.textContent = "0";

  clickBtn.disabled = false;

  timerInterval = setInterval(() => {
    timeLeft--;
    timerEl.textContent = timeLeft;
    if (timeLeft <= 0) clearInterval(timerInterval);
  }, 1000);
}

function endGame(msg) {
  clickBtn.disabled = true;
  clearInterval(timerInterval);

  gameEl.classList.add("hidden");
  resultEl.classList.remove("hidden");

  let text = "";
  if (msg.result === "win") text = "🏆 You Win!";
  else if (msg.result === "lose") text = "❌ You Lose!";
  else text = "🤝 Draw";

  resultEl.textContent = `${text} (${msg.your_score} : ${msg.opponent_score})`;
}

// ---- Click handler ----
clickBtn.onclick = () => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "click" }));
  }
};

// Start
connect();
