# Coordinator Round 17 Human Approval Verification

Commands run:

```bash
python3 scripts/analyze.py --all
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
sha256sum results/common/human_approval.json results/common/real_platform_inventory.json results/common/real_platform_field_status.json results/common/search_model_real_platform.json results/common/experiment_quality.md results/common/real_platform_risk_acceptance_request.json
```

Observed results:

- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: PASS.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: PASS.
- Inventory gate status: `PASS`.
- Confidence: `approved_real_platform`.
- Approval status: `approved`.
- Accepted risk count: 9.

Final hashes:

- Human approval: `f85dc41ffdea94249da33fe9dad29b6879de51616463b806cf4c6cd27228f2fd`
- Inventory: `857590b16d9690eaa502f2fb589b8b0e79a20f5b6dba2112c44e02d01c379759`
- Field status: `079cb94d27e98bdcf9df0ae0595a6e12b101e4c8c5a3d46f7d627dd4c81c1432`
- Real search: `3d72fd2e87b517e3e7ba3699eb214b8f35874055f3ed51c519aa4671d5f002bd`
- Quality report: `57c8d84dff3816459fffbbdab3643e3c196bb6adc17b4db2dcc5accada9905ce`
- Risk request: `1605e9af6e64d5a8c77b466c7cd8ddf7ad68fe6fe161821e4fb5054418daa913`
