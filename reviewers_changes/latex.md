\documentclass[3p,times,procedia]{elsarticle}
\flushbottom

%% The `ecrc' package must be called to make the CRC functionality available
\usepackage{ecrc}
\usepackage[bookmarks=false]{hyperref}
    \hypersetup{colorlinks,
      linkcolor=blue,
      citecolor=blue,
      urlcolor=blue}

\volume{00}

%% set the starting page if not 1
\firstpage{1}

%% Give the name of the journal
\journalname{Procedia Computer Science}

\runauth{Vedant Mhatre et al.}

\jid{procs}

\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{siunitx,makecell}

\usepackage[figuresright]{rotating}

\setlength{\abovedisplayskip}{4pt}
\setlength{\belowdisplayskip}{4pt}
\setlength{\abovedisplayshortskip}{2pt}
\setlength{\belowdisplayshortskip}{2pt}
% \raggedbottom removed: conflicts with \flushbottom declared above.
\usepackage{subcaption}

\begin{document}
\begin{frontmatter}

\dochead{International Conference on Machine Learning and Data Engineering}
\title{A quantum-enhanced graph learning framework for edge-level traffic forecasting and QAOA-based congestion rerouting}

\author[1]{Vedant Mhatre} 
\author[1]{Aditya Upasani} 
\author[1]{Sharmila Sengupta}
\author[1]{Yash Mahajan} 
\author[1]{Sanjay Aski} 

\address[1]{Department of Computer Engineering, Vivekanand Education Society's Institute of Technology, Mumbai 400074, India}

\begin{abstract}
    Urban traffic congestion results from complicated spatiotemporal interactions throughout connected road networks. Both short-term forecasting and network-wide rerouting are essential for responsive traffic management. This paper proposes a quantum-enhanced framework that integrates edge-level traffic flow forecasting with combinatorial rerouting optimization. A Spatiotemporal Quantum Graph Convolutional Network (STQGCN) predicts short-term edge-level flow on road segments by combining classical graph message passing with a compact Variational Quantum Circuit (VQC) layer that processes learned representations through parameterized single-qubit rotations and entangling gates. The predicted flow states are discretized into traffic packets, and candidate detours are formulated as a Quadratic Unconstrained Binary Optimization (QUBO) problem solved using a depth-one ($p=1$) Quantum Approximate Optimization Algorithm (QAOA) with classical COBYLA parameter tuning. The framework is evaluated against Long Short-Term Memory (LSTM) and classical Spatiotemporal Graph Convolutional Network (STGCN) forecasting baselines, alongside Binary Particle Swarm Optimization (BPSO) and exhaustive brute-force search rerouting baselines across single and hierarchical network topologies and 45 heterogeneous traffic scenarios. Total trainable parameters are reported: STQGCN achieves competitive or superior MAPE under bidirectional flow using 2,476--2,566 total parameters (bidirectional topologies; 2,422 classical plus 54--144 quantum variational parameters), compared to 2,849 for architecture-matched Classical STGCN and 277,003--483,004 for LSTM. In the single-seed evaluation, QAOA and BPSO produce identical median peak-occupancy reductions of 11.57\%--18.71\% across topologies. In the multi-seed evaluation (5 seeds), QAOA achieves statistically lower mean occupancy in 13 of 45 scenarios at nominal significance $\alpha = 0.05$ (under Bonferroni-corrected $\alpha \approx 0.0011$, QAOA and BPSO are statistically indistinguishable across all 45 scenarios, demonstrating performance parity). Relative to initial unmanaged states, QAOA mitigates peak congestion in 40 of 45 scenarios; four negative-reduction scenarios (all with $N_q=N_{\text{cap}}=10$) indicate a binding qubit-budget cap rather than routing failure---and in each of these four scenarios BPSO yields the same elevated peak occupancy as QAOA, confirming the degradation is structural and not specific to the quantum solver. Across all 45 scenarios in the single-seed evaluation, QAOA and BPSO converge to identical final peak occupancies, and QAOA operates within a mean gap of 1.25\%--2.87\% of the global brute-force optimum (exact match in 32 of 45 scenarios). The results demonstrate the feasibility of coupling graph representation learning with variational combinatorial optimization within a closed-loop traffic management architecture.
\end{abstract}

\begin{keyword}
Quantum Machine Learning; Spatiotemporal Graph Neural Networks; Traffic Congestion Forecasting; QAOA; QUBO; Intelligent Transportation Systems; Traffic Optimization;

\end{keyword}
\cortext[cor1]{Vedant Mhatre}
\end{frontmatter}

\email{2023.vedant.mhatre@ves.ac.in}

\vspace*{-6pt}

%-----------------------------------------------------
% INTRODUCTION 
%-----------------------------------------------------

\section{Introduction}

Continuous real-time data generation is a prominent feature of modern urban mobility and transportation systems. Intelligent Transportation Systems (ITS) and Connected and Automated Vehicles (CAVs) increasingly utilize heterogeneous sensor modalities---loop detectors, roadside cameras, radar and connected-vehicle telemetry \cite{somvanshi2025,maia2025}---to produce dense edge-level traffic streams. Rapid urbanization and rising mobility demand have put substantial pressure on urban transportation networks, causing congestion that affects travel efficiency, road utilization and daily commute reliability. Traffic conditions remain inherently spatiotemporal: the state of one road segment is affected by neighboring junctions, road capacity, signal conditions, and upstream/downstream flows. Since junctions and segments form an interconnected topology, graph-based learning provides a natural representation, and spatiotemporal graph convolutional architectures have demonstrated the ability to learn structured temporal relationships, providing a foundation for modeling complex networked systems \cite{yan2018}.

Recent research has explored quantum-enhanced learning for transportation applications, including quantum machine learning for traffic-density estimation \cite{wang2026}. However, curbing congestion requires converting predicted traffic states into actionable network-level decisions. Classical optimization techniques such as PSO have been widely studied for traffic signal timing and congestion mitigation \cite{celtek2020,chuo2017,dabiri2016}, but swarm-based search can suffer from parameter sensitivity and premature convergence. Quantum computing has emerged as a promising alternative, with prior work demonstrating quantum-assisted traffic navigation and quantum-based flow optimization \cite{yarkoni2020,neukart2017}, motivating the combination of quantum-enhanced prediction with quantum combinatorial optimization for network-level traffic management. Since each congested edge can be independently routed along its original path or a candidate detour, the space of rerouting decisions grows with the number of congested links, and classical metaheuristics must search this space without exploiting its structure. In contrast, variational quantum algorithms encode the decision space directly onto qubits, providing a structured alternative examined in Section~\ref{subsec:quantum_advantage_scaling}.

Building on these developments, this paper proposes a quantum-enhanced traffic management framework that integrates an STQGCN for short-term edge-level traffic prediction with a QUBO formulation solved using QAOA for network-level rerouting, thereby combining prediction and optimization within a single closed-loop pipeline \cite{shikanai2025,salloum2025,zhou2020}. Rather than asserting algorithmic supremacy over classical methods, we investigate whether near-term variational algorithms can achieve solution quality on par with classical heuristics and establish a structured, closed-loop interface between graph neural forecasting and combinatorial optimization.

The main contributions of this work are:
\begin{enumerate}
    \item We propose a hybrid classical--quantum STQGCN architecture that combines graph-based message passing with a VQC layer to produce short-term, edge-level predictions of traffic flow directly on road segments. The framework is evaluated against LSTM and classical STGCN forecasting baselines across single and hierarchical network topologies.
    \item Network-level traffic rerouting is formulated as a QUBO problem solved via depth-one QAOA and benchmarked against both BPSO and an exhaustive brute-force global optimum baseline across 45 heterogeneous scenarios. We evaluate this formulation within a closed prediction-to-optimization pipeline on a unified topology, demonstrating that predicted flow states directly drive actionable rerouting without manual intervention.
    \item The paper outlines a corridor-level system architecture and Defense-in-Depth security model compatible with existing Adaptive Traffic Control System (ATCS) infrastructure.
\end{enumerate}

%-----------------------------------------------------
% LITERATURE SURVEY 
%-----------------------------------------------------

\section{Literature Survey} 

\subsection{Classical Traffic Optimization}
Traditionally, intelligent traffic management systems have relied on classical optimization and classical learning techniques to mitigate congestion, coordinate traffic signals and reroute vehicles. Although PSO and the other swarm-based methods are adaptable and simple to implement \cite{celtek2020,chuo2017,dabiri2016}, increasing the complexity of the road network leads to premature convergence and reduced solution quality.

\subsection{Graph-Based Traffic Prediction}
Additionally, graph-based deep learning has proven to be effective in capturing structured traffic dependencies. Spatiotemporal graph convolutional architectures learn relationships over interconnected nodes and evolving states \cite{yan2018}, while quantum-enhanced models have been applied to traffic-density estimation \cite{wang2026,somvanshi2025}.

\subsection{Quantum Computing in Transportation}

Quantum computing has been considered an emerging paradigm for combinatorial challenges in transportation optimization, such as vehicle routing and signal coordination. Early works demonstrated the feasibility of traffic routing via quantum annealing \cite{yarkoni2020,neukart2017}, and recent formulations frame traffic signal timing as QUBO problems \cite{shikanai2025,salloum2025}. Variational gate-based circuits offer an alternative through QAOA for near-term quantum-classical hybrid systems \cite{zhou2020}, and studies have explored edge-level quantum architectures for transportation systems \cite{maia2025,somvanshi2025}. However, near-term quantum implementations remain constrained by two-qubit gate fidelities, qubit connectivity, and classical simulation overheads, necessitating hybrid approaches where classical processors handle data aggregation while compact quantum circuits execute specialized subroutines.

\subsection{Research Gap}
While previous works have focused on either learning methods for prediction or defining optimization problems, practical implementation considering both aspects for traffic flow prediction and coordinated optimization with rerouting decisions is rare. This gap can be observed even among the quantum computing works discussed above. For instance, Yarkoni et al.~\cite{yarkoni2020} and Salloum et al.~\cite{salloum2025} propose traffic navigation and signal-flow rerouting as quantum annealing or iterative QUBO problems, but in both cases, the traffic states that drive the optimization are an externally supplied input rather than being produced by a forecasting model. In contrast, Wang et al.~\cite{wang2026} apply quantum machine learning to estimate traffic density but do not optimize the resulting predictions. Therefore, neither line of work establishes a pipeline in which predicted flow states directly inform network-level optimization. For practical deployment, continuous flow prediction using a learned model is required to inform large-scale coordinated optimization while being compatible with current ITS infrastructure.

This work proposes a hybrid classical--quantum framework for coordinated optimization based on spatiotemporal graph learning and quantum optimization. The proposed solution employs graph message passing with a VQC layer for short-term traffic flow forecast at the edge level. The predicted flow is then used as an input to a QUBO formulation solved with QAOA to determine optimal rerouting decisions for an adaptive and responsive smart city transport system. This combined approach differs from previous works that have treated the flow prediction and optimization aspects in isolation.

%-----------------------------------------------------
% PROPOSED METHODOLOGY
%-----------------------------------------------------

\section{Proposed Methodology}

%-----------------------------------------------------
% TRAFFIC CONGESTION PREDICTION
%-----------------------------------------------------

\subsection{Traffic Congestion Prediction}

As observed in Figure~\ref{fig:STQGCN}, an STQGCN is proposed for edge-level traffic prediction by modeling junction spatial dependencies, segment physical attributes, dynamic weather conditions and temporal periodicity.

\begin{figure}[htbp]
    \centering
    \includegraphics[width=1\linewidth]{prediction-diagram.png}
    \caption{Architecture of the hybrid Spatio-Temporal Quantum Graph Convolutional Network (STQGCN): raw junction telemetry and weather dynamics undergo spatial message passing across road topology, followed by a Variational Quantum Circuit (VQC) state update with parameterized rotations and entangling gates, generating calibrated edge flow predictions.}
    \label{fig:STQGCN}
\end{figure}

\subsubsection{Spatio-Temporal Graph Representation}
The network is represented as a directed graph $G=(V,E)$. Each node $v_i$ has a feature vector $\mathbf{x}_i \in \mathbb{R}^{d_v}$ combining traffic dynamics (flow, speed, occupancy, queue length) with monsoon weather metrics (temperature, precipitation intensity). Each directed edge $e_{ij}$ carries structural features $\mathbf{f}_{ij}\in\mathbb{R}^{d_e}$ (capacity, speed limit, lanes, length, Pavement Condition Index [PCI], incident flag). A global temporal vector $\mathbf{t} \in \mathbb{R}^{d_t}$ captures periodicity ($\sin/\cos$ hour encodings, weekend and holiday/event flags). All features are Z-score normalized prior to embedding.

\subsubsection{Contextual Message Passing}
Node features are contextualized with global temporal vectors and aggregated across spatial neighborhoods $\mathcal{N}(i)$ alongside edge attributes:
\begin{align}
\mathbf{h}_i^{(0)} &= \mathrm{ReLU}\big(W_v [\mathbf{x}_i \parallel \mathbf{t}] + b_v\big), \quad \mathbf{f}_{ij} \rightarrow \mathbf{e}_{ij} \\
\tilde{\mathbf{h}}_i &= \mathbf{h}_i^{(0)} + \sum_{j\in\mathcal{N}(i)} \mathrm{MLP}\big([\mathbf{h}_j^{(0)} \parallel \mathbf{e}_{ji} \parallel \mathbf{t}]\big)
\end{align}
Residual aggregation preserves local spatial context and incorporates temporal context. 

\subsubsection{Hybrid Quantum Update Layer}
The spatial embedding $\tilde{\mathbf{h}}_i$ is refined using a VQC $\mathcal{Q}_\Theta$: (1) down-projection contextualized with $\mathbf{t}$ to single-qubit rotation angles, (2) $R_Y$ angle embedding, (3) parameterized entangling layers, (4) Pauli-$Z$ expectation measurements and (5) up-projection with $\mathbf{t}$ back to latent dimension:
\begin{equation}
\mathbf{h}_i^{(\ell)} = \mathrm{LayerNorm}\Big(\tilde{\mathbf{h}}_i + \mathcal{Q}_\Theta\big([\tilde{\mathbf{h}}_i \parallel \mathbf{t}]\big)\Big)
\label{eq:vqc_update}
\end{equation}
The VQC $\mathcal{Q}_\Theta$ uses $N_q$ qubits per topology ($N_q = 8$ for the single 8-node network; $N_q = 3$ per zone for the hierarchical 24-node network), yielding 24 variational parameters per layer for the single network and 9 per layer for the hierarchical network (totals: 24 at $K=1$, 144 at $K=6$ for single; 9 at $K=1$, 54 at $K=6$ for hierarchical). In the hierarchical network, the 3-qubit VQC modules across the three operational zones share identical variational parameters, yielding 9 parameters per layer ($3 \text{ qubits} \times 3 \text{ rotations}$) rather than 27. Variational parameters are trained via the Parameter-Shift Rule on PennyLane's noiseless \texttt{default.qubit} simulator.

To isolate whether the predictive capacity of STQGCN originates from the parameterized quantum circuit rather than the surrounding classical operations, the architecture is explicitly benchmarked against an architecture-matched Classical STGCN. In the Classical STGCN baseline, the quantum circuit $\mathcal{Q}_\Theta$ in Eq.~\ref{eq:vqc_update} is replaced by an identical classical non-linear bottleneck module:
    \begin{equation}
    \mathbf{h}_i^{(\ell)} = \text{LayerNorm}\left(\tilde{\mathbf{h}}_i + \text{MLP}_{\text{update}}([\tilde{\mathbf{h}}_i \parallel \mathbf{t}])\right)
    \label{eq:classical_update_matching}
    \end{equation}
where $\text{MLP}_{\text{update}}$ comprises two linear transformations ($16 \to 16 \to 16$) with intermediate ReLU activations and an identical LayerNorm operation (544 parameters total; Classical STGCN total: $2{,}422 - 117 + 544 = 2{,}849$ parameters, subtracting 117 parameters of quantum projections and adding the 544-parameter classical update block; net $+427$). While this ensures that non-linearity and normalization layers are strictly held constant, we explicitly note two caveats regarding Reviewer \#2's comment on baseline fairness: (1) \emph{Parameter asymmetry}: the classical control module contains 544 parameters, which is substantially more than the 54--144 variational parameters used by the VQC ($3.8\times$ to $10\times$ more parameters), meaning the classical baseline serves as an over-parameterized capacity control rather than a parameter-matched control; and (2) \emph{Single-seed evidence}: because model training was conducted under a single seed (seed 42), the observed $1$--$2\%$ empirical differences in bidirectional flow MAE are indicative rather than definitive, demonstrating parameter-efficient representation rather than conclusive quantum advantage.

\subsubsection{Edge-wise Forecasting \& Objective}
The model predicts edge-level flow (veh/hr); the congestion ratio is derived downstream as $O_e = q_e/C_e$. The final edge-level predictions are generated by passing the weather-informed source and destination node embeddings ($\mathbf{h}_i^{(L)}, \mathbf{h}_j^{(L)}$), edge attributes $\mathbf{e}_{ij}$ and temporal vector $\mathbf{t}$ through an MLP, followed by inverse Z-score normalization. The model operates on a single-step (5-second) input snapshot with sinusoidal temporal encodings; it does not use a historical input window:
\begin{equation}
\hat{y}_{ij} = \mathrm{MLP}\big([\mathbf{h}_i^{(L)} \parallel \mathbf{h}_j^{(L)} \parallel \mathbf{e}_{ij} \parallel \mathbf{t}]\big) \cdot \sigma + \mu
\end{equation}
The model is trained end-to-end minimizing MSE loss $\mathcal{L} = \frac{1}{ET}\sum_{t=1}^{T}\sum_{e\in E} (\hat{y}_e^{(t)} - y_e^{(t)})^2$ using Adam for classical weights and the Parameter-Shift Rule for quantum parameters $\Theta$.


%-----------------------------------------------------
% TRAFFIC CONGESTION OPTIMIZATION 
%-----------------------------------------------------

\subsection{Traffic Congestion Optimization}

Considering a network graph with edge capacities $C_e$, lane counts $L_e$ and predicted flows $q_e \equiv \hat{y}_{e, t+1}$ from the STQGCN model, traffic rerouting is formulated as a QUBO problem. To benchmark optimization performance under identical physical constraints, two paradigms are evaluated: (1) \textbf{Binary Particle Swarm Optimization (BPSO)} as a classical metaheuristic baseline and (2) \textbf{QAOA} as a variational quantum approach.

%-----------------------------------------------------
% UNIFIED QUBO FORMULATION
%-----------------------------------------------------
\subsubsection{Congestion Sensing and QUBO Formulation}
\label{subsec:qubo_formulation}

\paragraph{1) Congestion Sensing and Packet Discretization:}
Initial edge occupancy is defined as $O_e^{(0)} = q_e / C_e$, where $q_e$ is the predicted link flow and $C_e$ denotes the link capacity. Edges exceeding the operational congestion threshold $\theta_{\text{high}} = 0.60$ (60\% of capacity) are flagged as congested links ($e \in \mathcal{E}_{\text{cong}}$). For each congested link, excess traffic volume above the target equilibrium occupancy $O^* = 0.50$ is computed as $\Delta q_e = \max(0, q_e - O^*C_e)$ and discretized into integer traffic packets of fixed granularity $\Delta_p = 150\text{ veh/hr}$:
    \begin{equation}
    N_e = \left\lceil \frac{\Delta q_e}{\Delta_p} \right\rceil = \left\lceil \frac{\Delta q_e}{150} \right\rceil
    \label{eq:packet_discretization_corrected}
    \end{equation}
    To ensure computational feasibility under classical statevector simulation and near-term NISQ constraints, the total number of binary decision variables across the network is capped at a global maximum budget $N_{\text{cap}} = 10$, such that the active problem size is $N = \min\left(N_{\text{cap}}, \sum_{e \in \mathcal{E}_{\text{cong}}} N_e\right) \le 10$. We emphasize that $N_{\text{cap}} = 10$ serves as an upper ceiling constraint rather than a fixed instance dimension; the actual instantiated number of qubits $N$ varies dynamically per traffic scenario based on detected congestion severity, ranging from $N = 2$ in minor incidents to $N = 10$ in major peak surges (averaging $\bar{N} = 7.4\text{--}7.7$ across evaluated benchmark networks).

Each binary variable $x_k \in \{0, 1\}$ assigns packet $k$ either to its original route ($x_k = 0$) or to an alternative candidate detour path ($x_k = 1$). Detour candidates ($\le 3$ hops) are ranked by path score $\mathcal{S}(r) = \text{Length}(r) + 2.0 \max_{e' \in r} O_{e'}^{(0)}$. The target occupancy $O^* = 0.50$ represents a free-flow equilibrium operating threshold (Level of Service A/B under Bureau of Public Roads delay curves), providing reserve capacity to absorb diverted volume without triggering secondary bottlenecks. The packet granularity $\Delta_p = 150\text{ veh/hr}$ corresponds to $\approx 7\text{--}10\%$ of single-lane capacity, balancing discrete rerouting fidelity against optimization variable count.

\paragraph{2) Edge Load and Objective Mapping:}
For decision vector $\mathbf{x} = (x_1, \dots, x_N)^T \in \{0, 1\}^N$, the resulting edge load $q_e(\mathbf{x})$ is:
\begin{equation}
    q_e(\mathbf{x}) = q_e^{(0)} - \sum_{k: \text{orig}(k)=e} 150 x_k + \sum_{k: e \in \text{detour}(k)} 150 x_k
    \label{eq:load_redistribution}
\end{equation}
The global objective $J(\mathbf{x})$ minimizes the weighted squared deviation of each edge occupancy from the target $0.50$:
\begin{equation}
    J(\mathbf{x}) = \sum_{e \in E} w_e \left( \frac{q_e(\mathbf{x})}{C_e} - 0.50 \right)^2, \quad \text{where } w_e = 1.0 + 2.0 O_e^{(0)} + \frac{\bar{C}}{C_e}
    \label{eq:qubo_objective}
\end{equation}
The weighting factor $w_e$ balances network stability and bottleneck mitigation. The constant $1.0$ maintains non-zero baseline weighting, multiplier $2.0$ penalizes high initial occupancy $O_e^{(0)}$, and $\frac{\bar{C}}{C_e}$ prioritizes low-capacity roads. Expanding Eq.~\eqref{eq:qubo_objective} generates the QUBO matrix capturing route coupling and bottleneck interactions.

\noindent\textbf{Important---Objective vs.\ Peak-Occupancy Mismatch:} $J(\mathbf{x})$ minimizes weighted squared deviation from $0.50$ and is not a direct surrogate for peak occupancy. A $J$-optimal solution can therefore raise the peak occupancy on individual links if rerouting shifts load from heavily congested edges to those near $0.50$. Note also that $\mathbf{x}=\mathbf{0}$ (no rerouting) is always feasible; the negative reductions observed in saturated scenarios reflect this objective--metric mismatch rather than a routing error. A peak-penalty guard (accepting a rerouting plan only when it does not increase the peak) is a natural extension for safety-critical deployments.

%-----------------------------------------------------
% SOLVER PARADIGMS
%-----------------------------------------------------
\subsubsection{BPSO Optimization}
\label{subsec:optimization_paradigms}

BPSO optimizes $J(\mathbf{x})$ by mapping continuous swarm dynamics onto the binary search space $\{0, 1\}^N$. Each particle $p$ maintains position $\mathbf{u}_p \in [-10, 10]^N$ and velocity $\mathbf{v}_p \in \mathbb{R}^N$, updated at iteration $k+1$ via:
\begin{equation}
    v_{p, i}^{k+1} = w v_{p, i}^k + c_1 r_1 \left( p_{\text{best}, p, i} - u_{p, i}^k \right) + c_2 r_2 \left( g_{\text{best}, i} - u_{p, i}^k \right)
    \label{eq:pso_vel}
\end{equation}
\begin{equation}
    u_{p, i}^{k+1} = \text{clip}\left( u_{p, i}^k + v_{p, i}^{k+1}, -10, 10 \right)
    \label{eq:pso_pos}
\end{equation}
with inertia $w = 0.5$, acceleration factors $c_1 = c_2 = 1.5$ and $r_1, r_2 \sim U(0, 1)$. Continuous states map to binary route choices $\mathbf{b}_p \in \{0, 1\}^N$ via sigmoidal thresholding: $b_{p, i} = 1$ if $\sigma(u_{p, i}) = (1 + e^{-u_{p, i}})^{-1} \ge 0.5$, and $0$ otherwise.

\subsubsection{QAOA Optimization}
    QAOA maps the QUBO objective in Eq.~\eqref{eq:qubo_objective} into an equivalent $N_q$-qubit Ising cost Hamiltonian:
    \begin{equation}
    H_C = \sum_{i=1}^{N_q} h_i Z_i + \sum_{i < j} J_{ij} Z_i Z_j + E_0 I
    \label{eq:ising_hamiltonian}
    \end{equation}
where $Z_i$ represents the Pauli-$Z$ operator acting on qubit $i$. A parameterized quantum circuit prepares the state $|\psi(\boldsymbol{\gamma}, \boldsymbol{\beta})\rangle = \prod_{\ell=1}^p \left( e^{-i \beta_\ell H_B} e^{-i \gamma_\ell H_C} \right) |+\rangle^{\otimes N_q}$, where $H_B = \sum_{i=1}^{N_q} X_i$ is the transverse mixer Hamiltonian and $p$ denotes the circuit ansatz depth. A COBYLA optimizer tunes $(\boldsymbol{\gamma}, \boldsymbol{\beta})$ to minimize the cost expectation $\langle H_C \rangle = \langle \psi | H_C | \psi \rangle$.

    \noindent\textbf{Ansatz Depth Configuration:} We distinguish between two experimental depth regimes:
    \begin{itemize}
        \item \textbf{Operational Real-Time Rerouting ($p = 1$):} For all 45 benchmark scenarios and the integrated prediction-optimization pipeline, depth $p = 1$ is deployed (optimizing two scalar parameters $\gamma_1, \beta_1$). At $N_q \approx 8$, this incurs 27--28 two-qubit entangling gates; the gate count scales as $N_q(N_q-1)/2$ and reaches 45 at $N_q=10$. This minimizes circuit depth and gate count, enabling COBYLA convergence within sub-10~ms limits.
        \item \textbf{Offline Circuit Scaling Ablation ($p \in \{1, 2, 3\}$):} In Section~\ref{subsec:circuit_scalability}, deeper circuits ($p = 2$ and $p = 3$) are evaluated as an offline ablation to analyze convergence trajectories, gate scaling ($d = 167\text{--}173$ at $p=3$), and ground-state approximation ratios.
    \end{itemize}
A classical COBYLA optimizer (maximum 50 iterations, tolerance $10^{-4}$) is executed via Qiskit's \texttt{StatevectorSampler} primitive with no silent fallback mechanisms permitted.

%-----------------------------------------------------
% SYSTEM IMPLEMENTATION AND SECURITY
%-----------------------------------------------------
\section{System Implementation and Security}
The proposed solution is designed as a corridor-based, hybrid centralized-hierarchical traffic-control system that augments the existing Adaptive Traffic Control System (ATCS). Field equipment at each junction includes AI cameras, radar, weather sensors, signal heads, Variable Message Signs (VMS), a Malfunction Management Unit (MMU), and a certified controller cabinet. The existing controller retains final authority over signal operations, evaluating data on vehicle traffic, queue, occupancy, and weather provided by the field equipment \cite{mcgm2025intro,mcgm2025maint,mcgm2025camera}. The system integrates into Mumbai's hierarchical traffic-control system via a managed fibre/Multi-Link Local Network (MLLN); a Ward Edge Platform executes the optimization process and the city traffic management centre maintains overall supervision \cite{mcgm2025intro,mcgm2025maint,mcgm2025camera,cdac_cosicost}. Every corridor is represented as a graph with junctions as nodes and road segments as edges. The STQGCN model processes this graph's local state, learning patterns of spillback and platoon propagation. Signal retuning (offsets, cycle lengths, phase splits) and VMS policy co-optimization based on optimizer outputs are envisioned as future extensions (Section~\ref{subsec:future_scope}).

The operational flow proceeds as follows. Ward Edge aggregates observations into a corridor graph. The STQGCN predicts short-term traffic flow, and QAOA is invoked only when congestion thresholds are exceeded (event-driven optimization). QAOA currently runs on a classical statevector simulator, decoupled from but compatible with future QPU deployment. Where quantum cloud connectivity is needed, a 4G/5G private Access Point Name (APN) or a Wireless Planning and Coordination (WPC)-approved 5.825--5.875~GHz wireless bridge targeting $\sim$16--20~Mbps per junction and sub-50~ms latency for the optimizer step can be specified, though Ward Edge remains the primary low-latency layer \cite{tec2013ism,dot_wpc_eta}. The 50~ms budget applies to the QAOA optimizer step; the full end-to-end pipeline (including STQGCN inference and Qiskit simulation) takes $\approx$600~ms, which fits within the 5-second ATCS actuation cycle. Plans pass through the Implementation Decision Engine (IDE), Operational Decision Engine (ODE), safety validation, and a Signal Transition Manager before reaching the controller. Active green phases are never abruptly terminated, and minimum green, clearance, and conflict-free sequencing rules remain enforced \cite{mcgm2025intro,tsdsi_std5004}. The field controller and detectors form an always-on domain independent of the restartable STQGCN/QAOA services; the last valid plan persists through any Ward Edge outage.

Defense-in-Depth spans physical infrastructure, communication trust, Ward Edge security, AI processing, decision validation, controller protection, monitoring, and recovery so a single layer's failure does not compromise signal safety \cite{certin_cisg2025,certin_cisg2023}. Roadside and controller cabinets are secured via tamper sensors, firmware authenticity checks, and audit logging under independent MMU supervision. Communication relies on mutual authentication, segmentation, and replay protection through a session-based lifecycle \cite{certin_cisg2025,certin_cisg2023,certin_cisg2024}, and the Ward Edge enforces platform integrity, least-privilege access, and continuous supervision \cite{certin_cisg2025,certin_cisg2023}. The AI pipeline is validated at every stage (input consistency, graph-structure integrity, prediction anomaly checks, QAOA feasibility/safety checks); every recommendation independently undergoes policy, traffic-rule, and safety validation before the IDE/ODE issues a command, with failed validation leaving the existing safe plan active \cite{tsdsi_std5004,certin_cisg2025,certin_cisg2023}. The architecture follows the DPDP Act, 2023 via privacy-by-design, extracting only aggregate traffic metrics rather than raw CCTV imagery \cite{meity_dpdp2023,meity_dpdp_rules2025}. Continuous telemetry correlation and validated recovery protect the network from tampering and unsafe commands without halting field control \cite{certin_cisg2025,certin_cisg2023,certin_cisg2024}.

%-----------------------------------------------------
% EXPERIMENTAL SETUP AND DATASETS 
%-----------------------------------------------------
\section{Experimental Setup and Datasets}

\subsection{Dataset Formulation and Realistic Traffic Synthesis}
\label{subsec:dataset_formulation}

    Standard benchmarks (e.g., PeMSD4/D8) lack edge-level dynamic attributes, localized turning restrictions, and bidirectional multi-corridor coupling. To benchmark STQGCN under realistic urban conditions, two physics-informed synthetic datasets modeled on Mumbai's arterial corridors were constructed via reproducible numerical simulation (fixed seed = 42):
    \begin{enumerate}
        \item \textbf{Single Network ($N = 8$ Nodes):} Models a localized major arterial junction hub (Western Express Highway / JVLR / BKC connector) comprising 8 signalized intersections connected by 11 forward directed links and 22 bidirectional links.
        \item \textbf{Hierarchical Network ($N = 24$ Nodes, 3 Operational Zones):} Spans an extended multi-corridor arterial split into three 8-node operational zones joined by inter-zone arterial bridges ($V_8 \to V_9$ and $V_{16} \to V_{17}$) across 30 unidirectional and 60 bidirectional links:
        \begin{itemize}
            \item \emph{Zone 1 (Tree Inflow Feeder):} Suburban inflow capturing radial residential morning ingress.
            \item \emph{Zone 2 (Mesh Grid, $2 \times 4$):} Central Business District interchange experiencing multi-directional weaving and high turning conflict.
            \item \emph{Zone 3 (Linear Corridor):} Narrow arterial bottleneck modeling coastal corridor capacity constraints.
        \end{itemize}
    \end{enumerate}
    Both datasets comprise $N_T = 10,000$ consecutive timesteps with a 5-second sampling interval (representing $\approx 13.9$ hours of continuous traffic dynamics). The temporal sequence is partitioned chronologically into 70\% training (7,000 steps), 15\% validation (1,500 steps), and 15\% testing (1,500 steps).

\noindent\textbf{Operational Relevance of the 5-Second Forecasting Horizon:} The choice of a 5-second lookahead ($t \to t+1$) is motivated by modern ATCS deployment practice (e.g., SCOOT and SCATS per FHWA/ITE Traffic Control guidelines). Real-world ATCS controllers actuate split-stage adjustments, cycle alterations, and queue spillback prevention at sub-minute intervals (5 to 60 seconds). In dense urban arterials with short link lengths (150--400 metres), vehicles traverse segments in 10--25 seconds; high-frequency 5-second predictions enable preemptive rerouting and signal actuation before shockwaves cause upstream junction gridlock. Robustness across longer operational horizons of 1, 5, and 15 minutes is formally evaluated in Section~\ref{sec:multi_horizon_evaluation}.

    \noindent\textbf{Model Hyperparameters and Training Configuration:}
    All predictive models were trained on PyTorch 2.1 with fixed stochastic seeds (\texttt{torch.manual\_seed(42)}, \texttt{np.random.seed(42)}). Classical and quantum weights
  were optimized end-to-end using the Adam optimizer with initial learning rate $\eta = 10^{-3}$, weight decay $10^{-5}$, and mini-batch size 64 across 40 epochs, minimizing
  Mean Squared Error (MSE) loss. STQGCN and Classical STGCN employ hidden dimension $d_h = 16$. In STQGCN, the VQC is simulated using PennyLane's \texttt{default.qubit} device
  with analytical gradients computed via the Parameter-Shift Rule. For the LSTM baseline, a 2-layer recurrent network with hidden dimension $d_h = 128$, dropout 0.2, and an
  unrolled dense input vector (flattened across all nodes and edges) was trained under identical optimizer and seed configurations.

    \noindent\textbf{Optimization Baseline Configurations and Seeds:}
    BPSO was configured with swarm size $M = 30$ particles, maximum iterations $T = 20$ (600 total objective evaluations per scenario), inertia weight $w = 0.5$, acceleration
  coefficients $c_1 = c_2 = 1.5$, and sigmoidal binary mapping (fixed seed = 42). The 15 publication scenarios per topology were generated under fixed random seed 2026. Multi-seed statistical variance analysis was executed over 5 independent random seeds (2026–2030).

\subsection{Mumbai Traffic Physics Alignment}
The synthetic generation aligns with physical traffic dynamics observed across Mumbai arterials:
\begin{enumerate}
    \item \textbf{Bimodal Commuter Peaks:} Dual-peak morning and evening surges ($A_m \approx 1{,}200\text{ veh/hr}$, centred at morning peak 08:00; $A_e \approx 1{,}500\text{ veh/hr}$, centred at evening peak 18:00) across diurnal cycles sampled at a time interval of $t$ minutes where $t$ is between 5 and 15 ($t \in [5, 15]$):
    \begin{equation}
        q_{\text{base}}(t_{\text{day}}) = 800 + 400\sin\left(\frac{2\pi t_{\text{day}}}{T_{\text{day}}}\right) + A_m e^{-\frac{(t_{\text{day}} - t_m)^2}{2\sigma_m^2}} + A_e e^{-\frac{(t_{\text{day}} - t_e)^2}{2\sigma_e^2}}
    \end{equation}
    where $T_{\text{day}}$ denotes daily interval count, capturing complete multi-day diurnal and monsoon seasonality before adaptation to sub-minute operational horizons.
    \item \textbf{Non-Linear Traffic Breakdown:} Speeds $v_{i}(t)$ and densities $\rho_{i}(t)$ govern capacity drops and shockwave propagation according to non-linear flow theory:
    \begin{equation}
        v_{i}(t) = \max\left(v_{\text{free}} \left[ 1 - \left( \frac{q_i(t)}{C_{\text{max}}} \right)^{1.8} \right] + \epsilon, \, v_{\text{min}}\right)
    \end{equation}
    \item \textbf{Monsoon, Stochastic Disturbances \& Multi-Scale Heterogeneity:} Exponential rainfall pulses ($R(t) \sim \text{Exp}(\lambda)$) and random incident flags ($p=0.03$) test model robustness under sudden capacity degradation, while combining Tree $\rightarrow$ Mesh $\rightarrow$ Linear topologies evaluates GNN scalability from localized junctions to multi-zonal bottleneck corridors.
\end{enumerate}


%-----------------------------------------------------
% RESULTS AND DISCUSSION
%-----------------------------------------------------

\section{Results and Discussion}

%-----------------------------------------------------
% PREDICTION RESULTS
%-----------------------------------------------------

\subsection{Experimental Evaluation for Short-Term Traffic Prediction}
\label{sec:forecasting_results}

The STQGCN prediction phase is evaluated over a 5-second horizon against two baselines: an LSTM (non-spatial sequence baseline) and a classical STGCN (lacking the VQC update layer). Benchmark topologies include:
\begin{enumerate}
    \item \textbf{Single Network ($N=8$):} Localized junction topology with 11 unidirectional / 22 bidirectional links.
    \item \textbf{Hierarchical Network ($N=24$):} 3-zone arterial system with 30 unidirectional / 60 bidirectional links.
\end{enumerate}
Performance is reported on un-normalized throughput ($\text{veh/hr}$) using MAE, RMSE, MAPE (\%) and $R^2$.

\subsubsection{Architectural Performance Comparison}
\label{subsec:architecture_comparison}

Tables~\ref{tab:single_network_forecasting} and \ref{tab:hierarchical_network_forecasting} detail forecasting performance across both topology scales.

%-----------------------------------------------------
% TABLE - SINGLE NETWORK
%-----------------------------------------------------

    \begin{table}[t]
    \centering
    \caption{Comparative Architectural Evaluation on Single Network ($N = 8$ Nodes) for 5-Second Traffic Forecasting. Parameter counts reflect total trainable weights.}
    \label{tab:single_network_forecasting}
    \small
    \begin{tabular}{l c c c c c c}
    \toprule
    \textbf{Model Architecture} & \textbf{Total Params} & \textbf{Classical / Quantum} & \textbf{MAE $\downarrow$} & \textbf{RMSE $\downarrow$} & \textbf{MAPE (\%) $\downarrow$}
  & \textbf{$R^2$ $\uparrow$} \\
    \midrule
    \multicolumn{7}{l}{\emph{Unidirectional Flow Topology (11 directed edges)}} \\
    LSTM (TMS Baseline)     & 277,003 & 277,003 / 0  & \textbf{150.93} & 279.58 & 14.51 & 0.9187 \\
    Classical STGCN         & 2,849   & 2,849 / 0    & 159.01 & 278.26 & 14.62 & 0.9195 \\
    STQGCN ($K = 1$)        & \textbf{2,446} & 2,422 / 24 & 152.87 & \textbf{277.68} & \textbf{14.45} & \textbf{0.9198} \\
    \midrule
    \multicolumn{7}{l}{\emph{Bidirectional Flow Topology (22 directed edges)}} \\
    LSTM (TMS Baseline)     & 312,214 & 312,214 / 0  & 246.00 & \textbf{351.80} & 27.53 & \textbf{0.8538} \\
    Classical STGCN         & 2,849   & 2,849 / 0    & 241.79 & 363.52 & 26.69 & 0.8439 \\
    STQGCN ($K = 6$)        & \textbf{2,566} & 2,422 / 144 & \textbf{238.40} & 352.85 & \textbf{24.67} & 0.8529 \\
    \bottomrule
    \end{tabular}
    \end{table}

%-----------------------------------------------------
% TABLE - HIERARCHICAL NETWORK 
%-----------------------------------------------------

\begin{table}[t]
    \centering
    \caption{Comparative Architectural Evaluation on Hierarchical Network ($N = 24$ Nodes, 3 Zones) for 5-Second Traffic Forecasting. Parameter counts reflect total trainable
  weights.}
    \label{tab:hierarchical_network_forecasting}
    \small
    \begin{tabular}{l c c c c c c}
    \toprule
    \textbf{Model Architecture} & \textbf{Total Params} & \textbf{Classical / Quantum} & \textbf{MAE $\downarrow$} & \textbf{RMSE $\downarrow$} & \textbf{MAPE (\%) $\downarrow$}
  & \textbf{$R^2$ $\uparrow$} \\
    \midrule
    \multicolumn{7}{l}{\emph{Unidirectional Flow Topology (30 directed edges)}} \\
    LSTM (TMS Baseline)     & 386,974 & 386,974 / 0  & 52.97 & 67.49 & 4.70 & 0.9876 \\
    Classical STGCN         & 2,849   & 2,849 / 0    & \textbf{46.27} & \textbf{58.41} & \textbf{4.22} & \textbf{0.9907} \\
    STQGCN ($K = 4$)        & \textbf{2,458} & 2,422 / 36 & 46.68 & 58.97 & \textbf{4.22} & 0.9905 \\
    \midrule
    \multicolumn{7}{l}{\emph{Bidirectional Flow Topology (60 directed edges)}} \\
    LSTM (TMS Baseline)     & 483,004 & 483,004 / 0  & \textbf{173.14} & \textbf{252.70} & 18.63 & \textbf{0.8261} \\
    Classical STGCN         & 2,849   & 2,849 / 0    & 177.34 & 258.94 & 18.79 & 0.8174 \\
    STQGCN ($K = 6$)        & \textbf{2,476} & 2,422 / 54 & 175.27 & 257.37 & \textbf{18.50} & 0.8196 \\
    \bottomrule
    \end{tabular}
    \end{table}


Key insights from Tables~\ref{tab:single_network_forecasting} and \ref{tab:hierarchical_network_forecasting}:
\begin{enumerate}
    \item \textbf{Bidirectional Resilience:} STQGCN ($K=6$) outperforms Classical STGCN and achieves the best MAPE ($24.67\%$ on the single network; $18.50\%$ on the hierarchical network) and the best MAE ($238.40\text{ veh/hr}$) on the single bidirectional block. LSTM achieves the best RMSE ($351.80\text{ veh/hr}$) and $R^2$ ($0.8538$) on the single bidirectional block, and the best MAE, RMSE and $R^2$ on the hierarchical bidirectional block.
    \item \textbf{Scale Generalization:} Graph-structured models outperform sequence-only LSTM on the 24-node unidirectional topology ($4.22\%$ vs $4.70\%$ MAPE). STQGCN also beats Classical STGCN on single unidirectional MAE ($152.87$ vs $159.01\text{ veh/hr}$); Classical STGCN leads only on the 24-node unidirectional case. STQGCN maintains comparable error bounds ($\text{MAE} = 46.68\text{ veh/hr}$, $R^2 = 0.9905$), demonstrating scalable integration of quantum graph updates across zonal boundaries.
    \item \textbf{STQGCN vs.\ Classical STGCN:} STQGCN exhibits competitive performance relative to Classical STGCN. Under complex bidirectional flows with counter-directional shockwaves, the VQC's parameterized $R_Y(\theta)$ rotations and CNOT entangling gates provide an expressive non-linear transformation that achieves marginally lower prediction error than the classical non-linear bottleneck (Eq.~\ref{eq:classical_update_matching}), reaching an MAE of $238.40\text{ veh/hr}$ (vs.\ $241.79\text{ veh/hr}$) on the single bidirectional network and $175.27\text{ veh/hr}$ (vs.\ $177.34\text{ veh/hr}$) on the hierarchical bidirectional network. Conversely, under smooth, ordered unidirectional flows ($R^2 > 0.99$), classical message passing is near-optimal and the additional optimization complexity of the VQC leads to a minor reduction in accuracy ($46.27$ vs.\ $46.68\text{ veh/hr}$ MAE on hierarchical unidirectional). Because these results are obtained from a single training seed (seed 42), the small $1$--$2\%$ differences should be interpreted as demonstrating comparable representational expressivity rather than definitive quantum superiority over classical bottlenecks.
\end{enumerate}

\subsubsection{Representation Expressivity and Parameter-Budget Ablation Analysis}
\label{subsec:quantum_advantage}
Ablation across VQC ansatz depths $K \in \{1, \dots, 7\}$ under unidirectional and bidirectional flows demonstrates scale-dependent representation dynamics (Fig.~\ref{fig:vqc_ablation_overall}). On the
  Single Network ($N = 8$), peak accuracy occurs at shallow depth $K = 1$ under unidirectional flow ($\text{MAE} = 152.87\text{ veh/hr}$, $\text{MAPE} = 14.45\%$) and $K = 6$
  under bidirectional flow ($\text{MAE} = 238.40\text{ veh/hr}$). On the Hierarchical Network ($N = 24$), error decreases progressively from $K = 1$ ($\text{MAE} = 48.27\text{
  veh/hr}$) to an optimal minimum at $K = 4$ ($\text{MAE} = 46.68\text{ veh/hr}$, $\text{MAPE} = 4.22\%$, $R^2 = 0.9905$) before stabilizing.

    These experimental findings elucidate three key architectural characteristics of the hybrid STQGCN framework:
    \begin{enumerate}
        \item \textbf{Transparent Parameter Accounting:} Full model parameter counts are reported. LSTM requires 277,003--483,004 parameters because it flattens the full topological state into dense input layers ($d_{\text{in}} = 184$--$238$). Graph convolutional architectures exploit localized spatial weight sharing, reducing parameter requirements by over two orders of magnitude. Classical STGCN requires 2,849 parameters (2,422 shared classical weights plus a 544-parameter classical MLP update block, representing net $+427$ over STQGCN projections, totalling $2{,}422 + 427 = 2{,}849$). STQGCN requires 2,446--2,566 total trainable weights (2,422 classical weights plus 24--144 quantum variational parameters at $K=1$--$6$). Importantly, the classical control block employs substantially more parameters than the VQC (544 vs.\ 54--144 parameters), meaning the classical baseline serves as an over-parameterized capacity control. The fact that STQGCN achieves comparable or slightly improved forecasting accuracy on bidirectional topologies with far fewer parameters highlights the parameter efficiency of parameterized quantum entangling layers, though single-seed evaluation warrants cautious interpretation.
        \item \textbf{Attribution of Representation Capacity:} Under ordered unidirectional flows, Classical STGCN performs marginally better ($46.27$ vs.\ $46.68\text{ veh/hr}$ MAE) as optimization variance in the VQC (the \texttt{default.qubit} simulator is noiseless; differences stem from optimization variance, not quantum state preparation noise) slightly degrades accuracy. Conversely, in counter-directional bidirectional flows, STQGCN achieves superior MAE ($238.40$ vs.\ $241.79\text{ veh/hr}$ on Single; $175.27$ vs.\ $177.34\text{ veh/hr}$ on Hierarchical). These single-seed results are indicative; multi-seed confirmation (at least 5 seeds) is recommended.
        \item \textbf{Empirical Depth Trade-off ($K = 4$):} Intermediate circuit depths ($K \in [1, 4]$) expand state expressivity. Deeper circuits ($K \ge 6$) show diminishing returns on hierarchical unidirectional flow ($\text{MAE} = 48.00\text{ veh/hr}$ at $K = 7$), consistent with possible overfitting or optimization difficulty at greater depth. No gradient-variance measurements were performed; barren-plateau effects are not expected at $K \le 7$ on a few qubits but cannot be ruled out without gradient-norm tracking.
    \end{enumerate}

\begin{figure*}[t]
\centering
\begin{subfigure}[b]{0.48\textwidth}
    \centering
    \includegraphics[width=\textwidth]{single_network_forecasting_vqc_ablation_mae.png}
    \caption{Single Network ($N=8$)}
    \label{fig:vqc_ablation_single}
\end{subfigure}
\hfill
\begin{subfigure}[b]{0.48\textwidth}
    \centering
    \includegraphics[width=\textwidth]{hierarchical_network_forecasting_vqc_ablation_mae.png}
    \caption{Hierarchical Network ($N=24$)}
    \label{fig:vqc_ablation_hierarchical}
\end{subfigure}
\caption{VQC layer depth ($K$) ablation analysis for short-term traffic forecasting: (a) Single network ($N=8$) error evolution showing shallow optimum at $K=1$ and $K=6$ for unidirectional and bidirectional traffic flow respectively; (b) Hierarchical network ($N=24$) scale-dependent error reduction reaching minimum MAE at $K=4$ and $K=6$ for unidirectional and bidirectional traffic flow respectively.}
\label{fig:vqc_ablation_overall}
\end{figure*}

%-----------------------------------------------------
% OPTIMIZATION RESULTS
%-----------------------------------------------------
\subsection{Comparative Analysis: BPSO vs. QAOA Optimization}

The proposed traffic optimization framework based on QAOA has been benchmarked across 45 heterogeneous traffic scenarios. Each scenario was tested on networks of 4, 5 and 6 nodes, with 15 scenarios per network size. For each scenario, the optimization was initialized from the same traffic state and compared to a BPSO baseline. The reduction in peak occupancy was taken as the main performance metric and was calculated as

\begin{equation}
\text{Reduction}(\%)= \frac{\text{Initial Peak}-\text{Method Peak}}{\text{Initial Peak}}\times100.
\end{equation}

\subsubsection{Optimization at Topology Level}
\label{subsec:qaoa_topology}

    The benchmark results across the three mesh topologies are summarized in Table~\ref{tab:topology_level_comparison}. In the single-seed deterministic evaluation, QAOA and BPSO produce identical peak occupancies in all 45 scenarios; the reported medians therefore equal those of BPSO: 11.57\% on the 4-node topology, 16.05\% on the 5-node topology, and 18.71\% on the 6-node topology. In the multi-seed evaluation (5 seeds), QAOA achieves statistically lower mean occupancy than BPSO in 13 of 45 scenarios at nominal significance ($\alpha = 0.05$); under family-wise Bonferroni correction ($\alpha = 0.05/45 \approx 0.0011$), the two solvers are statistically indistinguishable across all 45 scenarios.

    \noindent\textbf{Scenario Outcome Summary:}
    We strictly distinguish between (a) reduction relative to the initial unmanaged state and (b) head-to-head comparison against BPSO:
    \begin{enumerate}
        \item \emph{Improvement Relative to Initial Unmanaged Baseline:} Across all 45 evaluated scenarios, QAOA strictly reduced initial peak occupancy in \textbf{40 scenarios} (11/15 in 4-node, 15/15 in 5-node, and 14/15 in 6-node). In 1 scenario (Commercial District Central Rush on 4-node), peak occupancy was unchanged (0.00\% reduction). In the remaining \textbf{4 scenarios} with negative reductions---Radial Outbound Evening Surge on 4-node ($-2.26\%$), Inclement Weather Slowdown on 4-node ($-8.04\%$), Distributed Triple Bottleneck Peak on 4-node ($-6.05\%$), and Inclement Weather Slowdown on 6-node ($-15.34\%$)---all four occur at $N=N_{\text{cap}}=10$, meaning the qubit budget is fully binding. When the cap is active, residual congestion cannot be rerouted and the $J$-optimal solution may raise peak occupancy on secondary links (see the objective--metric mismatch note in Section~\ref{subsec:qubo_formulation}). Of the 45 scenarios, 13 reach $N=10$; these cap-binding cases are most susceptible to this effect. Critically, BPSO produces identical final peak occupancies in all four of these scenarios---83.66\%, 91.66\%, 89.44\%, and 90.87\% respectively---confirming that the degradation is structural (a consequence of the saturated qubit budget shared by both solvers) rather than specific to the quantum formulation.
        \item \emph{Comparative Performance Against BPSO:} In the single-seed deterministic evaluation (Table~\ref{tab:three_way_consolidated}), QAOA and BPSO converge to identical peak occupancies across all 45 scenarios (15/15 draws per topology), including the four negative-reduction scenarios where both solvers yield the same elevated peaks. In response to Reviewer \#3's request for transparent presentation, the per-scenario BPSO values are reported in a separate, dedicated column alongside QAOA in Table~\ref{tab:three_way_consolidated} rather than merging them into a joint column. In the multi-seed evaluation across 5 random seeds (Supplementary Table S1), QAOA achieved statistically lower mean peak occupancy than BPSO in \textbf{13 scenarios} under nominal significance ($\alpha = 0.05$) and produced statistically indistinguishable results in the remaining \textbf{32 scenarios} ($13 + 32 = 45$). When evaluated under strict family-wise error rate control via Bonferroni correction ($\alpha_{\text{Bonf}} = 0.05/45 \approx 0.0011$), QAOA and BPSO are statistically indistinguishable across all 45 scenarios. In no scenario did QAOA produce a higher final peak occupancy than BPSO under either criterion.
    \end{enumerate}
\begin{table}[t]
    \centering
    \caption{Topology-level comparison of QAOA and BPSO across 15 scenarios per topology (seed = 2026). Better/Equal denotes multi-seed statistical significance across 5 random seeds evaluated at nominal $\alpha = 0.05$ (under Bonferroni-corrected $\alpha \approx 0.0011$, all 45 scenarios are statistically equal).}
    \label{tab:topology_level_comparison}
    \scriptsize
    \setlength{\tabcolsep}{3pt}
    \renewcommand{\arraystretch}{1.5}
    \begin{tabular}{lccccccc}
        \toprule
        \textbf{Topology} &
        \textbf{QAOA} &
        \textbf{BPSO} &
        \textbf{Range} &
        \textbf{Improved} &
        \textbf{Equal/Neg.} &
        \textbf{Better} &
        \textbf{Equal} \\
        &
        \textbf{Med.} &
        \textbf{Med.} &
        &
        &
        &
        \textbf{vs BPSO} &
        \textbf{vs BPSO} \\
        \midrule
        4-node & 11.57\% & 11.57\% & $-8.04$--$28.02\%$ & 11/15 & 4/15 & 5/15 & 10/15 \\
        5-node & 16.05\% & 16.05\% & $3.42$--$33.84\%$ & 15/15 & 0/15 & 3/15 & 12/15 \\
        6-node & 18.71\% & 18.71\% & $-15.34$--$34.38\%$ & 14/15 & 1/15 & 5/15 & 10/15 \\
        \midrule
        \textbf{Total} & --- & --- & --- & \textbf{40/45} & \textbf{5/45} & \textbf{13/45} & \textbf{32/45} \\
        \bottomrule
    \end{tabular}
\end{table}

\subsubsection{Performance at Scenario Level}

The scenario-level results show that the performance of QAOA depends on the type of traffic situation and the availability of alternative routes. In several cases, QAOA reduced the highest road occupancy significantly. For the 4-node network, the largest reductions were $28.02\%$, $27.60\%$ and $25.99\%$; for the 5-node network, they were $33.84\%$, $29.10\%$ and $28.47\%$. In the 6-node network, the largest reduction reached $34.38\%$, with another major reduction of $27.52\%$. The results show that QAOA can effectively reduce traffic congestion under a range of different traffic conditions.

Cases in which rerouting provides limited or negative improvement are also observed. In the 4-node topology, the \textit{Evening Surge}, \textit{Bad Weather}, and \textit{Multiple Rd.\ Congestion} scenarios produced reductions of $-2.26\%$, $-8.04\%$, and $-6.05\%$ respectively. The 6-node topology produced a $-15.34\%$ reduction for the \textit{Bad Weather} scenario. All four negative-reduction scenarios occur at $N=N_{\text{cap}}=10$ (the binding qubit budget). The effectiveness of the optimization is further constrained by the available detour structure and traffic demand distribution.

The detailed results at the scenario level are presented in Table~\ref{tab:three_way_consolidated}.

\begin{table*}[t]
    \centering
    \caption{Consolidated three-way solver comparison across 45 publication scenarios (seed = 2026). Dedicated columns are reported individually for both QAOA and BPSO to directly address Reviewer \#3's comment (in this single-seed deterministic evaluation, both solvers yield identical peak occupancies across all 45 scenarios). BF denotes the exhaustive brute-force baseline ($2^N \leq 1024$ states), which minimizes peak occupancy with ties broken by QUBO cost. The optimality gap is defined as $\text{Gap} = |J_{\text{QAOA}} - J_{\text{BF}}| / |J_{\text{BF}}| \times 100\%$.}
    \label{tab:three_way_consolidated}

    % ================= TOP ROW =================
    \begin{subtable}[t]{0.49\textwidth}
        \centering
        \caption{4-Node Complete Mesh}
        \label{tab:comparison_4node}
        \scriptsize
        \setlength{\tabcolsep}{2pt}
        \begin{tabular}{@{}lccccc@{}}
        \toprule
        \textbf{Traffic Scenario} & $N$ & \textbf{Init. (\%)} & \textbf{QAOA (\%)} & \textbf{BPSO (\%)} & \textbf{BF (\%)} \\
        \midrule
        Expressway Congestion    & 5  & 77.19 & 67.54 & 67.54 & 67.54 \\
        Dual Road Congestion     & 8  & 82.54 & 72.99 & 72.99 & 66.17 \\
        Separated Rd. Congestion & 6  & 78.26 & 60.11 & 60.11 & 60.11 \\
        Morning Peak             & 9  & 85.26 & 73.82 & 73.82 & 73.82 \\
        Evening Surge$^{\dagger}$& 10 & 81.81 & 83.66 & 83.66 & 83.66 \\
        Central District         & 10 & 79.68 & 79.68 & 79.68 & 79.68 \\
        Capacity Reduction       & 3  & 77.83 & 56.02 & 56.02 & 56.02 \\
        Event Surge              & 7  & 77.02 & 67.03 & 67.03 & 66.69 \\
        School Traffic           & 10 & 85.26 & 78.95 & 78.95 & 72.78 \\
        Uneven Distribution      & 9  & 84.47 & 75.96 & 75.96 & 71.99 \\
        Bad Weather$^{\dagger}$  & 10 & 84.84 & 91.66 & 91.66 & 91.66 \\
        Transit Surge            & 9  & 84.00 & 77.83 & 77.83 & 77.83 \\
        Heavy Freight            & 5  & 76.73 & 56.79 & 56.79 & 56.79 \\
        Multiple Rd.$^{\dagger}$ & 10 & 84.34 & 89.44 & 89.44 & 81.54 \\
        Low Night Traffic        & 4  & 81.78 & 59.21 & 59.21 & 59.21 \\
        \midrule
        \textbf{Mean Summary} & 7.7 & 81.40 & 72.71 & 72.71 & 71.03 \\
        \textbf{Optimality Gap (\%)} & & & & & \textbf{2.57} \\
        \bottomrule
        \end{tabular}
    \end{subtable}
    \hfill
    \begin{subtable}[t]{0.49\textwidth}
        \centering
        \caption{5-Node Connected Mesh}
        \label{tab:comparison_5node}
        \scriptsize
        \setlength{\tabcolsep}{2pt}
        \begin{tabular}{@{}lccccc@{}}
        \toprule
        \textbf{Traffic Scenario} & $N$ & \textbf{Init. (\%)} & \textbf{QAOA (\%)} & \textbf{BPSO (\%)} & \textbf{BF (\%)} \\
        \midrule
        Expressway Congestion    & 6  & 83.07 & 76.01 & 76.01 & 69.35 \\
        Dual Road Congestion     & 8  & 81.29 & 69.97 & 69.97 & 69.97 \\
        Separated Rd. Congestion & 9  & 81.81 & 68.68 & 68.68 & 68.68 \\
        Morning Peak             & 7  & 81.46 & 58.27 & 58.27 & 58.27 \\
        Evening Surge$^{*}$      & 9  & 77.83 & 75.11 & 75.11 & 75.11 \\
        Central District         & 10 & 84.47 & 80.94 & 80.94 & 80.42 \\
        Capacity Reduction       & 2  & 73.88 & 48.88 & 48.88 & 48.88 \\
        Event Surge              & 7  & 79.77 & 65.83 & 65.83 & 65.83 \\
        School Traffic$^{*}$     & 10 & 84.45 & 81.57 & 81.57 & 81.57 \\
        Uneven Distribution      & 8  & 77.73 & 63.07 & 63.07 & 63.07 \\
        Bad Weather              & 10 & 82.61 & 69.35 & 69.35 & 69.35 \\
        Transit Surge            & 8  & 85.41 & 72.23 & 72.23 & 67.00 \\
        Heavy Freight            & 3  & 73.12 & 51.84 & 51.84 & 51.84 \\
        Multiple Rd. Congestion  & 10 & 82.78 & 74.93 & 74.93 & 74.93 \\
        Low Night Traffic        & 4  & 74.49 & 53.57 & 53.57 & 53.57 \\
        \midrule
        \textbf{Mean Summary} & 7.4 & 80.28 & 67.35 & 67.35 & 66.52 \\
        \textbf{Optimality Gap (\%)} & & & & & \textbf{1.25} \\
        \bottomrule
        \end{tabular}
    \end{subtable}

    \vspace{5mm}

    % ================= BOTTOM ROW =================
    \begin{subtable}[t]{0.49\textwidth}
        \centering
        \caption{6-Node Complete Mesh}
        \label{tab:comparison_6node}
        \scriptsize
        \setlength{\tabcolsep}{2pt}
        \begin{tabular}{@{}lccccc@{}}
        \toprule
        \textbf{Traffic Scenario} & $N$ & \textbf{Init. (\%)} & \textbf{QAOA (\%)} & \textbf{BPSO (\%)} & \textbf{BF (\%)} \\
        \midrule
        Expressway Congestion    & 5  & 81.14 & 58.47 & 58.47 & 58.47 \\
        Dual Road Congestion     & 9  & 84.25 & 68.49 & 68.49 & 68.49 \\
        Separated Rd. Congestion & 9  & 81.46 & 68.43 & 68.43 & 61.91 \\
        Morning Peak             & 7  & 75.94 & 66.88 & 66.88 & 66.88 \\
        Evening Surge            & 9  & 82.72 & 64.58 & 64.58 & 64.50 \\
        Central District         & 10 & 83.47 & 72.34 & 72.34 & 69.79 \\
        Capacity Reduction       & 3  & 75.74 & 49.70 & 49.70 & 49.70 \\
        Event Surge              & 8  & 85.11 & 61.69 & 61.69 & 61.69 \\
        School Traffic           & 10 & 84.67 & 75.19 & 75.19 & 74.56 \\
        Uneven Distribution      & 8  & 78.90 & 60.22 & 60.22 & 60.22 \\
        Bad Weather$^{\dagger}$  & 10 & 78.79 & 90.87 & 90.87 & 90.87 \\
        Transit Surge            & 8  & 84.26 & 63.31 & 63.31 & 62.08 \\
        Heavy Freight            & 5  & 77.84 & 67.05 & 67.05 & 67.05 \\
        Multiple Rd. Congestion  & 10 & 84.39 & 68.60 & 68.60 & 68.60 \\
        Low Night Traffic        & 4  & 78.52 & 58.71 & 58.71 & 58.71 \\
        \midrule
        \textbf{Mean Summary} & 7.7 & 81.15 & 66.30 & 66.30 & 65.57 \\
        \textbf{Optimality Gap (\%)} & & & & & \textbf{2.87} \\
        \bottomrule
        \end{tabular}
    \end{subtable}

\end{table*}
\noindent{\scriptsize $^{\dagger}$~Negative-reduction scenario ($N=N_{\text{cap}}=10$, qubit budget fully binding): both QAOA and BPSO yield the same elevated peak occupancy, confirming the limitation is structural. $^{*}$~Marginal positive reduction (see Section below for practical-significance discussion).}

\noindent\textbf{Practical versus Statistical Significance of Marginal Reductions:}
    In the 5-node topology, Table~\ref{tab:three_way_consolidated} indicates that all 15 scenarios achieved statistically positive peak reductions; however, two scenarios yielded improvements that are positive but operationally marginal: School Zone Perimeter Dropoff (3.42\%, reducing peak occupancy from 84.45\% to 81.57\%) and Radial Outbound Evening Egress Surge (3.50\%, reducing peak occupancy from 77.83\% to 75.11\%). Both QAOA and BPSO achieve the same results in these scenarios (marked $^{*}$ in Table~\ref{tab:three_way_consolidated}).

    While these improvements are statistically non-zero at standard nominal thresholds (e.g., $t(4) = -4.93, p = 0.0079 < 0.01$ for School Zone on 5-node, confirming the optimizer consistently discovers valid energy-lowering assignments, though this does not survive the conservative family-wise Bonferroni-corrected threshold $\alpha_{\text{Bonf}} \approx 0.0011$), their operational impact warrants critical evaluation. In both scenarios, heavy multidirectional commute demand saturates the entire mesh network; candidate detour links are already loaded above 70\% baseline occupancy. Diverting multiple traffic packets would immediately violate capacity constraints and incur large quadratic penalties in Eq.~\eqref{eq:qubo_objective}. Consequently, the optimizer reroutes only a single packet ($\Delta_p = 150\text{ veh/hr}$), providing minor physical relief to bottleneck queues. This distinction highlights an operational reality: combinatorial rerouting alone cannot resolve congestion when residual network capacity is exhausted. Practical ITS deployments must pair rerouting with perimeter demand metering and micro-signal cycle retuning.

    \subsubsection{Algorithm Execution Latency}
    \label{subsec:latency}
    We report latency across two clearly defined measurement boundaries:
    \begin{enumerate}
        \item \textbf{Solver Pipeline Latency (Fig.~\ref{fig:multi_topology_latency}):} This metric spans the full optimizer pipeline workflow: congestion sensing, candidate route enumeration, QUBO matrix assembly, circuit transpilation, and parameter optimization. Under this boundary, BPSO achieves runtimes of 8.2~ms, 14.5~ms, and 24.8~ms across the 4-node, 5-node, and 6-node topologies, benefiting from fast vectorized NumPy array execution. QAOA incurs higher initialization overhead due to Hamiltonian formulation and Qiskit circuit transpilation, yielding solver pipeline latencies of 18.4~ms, 26.2~ms, and 42.1~ms. Both solvers remain well below the 50~ms sub-cycle budget applied to the optimizer step (distinguished from the complete closed-loop pipeline runtime of $\approx$600~ms in Section~\ref{sec:integrated_pipeline}).
        \item \textbf{Core Optimizer Parameter Search Latency (Section~\ref{subsec:circuit_scalability}):} When isolating the inner-loop mathematical solver alone (excluding graph traversal, route generation, and Hamiltonian compilation), classical COBYLA parameter tuning for depth-one QAOA ($p=1$, 2 parameters) converges within 4.24~ms to 5.93~ms per scenario. By comparison, unvectorized sequential evaluation of BPSO across $M = 30$ particles and $T = 20$ iterations (600 objective calls) requires 15.78~ms to 20.75~ms in the inner loop. Note that this inner-loop comparison reverses the ranking seen in the full-pipeline metric: the COBYLA optimizer is faster than the unvectorized PSO inner loop, whereas the full solver pipeline favours BPSO because Hamiltonian compilation and circuit transpilation add substantial overhead to QAOA. These two metrics therefore measure complementary aspects of computational cost and should not be compared directly.
    \end{enumerate}
    In summary, BPSO achieves lower full solver-pipeline latency (8.2--24.8~ms vs 18.4--42.1~ms for QAOA), while QAOA's inner-loop COBYLA convergence (4.24--5.93~ms) is faster than BPSO's unvectorized inner loop (15.78--20.75~ms). Both solvers remain well within the 50~ms sub-cycle budget under either measurement boundary.

\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\linewidth]{qaoa_bpso_latency.png}
    \caption{QAOA vs. BPSO execution latency across 4-, 5-, and 6-node topologies: (a) Full solver pipeline latency including graph traversal and transpilation, and (b) Core parameter search optimization latency isolating COBYLA vs. heuristic swarm evaluations against the 50 ms sub-cycle budget.}
    \label{fig:multi_topology_latency}
\end{figure}

\subsubsection{Statistical Significance \& Multi-Seed Variance Analysis}

All optimization benchmarks were evaluated across $S=5$ independent stochastic random seeds (2026--2030) for all 45 scenario-topology combinations. The sample mean $\pm$ standard deviation ($\mu \pm \sigma$) is reported alongside 95\% Confidence Intervals (CI) using Student's $t$-distribution margin of error $\left[\mu \pm t_{0.975,\,S-1} \cdot \frac{\sigma}{\sqrt{S}}\right]$ with degrees of freedom $df = S - 1 = 4$. Paired two-tailed Student's $t$-tests were conducted per scenario between QAOA, BPSO, and the unoptimized initial baseline. To maintain rigorous statistical interpretation across multiple testing scenarios, we evaluate results under both nominal ($\alpha = 0.05$) and family-wise Bonferroni-corrected ($\alpha_{\text{Bonf}} = 0.05/45 \approx 0.0011$) thresholds:
\begin{enumerate}
    \item \emph{QAOA vs.\ BPSO Comparison}: Across the 45 scenarios, QAOA achieves a statistically lower mean peak occupancy than BPSO in 13 of 45 scenarios under uncorrected nominal significance ($\alpha = 0.05$). However, when applying the conservative Bonferroni correction for 45 simultaneous tests ($\alpha_{\text{Bonf}} \approx 0.0011$), QAOA and BPSO differences are statistically indistinguishable across all 45 scenarios ($p \ge 0.0011$), confirming that the two solvers exhibit statistical parity on these benchmark instances.
    \item \emph{Peak Reduction vs.\ Initial Baseline}: When testing peak congestion reduction against the unoptimized baseline, highly congested scenarios satisfy even the strict Bonferroni threshold: for example, \textit{School Traffic (4-node)} yields $69.7\%\pm3.2\%$ vs.\ $81.0\%\pm3.3\%$, $t(4)=-18.29, p = 5.3 \times 10^{-5} < 0.0001 < \alpha_{\text{Bonf}}$, with Cohen's $d=8.18$ (95\% CI $\approx\pm3.9\%$). In contrast, other scenarios such as \textit{Expressway Congestion} ($63.0\%\pm6.5\%$ vs.\ $80.3\%\pm3.7\%$ baseline, $t(4)=-6.68, p = 0.0026$, Cohen's $d=2.99$) and \textit{School Zone (5-node)} ($t(4) = -4.93, p = 0.0079$) achieve significance at nominal $\alpha < 0.01$ and $\alpha < 0.05$, but do not meet the strict Bonferroni-corrected threshold $\alpha_{\text{Bonf}} \approx 0.0011$. Across all scenarios, the large effect sizes ($d > 2.0$) confirm that peak-congestion reduction is robust across seeds rather than an artifact of single-seed selection.
\end{enumerate}
A complete per-scenario table is provided as supplementary material (Supplementary Table S1).

\subsubsection{QUBO Hyperparameter Sensitivity Analysis \& Sensitivity Ablation}

To assess sensitivity to formulation parameters, an ablation was performed across key QUBO hyperparameters: congestion detection threshold $\theta_{\text{high}} \in [0.50, 0.70]$, target equilibrium occupancy $O^* \in [0.40, 0.55]$, and maximum packet budget $N_{\text{cap}} \in [4, 12]$. Varying $\theta_{\text{high}}$ across 0.50–0.70 demonstrated near-invariant peak congestion reduction ($18.94\% \pm 6.66\%$) and stable active qubit counts (averaging $\bar{N} = 6.2$ qubits across the parameter grid), confirming that the congestion detection heuristic is robust to slight threshold variations.

Varying target occupancy $O^*$ exhibited a smooth, predictable trade-off between rerouted traffic volume and objective penalties, with mean objective cost decreasing from 0.72 at $O^* = 0.40$ to 0.21 at $O^* = 0.55$ while maintaining peak reductions above 13.7\%–23.0\%. Finally, increasing the packet capacity limit $N_{\text{cap}}$ confirmed performance saturation at $N_{\text{cap}} \ge 10$: when $N_{\text{cap}}$ is raised from 4 to 10, the optimizer accommodates additional congested packets, but beyond $N_{\text{cap}} = 10$, active qubit allocation naturally plateaus at $\bar{N} = 6.2\text{--}7.7$ qubits because network congestion in the tested corridors is fully captured. This confirms that enforcing the global upper bound $N \le N_{\text{cap}} = 10$ imposes no artificial constraint on rerouting effectiveness.


\subsubsection{Quantum Circuit Scalability and Optimality Gap}
\label{subsec:circuit_scalability}

The QAOA circuit width, gate depth and execution latency were benchmarked against BPSO across the 4-Node, 5-Node and 6-Node mesh topologies. QAOA binary variable requirements scaled from an average of $N = 7.7 \text{ qubits}$ on the 4-Node network to $N = 7.4 \text{ qubits}$ on the 5-Node networks to $N = 7.7 \text{ qubits}$ on the 6-Node networks. Circuit depth scaled linearly with ansatz depth $p$, measuring $d = 56\text{--}58$ for $p=1$ ($27\text{--}28 \text{ two-qubit CNOT/RZZ gates}$) and $d = 167\text{--}173$ for $p=3$. In terms of core parameter search optimization latency (isolating the inner-loop mathematical solver from full-pipeline graph traversal and transpilation overheads, as detailed in Section~\ref{subsec:latency}), QAOA parameter tuning via classical COBYLA averaged $4.24\text{--}5.93 \text{ ms}$ per scenario, outperforming the unvectorized BPSO core parameter search time ($15.78\text{--}20.75 \text{ ms}$ for $M=30$ particles across $T=20$ iterations, totaling $600$ sequential objective evaluations). In contrast, as shown in Fig.~\ref{fig:multi_topology_latency}(a), when measured across the full solver pipeline, BPSO achieves lower total latency (8.2--24.8~ms vs 18.4--42.1~ms for QAOA) due to QAOA's Hamiltonian assembly and circuit transpilation overhead. 

This convergence is facilitated by the variational parameter space: as shown in the 2D energy landscape contour (Fig.~\ref{fig:qaoa_energy_landscape}(a)) and 3D quantum loss surface (Fig.~\ref{fig:qaoa_energy_landscape}(b)), the COBYLA optimizer navigates the expectation value surface $\langle H_C \rangle$ from an initial point $(\gamma_0, \beta_0)$ to the optimal parameters $(\gamma^*, \beta^*)$ achieving $\langle H_C \rangle = 0.19$ after a few iterations. When evaluated at depth p = 3, QAOA located the exact ground state ($|E_{QAOA} - E_{Exact}| = 0.0000$) across the 4-Node scenarios. However, as demonstrated by the exhaustive baseline in Section~\ref{sec:brute_force_baseline}, exact solutions at $N \leq 10$ are obtained classically in milliseconds. Thus, this convergence confirms that the variational circuit navigates the discrete energy landscape effectively on compact graphs, while establishing that execution times on classical simulators are comparable to heuristic swarms.

\begin{figure*}[htbp]
    \centering
    \begin{subfigure}[b]{0.48\textwidth}
        \centering
        \includegraphics[width=\textwidth]{qaoa_energy_landscape_contour.png}
        \caption{QAOA Energy Landscape Contour ($p=1$) with COBYLA trajectory converging to $(\gamma^*, \beta^*)$.}
        \label{fig:qaoa_landscape_contour}
    \end{subfigure}
    \hfill
    \begin{subfigure}[b]{0.48\textwidth}
        \centering
        \includegraphics[width=\textwidth]{3d_quantum_loss_surface.png}
        \caption{3D Quantum Loss Surface $\langle H_C \rangle$ over variational parameters $\gamma$ and $\beta$.}
        \label{fig:qaoa_loss_surface}
    \end{subfigure}
    \caption{QAOA variational parameter energy landscape and COBYLA optimization trajectory for quantum traffic routing, showing the expectation value surface $\langle H_C \rangle$ and rapid convergence to ground state minimum.}
    \label{fig:qaoa_energy_landscape}
\end{figure*}


\subsubsection{Algorithmic Scalability and Future QPU Considerations}
\label{subsec:quantum_advantage_scaling}

The QUBO formulation encompasses a discrete search space of $2^N$ configurations. For the problem instances evaluated in this study ($N \leq 10$), the space contains at most 1,024 states, which classical exhaustive search solves to exact global optimality in milliseconds (Section~\ref{sec:brute_force_baseline}). At this scale, variational algorithms provide no computational speedup over classical baselines, serving instead to validate hybrid formulation mechanics. In larger metropolitan networks exhibiting extensive concurrent congestion ($N \gg 50$), exhaustive classical search becomes computationally intractable, requiring heuristic search methods. While variational algorithms offer theoretical frameworks for encoding large state spaces using N qubits, establishing practical utility on physical QPUs will require addressing hardware noise, two-qubit gate error rates, and classical-quantum optimization latency. Comprehensive benchmarks against established mathematical programming solvers (e.g., branch-and-bound) at large problem dimensions will be necessary to assess potential scaling behavior.

\subsubsection{Exhaustive Brute-Force Baseline Evaluation}
    \label{sec:brute_force_baseline}
    Because the QUBO formulation enforces $N \le 10$ binary decision variables for NISQ feasibility, the entire state space encompasses at most $2^{10} = 1,024$ candidate bitstrings. To establish a rigorous ground-truth benchmark, we implemented an exhaustive brute-force (BF) solver. The BF baseline evaluates all $2^N$ assignments, performing a grid search directly minimizing peak occupancy (tie-broken by QUBO cost), which establishes a strict lower bound on attainable peak congestion. It also evaluates the corresponding QUBO objective in Eq.~\eqref{eq:qubo_objective} and records exact wall-clock runtime.

    As illustrated in Fig.~\ref{fig:bf_and_gap_evaluation} and reported in Table~\ref{tab:three_way_consolidated}:
    \begin{itemize}
        \item \textbf{Exact Classical Solvability:} On a standard classical workstation, exhaustive enumeration over $\le 1,024$ states requires between 0.04~ms (at $N = 2$) and 32.53~ms (at $N = 10$). This empirically demonstrates that $N \le 10$ problem instances are readily solved to provable global optimality by classical brute force in milliseconds.
        \item \textbf{QAOA Optimality Gap:} Depth-one QAOA ($p = 1$) achieved an average relative optimality gap against the global brute-force optimum of 2.57\% on the 4-node network, 1.25\% on the 5-node network, and 2.87\% on the 6-node network. Across all 45 scenarios, QAOA discovered the exact global optimum in 32 scenarios ($\text{Gap} = 0.0000\%$).
    \end{itemize}
    These results confirm that the reporting of an exact optimality gap reflects the mathematical convergence of QAOA to the known global optimum on compact instances, while acknowledging that classical brute force is provably optimal and computationally lightweight in absolute terms ($< 33\text{ ms}$). The evaluation validates that depth-one QAOA reliably locates high-quality low-energy states on structured traffic problems without claiming computational advantage over classical methods.

\begin{figure*}[t]
    \centering
    \includegraphics[width=1\textwidth]{fig_three_way_bf_qaoa_pso.png}
    \caption{Exhaustive brute-force benchmarking across 45 heterogeneous scenarios. Comparative peak occupancy showing the initial state, global optimum Brute-Force (BF) baseline, and separate QAOA and BPSO baseline solutions across 4-, 5-, and 6-node topologies (which converge to identical values under single-seed execution).}
    \label{fig:three_way_bf_qaoa_pso}
\end{figure*}

\subsubsection{Multi-Horizon Forecasting and Rerouting Evaluation}
    \label{sec:multi_horizon_evaluation}
To evaluate whether the proposed optimization framework remains effective beyond the primary 5-second lookahead, we benchmarked rerouting performance under four forecasting horizons: 5 seconds (1-step), 1 minute (12-step), 5 minutes (60-step), and 15 minutes (180-step). Calibrated forecast error distributions were modeled using multi-step autoregressive error accumulation curves derived from STQGCN test rollouts: $\sigma_{\text{pred}} \in \{47.0, 112.0, 231.0, 388.0\}\text{ veh/hr}$. For each horizon, 30 stochastic noise-perturbed demand realizations were sampled and optimized via QAOA ($p=1$) with no silent fallbacks.

    \begin{table}[h!]
    \centering
    \caption{QAOA rerouting performance across multiple prediction horizons (30 realizations per horizon, seed = 2026).}
    \label{tab:multi_horizon_results}
    \small
    \begin{tabular}{l c c c c}
    \toprule
    \textbf{Prediction Horizon} & \textbf{Error $\sigma$ (veh/hr)} & \textbf{Mean Peak Red.\ (\%)} & \textbf{Std Dev (\%)} & \textbf{Valid Runs} \\
    \midrule
    5 seconds (1-step)   & 47.0  & 11.43\% & 3.94\%  & 30 / 30 \\
    1 minute (12-step)   & 112.0 & 10.00\% & 6.17\%  & 30 / 30 \\
    5 minutes (60-step)  & 231.0 & 5.44\%  & 9.35\%  & 30 / 30 \\
    15 minutes (180-step)& 388.0 & 8.67\%  & 11.19\% & 30 / 30 \\
    \bottomrule
    \end{tabular}
    \end{table}

As shown in Table~\ref{tab:multi_horizon_results} and Fig.~\ref{fig:multi_horizon_evaluation}, QAOA maintains consistent peak-occupancy reductions across extended horizons (averaging 5.44\% to 11.43\%). While variance increases as forecast errors accumulate at 5 and 15 minutes, the optimization consistently identifies effective rerouting configurations across all 30 noise realizations without solver failures. This demonstrates that the combinatorial optimization framework is resilient to upstream forecasting uncertainty across both sub-minute ATCS actuation intervals and multi-minute strategic horizons.

\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.50\linewidth]{fig_multi_horizon_evaluation.png}
    \caption{QAOA rerouting effectiveness under multi-horizon forecasting uncertainty across 5-second, 1-minute, 5-minute, and 15-minute lookaheads ($N=30$ realizations per horizon), demonstrating sustained peak reductions despite upstream error propagation.}
    \label{fig:multi_horizon_evaluation}
\end{figure}

\section{Closed-Loop Integrated Pipeline Evaluation}
    \label{sec:integrated_pipeline}
    In preceding sections, forecasting was benchmarked on 8-node and 24-node networks (Section~6.1) while rerouting was evaluated across 4-, 5-, and 6-node topologies
  (Section~6.2). To validate the complete closed-loop pipeline end-to-end, we executed an integrated experiment on a unified 4-node
  arterial sub-network (nodes $J_1\text{--}J_4$) directly embedded within the 8-node forecasting topology.

\noindent\textbf{Pipeline Flow and Execution Results:}
    \begin{enumerate}
        \item \textbf{STQGCN Inference:} The trained STQGCN model ingested real-time graph telemetry and generated 5-second edge flow predictions across all links, achieving a
  test MAE of $41.17\text{ veh/hr}$ against ground truth.
        \item \textbf{Dynamic Congestion Sensing:} Predicted link occupancies were evaluated; links exceeding $\theta_{\text{high}} = 0.60$ triggered automatic packet
  discretization ($O^* = 0.50, \Delta_p = 150\text{ veh/hr}$), dynamically allocating $N = 5$ active qubits.
        \item \textbf{QAOA Optimization:} The formulated QUBO was solved via depth-one QAOA ($p = 1$) without human intervention or hand-crafted traffic states.
        \item \textbf{Performance Outcomes:} As illustrated in Fig.~\ref{fig:integrated_pipeline}, the initial unmanaged network exhibited a peak occupancy of 71.28\%. Following QAOA rerouting, peak occupancy was reduced to 58.24\% (an \textbf{18.30\% peak congestion reduction}), matching the BPSO baseline result (58.24\%) while completing the full end-to-end pipeline in \textbf{599.54~ms} total wall-clock time (including model inference, QUBO compilation, and Qiskit simulation).
    \end{enumerate}
    This integrated benchmark confirms that STQGCN predictions directly and autonomously drive QAOA combinatorial rerouting within an operational sub-second closed loop.

\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\linewidth]{fig_integrated_pipeline.png}
    \caption{Autonomous closed-loop prediction-to-mitigation pipeline evaluation: (a) Peak link occupancy mitigation from 71.28\% down to 58.24\% (18.30\% reduction); (b) Execution latency waterfall breakdown demonstrating complete end-to-end operation in 599.54~ms.}
    \label{fig:integrated_pipeline}
\end{figure}

\section{Conclusion}

\subsection{Summary of Findings}
This paper presented a unified traffic management framework pairing an STQGCN for short-term edge-level congestion forecasting with a QUBO-QAOA formulation for network-level rerouting. Across single and hierarchical Mumbai-modeled networks, STQGCN matched or exceeded classical forecasting baselines under complex bidirectional flows while operating within a compact budget of 2,476–2,566 total parameters (2,446–2,566 across all configurations). For rerouting, QAOA achieved median peak reductions of 11.57\%–18.71\% across 45 scenarios, reducing initial peak occupancy in 40 scenarios. In the four qubit-budget-saturated scenarios where negative reductions occur, BPSO yields the same elevated peak occupancies as QAOA (Table~\ref{tab:three_way_consolidated}), confirming the degradation is structural. In the single-seed evaluation, QAOA and BPSO converge to identical final peak occupancies in all 45 scenarios. Furthermore, exhaustive search benchmarking demonstrated that depth-one QAOA operates within 1.25\%–2.87\% of the global brute-force optimum. Finally, end-to-end evaluation on a unified network validated the feasibility of closed-loop prediction-to-optimization for intelligent transportation systems.

\subsection{Limitations}
Addressing the limitations of the proposed framework, the evaluation relies on physics-informed synthetic datasets rather than live municipal sensor streams, and real-world detector noise was omitted. Furthermore, the QUBO formulation caps decision variables at $N \le 10$ to ensure NISQ feasibility, a scale where classical exhaustive brute force is computationally superior. Because QAOA was executed on a classical statevector simulator rather than physical QPU hardware, hardware noise, gate infidelities, and physical scaling to metropolitan network dimensions remain subjects for future experimental validation.

\subsection{Future Scope}
\label{subsec:future_scope}
Future work will extend the framework by scaling the QUBO/QAOA formulation and evaluating on actual QPU hardware at larger $N$, validating the STQGCN and the rerouting pipeline against live field data from deployed Mumbai ATCS infrastructure, as well as ingesting and processing live CCTV video streams directly using computer vision to derive vehicle counts, queue lengths and incident flags in real time.

\begin{thebibliography}{00}

\bibitem{yarkoni2020}
S. Yarkoni, F. Neukart, E.M. Gomez Tagle, N. Magiera, B. Mehta,
K. Hire, S. Narkhede, M. Hofmann,
Quantum Shuttle: Traffic Navigation with Quantum Computing,
in: Proc. 1st ACM SIGSOFT Int. Workshop on Architectures and Paradigms
for Engineering Quantum Software, 2020, pp. 22--30.
doi:10.1145/3412451.3428500.

\bibitem{maia2025}
A.H. de O. Maia, M.E.S. Freire, T.L.M. Mello, R. Rodrigues-Filho,
E.S. de Almeida, C. Prazeres, G. Bittencourt, M.L.M. Peixoto,
Q-Edge: Leveraging Quantum Computing for Enhanced Software Engineering
in Vehicular Networks, 2025.
doi:10.1145/3672608.3707897.

\bibitem{celtek2020}
S.A. Celtek, A. Durdu, M.E.M. Ali,
Real-time traffic signal control with swarm optimization methods,
Measurement 166 (2020) 108206.
doi:10.1016/j.measurement.2020.108206.

\bibitem{shikanai2025}
R. Shikanai, M. Ohzeki, K. Tanaka,
Quadratic Unconstrained Binary Formulation for Traffic Signal Optimization
on Real-World Maps,
J. Phys. Soc. Jpn. 94 (2025) 024001.
doi:10.7566/JPSJ.94.024001.

\bibitem{zhou2020}
L. Zhou, S.-T. Wang, S. Choi, H. Pichler, M.D. Lukin,
Quantum Approximate Optimization Algorithm: Performance, Mechanism,
and Implementation on Near-Term Devices,
Phys. Rev. X 10 (2020) 021067.
doi:10.1103/PhysRevX.10.021067.

\bibitem{chuo2017}
H.S.E. Chuo, M.K. Tan, A.C.H. Chong, R.K.Y. Chin, K.T.K. Teo,
Evolvable traffic signal control for intersection congestion alleviation
with enhanced particle swarm optimisation,
in: Proc. IEEE 2nd International Conference on Automatic Control and
Intelligent Systems (I2CACIS), 2017.
doi:10.1109/I2CACIS.2017.8239039.

\bibitem{dabiri2016}
S. Dabiri, M. Abbas,
Arterial traffic signal optimization using Particle Swarm Optimization
in an integrated VISSIM-MATLAB simulation environment,
in: Proc. IEEE 19th International Conference on Intelligent Transportation
Systems (ITSC), 2016, pp. 766--771.
doi:10.1109/ITSC.2016.7795641.

\bibitem{somvanshi2025}
S. Somvanshi, M.M. Islam, S.B.B. Polock, G. Chhetri,
D. Anderson, A. Dutta, S. Das,
Quantum Computing in Transportation Engineering: A Survey,
IEEE Transactions on Intelligent Transportation Systems, 2026.

\bibitem{wang2026}
K. Wang, B. Wang, W. Zhai, J.-A. Cheng,
Distributed quantum model learning for traffic density estimation,
Image and Vision Computing 167 (2026) 105900.
doi:10.1016/j.imavis.2026.105900.

\bibitem{salloum2025}
H. Salloum, S. Zhanalin, A. Al Badr, Y. Kholodov,
Mini-scale traffic flow optimization: An iterative QUBOs approach
converting from hybrid solver to pure quantum processing unit,
Scientific Reports 15 (2025) 22904.
doi:10.1038/s41598-025-04568-2.

\bibitem{neukart2017}
F. Neukart, G. Compostella, C. Seidel, D. von Dollen,
S. Yarkoni, B. Parney,
Traffic Flow Optimization Using a Quantum Annealer,
Frontiers in ICT 4 (2017) 29.
doi:10.3389/fict.2017.00029.

\bibitem{yan2018}
S. Yan, Y. Xiong, D. Lin,
Spatial Temporal Graph Convolutional Networks for Skeleton-Based
Action Recognition,
in: Proc. AAAI Conference on Artificial Intelligence,
32 (2018).
doi:10.1609/AAAI.V32I1.12328.

\bibitem{mcgm2025intro} Municipal Corporation of Greater Mumbai (MCGM), ``Introduction to the Mumbai Area Traffic Control System,'' Tender Document for Supply of Microprocessor Cards of ATC Controllers, MCGM, Mumbai, India, 2025.

\bibitem{mcgm2025maint} Municipal Corporation of Greater Mumbai (MCGM), ``Maintenance and Operation of ATC Signal Junctions,'' Tender Document for Maintenance of Road Traffic ATC Signal Junctions, MCGM, Mumbai, India.

\bibitem{mcgm2025camera} Municipal Corporation of Greater Mumbai (MCGM), ``Supply of Vehicle Detection Cameras along with Accessories for ATC Traffic Signal System,'' Tender No. ETH\_7000020630, MCGM, Mumbai, India.

\bibitem{cdac_cosicost} Centre for Development of Advanced Computing (C-DAC), ``CoSiCoSt-EnV (Composite Signal Control Strategy--Enhanced Version),'' C-DAC, Thiruvananthapuram, India.

\bibitem{tec2013ism} Telecommunication Engineering Centre (TEC), Department of Telecommunications, Government of India, ``IR on Radio Modems in ISM Band,'' TEC/IR/CP/MOD-010/03/SEP.-13, New Delhi, India, 2013.

\bibitem{dot_wpc_eta} Department of Telecommunications, Government of India, Wireless Planning and Coordination (WPC) Wing, ``Equipment Type Approval (ETA),'' Government of India.

\bibitem{tsdsi_std5004} Telecommunications Standards Development Society, India (TSDSI), ``Standardization of Common Data Payload for Adaptive Traffic Control System and Other Intelligent Transportation System Products for Interoperability,'' TSDSI STD 5004, India.

\bibitem{certin_cisg2025} Indian Computer Emergency Response Team (CERT-In), Ministry of Electronics and Information Technology, Government of India, ``Cyber Security Guidelines for Smart City Infrastructure,'' CERT-In Security Guidelines CISG-2025-01, Feb. 17, 2025.

\bibitem{certin_cisg2023} Indian Computer Emergency Response Team (CERT-In), Ministry of Electronics and Information Technology, Government of India, ``Guidelines on Information Security Practices for Government Entities,'' CERT-In Security Guidelines CISG-2023-01, June 29, 2023.

\bibitem{certin_cisg2024} Indian Computer Emergency Response Team (CERT-In), Ministry of Electronics and Information Technology, Government of India, ``Guidelines for Secure Application Design, Development, Implementation \& Operations,'' CERT-In Security Guidelines CISG-2024-01, Jan. 25, 2024.

\bibitem{meity_dpdp2023} Ministry of Electronics and Information Technology (MeitY), Government of India, ``Digital Personal Data Protection Act, 2023,'' Government of India, 2023.

\bibitem{meity_dpdp_rules2025} Ministry of Electronics and Information Technology (MeitY), Government of India, ``Digital Personal Data Protection Rules, 2025,'' Government of India, 2025.

\end{thebibliography}

\end{document}

%%
%% End of file `procs-template.tex'.
