#!/usr/bin/env bash
# Publishes firestore.rules through the Firebase Rules REST API.
# Needs only roles/firebase.rulesAdmin; firebase-tools also calls Service Usage
# (serviceusage.services.get), which the deploy service account does not have.
#
# Required env: FIREBASE_PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS
# Optional env: RULES_FILE (default firestore.rules), FIRESTORE_DATABASE (default "(default)")
set -euo pipefail

project="${FIREBASE_PROJECT_ID:?FIREBASE_PROJECT_ID is required}"
rules_file="${RULES_FILE:-firestore.rules}"
database="${FIRESTORE_DATABASE:-(default)}"
api="https://firebaserules.googleapis.com/v1"

if [ "$database" = "(default)" ]; then
  release_id="cloud.firestore"
else
  release_id="cloud.firestore/${database}"
fi
release_name="projects/${project}/releases/${release_id}"

gcloud auth activate-service-account --key-file "$GOOGLE_APPLICATION_CREDENTIALS" --quiet >/dev/null 2>&1
token="$(gcloud auth print-access-token)"
echo "::add-mask::${token}"

body_file="$(mktemp)"
trap 'rm -f "$body_file"' EXIT

call() {
  local method="$1" url="$2" payload="${3:-}"
  local status
  if [ -n "$payload" ]; then
    status="$(curl -sS -o "$body_file" -w '%{http_code}' -X "$method" "$url" \
      -H "Authorization: Bearer ${token}" -H 'Content-Type: application/json' -d "$payload")"
  else
    status="$(curl -sS -o "$body_file" -w '%{http_code}' -X "$method" "$url" \
      -H "Authorization: Bearer ${token}")"
  fi
  echo "$status"
}

fail() {
  echo "::error::$1 (HTTP $2): $(jq -r '.error.message // "no error message"' "$body_file" 2>/dev/null || echo 'unparseable response')"
  exit 1
}

ruleset_payload="$(jq -n --rawfile content "$rules_file" \
  '{source: {files: [{name: "firestore.rules", content: $content}]}}')"

status="$(call POST "${api}/projects/${project}/rulesets" "$ruleset_payload")"
[ "$status" = "200" ] || fail "Creating ruleset failed" "$status"
ruleset_name="$(jq -r '.name' "$body_file")"
echo "Created ruleset ${ruleset_name}"

release_payload="$(jq -n --arg name "$release_name" --arg ruleset "$ruleset_name" \
  '{release: {name: $name, rulesetName: $ruleset}}')"

status="$(call PATCH "${api}/${release_name}" "$release_payload")"
if [ "$status" = "404" ]; then
  create_payload="$(jq -n --arg name "$release_name" --arg ruleset "$ruleset_name" \
    '{name: $name, rulesetName: $ruleset}')"
  status="$(call POST "${api}/projects/${project}/releases" "$create_payload")"
fi
[ "$status" = "200" ] || fail "Releasing ruleset failed" "$status"

echo "Released ${ruleset_name} as ${release_name}"
