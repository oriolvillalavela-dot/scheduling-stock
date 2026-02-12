# Lab Plate & Stock Assistant

A specialized web application for designing high-throughput experimentation (HTE) plates and calculating reagent stock solutions. This tool assists in visualizing 24/48/96-well plate layouts and generating printable PDF guides for laboratory workflows.

## Features

- **Interactive Plate Visualization**: Dynamic 24/48/96-well plate views mapping reaction components.
- **Stock Solution Calculator**: Automated planning for reagent stocks based on daily schedule.
- **PDF Generation**: Export PDFs for both plate layouts and stock preparation instructions.
- **Chemical Normalization**: Automatic calculation and normalization of chemical data (IDs, SMILES, Molar Weights and Plate configuration) from Excel inputs.

## Architecture

The application follows a modern client-server architecture:

- **Frontend**: React application built with Vite, TypeScript, and TailwindCSS for a responsive user interface.
- **Backend**: FastAPI (Python) server handling data processing, Excel parsing (Pandas), and PDF generation (ReportLab).
- **Communication**: The frontend communicates with the backend via a REST API (default: `http://127.0.0.1:8000`).

## Requirements

- **Python**: 3.9+ (Verified with Python 3.x)
- **Node.js**: 18+ (Recommended for frontend build)

## Quickstart (Local Development)

Follow these steps to run the application locally.

### 1. Backend Setup

The backend servers the API and handles data processing.

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
The backend will start at `http://127.0.0.1:8000`. You can verify it is running by visiting `http://127.0.0.1:8000/docs` for the interactive API documentation.

### 2. Frontend Setup

The frontend provides the user interface.

```bash
# Open a new terminal and navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
The application will be accessible at `http://localhost:5173`.

## Configuration

### Environment Variables

| Component | Variable | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| Frontend  | `VITE_API_URL` | No | `http://127.0.0.1:8000` | Base URL of the backend API. |

To configure the frontend to talk to a different backend URL, create a `.env` file in the `frontend` directory:

```env
VITE_API_URL=http://your-backend-url:8000
```

### Data Inputs

The application reads data from Excel files located in `backend/app/data/`. If these files are missing, the system will load built-in demo data.

## API Reference

The backend provides the following REST endpoints:

- `GET /api/plate`: Retrieve the grid layout for a specific day and plate.
- `POST /api/plate/pdf`: Generate and download a PDF of the plate layout.
- `POST /api/stocks/plan`: Calculate the stock solution plan based on selected parameters.
- `POST /api/stocks/pdf`: Generate and download a PDF of the stock preparation plan.

Detailed interactive documentation is available at `/docs` when the backend is running.


## Project Structure

```
library_plates/
├── backend/
│   ├── app/
│   │   ├── data/           # Excel input files (chemicals, reactions)
│   │   ├── services/       # Core logic (loader, pdf renderer, stock calc)
│   │   ├── config.py       # Path configurations
│   │   ├── main.py         # Application entry point
│   │   └── schemas.py      # Pydantic models
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── lib/            # API client (api.ts)
│   │   ├── pages/          # React views
│   │   └── App.tsx         # Main component
│   ├── package.json        # NPM dependencies
│   └── vite.config.ts      # Vite configuration
└── README.md               # Project documentation
```

## Screenshots

![Plate Preview](docs/screenshots/plate.png)

![Stock Solutions](docs/screenshots/stocks1.png)

![Pipetting Scheme](docs/screenshots/stocks2.png)

## Acknowledgements

- **Author**: Oriol Villa Lavela
- **Affiliation**: [Roche]