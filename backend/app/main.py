
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, Dict, List
from .services.loader import data, PlateQuery
from .services.pdf import render_plate_pdf, render_stocks_pdf
from .services.stocks import stock_plan

app = FastAPI(title="Lab Plate & Stock Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlatePdfGridCell(BaseModel):
    r: int
    c: int
    label: str
    control: bool = False

class PlatePdfPayload(BaseModel):
    title: str
    grid: Dict[str, Any]

class StocksPayload(BaseModel):
    day: int
    include_next_day: bool = False
    settings: Dict[str, Any]
    other_reagents: List[Dict[str, Any]]

@app.on_event("startup")
def _startup():
    data.load_all()

@app.get("/api/plate")
def get_plate(day: int = 1, plate: int = 1):
    q = PlateQuery(day=day, plate_in_day=plate)
    grid = data.plate_grid(q)
    return {"grid": grid}

@app.post("/api/plate/pdf")
def post_plate_pdf(payload: PlatePdfPayload):
    try:
        buf = render_plate_pdf(title=payload.title, grid=payload.grid)
        return StreamingResponse(buf, media_type="application/pdf", headers={
            "Content-Disposition": 'attachment; filename="plate.pdf"'
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stocks/plan")
def post_stocks_plan(payload: StocksPayload):
    try:
        out = stock_plan(day=payload.day, include_next=payload.include_next_day, settings=payload.settings, other_list=payload.other_reagents)
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stocks/pdf")
def post_stocks_pdf(payload: StocksPayload):
    try:
        plan = stock_plan(day=payload.day, include_next=payload.include_next_day, settings=payload.settings, other_list=payload.other_reagents)
        buf = render_stocks_pdf(payload.settings, payload.other_reagents, plan)
        return StreamingResponse(buf, media_type="application/pdf", headers={
            "Content-Disposition": 'attachment; filename="stocks.pdf"'
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
