import asyncio
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# ---- Global state (OK for prototype) ----
waiting_players = []
matches = {}  # websocket -> match_id


class Match:
    def __init__(self, p1: WebSocket, p2: WebSocket):
        self.players = [p1, p2]
        self.scores = {p1: 0, p2: 0}
        self.start_time = time.time()
        self.ended = False


# ---- Helpers ----
async def safe_send(ws: WebSocket, data: dict):
    try:
        await ws.send_json(data)
    except:
        pass


async def end_match(match: Match):
    if match.ended:
        return

    match.ended = True
    p1, p2 = match.players
    s1, s2 = match.scores[p1], match.scores[p2]

    result_p1 = "win" if s1 > s2 else "lose" if s1 < s2 else "draw"
    result_p2 = "win" if s2 > s1 else "lose" if s2 < s1 else "draw"

    await safe_send(p1, {
        "type": "end",
        "result": result_p1,
        "your_score": s1,
        "opponent_score": s2
    })

    await safe_send(p2, {
        "type": "end",
        "result": result_p2,
        "your_score": s2,
        "opponent_score": s1
    })

    matches.pop(p1, None)
    matches.pop(p2, None)


async def match_timer(match: Match):
    await asyncio.sleep(10)
    await end_match(match)


# ---- WebSocket endpoint ----
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    try:
        # Player joins
        await safe_send(ws, {"type": "waiting"})
        waiting_players.append(ws)

        # Matchmaking
        if len(waiting_players) >= 2:
            p1 = waiting_players.pop(0)
            p2 = waiting_players.pop(0)

            match = Match(p1, p2)
            matches[p1] = match
            matches[p2] = match

            # Notify players
            await safe_send(p1, {"type": "start", "duration": 10})
            await safe_send(p2, {"type": "start", "duration": 10})

            asyncio.create_task(match_timer(match))

        # ---- Game loop ----
        while True:
            data = await ws.receive_json()

            if data.get("type") == "click":
                match = matches.get(ws)
                if not match or match.ended:
                    continue

                # Time check (anti-cheat)
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
        # Handle disconnect
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
            match.ended = True
            matches.pop(opponent, None)
            matches.pop(ws, None)
