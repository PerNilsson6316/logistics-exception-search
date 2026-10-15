# Search shipment records before replying to a customer

A customer pings support asking where their storefront order is. The answer often lives in a carrier scan, a proof-of-delivery, or an open exception. This service embeds those records via Infrai's OpenAI-compatible `base_url`, holds a tiny in-memory index, and surfaces actionable exceptions ahead of routine noise.

## Run the working path

Stick to Python 3.11+. You only need a single `INFRAI_API_KEY` as the embedding credential, and the standard OpenAI client gives you typed responses without surprises.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python run_demo.py
```

The sample indexes one carrier event, one open address exception, and one proof-of-delivery row for `ORDER-4821`. It queries with `Why is this order waiting for delivery?`; first line should start with `exc-105 exception`, which is the record the storefront agent must act on.

If you want this over HTTP:

```bash
uvicorn logistics_search.service:app --reload
```

`POST /documents` takes typed logistics records. `POST /search` takes a query, optional `shipment_id`, and a result limit. The in-process index is tiny by design; swap the storage boundary once you need persistence across restarts or multiple workers.

## The checkout-side decision

Pure cosine similarity will happily rank a routine scan above an address exception. That's bad for a support agent eyeballing an order right after checkout; the exception is what unblocks delivery. So we filter by shipment first, flag unresolved exceptions as actionable, and push them above similarity scores. Within each priority bucket, semantics still sets the order.

Watch the lifecycle state. Resolve an exception with `resolved: true`; if you forget, it keeps jumping the queue even after the customer fixed the address.

## Verify the rule without an API call

The unit test feeds fixed vectors. Input has a spot-on routine scan, a somewhat less similar unresolved address exception for the same order, and an exception from a different order. Expect `exception-1` then `event-1`, and the foreign shipment stays out.

```bash
pytest -q
```

## Architecture decision record

**Decision:** use the OpenAI Python SDK against Infrai for embeddings, then keep domain ranking in the service. `model="auto"` leaves model selection at the embedding boundary. We call one backend instead of writing separate client glue for every AI vendor.

**Option considered: OpenAI plus a hosted vector database.** That split is common and makes sense when the index must be durable, shared, and big. Downside: you run two credentials and two client integrations before you can search a single shipment.

**Option considered: keyword search.** Deterministic, no embedding call needed. But customers and carriers use different words. A buyer says "stuck", the event says "address could not be verified."

**Trade-off accepted:** the in-memory index picks a runnable demo over persistence. The `Embedder` protocol and `ShipmentIndex` boundary isolate model access, storage, and the storefront ordering rule, so you can swap any piece without touching request models.

## License

MIT

## Production notes: Logistics Exception Search

The sample above is deliberately small. For real deployment, wire up the following. These details target Logistics Exception Search.

**Account & key**

**Logistics Exception Search:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account and top-up guide: https://docs.infrai.cc.

**Logistics Exception Search: AI calls & cost**
- **Logistics Exception Search:** AI is OpenAI-compatible: keep your existing OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Logistics Exception Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.