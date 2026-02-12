
import React, { useEffect, useMemo, useState } from "react";
import { fetchPlate, downloadPlatePreviewPDF } from "../lib/api";

type Cell = { r:number; c:number; label:string; control:boolean };

export default function PlatePreview(){
  const [day, setDay] = useState<string>("1");
  const [plate, setPlate] = useState<string>("1");
  const [cells, setCells] = useState<Cell[]>([]);

  const title = useMemo(()=>`Day ${day} - Plate ${plate}`, [day, plate]);

  async function load(){
    const d = parseInt(day || "1") || 1;
    const p = parseInt(plate || "1") || 1;
    const res = await fetchPlate(d, p);
    const grid = res.grid;
    let out: Cell[] = (grid?.cells ?? []).map((c: any) => ({
      r: Number(c.r ?? 0),
      c: Number(c.c ?? 0),
      label: String(c.label ?? ""),
      control: Boolean(c.control ?? false) || String(c.label ?? "").trim().toUpperCase() === "CONTROL",
    }));
    setCells(out);
  }

  useEffect(()=>{ load(); /* eslint-disable-next-line */ }, []);

  const matrix: Cell[][] = useMemo(()=>{
    const m: Cell[][] = Array.from({length:4}, (_,r)=>Array.from({length:6},(_,c)=>({r, c, label:"", control:false})));
    for(const cell of cells){
      if(cell.r>=0 && cell.r<4 && cell.c>=0 && cell.c<6) m[cell.r][cell.c] = cell;
    }
    return m;
  }, [cells]);

  const rows = ["A","B","C","D"];

  function toPdfCells(m: Cell[][]){
    const list: any[] = [];
    for(let r=0;r<m.length;r++){
      for(let c=0;c<m[r].length;c++){
        const cell = m[r][c];
        list.push({
          r, c,
          label: cell.control ? "CONTROL" : cell.label,
          control: !!cell.control
        });
      }
    }
    return list;
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <div>
            <div className="text-sm opacity-80">Day</div>
            <input type="text" inputMode="numeric" pattern="[0-9]*" className="border rounded-md px-2 py-1 w-28 bg-slate-950 border-white/10" value={day} onChange={e=>setDay(e.target.value)} />
          </div>
          <div>
            <div className="text-sm opacity-80">Plate in day</div>
            <input type="text" inputMode="numeric" pattern="[0-9]*" className="border rounded-md px-2 py-1 w-28 bg-slate-950 border-white/10" value={plate} onChange={e=>setPlate(e.target.value)} />
          </div>
          <div className="flex items-end">
            <button className="px-3 py-1.5 rounded-md bg-indigo-600 hover:bg-indigo-500 transition text-white" onClick={load}>Load</button>
          </div>
          <div className="flex items-end md:col-span-2">
            <button
              className="px-3 py-1.5 rounded-md border border-white/10 hover:border-white/30"
              onClick={() => downloadPlatePreviewPDF({ title, grid: { rows:4, cols:6, cells: toPdfCells(matrix) } })}
            >
              Download plate PDF
            </button>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-4">
        <div className="text-lg md:text-xl font-semibold mb-3">{title}</div>
        <div className="overflow-auto">
          <div className="inline-grid grid-cols-[40px_repeat(6,1fr)] gap-2">
            <div></div>
            {[1,2,3,4,5,6].map(c => <div key={c} className="text-center text-sm opacity-80">{c}</div>)}
            {rows.map((rl, r) => (
              <React.Fragment key={rl}>
                <div className="text-right pr-2 text-sm opacity-80">{rl}</div>
                {matrix[r].map((cell, c) => (
                  <div key={`${r}-${c}`} className={`rounded-lg border h-20 w-36 flex items-center justify-center text-center p-1
                      ${cell.control ? 'bg-amber-100 border-amber-300' : 'bg-slate-100 border-slate-300'}
                      text-slate-900`}>
                    {cell.control ? (
                      <div className="font-semibold">CONTROL</div>
                    ) : (
                      <div className="text-xs leading-tight">
                        {cell.label.includes('/') ? (
                          <>
                            <div>{cell.label.split('/')[0].trim()}</div>
                            <div>{cell.label.split('/')[1].trim()}</div>
                          </>
                        ) : <div>{cell.label}</div>}
                      </div>
                    )}
                  </div>
                ))}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
