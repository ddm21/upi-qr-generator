# QR Code Generator (UPI)

FastAPI service that returns a PNG QR code for UPI payment links.

## Run
- Python: `pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000`
- Docker: `docker compose up --build`

## Use (UPI only)
- GET (query params):
  ```
  http://localhost:8000/qr?pa=foobar@upi&pn=Dhruv&am=340.00&cu=INR&tn=Test%20Payment&tr=INV-0042
  ```
- POST (JSON body builds UPI link for you):
  ```
  curl -X POST http://localhost:8000/qr \
    -H "Content-Type: application/json" \
    -o qr.png \
    -d '{
          "pa": "foobar@upi",
          "pn": "Dhruv",
          "am": 340.00,
          "cu": "INR",
          "tn": "Test Payment",
          "tr": "INV-0042"
        }'
  ```
Note: Use your full UPI ID (e.g., `name@upi`), not just a phone number handle; some apps reject bare numbers.

## Endpoints
- `GET /qr?pa=...&pn=...&am=...&cu=...&tn=...&tr=...` -> PNG QR (UPI only)
- `POST /qr` with JSON `{pa, pn, am, cu, tn?, tr?}` -> PNG QR (UPI only)

## UPI fields
| Parameter | Full Name | Description |
|---|---|---|
| `pa` | Payee Address | The recipient's UPI ID (VPA). Example: `foobar@upi` |
| `pn` | Payee Name | Display name shown to the payer in their UPI app |
| `am` | Amount | Payment amount in decimal format. Example: `340.00`. If omitted, payer enters it manually |
| `cu` | Currency | Currency code. Always `INR` for Indian payments |
| `tn` | Transaction Note | Short description shown to the payer. Example: `Monthly Retainer` |
| `tr` | Transaction Reference | Your internal reference ID, great for linking to invoice numbers. Example: `INV-0042` |

`pa` and `pn` are mandatory. Everything else is optional.

