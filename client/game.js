const WS_URL =
  location.protocol === "https:"
    ? `wss://${location.host}/ws`
    : `ws://${location.host}/ws`;

const statusEl = document.getElementById("status");
const onlineEl = document.getElementById("online");
const gameEl = document.getElementById("game");
const resultEl = document.getElementById("result");

const clickBtn = document.getElementById("clickBtn");
const timerEl = document.getElementById("timer");
const youEl = document.getElementById("you");
const oppEl = document.getElementById("opponent");

let ws;
let timer;

ws = new WebSocket(WS_URL);

ws.onopen = () => {
  statusEl.textContent = "Waiting for opponent…";
};

ws.onmessage = (e) => {
  const msg = JSON.parse(e.data);

  if (msg.type === "online_count") {
    onlineEl.textContent = `🟢 Online: ${msg.count}`;
  }

  if (msg.type === "waiting") {
    statusEl.textContent = "Waiting for opponent…";
  }

  if (msg.type === "start") {
    startGame(msg.duration);
  }

  if (msg.type === "score_update") {
    youEl.textContent = msg.you;
    oppEl.textContent = msg.opponent;
  }

  if (msg.type === "end") {
    endGame(msg);
  }
};

function startGame(duration) {
  gameEl.classList.remove("hidden");
  resultEl.classList.add("hidden");
  statusEl.textContent = "GO!";
  clickBtn.disabled = false;

  youEl.textContent = 0;
  oppEl.textContent = 0;

  let time = duration;
  timerEl.textContent = time;

  timer = setInterval(() => {
    time--;
    timerEl.textContent = time;
    if (time <= 0) clearInterval(timer);
  }, 1000);
}

function endGame(msg) {
  clickBtn.disabled = true;
  gameEl.classList.add("hidden");
  resultEl.classList.remove("hidden");

  let text =
    msg.result === "win" ? "🏆 You Win!" :
    msg.result === "lose" ? "❌ You Lose!" :
    "🤝 Draw";

  resultEl.textContent = `${text} (${msg.your_score} : ${msg.opponent_score})`;
}

clickBtn.onclick = () => {
  ws.send(JSON.stringify({ type: "click" }));
};
