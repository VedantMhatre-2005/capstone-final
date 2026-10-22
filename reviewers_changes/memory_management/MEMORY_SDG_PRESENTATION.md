# Memory management: Presentation Content

## Paragraph for presentation

Our traffic-management framework controls memory requirements through a compact STQGCN forecasting model and a bounded QUBO rerouting problem. In the saved hierarchical bidirectional model pair, STQGCN contains 2,476 FP32 weight values, occupying 9.67 KiB, compared with 483,004 values and 1.84 MiB for the LSTM baseline. This represents 99.49% lower model-weight storage. The primary rerouting experiments also limit each QAOA problem to 10 binary decisions, bounding the size of the simulated quantum state. These design choices align with SDG 9, particularly Target 9.5 on technological research and innovation, and have a potential supporting connection to SDG 12, Target 12.2 on resource efficiency. We report model storage and theoretical state-array memory separately from total application RAM.

## Bullet points for a slide

- **Compact forecasting weights:** hierarchical bidirectional STQGCN, K=6, stores **2,476 FP32 values**, compared with **483,004** for the matching LSTM baseline.
- **Weight-storage reduction:** **9,904 bytes (9.67 KiB)** versus **1,932,016 bytes (1.84 MiB)**, giving **99.49% less weight storage**, or approximately **195 times smaller**.
- **Bounded optimization size:** the primary QAOA benchmark uses **at most 10 qubits/binary decisions** per traffic instance. The separately labeled budget diagnostics test larger caps.
- **Simulation-memory estimate:** a single complex128 pure-state array needs **16 x 2^n bytes**. This is **16 KiB at 10 qubits**, **16 MiB at 20 qubits**, and **16 GiB at 30 qubits**, before framework and workspace overhead. Every additional qubit doubles this array's memory.
- **SDG mapping:** **SDG 9 / Target 9.5** supports the project's technological research and innovation. **SDG 12 / Target 12.2** is an indirect resource-efficiency alignment; reduced hardware/material use has not been measured.
- **Global sustainability context:** the ITU/UNITAR _Global E-waste Monitor 2024_ reports **62 million tonnes of e-waste generated in 2022**, with only **22.3% documented as formally collected and recycled**. These are global context statistics, not waste reductions achieved by our project.

## What to say if industry experts ask about the numbers

**Does the project use 99.49% less total RAM?**

No. This comparison is for stored FP32 model-weight payloads in the selected matching hierarchical bidirectional checkpoint pair. It excludes activations, gradients, Adam optimizer state, datasets, quantum-simulation buffers and framework/interpreter overhead. Total peak RAM was not profiled for this presentation.

**Are you counting only quantum parameters?**

No. The STQGCN total includes classical and quantum weights. The K=6 hierarchical model has 2,422 classical parameters plus 54 variational quantum parameters, totaling 2,476. The model definition uses three zone qubits and six layers: 3 x 3 x 6 = 54 quantum parameters.

**How were the storage figures verified?**

The ZIP-format PyTorch checkpoints were inspected without unpickling or executing them. Their tensor storage records identify FloatStorage, and the stored raw tensor byte counts are 9,904 and 1,932,016. Both training scripts save model.state_dict(). The reported KiB/MiB values exclude checkpoint-container metadata; actual checkpoint file sizes are separately recorded in memory_statistics.json.

**Does mini-batching mean the dataset is streamed from disk?**

No. The current scripts load datasets and normalized arrays into memory, then use DataLoader mini-batches of 64 for model computation. Mini-batching limits the active computation batch, but the current implementation still keeps datasets and additional arrays resident. Do not describe this as out-of-core streaming.

**Is the quantum method proven to use less memory than classical optimization?**

No such comparison was measured. The 10-qubit limit controls the problem size. Classical simulation of quantum states itself grows exponentially with qubit count, so fewer neural-network weights alone do not establish lower end-to-end memory consumption. These are compact-instance simulator experiments; hardware control-system memory is outside this estimate.

**Do smaller weights establish an SDG outcome?**

They provide an engineering measurement that supports the stated design alignment. They do not quantify changes in official UN SDG indicators, device replacement, natural-resource extraction, energy consumption, or e-waste generation. Reuse of existing hardware is a possible future deployment benefit requiring validation.

## Sources and calculation

Local evidence:

- `prediction-final/Traffic Forecasting/Hierarchical Network/Bidirectional/STQGCN/hierarchical_bidirectional_stqgcn_K6_model.pt`
- `prediction-final/Traffic Forecasting/Hierarchical Network/Bidirectional/LSTM/hierarchical_bidirectional_lstm_model.pt`
- Corresponding `train_stqgcn.py` and `train_lstm.py` model definitions.
- `reviewers_changes/traffic_scenarios/experiment.py`: primary packet cap of 10.
- `memory_statistics.json`: exact byte counts, checkpoint hashes, and state-array calculations.

Weight-storage reduction = 100 x (1 - 9,904 / 1,932,016) = **99.4873748458%**.

International sources, checked 22 October 2026:

- [United Nations: SDG 9, Target 9.5](https://sdgs.un.org/goals/goal9)
- [United Nations: SDG 12, Target 12.2](https://sdgs.un.org/goals/goal12)
- [ITU/UNITAR: Global E-waste Monitor 2024, 2022 statistics](https://www.itu.int/en/ITU-D/Environment/Pages/Publications/The-Global-E-waste-Monitor-2024.aspx)
- [Qiskit Aer documentation: double-precision statevector memory scaling](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html)
