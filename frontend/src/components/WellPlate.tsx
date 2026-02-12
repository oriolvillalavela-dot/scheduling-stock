import React from "react";
import { motion } from "framer-motion";

const ROWS = ["A","B","C","D"];
const COLS = ["1","2","3","4","5","6"];

type Cell = { well: string; is_control: boolean; alkyl_id?: string|null; aryl_id?: string|null };

export default function WellPlate({ cells }: { cells: Cell[] }){
  const map = new Map(cells.map(c => [c.well, c]));
  const baseCell = "rounded-2xl p-2 h-24 flex flex-col items-center justify-center text-xs border shadow-sm";
  return (
    <div className="inline-block">
      <div className="grid grid-cols-[auto_repeat(6,1fr)] gap-2">
        <div />{/* corner */}
        {COLS.map(c => <div key={c} className="text-center text-xs text-slate-300">{c}</div>)}
        {ROWS.map(r => (
          <React.Fragment key={r}>
            <div className="text-right pr-1 text-xs text-slate-300">{r}</div>
            {COLS.map((c) => {
              const w = `${r}${c}`;
              const cell = map.get(w);
              const ctrl = cell?.is_control;
              return (
                <motion.div
                  key={w}
                  whileHover={{ scale: 1.03 }}
                  className={`${baseCell} ${ctrl ? "bg-rose-50 border-rose-300 text-rose-900" : "bg-white border-slate-200 text-slate-900"}`}
                  title={w}
                >
                  <div className="text-[10px] text-slate-500 self-start">{w}</div>
                  {ctrl ? (
                    <div className="font-semibold">CONTROL</div>
                  ) : (
                    <>
                      <div className="font-semibold">{cell?.alkyl_id ?? ""}</div>
                      <div className="text-slate-700">{cell?.aryl_id ?? ""}</div>
                    </>
                  )}
                </motion.div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
