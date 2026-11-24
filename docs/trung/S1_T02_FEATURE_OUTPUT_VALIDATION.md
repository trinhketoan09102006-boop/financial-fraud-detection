# S1-T02 feature output validation

Outputs are currently under `C:\Users\MSI\Documents\Codex\2026-11-22\files-pasted-by-the-user-task\behavioral_v1`. Their target location inside the repository was blocked by filesystem permissions.

| Split | Rows | SHA-256 |
|---|---:|---|
| train | 1,037,340 | `5184322dc4b88f73fa59a091406d34b746c253c93533f48427c2589c818d32b1` |
| validation | 259,335 | `cb34d6e44f194eb927c460e4da78a349536a64b48a93271182093a69e12c8b63` |
| test | 555,719 | `7bd3d66ac276e0837d94ad2596b9beb450606a2b809b1ed45d13c13c150e3093` |

Independent readback verified exact feature order, Arrow string ID, three int32 counts, seven float64 features, unique IDs and exact per-split manifest ID sets, and file checksums against metadata. Split hash is `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`. Builder asserted no infinities and `1h <= 24h <= 7d`. `metadata.json` records per-feature null counts, min/max, median, 95th percentile and input/output hashes. Null *rates* may be computed as null count divided by split rows; they are not explicitly recorded. Peak memory was not measured.

## Final verification — installed artifacts

Installed path `data/features/behavioral_v1/`: train 1,037,340; validation 259,335; test 555,719; total 1,852,394. File hashes match those listed above and metadata. Output columns are exactly ID plus ten ordered features; no label, card ID or split field. Arrow types and one-to-one ID sets match the manifest, with no missing/duplicate IDs. No infinities; count windows are ordered. Null counts match metadata. Input checksums and manifest semantic hash match current data. Feature version and explicit null policy validated.

Peak Windows working set **700,493,824 bytes (668.0 MiB)** was measured during the independent full-artifact validation run, not during the earlier full feature generation. Full build runtime was 140.53 s, peak memory not measured for that run. Metadata original SHA-256 `16a812df1dcd6109a4fa0ef319ac83c151d1c69a3aa71cf0833ffb8d15160163` matched on initial copy; after adding the missing null policy, installed metadata SHA-256 is `4fa810a1d2452ed3f5dbfdc0d01cf666b69e1c4a00939a514d66b25c4bc3fd11`. Original is preserved in workspace.
