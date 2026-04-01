from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field
import io
import qrcode
from urllib.parse import urlencode, quote

app = FastAPI(title="QR Code Generator")


class UpiPayload(BaseModel):
    # Mandatory
    pa: str = Field(..., description="Payee VPA, e.g., NUMBER@ybl")
    pn: str = Field(..., description="Payee name")

    # Optional
    am: float | None = Field(
        None, gt=0, description="Amount (optional; must be >0 if provided)"
    )
    cu: str | None = Field(
        "INR", description="Currency, e.g., INR (optional; defaults to INR)"
    )
    tn: str | None = Field(None, description="Note (optional)")
    tr: str | None = Field(None, description="Transaction reference (optional)")


def _qr_response(data: str) -> StreamingResponse:
    """Generate PNG QR code image for the given string."""
    img = qrcode.make(data)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")


def build_upi_url(payload: UpiPayload) -> str:
    """Build a UPI payment deep link from the provided payload."""
    params = {
        "pa": payload.pa,
        "pn": payload.pn,
    }

    if payload.am is not None:
        params["am"] = f"{payload.am:.2f}"
    if payload.cu:
        params["cu"] = payload.cu
    if payload.tn:
        params["tn"] = payload.tn
    if payload.tr:
        params["tr"] = payload.tr

    # Use quote to avoid plus signs for spaces
    query = urlencode(params, quote_via=quote)
    return f"upi://pay?{query}"


@app.get("/qr")
async def generate_qr(
    pa: str = Query(..., description="Payee VPA"),
    pn: str = Query(..., description="Payee name"),
    am: float | None = Query(None, gt=0, description="Amount (optional)"),
    cu: str | None = Query(
        "INR", description="Currency (optional; defaults to INR when omitted)"
    ),
    tn: str | None = Query(None, description="Transaction note"),
    tr: str | None = Query(None, description="Transaction reference"),
):
    """Generate a UPI QR via query parameters (UPI-only)."""
    payload = UpiPayload(pa=pa, pn=pn, am=am, cu=cu, tn=tn, tr=tr)
    upi_url = build_upi_url(payload)
    return _qr_response(upi_url)


@app.post("/qr")
async def generate_qr_from_upi(payload: UpiPayload):
    """
    Build a UPI payment URL from JSON body and return its QR code (UPI-only).

    Example body:
    {
        "pa": "NUMBER@ybl",
        "pn": "Dhruv",
        "am": 340.00,
        "cu": "INR",
        "tn": "Test Payment",
        "tr": "INV-0042"
    }
    """
    upi_url = build_upi_url(payload)
    return _qr_response(upi_url)


@app.get("/")
async def root():
    return {
        "message": "UPI-only: GET /qr with pa,pn required; am?,cu?,tn?,tr? optional (or POST /qr with the same JSON) to get a QR code PNG."
    }


@app.get("/ui", response_class=HTMLResponse)
async def ui():
    """Minimal front-end to generate and download a QR without persisting data."""
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>UPI QR Generator</title>
      <style>
        :root {
          --bg: #0b1021;
          --card: #121936;
          --border: #273056;
          --accent: #6e8bff;
          --accent-2: #8c7bff;
          --text: #e8ebff;
          --muted: #9aadff;
        }
        * { box-sizing: border-box; }
        body { font-family: "Segoe UI", system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 24px; }
        .card { max-width: 760px; margin: 0 auto; background: var(--card); padding: 24px; border-radius: 14px; box-shadow: 0 12px 40px rgba(0,0,0,0.35); }
        h1 { margin-top: 0; letter-spacing: 0.3px; }
        label { display: block; margin: 12px 0 4px; font-weight: 600; color: var(--muted); }
        input { width: 100%; padding: 11px 12px; border-radius: 9px; border: 1px solid var(--border); background: #0e1530; color: var(--text); }
        input:focus { outline: 2px solid var(--accent); border-color: var(--accent); }
        .row { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
        button { margin-top: 16px; padding: 12px 16px; border: none; border-radius: 10px; background: linear-gradient(120deg, var(--accent), var(--accent-2)); color: #0b1021; font-weight: 700; cursor: pointer; box-shadow: 0 10px 30px rgba(110,139,255,0.35); }
        button:disabled { opacity: 0.65; cursor: not-allowed; }
        #result { margin-top: 18px; word-break: break-all; font-family: "SFMono-Regular", Consolas, monospace; background: #0e1530; padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: #b7c4ff; }
        #qr { display: block; margin: 16px auto 0; max-width: 280px; background: white; padding: 12px; border-radius: 12px; }
        .hint { color: var(--muted); font-size: 0.95rem; }
        .actions { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
        a.button-link { text-decoration: none; color: #0b1021; background: #cde0ff; padding: 10px 12px; border-radius: 9px; font-weight: 700; display: inline-flex; align-items: center; gap: 6px; }
        a.button-link[aria-disabled="true"] { opacity: 0.5; pointer-events: none; }
      </style>
    </head>
    <body>
      <div class="card">
        <h1>UPI QR Generator</h1>
        <p class="hint">Enter payee details; amount and currency are optional. The QR is built in memory—nothing is stored.</p>
        <form id="upi-form">
          <label for="pa">Payee VPA *</label>
          <input id="pa" name="pa" placeholder="number@ybl" required />

          <label for="pn">Payee Name *</label>
          <input id="pn" name="pn" placeholder="Dhruv Kumar" required />

          <div class="row">
            <div>
              <label for="am">Amount (optional)</label>
              <input id="am" name="am" type="number" min="0" step="0.01" placeholder="499.00" />
            </div>
            <div>
              <label for="cu">Currency (defaults to INR)</label>
              <input id="cu" name="cu" placeholder="INR" />
            </div>
          </div>

          <label for="tn">Note (optional)</label>
          <input id="tn" name="tn" placeholder="Thanks for your support!" />

          <label for="tr">Transaction Ref (optional)</label>
          <input id="tr" name="tr" placeholder="INV-0042" />

          <div class="actions">
            <button type="submit">Generate QR</button>
            <a id="download" class="button-link" href="#" download="upi-qr.png" aria-disabled="true">Download PNG</a>
          </div>
        </form>

        <div id="result" hidden></div>
        <img id="qr" alt="QR code" hidden />
      </div>

      <script>
        const form = document.getElementById('upi-form');
        const result = document.getElementById('result');
        const qr = document.getElementById('qr');
        const downloadLink = document.getElementById('download');

        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          result.hidden = true;
          qr.hidden = true;
          downloadLink.setAttribute('aria-disabled', 'true');
          downloadLink.removeAttribute('href');

          const data = new FormData(form);
          const params = new URLSearchParams();
          ['pa','pn','am','cu','tn','tr'].forEach((key) => {
            const value = data.get(key);
            if (value && String(value).trim() !== '') {
              params.append(key, value.trim());
            }
          });

          if (!params.get('pa') || !params.get('pn')) {
            alert('Payee VPA and Payee Name are required.');
            return;
          }

          const button = form.querySelector('button');
          button.disabled = true;
          button.textContent = 'Generating...';

          try {
            const res = await fetch('/qr?' + params.toString());
            if (!res.ok) {
              const errorText = await res.text();
              throw new Error(errorText || 'Request failed');
            }
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            qr.src = url;
            qr.hidden = false;

            const upiUrl = 'upi://pay?' + params.toString();
            result.textContent = upiUrl;
            result.hidden = false;

            downloadLink.href = url;
            downloadLink.setAttribute('aria-disabled', 'false');
          } catch (err) {
            alert('Error: ' + err.message);
          } finally {
            button.disabled = false;
            button.textContent = 'Generate QR';
          }
        });
      </script>
    </body>
    </html>
    """
