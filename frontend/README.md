# Qiskit Fall Fest Frontend

This static frontend is served by Nginx and proxies `/api/*` requests to FastAPI. The backend provides the QFF 8-node topology, runs the repository's trained STQGCN K=5 checkpoint for scenario predictions, then sends those predictions to its QAOA optimizer. Returned model and optimization results are rendered in the graphs and metrics.

From the repository root, start the integrated app with:

```sh
docker compose -f optimization_algorithms/capstone-optimization/docker-compose.yml up --build
```

Open <http://localhost:5173>. The backend API is available at <http://localhost:8000>.
