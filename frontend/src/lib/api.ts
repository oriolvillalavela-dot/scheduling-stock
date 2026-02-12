
const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function fetchPlate(day:number, plate:number){
  const r = await fetch(`${API}/api/plate?day=${day}&plate=${plate}`);
  if(!r.ok) throw new Error(await r.text());
  return await r.json();
}

export function downloadPlatePreviewPDF(payload: any){
  return fetch(`${API}/api/plate/pdf`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  }).then(async r => {
    if(!r.ok) throw new Error(await r.text());
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'plate.pdf';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });
}

export async function postStockPlan(payload: any){
  const r = await fetch(`${API}/api/stocks/plan`, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  if(!r.ok) throw new Error(await r.text());
  return await r.json();
}

export function downloadStockPDF(payload:any){
  return fetch(`${API}/api/stocks/pdf`, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  }).then(async r => {
    if(!r.ok) throw new Error(await r.text());
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'stocks.pdf';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  })
}
