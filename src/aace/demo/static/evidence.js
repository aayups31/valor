/* Plain-language descriptions of recorded evidence. No generated inner monologue. */
"use strict";
(function(root) {
  const plans = {
    direct: ["Continue toward the goal", "Follow the direct route", "→"],
    detour_north: ["Take the upper detour", "Go around the rough ground from above", "↗"],
    detour_south: ["Take the lower detour", "Go around the rough ground from below", "↘"],
    return: ["Head home now", "Aim for home, even if the site is not inspected", "↩"],
    brake: ["Apply the brakes", "Reduce motion with a bounded braking command", "⊙"],
    coast: ["Coast for a moment", "Apply no acceleration; momentum still carries the rover", "⇢"]
  };
  const controllers = {
    heuristic_direct: {title:"Follow the direct route", short:"Direct rule", description:"Heads toward the next goal using a fixed rule.", eyebrow:"THE SIMPLE APPROACH"},
    heuristic_detour: {title:"Take the known detour", short:"Detour rule", description:"Uses a fixed rule to go around the visible rough ground.", eyebrow:"THE DETOUR APPROACH"},
    oracle_planner: {title:"Look before moving", short:"Planner", description:"Tests six possible plans in the simulator before each move.", eyebrow:"THE PLANNING APPROACH"}
  };
  const missions = {
    shortcut:["The risky shortcut.","Inspect the site and return home. Rough ground lies along the shortest route.","The risky shortcut"],
    benign:["A clear path home.","Visit the inspection site and return home on open ground.","Open ground"],
    recoverable_damage:["A little damage. A real tradeoff.","The rough ground is gentler here. Watch how damage affects the rest of the mission.","Gentler rough ground"],
    low_reserve:["Every bit of energy counts.","Start with just 9% battery. Inspection is only half the job: the rover must get home.","Low battery"],
    deadline:["When time is too short.","Only six seconds are available. This mission is deliberately too tight to complete.","An impossible deadline"],
    changed_dynamics:["Same ground. Different consequences.","The central terrain is less damaging and has more grip. Compare the recorded choices.","Less damaging terrain"]
  };
  const statuses = {running:"In progress",completed:"Home safely",actuator_loss:"Unable to move",battery_depleted:"Out of energy",deadline_missed:"Time ran out",time_limit:"Run limit reached"};
  const candidateStatuses = {selected:"Chosen",lower_score:"Lower value",constraint_rejected:"Over the limit",unexplored:"Not tested",selected_fallback:"Braking fallback",guard_overridden:"Action adjusted"};
  const reasons = {
    heuristic_rule:"The fixed rule selected this route. It did not simulate alternatives.",
    no_forecast_budget:"This option was listed but not simulated. There is no forecast to compare.",
    best_admissible_score:"It had the highest recorded mission score among the tested plans that met the demo’s failure rule.",
    lower_score:"It met the demo’s failure rule, but another tested plan had a higher mission score.",
    failure_limit:"Too many sampled futures ended in loss of movement or energy. Their failure frequency exceeded the mission’s limit.",
    no_admissible_plan:"None of the tested plans met the demo’s failure rule, so the planner chose braking as a fallback.",
    external_stop:"You requested braking. The controller was bypassed and a bounded braking action was applied.",
    invalid_action:"The controller’s command was invalid, so the action guard replaced it with braking.",
    action_clipped:"The command exceeded the permitted range. The action guard reduced it before applying it."
  };
  const plan = name => plans[name] || [String(name).replaceAll("_"," "),"Recorded plan","→"];
  const reason = candidate => (candidate.reason_codes || []).map(code=>reasons[code] || code).join(" ");
  function runStory(run) {
    const s=run.observation.state;
    if(s.status==="completed") return "Site inspected. Back home before the deadline.";
    if(s.status==="actuator_loss") return "Damage left the rover unable to move. The mission ended.";
    if(s.status==="battery_depleted") return "The battery ran out before the rover finished its mission.";
    if(s.status==="deadline_missed") return s.inspected ? "The site was inspected, but the rover did not get home in time." : "Time ran out before the inspection was completed.";
    if(s.status==="time_limit") return "The simulation’s step limit was reached.";
    if(!s.step) return "Ready to leave home, inspect the site, and return.";
    if(s.inspected) return s.health<.98 ? "Inspection done. Returning home with lasting damage." : "Inspection done. The next goal is getting home.";
    return s.health<.98 ? "Heading to the site. Damage now reduces movement and raises energy use." : "Heading toward the inspection site.";
  }
  function observed(decision) {
    const before=decision.observation.state, after=decision.actual_outcome.state;
    const events=decision.actual_outcome.events;
    if(after.status!=="running") return runStory({observation:{state:after}});
    if(events.includes("waypoint_inspected")) return "The rover reached the site and completed the inspection. Home is now the goal.";
    if(events.includes("damage")) return "Damage occurred. Movement capacity fell from "+Math.round(before.health*100)+"% to "+Math.round(after.health*100)+"%.";
    if(events.includes("boundary_impact")) return "The rover hit the map boundary. Its velocity was stopped and damage was recorded.";
    const distance=Math.hypot(after.x-before.x,after.y-before.y);
    return "Moved "+distance.toFixed(2)+" map units. Used "+Math.max(0,before.battery-after.battery).toFixed(2)+" battery points. "+(after.inspected?"The return journey continues.":"The inspection is still ahead.");
  }
  function describe(decision) {
    if(!decision) return {title:"See the choice. Then check the result.",summary:"Start the mission or take one decision. The recorded comparisons will appear here.",choice:"Waiting for the first move.",reason:"Reasons come from the recorded calculations.",outcome:"The observed result appears after the move."};
    const selected=decision.candidates.find(c=>c.plan===decision.selected_plan);
    let why=selected?reason(selected):"No candidate reason was recorded.";
    if(decision.guard_reason) why=reasons[decision.guard_reason] || why;
    const name=plan(decision.selected_plan)[0];
    const forecasted=decision.candidates.filter(c=>c.forecast).length;
    const f=(selected && selected.forecast) || (decision.candidates.find(c=>c.forecast) || {}).forecast;
    let summary=forecasted ? "Compared "+forecasted+" plans, with "+f.particles+" sampled futures per plan and up to "+f.horizon_s+" seconds of lookahead. Scores weigh progress, time, energy and damage." : "This move came from a fixed control rule. Alternative plans were not forecast.";
    if(decision.controller_bypassed) summary="Your braking request bypassed the controller. One bounded braking action was applied.";
    else if(decision.guard_reason) summary+=" The action guard adjusted the command before applying it.";
    return {title:name+".",summary,choice:decision.guard_reason&&!decision.controller_bypassed?name+" was proposed; the applied action was adjusted.":name+". Only the next action is applied; later choices can change.",reason:why,outcome:observed(decision)};
  }
  const api={plans,controllers,missions,statuses,candidateStatuses,reasons,plan,reason,runStory,observed,describe};
  if(typeof module!=="undefined" && module.exports) module.exports=api;
  else root.ValorEvidence=api;
})(typeof window!=="undefined" ? window : this);
