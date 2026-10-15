# Traffic case studies

Traffic is fixed in each case. QAOA/BPSO means and sample SD use five solver seeds. Packet traces below use seed 42 consistently, not a selected best trial. Exact J uses minimum peak among tied J optima.

## Strong relief: legacy_n4_07

7. Construction Capacity Reduction Incident. Initial peak **77.83%**; QAOA **56.02% +/- 0.00 pp**; BPSO **56.02% +/- 0.00 pp**. QAOA relative reduction **28.02%**, absolute relief **21.81 pp**.

Exact minimum-J peak: 56.02%; minimum attainable candidate peak: 56.02%. QAOA reached the J ground state in 5/5 trials. Requested/allocated packets: 3/3; budget omissions: 0.

The exact-J reference attains the minimum peak available in this candidate set. Any remaining QAOA objective gap is a solver approximation; remaining congestion also reflects the represented routing choices.

The mean final peak is at or below the 60% trigger; consult individual trials before claiming every run clears congestion.

| Edge | Capacity (veh/hr) | Initial (%) | QAOA mean (%) | BPSO mean (%) | Exact J (%) |
| --- | --- | --- | --- | --- | --- |
| A--B | 1200 | 77.83 | 40.33 | 40.33 | 40.33 |
| A--C | 1900 | 30.03 | 45.82 | 45.82 | 45.82 |
| A--D | 1700 | 41.12 | 49.94 | 49.94 | 49.94 |
| B--C | 1600 | 37.27 | 56.02 | 56.02 | 56.02 |
| B--D | 2400 | 34.57 | 40.82 | 40.82 | 40.82 |
| C--D | 1900 | 37.00 | 37.00 | 37.00 | 37.00 |

Seed-42 QAOA packet trace (each packet carries 150 veh/hr):

| Packet | Origin | Bit | Selected detour |
| --- | --- | --- | --- |
| P1 | A--B | 1 | A -> D -> B |
| P2 | A--B | 0 | A -> C -> B |
| P3 | A--B | 0 | A -> C -> B |

## Strong relief: legacy_n5_07

7. Construction Capacity Reduction Incident. Initial peak **73.88%**; QAOA **48.88% +/- 0.00 pp**; BPSO **48.88% +/- 0.00 pp**. QAOA relative reduction **33.84%**, absolute relief **25.00 pp**.

Exact minimum-J peak: 48.88%; minimum attainable candidate peak: 48.88%. QAOA reached the J ground state in 5/5 trials. Requested/allocated packets: 2/2; budget omissions: 0.

The exact-J reference attains the minimum peak available in this candidate set. Any remaining QAOA objective gap is a solver approximation; remaining congestion also reflects the represented routing choices.

The mean final peak is at or below the 60% trigger; consult individual trials before claiming every run clears congestion.

| Edge | Capacity (veh/hr) | Initial (%) | QAOA mean (%) | BPSO mean (%) | Exact J (%) |
| --- | --- | --- | --- | --- | --- |
| A--B | 2200 | 39.24 | 46.05 | 46.05 | 46.05 |
| A--C | 2000 | 37.65 | 37.65 | 37.65 | 37.65 |
| A--D | 1700 | 42.84 | 42.84 | 42.84 | 42.84 |
| A--E | 1400 | 33.26 | 43.98 | 43.98 | 43.98 |
| B--C | 2200 | 38.39 | 45.21 | 45.21 | 45.21 |
| B--D | 2000 | 41.40 | 41.40 | 41.40 | 41.40 |
| B--E | 1200 | 73.88 | 48.88 | 48.88 | 48.88 |
| C--D | 1600 | 38.62 | 38.62 | 38.62 | 38.62 |
| C--E | 2300 | 35.64 | 42.16 | 42.16 | 42.16 |
| D--E | 1900 | 40.73 | 40.73 | 40.73 | 40.73 |

Seed-42 QAOA packet trace (each packet carries 150 veh/hr):

| Packet | Origin | Bit | Selected detour |
| --- | --- | --- | --- |
| P1 | B--E | 0 | B -> C -> E |
| P2 | B--E | 1 | B -> A -> E |

## Strong relief: legacy_n6_07

7. Construction Capacity Reduction Incident. Initial peak **75.74%**; QAOA **49.70% +/- 0.00 pp**; BPSO **49.70% +/- 0.00 pp**. QAOA relative reduction **34.38%**, absolute relief **26.04 pp**.

Exact minimum-J peak: 49.70%; minimum attainable candidate peak: 49.70%. QAOA reached the J ground state in 5/5 trials. Requested/allocated packets: 3/3; budget omissions: 0.

The exact-J reference attains the minimum peak available in this candidate set. Any remaining QAOA objective gap is a solver approximation; remaining congestion also reflects the represented routing choices.

The mean final peak is at or below the 60% trigger; consult individual trials before claiming every run clears congestion.

| Edge | Capacity (veh/hr) | Initial (%) | QAOA mean (%) | BPSO mean (%) | Exact J (%) |
| --- | --- | --- | --- | --- | --- |
| A--B | 2300 | 34.94 | 47.99 | 47.99 | 47.99 |
| A--C | 1900 | 43.49 | 43.49 | 43.49 | 43.49 |
| A--D | 1800 | 33.03 | 49.70 | 49.70 | 49.70 |
| A--E | 1600 | 31.59 | 31.59 | 31.59 | 31.59 |
| A--F | 2400 | 35.15 | 35.15 | 35.15 | 35.15 |
| B--C | 2000 | 31.41 | 38.91 | 38.91 | 38.91 |
| B--D | 1200 | 75.74 | 38.24 | 38.24 | 38.24 |
| B--E | 1500 | 42.80 | 42.80 | 42.80 | 42.80 |
| B--F | 2400 | 34.46 | 34.46 | 34.46 | 34.46 |
| C--D | 2000 | 38.20 | 45.70 | 45.70 | 45.70 |
| C--E | 1750 | 33.34 | 33.34 | 33.34 | 33.34 |
| C--F | 1500 | 39.35 | 39.35 | 39.35 | 39.35 |
| D--E | 2300 | 31.79 | 31.79 | 31.79 | 31.79 |
| D--F | 1900 | 41.06 | 41.06 | 41.06 | 41.06 |
| E--F | 1700 | 35.92 | 35.92 | 35.92 | 35.92 |

Seed-42 QAOA packet trace (each packet carries 150 veh/hr):

| Packet | Origin | Bit | Selected detour |
| --- | --- | --- | --- |
| P1 | B--D | 1 | B -> C -> D |
| P2 | B--D | 0 | B -> A -> D |
| P3 | B--D | 0 | B -> A -> D |

## Marginal relief: legacy_n5_09

9. School Zone Perimeter Dropoff. Initial peak **84.45%**; QAOA **81.57% +/- 0.00 pp**; BPSO **81.57% +/- 0.00 pp**. QAOA relative reduction **3.42%**, absolute relief **2.89 pp**.

Exact minimum-J peak: 81.57%; minimum attainable candidate peak: 81.57%. QAOA reached the J ground state in 5/5 trials. Requested/allocated packets: 10/10; budget omissions: 0.

The exact-J reference attains the minimum peak available in this candidate set. Any remaining QAOA objective gap is a solver approximation; remaining congestion also reflects the represented routing choices.

The mean final peak remains above the 60% trigger.

| Edge | Capacity (veh/hr) | Initial (%) | QAOA mean (%) | BPSO mean (%) | Exact J (%) |
| --- | --- | --- | --- | --- | --- |
| A--B | 2400 | 73.65 | 48.65 | 48.65 | 48.65 |
| A--C | 1900 | 39.28 | 78.76 | 78.76 | 78.76 |
| A--D | 1800 | 41.48 | 41.48 | 41.48 | 41.48 |
| A--E | 1600 | 36.62 | 64.75 | 64.75 | 64.75 |
| B--C | 2400 | 37.82 | 81.57 | 81.57 | 81.57 |
| B--D | 1900 | 43.42 | 43.42 | 43.42 | 43.42 |
| B--E | 1800 | 39.78 | 81.45 | 81.45 | 81.45 |
| C--D | 1400 | 40.43 | 40.43 | 40.43 | 40.43 |
| C--E | 2400 | 84.45 | 46.95 | 46.95 | 46.95 |
| D--E | 1800 | 33.02 | 33.02 | 33.02 | 33.02 |

Seed-42 QAOA packet trace (each packet carries 150 veh/hr):

| Packet | Origin | Bit | Selected detour |
| --- | --- | --- | --- |
| P1 | A--B | 0 | A -> C -> B |
| P2 | A--B | 1 | A -> E -> B |
| P3 | A--B | 0 | A -> C -> B |
| P4 | A--B | 0 | A -> C -> B |
| P5 | C--E | 1 | C -> B -> E |
| P6 | C--E | 1 | C -> B -> E |
| P7 | C--E | 1 | C -> B -> E |
| P8 | C--E | 1 | C -> B -> E |
| P9 | C--E | 0 | C -> A -> E |
| P10 | C--E | 0 | C -> A -> E |

## Marginal relief: legacy_n5_05

5. Radial Outbound Evening Egress Surge. Initial peak **77.83%**; QAOA **75.11% +/- 0.00 pp**; BPSO **75.11% +/- 0.00 pp**. QAOA relative reduction **3.50%**, absolute relief **2.72 pp**.

Exact minimum-J peak: 75.11%; minimum attainable candidate peak: 75.11%. QAOA reached the J ground state in 5/5 trials. Requested/allocated packets: 9/9; budget omissions: 0.

The exact-J reference attains the minimum peak available in this candidate set. Any remaining QAOA objective gap is a solver approximation; remaining congestion also reflects the represented routing choices.

The mean final peak remains above the 60% trigger.

| Edge | Capacity (veh/hr) | Initial (%) | QAOA mean (%) | BPSO mean (%) | Exact J (%) |
| --- | --- | --- | --- | --- | --- |
| A--B | 2400 | 43.86 | 75.11 | 75.11 | 75.11 |
| A--C | 1900 | 30.82 | 62.40 | 62.40 | 62.40 |
| A--D | 1800 | 35.02 | 35.02 | 35.02 | 35.02 |
| A--E | 1400 | 40.22 | 50.94 | 50.94 | 50.94 |
| B--C | 2400 | 76.40 | 45.15 | 45.15 | 45.15 |
| B--D | 1900 | 37.94 | 69.52 | 69.52 | 69.52 |
| B--E | 1700 | 77.83 | 42.54 | 42.54 | 42.54 |
| C--D | 1400 | 40.84 | 51.55 | 51.55 | 51.55 |
| C--E | 2200 | 43.42 | 43.42 | 43.42 | 43.42 |
| D--E | 2000 | 42.44 | 64.94 | 64.94 | 64.94 |

Seed-42 QAOA packet trace (each packet carries 150 veh/hr):

| Packet | Origin | Bit | Selected detour |
| --- | --- | --- | --- |
| P1 | B--C | 1 | B -> A -> C |
| P2 | B--C | 0 | B -> D -> C |
| P3 | B--C | 1 | B -> A -> C |
| P4 | B--C | 1 | B -> A -> C |
| P5 | B--C | 1 | B -> A -> C |
| P6 | B--E | 0 | B -> D -> E |
| P7 | B--E | 0 | B -> D -> E |
| P8 | B--E | 1 | B -> A -> E |
| P9 | B--E | 0 | B -> D -> E |

## Deterioration: legacy_n4_05

5. Radial Outbound Evening Egress Surge. Initial peak **81.81%**; QAOA **83.66% +/- 0.00 pp**; BPSO **83.66% +/- 0.00 pp**. QAOA relative reduction **-2.26%**, absolute relief **-1.85 pp**.

Exact minimum-J peak: 83.66%; minimum attainable candidate peak: 83.66%. QAOA reached the J ground state in 5/5 trials. Requested/allocated packets: 10/10; budget omissions: 0.

Every represented routing assignment has a higher peak than the unmanaged input. The current mandatory-detour candidate set cannot preserve the original state in this case.

The mean final peak remains above the 60% trigger.

| Edge | Capacity (veh/hr) | Initial (%) | QAOA mean (%) | BPSO mean (%) | Exact J (%) |
| --- | --- | --- | --- | --- | --- |
| A--B | 2400 | 76.47 | 57.72 | 57.72 | 57.72 |
| A--C | 1900 | 39.74 | 55.53 | 55.53 | 55.53 |
| A--D | 1750 | 34.39 | 77.25 | 77.25 | 77.25 |
| B--C | 1500 | 33.66 | 83.66 | 83.66 | 83.66 |
| B--D | 2300 | 81.81 | 68.77 | 68.77 | 68.77 |
| C--D | 2000 | 33.19 | 55.69 | 55.69 | 55.69 |

Seed-42 QAOA packet trace (each packet carries 150 veh/hr):

| Packet | Origin | Bit | Selected detour |
| --- | --- | --- | --- |
| P1 | A--B | 0 | A -> C -> B |
| P2 | A--B | 0 | A -> C -> B |
| P3 | A--B | 1 | A -> D -> B |
| P4 | A--B | 1 | A -> D -> B |
| P5 | A--B | 1 | A -> D -> B |
| P6 | B--D | 1 | B -> A -> D |
| P7 | B--D | 1 | B -> A -> D |
| P8 | B--D | 0 | B -> C -> D |
| P9 | B--D | 0 | B -> C -> D |
| P10 | B--D | 0 | B -> C -> D |

## Deterioration: legacy_n4_11

11. Inclement Weather Network Slowdown. Initial peak **84.84%**; QAOA **91.66% +/- 0.00 pp**; BPSO **91.66% +/- 0.00 pp**. QAOA relative reduction **-8.04%**, absolute relief **-6.82 pp**.

Exact minimum-J peak: 91.66%; minimum attainable candidate peak: 91.66%. QAOA reached the J ground state in 5/5 trials. Requested/allocated packets: 15/10; budget omissions: 5.

Every represented routing assignment has a higher peak than the unmanaged input. The current mandatory-detour candidate set cannot preserve the original state in this case.

The mean final peak remains above the 60% trigger.

| Edge | Capacity (veh/hr) | Initial (%) | QAOA mean (%) | BPSO mean (%) | Exact J (%) |
| --- | --- | --- | --- | --- | --- |
| A--B | 2200 | 83.03 | 55.75 | 55.75 | 55.75 |
| A--C | 2000 | 38.94 | 91.45 | 91.45 | 91.45 |
| A--D | 1700 | 81.24 | 72.41 | 72.41 | 72.41 |
| B--C | 1400 | 37.64 | 69.79 | 69.79 | 69.79 |
| B--D | 2200 | 84.84 | 91.66 | 91.66 | 91.66 |
| C--D | 2000 | 33.27 | 63.27 | 63.27 | 63.26 |

Seed-42 QAOA packet trace (each packet carries 150 veh/hr):

| Packet | Origin | Bit | Selected detour |
| --- | --- | --- | --- |
| P1 | A--B | 0 | A -> C -> B |
| P2 | A--B | 1 | A -> D -> B |
| P3 | A--B | 0 | A -> C -> B |
| P4 | A--B | 0 | A -> C -> B |
| P5 | A--B | 1 | A -> D -> B |
| P6 | A--D | 0 | A -> C -> D |
| P7 | A--D | 0 | A -> C -> D |
| P8 | A--D | 0 | A -> C -> D |
| P9 | A--D | 0 | A -> C -> D |
| P10 | B--D | 1 | B -> A -> D |

## Deterioration: legacy_n4_14

14. Distributed Triple Bottleneck Peak. Initial peak **84.34%**; QAOA **89.44% +/- 0.00 pp**; BPSO **89.44% +/- 0.00 pp**. QAOA relative reduction **-6.05%**, absolute relief **-5.10 pp**.

Exact minimum-J peak: 89.44%; minimum attainable candidate peak: 81.54%. QAOA reached the J ground state in 5/5 trials. Requested/allocated packets: 11/10; budget omissions: 1.

A lower-peak candidate exists than the one preferred by the exact QUBO objective. This is direct evidence that minimizing J and minimizing peak congestion differ here.

The mean final peak remains above the 60% trigger.

| Edge | Capacity (veh/hr) | Initial (%) | QAOA mean (%) | BPSO mean (%) | Exact J (%) |
| --- | --- | --- | --- | --- | --- |
| A--B | 2400 | 39.23 | 64.23 | 64.23 | 64.23 |
| A--C | 1900 | 84.34 | 68.55 | 68.55 | 68.55 |
| A--D | 1750 | 34.97 | 69.26 | 69.26 | 69.26 |
| B--C | 1400 | 76.46 | 76.46 | 76.46 | 76.46 |
| B--D | 2400 | 34.39 | 46.89 | 46.89 | 46.89 |
| C--D | 1900 | 73.65 | 89.44 | 89.44 | 89.44 |

Seed-42 QAOA packet trace (each packet carries 150 veh/hr):

| Packet | Origin | Bit | Selected detour |
| --- | --- | --- | --- |
| P1 | A--C | 0 | A -> D -> C |
| P2 | A--C | 1 | A -> B -> C |
| P3 | A--C | 1 | A -> B -> C |
| P4 | A--C | 0 | A -> D -> C |
| P5 | A--C | 1 | A -> B -> C |
| P6 | B--C | 1 | B -> A -> C |
| P7 | B--C | 0 | B -> D -> C |
| P8 | B--C | 0 | B -> D -> C |
| P9 | C--D | 1 | C -> A -> D |
| P10 | C--D | 1 | C -> A -> D |

## Deterioration: legacy_n6_11

11. Inclement Weather Network Slowdown. Initial peak **78.79%**; QAOA **90.87% +/- 0.00 pp**; BPSO **90.87% +/- 0.00 pp**. QAOA relative reduction **-15.34%**, absolute relief **-12.08 pp**.

Exact minimum-J peak: 90.87%; minimum attainable candidate peak: 90.87%. QAOA reached the J ground state in 5/5 trials. Requested/allocated packets: 11/10; budget omissions: 1.

Every represented routing assignment has a higher peak than the unmanaged input. The current mandatory-detour candidate set cannot preserve the original state in this case.

The mean final peak remains above the 60% trigger.

| Edge | Capacity (veh/hr) | Initial (%) | QAOA mean (%) | BPSO mean (%) | Exact J (%) |
| --- | --- | --- | --- | --- | --- |
| A--B | 2300 | 37.97 | 37.97 | 37.97 | 37.97 |
| A--C | 1800 | 36.83 | 53.49 | 53.49 | 53.49 |
| A--D | 1750 | 35.17 | 52.31 | 52.31 | 52.31 |
| A--E | 1500 | 34.13 | 84.13 | 84.13 | 84.13 |
| A--F | 2200 | 39.50 | 46.32 | 46.32 | 46.32 |
| B--C | 2000 | 35.12 | 50.12 | 50.12 | 50.12 |
| B--D | 1700 | 36.09 | 53.74 | 53.74 | 53.74 |
| B--E | 1500 | 40.87 | 90.87 | 90.87 | 90.87 |
| B--F | 2200 | 43.25 | 50.06 | 50.06 | 50.06 |
| C--D | 2000 | 43.91 | 43.91 | 43.91 | 43.91 |
| C--E | 1750 | 78.79 | 44.50 | 44.50 | 44.50 |
| C--F | 1400 | 31.94 | 31.94 | 31.94 | 31.94 |
| D--E | 2200 | 72.35 | 45.08 | 45.08 | 45.08 |
| D--F | 1800 | 36.93 | 36.93 | 36.93 | 36.93 |
| E--F | 1800 | 73.07 | 56.40 | 56.40 | 56.40 |

Seed-42 QAOA packet trace (each packet carries 150 veh/hr):

| Packet | Origin | Bit | Selected detour |
| --- | --- | --- | --- |
| P1 | C--E | 0 | C -> A -> E |
| P2 | C--E | 1 | C -> B -> E |
| P3 | C--E | 1 | C -> B -> E |
| P4 | C--E | 0 | C -> A -> E |
| P5 | D--E | 0 | D -> A -> E |
| P6 | D--E | 0 | D -> A -> E |
| P7 | D--E | 1 | D -> B -> E |
| P8 | D--E | 1 | D -> B -> E |
| P9 | E--F | 0 | E -> A -> F |
| P10 | E--F | 1 | E -> B -> F |
