import json
import threading
import time
from collections import OrderedDict
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from aace.envs.scenarios import SCENARIOS
from aace.runtime import Session
from aace.schemas import SCHEMA_VERSION

CONTROLLERS = ("heuristic_direct", "heuristic_detour", "oracle_planner")
STATIC = Path(__file__).parent/"static"


class PairSession:
    """Single worker owns engines; requests read published immutable snapshots.

    The condition protects commands only. No HTTP writer/viewer lock is held
    during planning. Slow/disconnected browsers cannot change numerical actions.
    """

    def __init__(self, scenario: str, seed: int, reference: str, comparison: str):
        self.id = uuid4().hex
        self.sessions = [Session(scenario, reference, seed), Session(scenario, comparison, seed)]
        self._condition = threading.Condition()
        self._running = False
        self._pending_steps = 0
        self._stop_once = False
        self._closed = False
        self._speed = 1.0
        self._error = None
        self._publish()
        self._thread = threading.Thread(target=self._loop, daemon=True, name=f"demo-{self.id[:6]}")
        self._thread.start()

    def _publish(self):
        self._published = {"session_id": self.id, "running": self._running,
                           "speed": self._speed, "error": self._error,
                           "left": self.sessions[0].view(), "right": self.sessions[1].view(),
                           "research_status": "engineering demo; AACE memory/learned models not implemented"}
        self._replay = {"schema_version": SCHEMA_VERSION, "session_id": self.id,
                        "claim": "Engineering examples; not aggregate research evidence",
                        "runs": [{"seed": s.seed, "controller": s.controller.name,
                                  "created_at_utc": s.started_at, **s.provenance,
                                  "config": asdict(s.env.config), "scenario": asdict(s.env.scenario),
                                  "observation_permission": "fully_observed_v1",
                                  "decisions": tuple(s.records), "final_state": s.env.state.to_dict()}
                                 for s in self.sessions]}

    def control(self, action: str, speed: float = 1.0):
        if action not in ("run", "pause", "step", "stop") or not 0.25 <= speed <= 8:
            raise ValueError("Invalid control action/speed")
        with self._condition:
            if self._closed:
                raise ValueError("Session closed")
            self._speed = speed
            if action == "run":
                self._running = True
            elif action == "pause":
                self._running = False
            elif action == "step":
                self._running = False
                self._pending_steps = min(20, self._pending_steps+1)
            else:
                self._running = False
                self._pending_steps = 1
                self._stop_once = True
            self._published = dict(self._published, running=self._running, speed=self._speed)
            self._condition.notify_all()

    def view(self) -> dict:
        # Paths are copied at publication; completed records are never modified.
        return self._published

    def replay(self) -> dict:
        return self._replay

    def _loop(self):
        while True:
            with self._condition:
                while not self._closed and not self._running and not self._pending_steps:
                    self._condition.wait()
                if self._closed:
                    return
                stop = self._stop_once
                self._stop_once = False
                self._pending_steps = max(0, self._pending_steps-1)
                delay = 0.1/self._speed
            try:
                for session in self.sessions:
                    if not session.ended:
                        session.step(external_stop=stop)
                with self._condition:
                    if all(session.ended for session in self.sessions):
                        self._running = False
                    self._publish()
            except Exception as error:
                with self._condition:
                    self._error = f"{type(error).__name__}: {error}"
                    self._running = False
                    self._pending_steps = 0
                    self._publish()
            with self._condition:
                if self._running:
                    self._condition.wait(timeout=delay)

    def close(self):
        with self._condition:
            self._closed = True
            self._condition.notify_all()
        self._thread.join(timeout=3)


class SessionManager:
    def __init__(self):
        self.sessions = OrderedDict()
        self.lock = threading.Lock()

    def create(self, payload: dict) -> PairSession:
        scenario = payload.get("scenario", "shortcut")
        seed = payload.get("seed", 42)
        reference = payload.get("reference", "heuristic_direct")
        comparison = payload.get("comparison", "oracle_planner")
        if scenario not in SCENARIOS or reference not in CONTROLLERS or comparison not in CONTROLLERS:
            raise ValueError("Unknown scenario/controller")
        if type(seed) is not int or not 0 <= seed < 2**31:
            raise ValueError("Seed must be an integer in [0, 2^31)")
        pair = PairSession(scenario, seed, reference, comparison)
        old = None
        with self.lock:
            if len(self.sessions) >= 4:
                _, old = self.sessions.popitem(last=False)
            self.sessions[pair.id] = pair
        if old:
            old.close()
        return pair

    def get(self, identifier: str) -> PairSession:
        with self.lock:
            if identifier not in self.sessions:
                raise ValueError("Session missing or expired; create a new comparison")
            return self.sessions[identifier]

    def close(self):
        with self.lock:
            pairs = list(self.sessions.values())
            self.sessions.clear()
        for pair in pairs:
            pair.close()


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int):
        self.manager = SessionManager()
        super().__init__(("127.0.0.1", port), Handler)

    def server_close(self):
        self.manager.close()
        super().server_close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _respond(self, data, status=200, content_type="application/json; charset=utf-8"):
        body = json.dumps(data, allow_nan=False).encode() if isinstance(data, (dict, list)) else data
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' blob:; object-src 'none'; frame-ancestors 'none'")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _local_request(self) -> bool:
        port = self.server.server_port
        allowed = (f"127.0.0.1:{port}", f"localhost:{port}")
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        if host not in allowed or (origin is not None and origin not in tuple(f"http://{h}" for h in allowed)):
            self._respond({"error": "Local same-origin requests only"}, 403)
            return False
        return True

    def do_GET(self):
        if not self._local_request():
            return
        path = urlsplit(self.path).path
        if path == "/api/health":
            return self._respond({"application": "valor", "interface_version": 2,
                                  "schema_version": SCHEMA_VERSION})
        if path == "/api/scenarios":
            return self._respond({"scenarios": list(SCENARIOS), "controllers": CONTROLLERS,
                                  "forecast_notice": "Oracle dynamics, finite samples; learned predictions pending"})
        if path.startswith("/api/session/"):
            segments = path.strip("/").split("/")
            try:
                pair = self.server.manager.get(segments[2])
                if len(segments) == 4 and segments[3] == "export":
                    return self._respond(pair.replay())
                if len(segments) == 3:
                    return self._respond(pair.view())
            except ValueError as error:
                return self._respond({"error": str(error)}, 404)
        assets = {"/": ("index.html", "text/html; charset=utf-8"),
                  "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                  "/evidence.js": ("evidence.js", "text/javascript; charset=utf-8"),
                  "/style.css": ("style.css", "text/css; charset=utf-8")}
        if path in assets:
            filename, kind = assets[path]
            return self._respond((STATIC/filename).read_bytes(), content_type=kind)
        self._respond({"error": "Not found"}, 404)

    def do_POST(self):
        if not self._local_request():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096 or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("Expected a small JSON request")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object")
            path = urlsplit(self.path).path
            if path == "/api/session":
                return self._respond(self.server.manager.create(payload).view(), 201)
            segments = path.strip("/").split("/")
            if len(segments) == 4 and segments[:2] == ["api", "session"] and segments[3] == "control":
                pair = self.server.manager.get(segments[2])
                pair.control(payload.get("action"), float(payload.get("speed", 1)))
                return self._respond({"accepted": True})
            self._respond({"error": "Not found"}, 404)
        except (ValueError, TypeError, KeyError) as error:
            self._respond({"error": str(error)}, 400)


def serve(port=8765):
    if not 1 <= port <= 65535:
        raise ValueError("Port must be in [1, 65535]")
    server = DemoServer(port)
    print(f"VALOR local demo: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
