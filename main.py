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
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
        :root {
          --bg: radial-gradient(circle at 15% 20%, rgba(255,255,255,0.12), transparent 32%), radial-gradient(circle at 85% 10%, rgba(255,255,255,0.18), transparent 34%), linear-gradient(145deg, #e3ebff 0%, #c8d7ff 40%, #b0c5ff 100%);
          --panel: rgba(255,255,255,0.9);
          --panel-border: rgba(255,255,255,0.35);
          --text: #1b2540;
          --muted: #4b5678;
          --accent: #556bff;
          --accent-2: #7a9bff;
          --divider: rgba(18, 44, 109, 0.12);
          --chip: #eef2ff;
          --shadow: 0 28px 80px rgba(63, 84, 135, 0.28);
        }
        * { box-sizing: border-box; }
        body {
          font-family: "Space Grotesk", "Segoe UI", system-ui, -apple-system, sans-serif;
          background: var(--bg);
          color: var(--text);
          margin: 0;
          padding: 32px;
        }
        .shell {
          max-width: 1100px;
          margin: 0 auto;
          background: var(--panel);
          border: 1px solid var(--panel-border);
          border-radius: 18px;
          box-shadow: var(--shadow);
          backdrop-filter: blur(10px);
          overflow: hidden;
        }
        header {
          padding: 22px 26px 12px;
          border-bottom: 1px solid var(--divider);
        }
        h1 { margin: 0 0 8px; font-size: 26px; letter-spacing: -0.2px; }
        .sub { margin: 0; color: var(--muted); }
        .grid {
          display: grid;
          grid-template-columns: 1.1fr 0.9fr;
          gap: 18px;
          padding: 22px 26px 26px;
        }
        @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
        .panel {
          background: white;
          border: 1px solid var(--divider);
          border-radius: 14px;
          padding: 16px 18px;
          box-shadow: inset 0 1px 0 rgba(255,255,255,0.5);
        }
        label { display: block; margin: 14px 0 6px; font-weight: 600; color: #1f2c4d; }
        input {
          width: 100%;
          padding: 11px 12px;
          border-radius: 10px;
          border: 1px solid #cfd6f0;
          background: #f7f8ff;
          color: #111b36;
          font-size: 15px;
          transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
        }
        input:focus {
          outline: none;
          border-color: var(--accent);
          box-shadow: 0 0 0 3px rgba(85, 107, 255, 0.18);
          background: white;
        }
        .row { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
        button.primary {
          margin-top: 18px;
          padding: 12px 16px;
          border: none;
          border-radius: 12px;
          background: linear-gradient(135deg, var(--accent), var(--accent-2));
          color: white;
          font-weight: 700;
          cursor: pointer;
          box-shadow: 0 12px 30px rgba(85, 107, 255, 0.25);
          transition: transform 0.12s ease, box-shadow 0.12s ease;
        }
        button.primary:hover { transform: translateY(-1px); box-shadow: 0 14px 34px rgba(85, 107, 255, 0.3); }
        button.primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; box-shadow: none; }
        .chip {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: var(--chip);
          color: #2d3c70;
          padding: 8px 12px;
          border-radius: 12px;
          font-weight: 600;
          font-size: 13px;
        }
        .muted { color: var(--muted); }
        #result {
          margin-top: 14px;
          word-break: break-all;
          font-family: "SFMono-Regular", Consolas, monospace;
          background: #f4f6ff;
          padding: 12px;
          border-radius: 10px;
          border: 1px dashed #cfd6f0;
          color: #22315d;
        }
        .preview {
          display: flex;
          flex-direction: column;
          gap: 12px;
          align-items: stretch;
        }
        .preview-card {
          border: 1px solid #dfe4f7;
          border-radius: 14px;
          padding: 14px;
          background: linear-gradient(180deg, #fdfdff 0%, #f2f4ff 100%);
          text-align: center;
        }
        #qr {
          display: block;
          margin: 10px auto 8px;
          width: min(78vw, 280px);
          max-width: 280px;
          background: white;
          padding: 12px;
          border-radius: 12px;
          box-shadow: 0 10px 32px rgba(21, 32, 75, 0.15);
        }
        .placeholder {
          width: min(78vw, 240px);
          height: min(78vw, 240px);
          border-radius: 16px;
          margin: 10px auto 8px;
          background: repeating-linear-gradient(135deg, #e3e9ff, #e3e9ff 12px, #f2f5ff 12px, #f2f5ff 24px);
          display: grid;
          place-items: center;
          color: #7a87b4;
          font-weight: 600;
        }
        .download-link {
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          justify-content: center;
          background: #111b36;
          color: white;
          padding: 11px 14px;
          border-radius: 12px;
          font-weight: 700;
          letter-spacing: 0.2px;
          transition: transform 0.12s ease, box-shadow 0.12s ease, opacity 0.12s ease;
          box-shadow: 0 10px 24px rgba(17, 27, 54, 0.25);
        }
        .download-link[aria-disabled="true"] { opacity: 0.5; pointer-events: none; box-shadow: none; }
        .download-link:not([aria-disabled="true"]):hover { transform: translateY(-1px); box-shadow: 0 12px 30px rgba(17, 27, 54, 0.35); }
        .upi-row {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          margin-top: 6px;
          color: #2b324f;
        }
        .upi-row img { height: 24px; }
        @media (max-width: 640px) {
          body { padding: 16px; }
          header { padding: 18px 18px 10px; }
          h1 { font-size: 22px; }
          .grid { padding: 16px 18px 20px; gap: 12px; }
          .panel { padding: 14px; }
          .row { grid-template-columns: 1fr; }
          .preview-card { padding: 12px; }
          #qr { width: min(82vw, 240px); padding: 10px; }
          .placeholder { width: min(82vw, 220px); height: min(82vw, 220px); }
          .download-link { width: 100%; }
          .chip { font-size: 12px; padding: 7px 10px; }
        }
      </style>
    </head>
    <body>
      <div class="shell">
        <header>
          <h1>Select UPI details</h1>
          <p class="sub">Generate a UPI deep link, preview the QR, and download the PNG instantly. No data is stored.</p>
        </header>

        <div class="grid">
          <div class="panel">
            <div class="chip">Payment | UPI</div>
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
                  <label for="cu">Currency (fixed to INR)</label>
                  <input id="cu" name="cu" value="INR" disabled />
                </div>
              </div>

              <label for="tn">Note (optional)</label>
              <input id="tn" name="tn" placeholder="Thanks for your support!" />

              <label for="tr">Transaction Ref (optional)</label>
              <input id="tr" name="tr" placeholder="INV-0042" />

              <button class="primary" type="submit">Generate QR</button>
            </form>
          </div>

          <div class="panel preview">
            <div class="preview-card">
              <div class="chip" style="justify-content:center;">Preview</div>
              <div id="placeholder" class="placeholder">QR will appear here</div>
              <img id="qr" alt="QR code" hidden />
              <div class="upi-row">
                <img src="https://upload.wikimedia.org/wikipedia/commons/e/e1/UPI-Logo-vector.svg" alt="UPI logo" />
              </div>
            </div>
            <div id="result" hidden></div>
            <a id="download" class="download-link" href="#" download="upi-qr.png" aria-disabled="true">Download PNG</a>
            <p class="muted" style="margin:0;">QR and link are generated in-memory from your inputs only.</p>
          </div>
        </div>
      </div>

      <script>
        const form = document.getElementById('upi-form');
        const result = document.getElementById('result');
        const qr = document.getElementById('qr');
        const downloadLink = document.getElementById('download');
        const placeholder = document.getElementById('placeholder');
        const currencyInput = document.getElementById('cu');
        const CURRENCY_DEFAULT = 'INR';
        const LOGO_URL = 'https://upload.wikimedia.org/wikipedia/commons/e/e1/UPI-Logo-vector.svg';
        let cachedLogoDataUrl = null;
        currencyInput.value = CURRENCY_DEFAULT;

        function blobToDataURL(blob) {
          return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
          });
        }

        async function loadLogoDataUrl() {
          if (cachedLogoDataUrl) return cachedLogoDataUrl;
          const res = await fetch(LOGO_URL);
          const blob = await res.blob();
          cachedLogoDataUrl = await blobToDataURL(blob);
          return cachedLogoDataUrl;
        }

        async function composeWithLogo(qrUrl, vpaText) {
          return new Promise((resolve, reject) => {
            const qrImg = new Image();
            const logo = new Image();
            qrImg.crossOrigin = 'anonymous';
            logo.crossOrigin = 'anonymous';
            let loaded = 0;
            const finish = () => {
              if (loaded === 2) {
                const padding = 18;
                const logoPadding = 16;
                const logoWidth = Math.min(logo.width || 120, qrImg.width * 0.375); // 25% smaller than before
                const logoHeight = logoWidth * (logo.height / logo.width || 0.25);
                const text = vpaText || '';
                const tempCanvas = document.createElement('canvas');
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.font = '15px \"Space Grotesk\", system-ui, sans-serif';
                const textWidth = text ? tempCtx.measureText(text).width : 0;
                const textHeight = text ? 18 : 0;
                const textGap = text ? 16 : 0; // extra breathing room under logo
                const width = Math.max(qrImg.width + padding * 2, textWidth + padding * 2, logoWidth + padding * 2);
                const height = qrImg.height + padding * 2 + logoHeight + logoPadding + textGap + textHeight;
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, width, height);
                const qrX = (width - qrImg.width) / 2;
                ctx.drawImage(qrImg, qrX, padding);
                const lx = (width - logoWidth) / 2;
                const ly = qrImg.height + padding * 2 + logoPadding / 2;
                ctx.drawImage(logo, lx, ly, logoWidth, logoHeight);
                if (text) {
                  ctx.fillStyle = '#1f2c4d';
                  ctx.textAlign = 'center';
                  ctx.font = '15px \"Space Grotesk\", system-ui, sans-serif';
                  ctx.fillText(text, width / 2, ly + logoHeight + textGap + textHeight / 2);
                }
                resolve(canvas.toDataURL('image/png'));
              }
            };
            qrImg.onload = () => { loaded += 1; finish(); };
            logo.onload = () => { loaded += 1; finish(); };
            qrImg.onerror = logo.onerror = (e) => reject(e);
            qrImg.src = qrUrl;
            loadLogoDataUrl()
              .then((dataUrl) => { logo.src = dataUrl; })
              .catch(reject);
          });
        }

        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          result.hidden = true;
          qr.hidden = true;
          placeholder.hidden = false;
          placeholder.style.display = 'grid';
          downloadLink.setAttribute('aria-disabled', 'true');
          downloadLink.removeAttribute('href');

          const data = new FormData(form);
          const params = new URLSearchParams();
          ['pa','pn','am','tn','tr'].forEach((key) => {
            const value = data.get(key);
            if (value && String(value).trim() !== '') {
              params.append(key, value.trim());
            }
          });
          // Always force INR currency
          params.append('cu', CURRENCY_DEFAULT);

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
            placeholder.hidden = true;
            placeholder.style.display = 'none';

            const upiUrl = 'upi://pay?' + params.toString();
            result.textContent = upiUrl;
            result.hidden = false;

            // Compose QR + UPI logo for download
            try {
              const composite = await composeWithLogo(url, params.get('pa'));
              downloadLink.href = composite;
            } catch (err) {
              console.warn('Logo compose failed, fallback to raw QR', err);
              downloadLink.href = url;
            }
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

