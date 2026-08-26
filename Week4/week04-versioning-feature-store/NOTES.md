# NOTES.md — Week 4: Versioning, Feature Store & Lineage

**Student ID used with `generate_for_student.py`:**
142301017


## v1 vs. v2 manifest comparison

v1 feature group was created using v1 raw data.
v2 feature group was created using v2 raw data.
Both versions contain the same 6 features:
avg_amount
card_id
event_time
max_amount
pct_card_present
txn_count
The main difference is which raw data version was used to create them.
v1 has 398 feature rows, while v2 has only 114 rows.

So, basically, the feature structure stayed the same, but the source data changed from v1 to v2, resulting in fewer rows in v2.


## Why treat amount_minor_units differently from amount?

In v1, the amount is already stored in dollars, for example 7.93 means $7.93.
In v2, the amount is stored in cents. For example, 1372 means $13.72.
So, before calculating things like average amount and maximum amount, build_features converts the v2 values from cents to dollars by dividing by 100.
This makes both v1 and v2 use the same unit (dollars).

In short: v1 is already in dollars, v2 is in cents, so v2 is converted to dollars to make the results comparable.