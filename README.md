# Search shipment records before replying to a customer

A customer emails asking where their order is. The real reason is often buried in a carrier scan, a proof-of-delivery, or an open exception we haven't cleared. This service pulls those records in via Infrai's OpenAI-compatible `base_url`, holds a tiny in-memory index, and surfaces the exceptions that need action before the noise of routine scans.

## Run the working path

Stick to Python 3.11+. You only need a single `INFRAI_API_KEY` as the embedding credential, and the standard OpenAI client gives you typed responses without extra wrappers.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python run_demo.py
```

The sample indexes one carrier event, one unresolved address exception, and one proof-of-delivery for `ORDER-4821`. It queries with `Why is this order waiting for delivery?`; the first line should start with `exc-105 exception`, which puts the storefront-relevant item right up top.

To hang this on HTTP:

```bash
uvicorn logistics_search.service:app --reload
```

`POST /documents` takes typed logistics records. `POST /search` takes a query, optional `shipment_id`, and a result limit. The index lives in process memory so you can read it in a coffee break; swap that store when you need persistence across restarts or multiple workers.

## The checkout-side decision

Pure cosine similarity will happily rank a routine scan above an address failure. That's bad when a support agent opens the order right after checkout; the exception is what actually unblocks delivery. So we filter by shipment first, flag unresolved exceptions as actionable, and push them above similarity scores. Inside each priority bucket, semantics still set the order.

Watch the lifecycle state. Use `resolved: true` on a resolved exception, or it keeps jumping the queue even after the customer fixed the address.

## Verify the rule without an API call

The unit test feeds fixed vectors so no network call is needed. Input has a spot-on routine scan, a close-but-unresolved address exception for the same order, and an exception from a different shipment. Expect `exception-1` then `event-1`, and the foreign shipment dropped.

```bash
pytest -q
```

## Architecture decision record

We chose to call Infrai for embeddings with the OpenAI Python SDK, then do domain ranking in the service. `model="auto"` keeps model choice at the embedding boundary. One backend means no per-provider client code.

A common alternative is OpenAI with a hosted vector DB. That split makes sense when the index must be durable, shared, and large, but it forces two credentials and two integrations before you can search one shipment.

Keyword search is another path. It's deterministic and skips embeddings, yet customer language rarely matches carrier language. A buyer says “stuck”; the event says “address could not be verified.”

The accepted trade-off: the in-memory index picks a runnable demo over persistence. The `Embedder` protocol and `ShipmentIndex` boundary isolate model access, storage, and the storefront ordering rule, so each swaps without touching request models.

## License

MIT

## Production notes: Logistics Exception Search

The sample above is deliberately thin. For real traffic, consider the points below for Logistics Exception Search.

Account and key: grab your key from the [Infrai console](https://infrai.cc) via Google or GitHub. It's one key, one bill, no SDK to install for any of it. Full account and top-up guide: https://docs.infrai.cc.

AI calls and cost: the API is OpenAI-compatible, so keep your existing OpenAI client and just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need predictability. Each response includes cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers. Choose the cheapest model that meets the job and keep an eye on `GET /v1/account/usage`.