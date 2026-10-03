# Research Questions

## Survival representation

1. Is continued viability best represented as probability of no catastrophe, distance from a viability set, future option count, or a learned latent variable?
2. Should “death” be an absorbing state, a severe cost, a terminal event in survival analysis, or all three?
3. Can the agent infer a viability envelope from experience instead of having boundaries given explicitly?
4. How should severity and recoverability interact? A low-probability irreversible failure may matter more than a likely recoverable one.

## Fear / threat

5. Should fear be a scalar or vector of threats?
6. How calibrated must risk estimates be before mode switching is useful?
7. Can threat estimates generalize to unseen hazards through latent dynamics rather than surface similarity?
8. How should epistemic uncertainty influence fear without making the agent terrified of everything unfamiliar?

## Regime switching

9. Are discrete modes better than a continuous risk-conditioned policy?
10. What hysteresis prevents chattering without delaying emergency response?
11. Should critical mode be a separate policy, planner, or constrained action set?
12. Can the system learn mode thresholds rather than hand-tune them?

## Adaptive compute

13. Does allocating more rollouts under threat outperform fixed compute at equal average cost?
14. What signal best predicts when more planning is worth the latency?
15. Can adaptive compute itself become unsafe because danger causes decision delay?

## Counterfactual guilt

16. Which past action caused the failure versus merely correlated with it?
17. How far back should the system search?
18. How should it represent uncertainty in counterfactual outcomes?
19. Should the memory store the best alternative action or the causal principle behind it?
20. Can one failure create useful avoidance without overgeneralizing fear?

## Memory

21. How should scars decay?
22. How should contradictory scars be merged?
23. Can scars be poisoned by model error?
24. How should memory retrieve by causal structure rather than visual/state similarity?
25. Is a dedicated scar system better than prioritized replay or episodic control?

## Safety

26. How does AACE fail under an adversarial or badly calibrated world model?
27. How should formal shields interact with affective modes?
28. Can the learned system become too conservative and abandon tasks unnecessarily?
29. Can self-preservation conflict with human instructions or external objectives? How is human authority kept lexicographically above machine self-preservation?
30. What must be hard-coded as non-negotiable safety policy rather than learned?

## Generalization

31. What counts as a genuinely novel hazard?
32. Can the same survival abstraction work in robotics and network infrastructure?
33. Which components transfer across domains: risk estimator, memory representation, mode controller, or none?
34. Can scars transfer between agents with different embodiments?

## Scientific novelty

35. Does AACE beat SafeDreamer when both have equal world-model capacity?
36. Does AACE beat a CVaR objective when average compute and data are equal?
37. Does mode switching matter once a strong recovery policy exists?
38. Does counterfactual reflection matter once prioritized replay exists?
39. Is “survival intelligence” a coherent measurable construct or just a bundle of safety tricks?


## Deliberate risk and consequence awareness

40. Can AACE distinguish the safest action from the best authorized action?
41. How should the system compare consequences of action, delay, retreat, and inaction?
42. Can the same physical danger be rejected under low stakes and accepted under high stakes without changing the hard safety envelope?
43. What representation best distinguishes calculated risk from recklessness?
44. Can a learned scar increase caution without becoming a permanent veto?
45. After a prior catastrophe, can the system deliberately repeat a structurally similar action when current consequences justify it?
46. Can world-model rollouts predict persistent capability loss before the agent experiences the exact failure?
47. Does threat-focused imagination improve tail-risk calibration or simply amplify model error?
48. How should mission urgency affect self-preservation weight without creating unstable objective switching?
49. What forms of controlled sacrifice can be safely specified as externally authorized test cases?
50. Can consequence-aware decision making outperform both reward maximization and monotonic risk minimization on matched dilemma suites?
