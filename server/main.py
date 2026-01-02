import asyncio
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pathlib import Path


app = FastAPI()

# ---- Serve frontend ----
BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/", StaticFiles(directory=BASE_DIR / "client", html=True), name="client")
# ---- Global state ----
waiting_players = []
matches = {}
connected_users = set()


class Match:
    def __init__(self, p1: WebSocket, p2: WebSocket):
        self.players = [p1, p2]
        self.scores = {p1: 0, p2: 0}
        self.start_time = time.time()
        self.ended = False


async def safe_send(ws: WebSocket, data: dict):
    try:
        await ws.send_json(data)
    except:
        pass


async def broadcast_online_count():
    count = len(connected_users)
    for ws in list(connected_users):
        await safe_send(ws, {
            "type": "online_count",
            "count": count
        })


async def end_match(match: Match):
    if match.ended:
        return

    match.ended = True
    p1, p2 = match.players
    s1, s2 = match.scores[p1], match.scores[p2]

    def result(a, b):
        return "win" if a > b else "lose" if a < b else "draw"

    await safe_send(p1, {
        "type": "end",
        "result": result(s1, s2),
        "your_score": s1,
        "opponent_score": s2
    })

    await safe_send(p2, {
        "type": "end",
        "result": result(s2, s1),
        "your_score": s2,
        "opponent_score": s1
    })

    matches.pop(p1, None)
    matches.pop(p2, None)


async def match_timer(match: Match):
    await asyncio.sleep(10)
    await end_match(match)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_users.add(ws)
    await broadcast_online_count()

    try:
        waiting_players.append(ws)
        await safe_send(ws, {"type": "waiting"})

        if len(waiting_players) >= 2:
            p1 = waiting_players.pop(0)
            p2 = waiting_players.pop(0)

            match = Match(p1, p2)
            matches[p1] = match
            matches[p2] = match

            await safe_send(p1, {"type": "start", "duration": 10})
            await safe_send(p2, {"type": "start", "duration": 10})

            asyncio.create_task(match_timer(match))

        while True:
            data = await ws.receive_json()

            if data.get("type") == "click":
                match = matches.get(ws)
                if not match or match.ended:
                    continue

                if time.time() - match.start_time > 10:
                    continue

                match.scores[ws] += 1

                p1, p2 = match.players
                await safe_send(p1, {
                    "type": "score_update",
                    "you": match.scores[p1],
                    "opponent": match.scores[p2]
                })
                await safe_send(p2, {
                    "type": "score_update",
                    "you": match.scores[p2],
                    "opponent": match.scores[p1]
                })

    except WebSocketDisconnect:
        if ws in waiting_players:
            waiting_players.remove(ws)

        match = matches.get(ws)
        if match and not match.ended:
            opponent = [p for p in match.players if p != ws][0]
            await safe_send(opponent, {
                "type": "end",
                "result": "win",
                "reason": "opponent_disconnected"
            })
            matches.pop(opponent, None)
            matches.pop(ws, None)

    finally:
        connected_users.discard(ws)
        await broadcast_online_count()
