# QR Code Generator (UPI)

FastAPI service that returns a PNG QR code for UPI payment links.

## Run
- Python: `pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000`
- Docker: `docker compose up --build`

## Use (UPI only)
- Web UI (no storage): open `http://localhost:8000/ui`, fill the form, click **Generate QR**, then **Download PNG**.
  - The UI adds the UPI logo under the QR automatically.

- GET (query params):
  ```
  http://localhost:8000/qr?pa=foobar@upi&pn=Dhruv&am=340.00&cu=INR&tn=Test%20Payment&tr=INV-0042&logo=true
  ```
  - `logo` (optional, default false): include the UPI logo beneath the QR.
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
          "tr": "INV-0042",
          "logo": true
        }'
  ```
Note: Use your full UPI ID (e.g., `name@upi`), not just a phone number handle; some apps reject bare numbers.

## Endpoints
- `GET /ui` -> simple HTML form to generate & download the PNG QR (no data is stored)
- `GET /qr?pa=...&pn=...&am=...&cu=...&tn=...&tr=...` -> PNG QR (UPI only)
- `POST /qr` with JSON `{pa, pn, am?, cu?, tn?, tr?}` -> PNG QR (UPI only)

## UPI fields
| Parameter | Full Name | Description |
|---|---|---|
| `pa` | Payee Address | The recipient's UPI ID (VPA). Example: `foobar@upi` |
| `pn` | Payee Name | Display name shown to the payer in their UPI app |
| `am` | Amount | Optional decimal amount. Example: `340.00`. If omitted, payer enters it manually |
| `cu` | Currency | Optional; defaults to `INR` |
| `tn` | Transaction Note | Short description shown to the payer. Example: `Monthly Retainer` |
| `tr` | Transaction Reference | Your internal reference ID, great for linking to invoice numbers. Example: `INV-0042` |
| `logo` | Logo under QR | `true` to draw the UPI logo under the QR; defaults to `false` |

`pa` and `pn` are mandatory. Everything else is optional.

