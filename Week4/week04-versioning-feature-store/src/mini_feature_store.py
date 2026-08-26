"""
A tiny, local, dependency-free feature store — enough to demonstrate the
three ideas from this week's lecture without needing a Hopsworks/Feast
account:

  1. Raw data versioning (content-hash based, like DVC).
  2. Feature groups built from raw data, with recorded lineage back to the
     exact raw version and transform that produced them.
  3. A breaking schema change (v1 -> v2 transactions) producing a NEW
     feature group version rather than silently overwriting history.

Everything is stored under a "registry" directory as plain JSON, so you can
open any file and read exactly what was recorded — that transparency is the
point of the exercise.

Fill in the four functions marked # TODO. Helpers above them are done.
"""
import csv
import hashlib
import json
import os
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def _read_csv_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def content_hash(file_path):
    """Sha256 of the file's bytes. Given — this is what makes versioning
    idempotent: the same bytes always produce the same hash."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _next_version_id(existing_dir):
    """Given a directory of existing v1/, v2/, ... subfolders, return the
    next version id string. Given — you don't need to touch this."""
    if not os.path.isdir(existing_dir):
        return "v1"
    nums = []
    for name in os.listdir(existing_dir):
        if name.startswith("v") and name[1:].isdigit():
            nums.append(int(name[1:]))
    return f"v{max(nums, default=0) + 1}"


# ---------------------------------------------------------------------------
# Part 1 — Raw data versioning
# ---------------------------------------------------------------------------

def snapshot_raw_version(input_path, registry_dir):
    """Register `input_path` as a new raw data version under
    `registry_dir/raw_versions/`.

    Must be IDEMPOTENT: if a file with this exact content hash has already
    been snapshotted, return the EXISTING version_id instead of creating a
    duplicate — this is what makes it safe to re-run.

    Steps:
      1. Compute content_hash(input_path).
      2. Look through registry_dir/raw_versions/*/manifest.json for one
         whose "content_hash" matches. If found, return its "version_id".
      3. Otherwise, allocate a new version id with _next_version_id(
         os.path.join(registry_dir, "raw_versions")).
      4. Create registry_dir/raw_versions/{version_id}/ and inside it write
         manifest.json with at least these keys:
           version_id, source_path, content_hash, columns (list, from the
           CSV header), row_count, created_at (use _now()).
      5. Return the version_id (str).
    """

    # Get the hash of the input file so we can identify its exact contents.
    file_hash = content_hash(input_path)

    # This is where we will keep all the raw data versions.
    raw_dir = os.path.join(registry_dir, "raw_versions")

    # Check the versions that already exist.
    if os.path.isdir(raw_dir):
        for version_id in os.listdir(raw_dir):
            manifest_path = os.path.join(raw_dir, version_id, "manifest.json")

            # If a manifest exists, read it and compare its file hash.
            if os.path.isfile(manifest_path):
                with open(manifest_path) as f:
                    manifest = json.load(f)

                # Same hash means the exact same file was already stored.
                if manifest["content_hash"] == file_hash:
                    return manifest["version_id"]

    # If the file is new, create the next version number.
    version_id = _next_version_id(raw_dir)
    version_dir = os.path.join(raw_dir, version_id)
    os.makedirs(version_dir, exist_ok=True)

    # Read the CSV to get its columns and number of rows.
    rows = _read_csv_rows(input_path)

    with open(input_path, newline="") as f:
        reader = csv.reader(f)
        columns = next(reader)

    # Store the important information about this raw data version.
    manifest = {
        "version_id": version_id,
        "source_path": input_path,
        "content_hash": file_hash,
        "columns": columns,
        "row_count": len(rows),
        "created_at": _now()
    }

    # Save the manifest so we can identify this version later.
    with open(os.path.join(version_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    return version_id


# ---------------------------------------------------------------------------
# Part 2 — Feature engineering (must handle the v1 -> v2 schema change)
# ---------------------------------------------------------------------------

def build_features(rows):
    """Given a list of transaction row-dicts (either v1 OR v2 schema —
    detect which by checking for the "country_code" key vs "country"),
    compute one feature row per distinct card_id with these keys:

      card_id        (str)
      txn_count      (int)   - number of transactions for this card
      avg_amount     (float, rounded to 2 dp) - mean transaction amount
      max_amount     (float, rounded to 2 dp) - max transaction amount
      pct_card_present (float, rounded to 3 dp) - fraction with card_present true
      event_time     (str)   - the MAX timestamp seen for this card (as-is string
                                comparison works fine since timestamps are ISO8601)

    Schema handling:
      - v1 rows have "amount" (already a float-ish string) and "country".
      - v2 rows have "amount_minor_units" (integer string, cents) instead of
        "amount", and "country_code" instead of "country". Convert
        amount_minor_units back to the same unit as v1's amount by dividing
        by 100 before aggregating, so features are comparable across
        versions.
      - "card_present" is the string "True"/"False" in both — treat it as
        true if it equals "True".

    Return: list of feature row dicts, one per card_id, in any order.
    """
    # Check which version of the schema we received.
    # v2 has "country_code", while v1 has "country".
    is_v2 = "country_code" in rows[0]

    # Store transactions separately for each card.
    card_data = {}

    for row in rows:
        card_id = row["card_id"]

        if card_id not in card_data:
            card_data[card_id] = []

        # Convert the amount into the same unit for both versions.
        if is_v2:
            amount = int(row["amount_minor_units"]) / 100
        else:
            amount = float(row["amount"])

        # Save the values we need for calculating the features.
        card_data[card_id].append({
            "amount": amount,
            "card_present": row["card_present"] == "True",
            "event_time": row["timestamp"]
        })

    # Create one feature row for each card.
    feature_rows = []

    for card_id, transactions in card_data.items():
        amounts = [transaction["amount"] for transaction in transactions]

        # Count how many transactions had the card physically present.
        card_present_count = sum(
            transaction["card_present"] for transaction in transactions
        )

        feature_row = {
            "card_id": card_id,
            "txn_count": len(transactions),
            "avg_amount": round(sum(amounts) / len(amounts), 2),
            "max_amount": round(max(amounts), 2),
            "pct_card_present": round(
                card_present_count / len(transactions), 3
            ),
            "event_time": max(
                transaction["event_time"] for transaction in transactions
            )
        }

        feature_rows.append(feature_row)

    return feature_rows


# ---------------------------------------------------------------------------
# Part 3 — Feature group registration (this IS the lineage record)
# ---------------------------------------------------------------------------

def register_feature_group(name, feature_rows, source_version_id, registry_dir, transform_version="v1"):
    """Register a new version of feature group `name`.

    Must NEVER overwrite a previous version — each call creates a new
    incrementing version under registry_dir/feature_groups/{name}/{fg_version_id}/,
    exactly like snapshot_raw_version does for raw data. This is what "a
    breaking schema change creates a new version rather than silently
    mutating history" means in practice.

    Steps:
      1. Allocate fg_version_id via _next_version_id(os.path.join(
         registry_dir, "feature_groups", name)).
      2. Create that directory.
      3. Write features.json inside it containing `feature_rows` (the list
         you were given, as-is).
      4. Write manifest.json inside it with at least these keys:
           feature_group_version_id, name, source_raw_version_id
           (= the source_version_id argument), transform_version, schema
           (sorted list of the keys present in feature_rows[0]), row_count,
           created_at (use _now()).
      5. Return fg_version_id (str).
    """
    # Find the folder where all versions of this feature group are stored.
    feature_group_dir = os.path.join(registry_dir, "feature_groups", name)

    # Give this feature group the next version number.
    fg_version_id = _next_version_id(feature_group_dir)

    # Create a separate folder for this version.
    version_dir = os.path.join(feature_group_dir, fg_version_id)
    os.makedirs(version_dir, exist_ok=True)

    # Save the features exactly as they were given to us.
    with open(os.path.join(version_dir, "features.json"), "w") as f:
        json.dump(feature_rows, f, indent=2)

    # Get the feature names from the first feature row.
    schema = sorted(feature_rows[0].keys())

    # Record where these features came from and how they were created.
    manifest = {
        "feature_group_version_id": fg_version_id,
        "name": name,
        "source_raw_version_id": source_version_id,
        "transform_version": transform_version,
        "schema": schema,
        "row_count": len(feature_rows),
        "created_at": _now()
    }

    # Save the manifest for this feature group version.
    with open(os.path.join(version_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    return fg_version_id

# ---------------------------------------------------------------------------
# Part 4 — Lineage lookup
# ---------------------------------------------------------------------------

def get_lineage(name, fg_version_id, registry_dir):
    """Trace a feature group version back to the raw source it was built
    from, and return a single dict describing the full chain:

      {
        "feature_group": { ...the feature group's manifest.json contents... },
        "raw_source": { ...the manifest.json of the raw version named by
                         the feature group's "source_raw_version_id"... }
      }

    Read both manifest.json files from disk and assemble this dict. Raise
    FileNotFoundError (the default behavior of open() on a missing file is
    fine — don't catch it) if either manifest is missing.
    """
    # Find the manifest for the feature group version we want.
    feature_manifest_path = os.path.join(
        registry_dir,
        "feature_groups",
        name,
        fg_version_id,
        "manifest.json"
    )

    # Read the feature group's manifest.
    with open(feature_manifest_path) as f:
        feature_manifest = json.load(f)

    # Get the raw data version that was used to create these features.
    source_version_id = feature_manifest["source_raw_version_id"]

    # Find the manifest of that raw data version.
    raw_manifest_path = os.path.join(
        registry_dir,
        "raw_versions",
        source_version_id,
        "manifest.json"
    )

    # Read the raw data manifest.
    with open(raw_manifest_path) as f:
        raw_manifest = json.load(f)

    # Return both manifests so we can see the complete lineage.
    return {
        "feature_group": feature_manifest,
        "raw_source": raw_manifest
    }
