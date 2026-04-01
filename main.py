from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import io
import qrcode
from urllib.parse import urlencode, quote

app = FastAPI(title="QR Code Generator")


class UpiPayload(BaseModel):
    pa: str = Field(..., description="Payee VPA, e.g., NUMBER@ybl")
    pn: str = Field(..., description="Payee name")
    am: float = Field(..., gt=0, description="Amount")
    cu: str = Field(..., description="Currency, e.g., INR")
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
        "am": f"{payload.am:.2f}",
        "cu": payload.cu,
    }
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
    am: float = Query(..., gt=0, description="Amount"),
    cu: str = Query(..., description="Currency (INR)"),
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
        "message": "UPI-only: GET /qr with pa,pn,am,cu,tn?,tr? or POST /qr with the same JSON to get a QR code PNG."
    }
