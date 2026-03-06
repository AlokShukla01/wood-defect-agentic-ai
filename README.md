# Wood Defect Agentic AI

Hybrid CNN-based wood defect detection system using supervised and unsupervised learning with an agentic AI backend.

This project implements a hybrid AI system for wood defect detection using:

- CNN feature extraction
- Unsupervised anomaly detection
- Supervised defect classification
- FastAPI backend
- Agentic AI decision pipeline
- React + Vite frontend dashboard

## Dataset
MVTec AD – Wood dataset

## Features
- Detect unknown defects
- Classify known defects
- Hybrid ML architecture
- API-based inference
- Interactive frontend dashboard

## Frontend (React + Vite)

The frontend interface is built using **React + Vite**.  
It provides a responsive dashboard for visualizing predictions and system metrics.

The Vite setup includes:

- Fast development server with HMR
- React Fast Refresh
- ESLint configuration for code quality

Two official plugins can be used:

- `@vitejs/plugin-react` – Uses Babel (or OXC with Rolldown) for Fast Refresh
- `@vitejs/plugin-react-swc` – Uses SWC for Fast Refresh

## Development Notes

The React Compiler is not enabled by default because it may impact development and build performance.  
For enabling it, see the React documentation:

https://react.dev/learn/react-compiler/installation

For production applications, using **TypeScript with type-aware ESLint rules** is recommended.  
See the official Vite TypeScript template for details.
