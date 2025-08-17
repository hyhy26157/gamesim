
const tickEl = document.getElementById("tick");
const agentsEl = document.getElementById("agentsN");
const canvas = document.getElementById("c");
const ctx = canvas.getContext("2d");

let gridW=25, gridH=25;
const cellSize = Math.floor(Math.min(canvas.width/gridW, canvas.height/gridH));

const ws = new WebSocket(`ws://${location.host}/ws`);

ws.onopen = () => {
  // Send a ping every 5s to keep connection alive (server expects receive_text)
  setInterval(()=> { try { ws.send("ping"); } catch(e){} }, 5000);
};

ws.onmessage = (ev) => {
  const data = JSON.parse(ev.data);
  gridW = data.width; gridH = data.height;
  draw(data);
};

function draw(state) {
  tickEl.textContent = state.tick;
  agentsEl.textContent = state.agents.length;

  // clear
  ctx.fillStyle = "#0a0a0a";
  ctx.fillRect(0,0,canvas.width, canvas.height);

  // food
  ctx.fillStyle = "#36ff03ff"; // green-ish
  for (const [x,y] of state.food) {
    ctx.fillRect(x*cellSize, y*cellSize, cellSize, cellSize);
  }

  // grid lines (light)
  ctx.strokeStyle = "rgba(255, 102, 0, 0.06)";
  ctx.lineWidth = 1;
  for (let x=0; x<=gridW; x++) {
    ctx.beginPath();
    ctx.moveTo(x*cellSize, 0);
    ctx.lineTo(x*cellSize, gridH*cellSize);
    ctx.stroke();
  }
  for (let y=0; y<=gridH; y++) {
    ctx.beginPath();
    ctx.moveTo(0, y*cellSize);
    ctx.lineTo(gridW*cellSize, y*cellSize);
    ctx.stroke();
  }

  // agents
  for (const a of state.agents) {
    // hunger color: low hunger = cyan, high hunger = red
    const h = Math.max(0, Math.min(1, a.hunger/100));
    const r = Math.floor(200*h + 30);
    const g = Math.floor(200*(1-h) + 30);
    const b = 160;
    ctx.fillStyle = `rgb(${r},${g},${b})`;
    const pad = Math.max(1, Math.floor(cellSize*0.15));
    ctx.fillRect(a.x*cellSize+pad, a.y*cellSize+pad, cellSize-2*pad, cellSize-2*pad);
    // ctx.fillRect(a.x*cs+pad, a.y*cs+pad, cs-2*pad, cs-2*pad);
  }

  // skulls (fade out)
  if (state.skulls) {
    for (const s of state.skulls) {
      ctx.save();
      ctx.globalAlpha = Math.max(0, Math.min(1, s.alpha));
      ctx.fillStyle = "#ffffff";
      ctx.font = Math.floor(cs*0.8) + "px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("☠", s.x*cs + cs/2, s.y*cs + cs/2);
      ctx.restore();
    }
  }
}
