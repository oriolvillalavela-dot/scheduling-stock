
import React, { useState } from "react";
import PlatePreview from "./pages/PlatePreview";
import StockSolutions from "./pages/StockSolutions";

export default function App(){
  const [tab, setTab] = useState<"plate"|"stocks">("plate");
  return (
    <div className="min-h-screen">
      <div className="sticky top-0 z-10 bg-slate-900/80 backdrop-blur border-b border-white/5">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="font-semibold">Lab Plate & Stock Assistant</div>
          <div className="flex gap-2">
            <button className={`px-3 py-1.5 rounded-md ${tab==='plate'?'bg-indigo-600':'border border-white/10'}`} onClick={()=>setTab('plate')}>Plate preview</button>
            <button className={`px-3 py-1.5 rounded-md ${tab==='stocks'?'bg-indigo-600':'border border-white/10'}`} onClick={()=>setTab('stocks')}>Stock solutions</button>
          </div>
        </div>
      </div>
      <div className="max-w-6xl mx-auto px-4 py-6">
        {tab==='plate'? <PlatePreview/> : <StockSolutions/>}
      </div>
    </div>
  )
}
