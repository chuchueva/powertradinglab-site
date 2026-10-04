# Methodology

Nine rules govern how the service handles data and time. Each rule exists
because the result would be wrong without it.

1. **One clock.** Every timestamp is UTC. Market-local time appears only as
   `delivery_day`, the day as the zone itself counts it (23, 24 or 25 hours).
2. **Two times per number.** `delivery_ts` is the 15-minute delivery period starts; 
   `knownby_ts` is when the number became known. Any value can be
    placed on both axes.
3. **Only what was published.** A decision for day D uses only data that was
   public before the day-ahead auction for D closed, in the latest version
   available at that moment. No later revision reaches back into a decision, no backfilling.
4. **Every revision is kept.** When the source corrects a price, the service
   stores the new value beside the old one, so the record can answer what
   was known at any past instant.
5. **Only changes are stored.** `knownby_ts` therefore means the first time
   the service saw that value. The first and last versions of a delivery period are its
   as-known and as-final states.
6. **Currency is read, not assumed.** Each source document states its
   currency. Values are reported in EUR; a non-EUR price is converted with the
   central bank's published rate for that day, and a day with no published
   rate gets no converted value.
7. **A day is scored exactly twice:** as-known, the morning after delivery,
   once imbalance prices are complete; as-final, after the 20th of the
   following month, once settlement has closed.
8. **A published file is never changed.** A correction is a new file beside
   the old one, and history is never re-rendered under a newer methodology.
   Every row states the versions in force when it was computed.
9. **Nothing is invented.** A gap stays a gap: no incomplete day scored as whole, no default decision where
   the signal did not form, no interpolation.

## What is NOT claimed

- **A yardstick, not a market size.** Every value is calculated per 1 MW, summed over a
  delivery day. It measures how much the spread between day-ahead and
  imbalance prices offered, and how much of that a simple rule captured.
- **Price-taker assumptions.** A 1 MW position is assumed to be filled at the
  clearing price and not to move any price. Fees, collateral and balancing
  obligations are not considered.
- **Not a trading recommendation.** The published decisions are a
  benchmark rule, made public so that it can be scored. They are not advice
  to take a position in any market.
- **Not investment advice.** Past values do not predict future ones; the
  regime of a market can change overnight, as Romania's did on
  2026-07-01, when it switched to single imbalance pricing.