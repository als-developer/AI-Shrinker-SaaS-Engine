# Sovereign Grid API Reference

## Base URL
`https://api.sovereigngrid.com/v1`

## Authentication
All requests require the `X-Sovereign-Key` header.

## Endpoints

### POST /sovereign/execute
Main execution endpoint for all engines.

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | User identifier |
| execution_mode | string | Yes | fact_check, micro_charge, bulk_compress, compliance_shield |
| text_payload | string | No | Text to process |
| fiat_amount | float | No | Amount for payment |
| currency_code | string | No | Currency (USD, TZS, KES) |
| bulk_models | array | No | Models for compression |

#### Response
```json
{
  "status": "success",
  "job_id": "job_123",
  "data": {}
}
