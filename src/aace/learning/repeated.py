"""Fit and export a small recurrent shock predictor from public events only."""

import json
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from aace.benchmarks.cascade import HIGH, LOW
from aace.benchmarks.repeated import BOUNDARY, CLEAR, SHOCK

VERSION = "release-public-gru4-v1"
GRID = (0., .05, .10, .15, .20, .25, .30, .40, .50)
SHAPES = {"input": (12, 3), "hidden": (12, 4), "input_bias": (12,),
          "hidden_bias": (12,), "head": (4,), "head_bias": (1,)}


def fit_markov(tokens):
    losses = []
    for q in GRID:
        state = np.full(len(tokens), .5)
        loss = 0.
        for event in tokens.T:
            state = np.where(event == BOUNDARY, q+(1-2*q)*state, state)
            observed = (event == SHOCK) | (event == CLEAR)
            a = np.where(event == SHOCK, LOW, 1-LOW)
            b = np.where(event == SHOCK, HIGH, 1-HIGH)
            likelihood = b*state+a*(1-state)
            loss -= float(np.log(likelihood[observed]).sum())
            state = np.where(observed, b*state/likelihood, state)
        losses.append(loss)
    return GRID[int(np.argmin(losses))], dict(zip(GRID, losses))


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(3, 4, batch_first=True)
        self.head = nn.Linear(4, 1)

    def forward(self, x):
        hidden, _ = self.gru(x)
        previous = torch.cat((torch.zeros_like(hidden[:, :1]), hidden[:, :-1]), dim=1)
        return LOW+(HIGH-LOW)*self.head(previous).squeeze(-1).sigmoid()

    def export(self):
        g = self.gru
        tensors = (g.weight_ih_l0, g.weight_hh_l0, g.bias_ih_l0, g.bias_hh_l0,
                   self.head.weight[0], self.head.bias)
        return {key: tensor.detach().tolist() for key, tensor in zip(SHAPES, tensors)}


def fit(tokens, seed, *, epochs=30):
    started = time.perf_counter()
    torch.set_num_threads(2)
    torch.manual_seed(seed)
    model = Net()
    optimizer = torch.optim.Adam(model.parameters(), lr=.01)
    events = torch.from_numpy(tokens.astype(np.int64))
    x = nn.functional.one_hot(events.clamp(min=0), 3).float()
    y = (events == SHOCK).float()
    mask = (events == SHOCK) | (events == CLEAR)
    losses, updates = [], 0
    for _ in range(epochs):
        for ids in torch.randperm(len(tokens)).split(128):
            p = model(x[ids])
            active = mask[ids]
            loss = nn.functional.binary_cross_entropy(p[active], y[ids][active])
            if not torch.isfinite(loss) or time.perf_counter()-started > 120:
                raise RuntimeError("Recurrent fit exceeded its numeric or time budget")
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            updates += 1
        with torch.no_grad():
            p = model(x)
            losses.append(float(nn.functional.binary_cross_entropy(p[mask], y[mask])))
    return {"version": VERSION, "seed": seed, "epochs": epochs, "updates": updates,
            "parameters": model.export(), "train_loss": losses, "elapsed_s": time.perf_counter()-started}


def sigmoid(x):
    return 1/(1+np.exp(-np.clip(x, -60, 60)))


class Predictor:
    initial = (0.,)*4

    def __init__(self, checkpoint):
        if checkpoint.get("version") != VERSION or set(checkpoint["parameters"]) != set(SHAPES):
            raise ValueError("Incompatible recurrent checkpoint")
        self.parameters = {}
        for key, shape in SHAPES.items():
            value = np.array(checkpoint["parameters"][key], dtype=float)
            if value.shape != shape or not np.isfinite(value).all() or np.max(np.abs(value)) > 100:
                raise ValueError("Invalid recurrent checkpoint parameter")
            value.setflags(write=False)
            self.parameters[key] = value

    def probability(self, state):
        p = self.parameters
        return float(LOW+(HIGH-LOW)*sigmoid(p["head"]@state+p["head_bias"][0]))

    def update(self, state, token):
        if token not in (BOUNDARY, SHOCK, CLEAR):
            raise ValueError("Unknown public event")
        p = self.parameters
        x = p["input"][:, token]+p["input_bias"]
        h = p["hidden"]@state+p["hidden_bias"]
        reset = sigmoid(x[:4]+h[:4])
        retain = sigmoid(x[4:8]+h[4:8])
        proposal = np.tanh(x[8:]+reset*h[8:])
        return tuple((1-retain)*proposal+retain*np.asarray(state))


def load(path: Path):
    return Predictor(json.loads(path.read_text(encoding="utf-8")))
