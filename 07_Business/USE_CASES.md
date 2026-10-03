# Use Cases and How the Abstraction Changes by Domain

## Autonomous field robotics

**Viability:** battery, localization, actuator health, temperature, stability, recoverability.

**Catastrophe:** rollover, collision, immobilization, unrecoverable battery depletion, loss of localization in unsafe area.

**Recovery:** retreat, safe stop, re-localize, return to dock, reduced-performance mode.

**Value:** fewer stranded/damaged assets and fewer repeated edge-case failures.

## Subsea / remote inspection

**Viability:** energy reserve, pressure integrity, tether/communication state, propulsion health.

**Catastrophe:** unrecoverable entanglement, loss of propulsion, unsafe depth/pressure, insufficient return energy.

**AACE advantage hypothesis:** actions should be evaluated by recoverability and return margin, not only mission progress.

## Space / remote exploration

**Viability:** thermal, power, communication windows, wheel/actuator health, safe-haven reachability.

**Catastrophe:** loss of power, thermal runaway, unrecoverable terrain trap.

**Important:** extremely conservative validation and independent flight-safety controls required.

## Industrial autonomous vehicles

**Viability:** braking, traction, battery, route recoverability, sensor confidence.

**Catastrophe:** collision, immobilization, entering unsafe zone.

**Value:** fewer interventions and higher uptime without simply slowing everything down.

## Power-grid operation

**Viability:** frequency/voltage/security margins and topology recoverability.

**Catastrophe:** cascading violations or service loss.

**Recovery:** reconfiguration to secure state.

**Research value:** proves the concept is not robot-specific.

## Network / cloud infrastructure

**Viability:** latency, redundancy, service health, data integrity, rollback capability.

**Catastrophe:** cascading outage, unrecoverable data corruption, security compromise.

**Recovery:** isolate, fail over, rollback, rate limit.

**Caution:** cyber/infrastructure control should begin in shadow/advisory mode with strict pre-authorized actions.

## Human performance training

**Viability variable belongs to the human, not the machine.** This is therefore a different ethical and scientific category. Physiological stress signals could adapt scenario difficulty, but the system should not optimize “breaking” the person. The objective would need to be safe training within expert-defined physiological/psychological limits. This should not be the initial AACE program.
