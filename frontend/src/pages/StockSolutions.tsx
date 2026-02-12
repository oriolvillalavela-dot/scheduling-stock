
import React, { useMemo, useState } from "react";
import { postStockPlan, downloadStockPDF } from "../lib/api";

type PlanTotalsRow = { id_or_name:string; mw_g_mol:number|null; uses:number; eq:number; stock_M:number; per_well_uL:number|null; total_mass_mg:number|null; total_volume_mL:number|null }
type Mix = { title:string; per_well_uL:number|null; total_volume_mL:number|null; components:{name:string; mw_g_mol:number|null; mix_conc_M:number|null; total_mass_mg:number|null}[] }

type PayloadSettings = {
  eq_aryl:number; M_aryl:number;
  eq_alkyl:number; M_alkyl:number;
  mmol_limitant_per_well:number;
  overage_pct:number; include_controls:boolean
}
type Other = { name:string; eq:number; M:number; smiles?:string }

const clean = (s:string) => s.replace(',', '.')
function parseNum(v: string, def=0){
  if(v.trim()==='') return def;
  const x = parseFloat(clean(v)); return isNaN(x) ? def : x
}

export default function StockSolutions(){
  const [day, setDay] = useState<string>("1");
  const [includeNext, setIncludeNext] = useState(false);

  const [eqA, setEqA] = useState<string>("1");
  const [MA, setMA] = useState<string>("0.0313");
  const [eqL, setEqL] = useState<string>("1.5");
  const [ML, setML] = useState<string>("0.047");
  const [mmolLim, setMmolLim] = useState<string>("0.0005");
  const [over, setOver] = useState<string>("50");
  const [inclCtrl, setInclCtrl] = useState<boolean>(false);

  const [others, setOthers] = useState<Other[]>([
    { name:'TTMSS', eq:1.2, M:0.0377, smiles:'C[Si](C)(C)[SiH]([Si](C)(C)C)[Si](C)(C)C' },
    { name:'NiCl2', eq:0.05, M:0.000893, smiles:'' },
    { name:'Ir Cat', eq:0.01, M:0.000279, smiles:'' },
    { name:'dtbbpy', eq:0.06, M:0.001397, smiles:'' },
  ]);

  const payload = useMemo(()=>({
    day: parseInt(day||'1')||1,
    include_next_day: includeNext,
    settings: {
      eq_aryl: parseNum(eqA,1),
      M_aryl: parseNum(MA,0.0313),
      eq_alkyl: parseNum(eqL,1.5),
      M_alkyl: parseNum(ML,0.047),
      mmol_limitant_per_well: parseNum(mmolLim,0.0005),
      overage_pct: parseNum(over,50),
      include_controls: inclCtrl,
    } as PayloadSettings,
    other_reagents: others
  }), [day, includeNext, eqA, MA, eqL, ML, mmolLim, over, inclCtrl, others]);

  const [result, setResult] = useState<any | null>(null);

  return (
    <div className="space-y-4">
      <h2 className="text-lg md:text-xl font-semibold">Stock solutions</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-4 space-y-2">
          <div className="font-medium">Scope</div>
          <label className="text-sm">Day</label>
          <input type="text" inputMode="numeric" pattern="[0-9]*" className="border rounded-md px-2 py-1 w-28 bg-slate-950 border-white/10" value={day} onChange={e=>setDay(e.target.value)} />
          <label className="flex items-center gap-2 mt-2 text-sm"><input type="checkbox" checked={includeNext} onChange={e=>setIncludeNext(e.target.checked)} /> Include next day</label>
          <label className="flex items-center gap-2 mt-2 text-sm"><input type="checkbox" checked={inclCtrl} onChange={e=>setInclCtrl(e.target.checked)} /> Include controls</label>
        </div>

        <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-4 space-y-2">
          <div className="font-medium">Equivalents</div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <label>Aryl eq</label><input className="border rounded px-2 bg-slate-950 border-white/10" type="text" inputMode="decimal" value={eqA} onChange={e=>setEqA(e.target.value)} />
            <label>Alkyl eq</label><input className="border rounded px-2 bg-slate-950 border-white/10" type="text" inputMode="decimal" value={eqL} onChange={e=>setEqL(e.target.value)} />
            <label>Overage % (display only)</label><input className="border rounded px-2 bg-slate-950 border-white/10" type="text" inputMode="decimal" value={over} onChange={e=>setOver(e.target.value)} />
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-4 space-y-2">
          <div className="font-medium">Stocks (fixed 0.8 mL each)</div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <label>Limiting reagent mmol / well</label><input className="border rounded px-2 bg-slate-950 border-white/10" type="text" inputMode="decimal" value={mmolLim} onChange={e=>setMmolLim(e.target.value)} />
            <label>Aryl conc (M)</label><input className="border rounded px-2 bg-slate-950 border-white/10" type="text" inputMode="decimal" value={MA} onChange={e=>setMA(e.target.value)} />
            <label>Alkyl conc (M)</label><input className="border rounded px-2 bg-slate-950 border-white/10" type="text" inputMode="decimal" value={ML} onChange={e=>setML(e.target.value)} />
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-4 space-y-2">
        <div className="font-medium">Other reagents</div>
        <div className="grid grid-cols-12 gap-2 text-xs font-medium opacity-80">
          <div className="col-span-3">Name (or SMILES below)</div>
          <div className="col-span-2">eq</div>
          <div className="col-span-2">Stock M</div>
          <div className="col-span-5">SMILES (optional)</div>
        </div>
        {others.map((o,i)=> (
          <div key={i} className="grid grid-cols-12 gap-2 text-sm items-center">
            <input className="col-span-3 border rounded px-2 bg-slate-950 border-white/10" value={o.name} onChange={e=>setOthers(arr=>arr.map((x,j)=> j===i?{...x, name:e.target.value}:x))} />
            <input className="col-span-2 border rounded px-2 bg-slate-950 border-white/10" type="text" inputMode="decimal" value={String(o.eq)} onChange={e=>setOthers(arr=>arr.map((x,j)=> j===i?{...x, eq:parseNum(e.target.value, x.eq)}:x))} />
            <input className="col-span-2 border rounded px-2 bg-slate-950 border-white/10" type="text" inputMode="decimal" value={String(o.M)} onChange={e=>setOthers(arr=>arr.map((x,j)=> j===i?{...x, M:parseNum(e.target.value, x.M)}:x))} />
            <input className="col-span-5 border rounded px-2 bg-slate-950 border-white/10" placeholder="Override SMILES (optional)" value={o.smiles ?? ''} onChange={e=>setOthers(arr=>arr.map((x,j)=> j===i?{...x, smiles:e.target.value}:x))} />
            <button className="text-rose-300 text-xs" onClick={()=>setOthers(arr=>arr.filter((_,j)=>j!==i))}>remove</button>
          </div>
        ))}
        <button className="mt-2 inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-white/10 hover:border-white/30" onClick={()=>setOthers(arr=>[...arr,{name:'', eq:1, M:0.1, smiles:''}])}>Add reagent</button>
      </div>

      <div className="flex gap-2">
        <button className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-indigo-600 hover:bg-indigo-500 transition text-white" onClick={async ()=>setResult(await postStockPlan(payload))}>Compute plan</button>
        {result && <button className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-white/10 hover:border-white/30" onClick={()=>downloadStockPDF(payload)}>Download PDF</button>}
      </div>

      {result && (
        <>
          <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-3 mb-3"><div className="font-semibold">Well summary by chemical</div><div className="text-xs opacity-70">e.g., Ar-001: Plate 1 (A1, B2, ...), Plate 2 (...)</div></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
            <PlanTable title="Aryl bromides (basis: limiting reagent mmol/well)" rows={result.totals.aryl} />
            <PlanTable title="Alkyl bromides" rows={result.totals.alkyl} />
            <PlanTable title="Other reagents" rows={result.totals.others} />
          </div>
          {result.totals.mixed && <MixedCard mix={result.totals.mixed} />}

          <div className="mt-6 space-y-4">
            <SummaryBlock title="Aryl IDs" mapping={result.summaries?.aryl || {}} />
            <SummaryBlock title="Alkyl IDs" mapping={result.summaries?.alkyl || {}} />

            {result.grids.map((g:any)=>(
              <div key={g.plate} className="rounded-2xl border border-white/10 bg-slate-900/50 p-3 overflow-auto">
                <div className="font-medium mb-2">Per-well pipetting grid — Plate {g.plate}</div>
                <PerWellGrid columns={g.columns} rows={g.rows} />
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function PlanTable({title, rows}:{title:string; rows:PlanTotalsRow[]}){
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-3">
      <div className="font-medium mb-2">{title}</div>
      <div className="overflow-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-white/5">
              {['ID/Name','MW','Uses','eq','Stock M','\u03BCL / well','Total mg (for 0.8 mL)','Total mL'].map(h=> <th key={h} className="p-1 text-left">{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((r,i)=> (
              <tr key={i} className={i%2? 'bg-white/0':'bg-white/5'}>
                <td className="p-1">{r.id_or_name}</td>
                <td className="p-1">{r.mw_g_mol ?? ''}</td>
                <td className="p-1">{r.uses}</td>
                <td className="p-1">{r.eq}</td>
                <td className="p-1">{r.stock_M}</td>
                <td className="p-1">{r.per_well_uL ?? ''}</td>
                <td className="p-1">{r.total_mass_mg ?? ''}</td>
                <td className="p-1">{r.total_volume_mL ?? ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function MixedCard({mix}:{mix:Mix}){
  return (
    <div className="mt-4 rounded-2xl border border-white/10 bg-indigo-900/20 p-4">
      <div className="font-semibold text-indigo-200 mb-2">{mix.title}</div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
        <div className="bg-white/10 rounded p-2"><div className="text-xs opacity-70">Per-well (\u03BCL)</div><div>{mix.per_well_uL ?? ''}</div></div>
        <div className="bg-white/10 rounded p-2"><div className="text-xs opacity-70">Final volume (mL)</div><div>{mix.total_volume_mL ?? ''}</div></div>
      </div>
      <div className="mt-3 overflow-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-white/10">
              <th className="p-1 text-left">Component</th>
              <th className="p-1 text-left">MW</th>
              <th className="p-1 text-left">Mix conc (M)</th>
              <th className="p-1 text-left">Mass for 0.8 mL (mg)</th>
            </tr>
          </thead>
          <tbody>
            {mix.components.map((c,i)=> (
              <tr key={i} className={i%2? 'bg-white/0':'bg-white/5'}>
                <td className="p-1">{c.name}</td>
                <td className="p-1">{c.mw_g_mol ?? ''}</td>
                <td className="p-1">{c.mix_conc_M ?? ''}</td>
                <td className="p-1">{c.total_mass_mg ?? ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function PerWellGrid({columns, rows}:{columns:string[]; rows:any[]}){
  return (
    <table className="min-w-[980px] text-sm">
      <thead>
        <tr className="bg-white/5">
          {columns.map((c:string)=>(<th key={c} className="p-1 text-left">{c}</th>))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r:any, i:number)=>(
          <tr key={i} className={i%2? 'bg-white/0':'bg-white/5'}>
            {columns.map((c:string)=>(<td key={c} className="p-1">{r[c]}</td>))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}


function SummaryBlock({title, mapping}:{title:string; mapping:Record<string, Record<string, string[]>>}){
  const chemNames = Object.keys(mapping || {}).sort((a,b)=> a.localeCompare(b, undefined, {numeric:true}));
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-3">
      <div className="font-medium mb-2">{title}</div>
      <div className="overflow-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-white/5">
              <th className="p-1 text-left">Chemical</th>
              <th className="p-1 text-left">Plates → Wells</th>
            </tr>
          </thead>
          <tbody>
            {chemNames.map((chem, i)=>(
              <tr key={chem} className={i%2? 'bg-white/0':'bg-white/5'}>
                <td className="p-1 whitespace-nowrap">{chem}</td>
                <td className="p-1">
                  {Object.keys(mapping[chem] || {}).sort((a,b)=> Number(a)-Number(b)).map((p, j)=>{
                    const wells = (mapping[chem][p]||[]).join(", ");
                    return <span key={p} className="whitespace-nowrap mr-4">Plate {p} ({wells}){j < Object.keys(mapping[chem]).length-1 ? '; ' : ''}</span>
                  })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
