"""Public-history forgetting/change controls with selection-only settings."""

import math
import time

import numpy as np

from aace.benchmarks.history import HIGH, LOW


def predict_control(sequence, specification, prior):
    history,query = sequence[:,:-1],sequence[:,-1]
    cue = history[:,:,:2].argmax(axis=2)
    observed = history[:,:,2]/.25
    selected = query[:,:2].argmax(axis=1)
    kind = specification["kind"]
    strength = specification.get("strength",2)
    count = len(sequence)
    if kind in ("counts","forgetting","window"):
        age = np.arange(history.shape[1]-1,-1,-1)
        weights = np.ones(history.shape[1])
        if kind == "forgetting":
            weights = specification["decay"]**age
        elif kind == "window":
            weights = (age < specification["window"]).astype(float)
        matched = history[:,:,:2]*weights[None,:,None]
        exposure = matched.sum(axis=1)
        damage = (matched*observed[:,:,None]).sum(axis=1)
        return ((damage+strength*prior)/(exposure+strength))[np.arange(count),selected]
    if kind == "cusum":
        exposure = np.zeros((count,2));damage = np.zeros((count,2))
        up = np.zeros((count,2));down = np.zeros((count,2));indices = np.arange(count)
        for step in range(history.shape[1]):
            current = cue[:,step];outcome = observed[:,step]
            mean = (damage[indices,current]+strength*prior)/(exposure[indices,current]+strength)
            up[indices,current] = np.maximum(0,up[indices,current]+outcome-mean-.05)
            down[indices,current] = np.maximum(0,down[indices,current]+mean-outcome-.05)
            reset = np.maximum(up[indices,current],down[indices,current]) > specification["threshold"]
            exposure[indices,current] = np.where(reset,0,exposure[indices,current])+1
            damage[indices,current] = np.where(reset,0,damage[indices,current])+outcome
            up[indices,current] = np.where(reset,0,up[indices,current])
            down[indices,current] = np.where(reset,0,down[indices,current])
        return ((damage+strength*prior)/(exposure+strength))[indices,selected]
    if kind == "markov_bayes":
        hazard = specification["hazard"]
        transition = np.full((3,3),hazard/2);np.fill_diagonal(transition,1-hazard)
        posterior = np.full((count,3),1/3)
        for step in range(history.shape[1]):
            probabilities = np.column_stack((np.where(cue[:,step]==0,HIGH,LOW),
                                              np.where(cue[:,step]==1,HIGH,LOW),np.full(count,LOW)))
            likelihood = np.where(observed[:,step,None]==1,probabilities,1-probabilities)
            posterior *= likelihood;posterior /= posterior.sum(axis=1,keepdims=True)
            posterior = posterior@transition
        probabilities = np.column_stack((np.where(selected==0,HIGH,LOW),np.where(selected==1,HIGH,LOW),np.full(count,LOW)))
        return (posterior*probabilities).sum(axis=1)
    raise ValueError("Unknown adaptive control")


def control_grids():
    return {
        "cue_counts":[{"kind":"counts","strength":s} for s in (1,2,4)],
        "forgetting_counts":[{"kind":"forgetting","strength":s,"decay":d} for d in (.5,.75,.9,1.) for s in (1,2,4)],
        "window_counts":[{"kind":"window","strength":s,"window":w} for w in (2,4,8,12) for s in (1,2,4)],
        "change_detector":[{"kind":"cusum","strength":2,"threshold":t} for t in (.75,1.25,2.)],
        "markov_bayes_reference":[{"kind":"markov_bayes","hazard":h} for h in (0.,.05,.15,.3)]}


def validate_controls(state):
    grids=control_grids()
    if type(state.get("prior")) not in (int,float) or not math.isfinite(state["prior"]) or not 0 < state["prior"] < 1:
        raise ValueError("Invalid adaptive control prior")
    if set(state.get("settings",{})) != set(grids) or set(state.get("selection_trials",{})) != set(grids) or state.get("selection_opportunities") != {name:len(grid) for name,grid in grids.items()}:
        raise ValueError("Adaptive control selection contract mismatch")
    for family,grid in grids.items():
        trials=state["selection_trials"][family]
        if len(trials)!=len(grid) or [t.get("setting") for t in trials]!=grid or any(type(t.get("selection_log_loss")) not in (int,float) or not math.isfinite(t["selection_log_loss"]) or t["selection_log_loss"]<0 for t in trials):
            raise ValueError("Invalid adaptive control selection trial")
        if state["settings"][family] != min(trials,key=lambda t:t["selection_log_loss"])["setting"]:
            raise ValueError("Adaptive control was not selected by recorded selection loss")


def fit_controls(training_labels, selection_sequence, selection_labels):
    started = time.perf_counter()
    prior = min(1-1e-4,max(1e-4,float(training_labels.mean())))
    grids=control_grids()
    settings,scores = {},{}
    for family,grid in grids.items():
        trials=[]
        for spec in grid:
            probability = np.clip(predict_control(selection_sequence,spec,prior),1e-7,1-1e-7)
            loss = float(np.mean(-selection_labels*np.log(probability)-(1-selection_labels)*np.log(1-probability)))
            if not math.isfinite(loss):
                raise ValueError("Nonfinite control selection loss")
            trials.append({"setting":spec,"selection_log_loss":loss})
        best = min(trials,key=lambda t:t["selection_log_loss"])
        settings[family]=best["setting"];scores[family]=trials
    return {"prior":prior,"settings":settings,"selection_trials":scores,
            "selection_opportunities":{name:len(grid) for name,grid in grids.items()},
            "selection_elapsed_s":time.perf_counter()-started,
            "notice":"Selection labels only; no check access. Different search/computation budgets are recorded, not equalized."}
