import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script_module(name, relative_path):
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = load_script_module("check_calibration_gate_under_test", "scripts/check_calibration_gate.py")
analyze = load_script_module("analyze_under_test", "scripts/analyze.py")


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def unresolved_field_status(field_sha):
    return {
        "exists": True,
        "path": "results/common/real_platform_field_status.json",
        "sha256": field_sha,
        "status": "blocked",
        "records_total": 1,
        "status_counts": {"non_identifiable": 1},
        "unresolved_total": 1,
        "unresolved": [
            {
                "risk_id": "llvm_field_status:vadd_vv:m1:Latency:non_identifiable",
                "instruction_id": "vadd_vv",
                "lmul": "m1",
                "field": "Latency",
                "status": "non_identifiable",
                "reason": "candidate set has multiple viable values",
            }
        ],
    }


class ApprovalGateHardeningTest(unittest.TestCase):
    def make_profile_root(self, *, stale_inventory_acceptance=False):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        profile_root = Path(tempdir.name) / "results"
        common = profile_root / "common"
        field_sha = "f" * 64
        inventory = {
            "field_status": unresolved_field_status(field_sha),
            "risk_acceptance": {
                "field_status_unresolved_risks_accepted": stale_inventory_acceptance,
                "accepted_risk_ids": [],
            },
        }
        inventory_path = common / "real_platform_inventory.json"
        write_json(inventory_path, inventory)
        return profile_root, common, inventory_path, inventory, gate.sha256_file(inventory_path), field_sha

    def write_approval(self, common, **overrides):
        approval = {
            "status": "approved",
            "approved_by": "unit-test-human",
            **overrides,
        }
        write_json(common / "human_approval.json", approval)

    def approval_check(self, profile_root, inventory_path, inventory):
        return gate.human_approval_failures(
            profile_root,
            inventory_path,
            inventory,
            total_traces=2,
            real_traces=2,
        )

    def test_non_identifiable_field_status_is_unresolved(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_json(
                root / "common" / "real_platform_field_status.json",
                {
                    "rows": [
                        {
                            "instruction_id": "vadd_vv",
                            "lmul": "m1",
                            "field": "Latency",
                            "status": "non_identifiable",
                        },
                        {
                            "instruction_id": "vadd_vv",
                            "lmul": "m1",
                            "field": "ReleaseAtCycles",
                            "status": "inferred",
                        },
                        {
                            "instruction_id": "vadd_vv",
                            "lmul": "m1",
                            "field": "ProcResource",
                            "status": "inferred",
                        },
                        {
                            "instruction_id": "vadd_vv",
                            "lmul": "m1",
                            "field": "NumMicroOps",
                            "status": "inferred",
                        },
                        {
                            "instruction_id": "vadd_vv",
                            "lmul": "m1",
                            "field": "SingleIssue",
                            "status": "inferred",
                        },
                    ]
                },
            )

            field_status = analyze.load_real_platform_field_status(root)

        self.assertEqual(field_status["status"], "blocked")
        self.assertEqual(field_status["unresolved_total"], 1)
        self.assertEqual(field_status["unresolved"][0]["status"], "non_identifiable")

    def test_approval_with_only_trace_count_fails_hash_binding(self):
        profile_root, common, inventory_path, inventory, _inventory_sha, _field_sha = self.make_profile_root()
        self.write_approval(common, trace_count=2, real_trace_count=2)

        valid, failures, _approval = self.approval_check(profile_root, inventory_path, inventory)

        self.assertFalse(valid)
        joined = "\n".join(failures)
        self.assertIn("inventory_sha256", joined)
        self.assertIn("real_platform_field_status_sha256", joined)

    def test_approval_with_stale_inventory_hash_fails(self):
        profile_root, common, inventory_path, inventory, _inventory_sha, field_sha = self.make_profile_root()
        self.write_approval(
            common,
            inventory_sha256="0" * 64,
            real_platform_field_status_sha256=field_sha,
            accepted_risk_ids=["all"],
        )

        valid, failures, _approval = self.approval_check(profile_root, inventory_path, inventory)

        self.assertFalse(valid)
        self.assertTrue(any("inventory sha256 does not match" in failure for failure in failures))

    def test_approval_with_stale_field_status_hash_fails(self):
        profile_root, common, inventory_path, inventory, inventory_sha, _field_sha = self.make_profile_root()
        self.write_approval(
            common,
            inventory_sha256=inventory_sha,
            real_platform_field_status_sha256="0" * 64,
            accepted_risk_ids=["all"],
        )

        valid, failures, _approval = self.approval_check(profile_root, inventory_path, inventory)

        self.assertFalse(valid)
        self.assertTrue(any("real_platform_field_status_sha256 does not match" in failure for failure in failures))

    def test_approval_missing_field_status_hash_fails(self):
        profile_root, common, inventory_path, inventory, inventory_sha, _field_sha = self.make_profile_root()
        self.write_approval(common, inventory_sha256=inventory_sha, accepted_risk_ids=["all"])

        valid, failures, _approval = self.approval_check(profile_root, inventory_path, inventory)

        self.assertFalse(valid)
        self.assertTrue(any("real_platform_field_status_sha256" in failure for failure in failures))

    def test_approval_missing_accepted_risk_scope_fails_even_if_inventory_claims_acceptance(self):
        profile_root, common, inventory_path, inventory, inventory_sha, field_sha = self.make_profile_root(
            stale_inventory_acceptance=True
        )
        self.write_approval(
            common,
            inventory_sha256=inventory_sha,
            real_platform_field_status_sha256=field_sha,
        )

        approval_valid, approval_failures, approval = self.approval_check(profile_root, inventory_path, inventory)
        field_failures = gate.real_platform_field_status_failures(
            inventory_path, inventory, approval_valid, approval
        )

        self.assertTrue(approval_valid, approval_failures)
        self.assertTrue(field_failures)
        self.assertIn("accepted risk", "\n".join(field_failures))

    def test_valid_all_risks_acceptance_passes_unresolved_field_status(self):
        profile_root, common, inventory_path, inventory, inventory_sha, field_sha = self.make_profile_root()
        self.write_approval(
            common,
            inventory_sha256=inventory_sha,
            real_platform_field_status_sha256=field_sha,
            accepted_risk_ids=["all"],
        )

        approval_valid, approval_failures, approval = self.approval_check(profile_root, inventory_path, inventory)
        field_failures = gate.real_platform_field_status_failures(
            inventory_path, inventory, approval_valid, approval
        )

        self.assertTrue(approval_valid, approval_failures)
        self.assertEqual([], field_failures)

    def test_yaml_block_list_risk_acceptance_passes_unresolved_field_status(self):
        profile_root, common, inventory_path, inventory, inventory_sha, field_sha = self.make_profile_root()
        (common / "human_approval.yaml").write_text(
            "\n".join(
                [
                    "status: approved",
                    "approved_by: unit-test-human",
                    f"inventory_sha256: {inventory_sha}",
                    f"real_platform_field_status_sha256: {field_sha}",
                    "accepted_risk_ids:",
                    "  - all",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        approval_valid, approval_failures, approval = self.approval_check(profile_root, inventory_path, inventory)
        field_failures = gate.real_platform_field_status_failures(
            inventory_path, inventory, approval_valid, approval
        )

        self.assertTrue(approval_valid, approval_failures)
        self.assertEqual([], field_failures)

    def test_pending_top_level_status_fails_even_if_nested_risk_acceptance_is_approved(self):
        profile_root, common, inventory_path, inventory, inventory_sha, field_sha = self.make_profile_root()
        self.write_approval(
            common,
            status="pending",
            inventory_sha256=inventory_sha,
            real_platform_field_status_sha256=field_sha,
            risk_acceptance={
                "status": "approved",
                "accepted_risk_ids": ["all"],
            },
        )

        approval_valid, approval_failures, approval = self.approval_check(profile_root, inventory_path, inventory)
        field_failures = gate.real_platform_field_status_failures(
            inventory_path, inventory, approval_valid, approval
        )

        self.assertFalse(approval_valid)
        self.assertTrue(any("approval status is not approved" in failure for failure in approval_failures))
        self.assertTrue(field_failures)
        discovered = analyze.discover_approval(profile_root)
        self.assertFalse(discovered["approved"])
        self.assertEqual("present_unapproved", discovered["status"])

    def test_top_level_approved_can_use_nested_risk_acceptance_scope(self):
        profile_root, common, inventory_path, inventory, inventory_sha, field_sha = self.make_profile_root()
        self.write_approval(
            common,
            inventory_sha256=inventory_sha,
            real_platform_field_status_sha256=field_sha,
            risk_acceptance={
                "accepted_risk_ids": ["all"],
            },
        )

        approval_valid, approval_failures, approval = self.approval_check(profile_root, inventory_path, inventory)
        field_failures = gate.real_platform_field_status_failures(
            inventory_path, inventory, approval_valid, approval
        )

        self.assertTrue(approval_valid, approval_failures)
        self.assertEqual([], field_failures)
        discovered = analyze.discover_approval(profile_root)
        self.assertTrue(discovered["approved"])
        self.assertEqual(["all"], discovered["accepted_risk_ids"])

    def test_human_approved_top_level_status_has_analyzer_gate_parity(self):
        profile_root, common, inventory_path, inventory, inventory_sha, field_sha = self.make_profile_root()
        write_json(
            common / "human_approval.json",
            {
                "human_approved": True,
                "approved_by": "unit-test-human",
                "inventory_sha256": inventory_sha,
                "real_platform_field_status_sha256": field_sha,
                "accepted_risk_ids": ["all"],
            },
        )

        approval_valid, approval_failures, approval = self.approval_check(profile_root, inventory_path, inventory)
        field_failures = gate.real_platform_field_status_failures(
            inventory_path, inventory, approval_valid, approval
        )
        discovered = analyze.discover_approval(profile_root)

        self.assertEqual(discovered["approved"], approval_valid, approval_failures)
        self.assertTrue(approval_valid, approval_failures)
        self.assertEqual([], field_failures)

    def test_nested_human_approval_is_not_discovered_or_gate_consumed(self):
        profile_root, _common, _inventory_path, _inventory, _inventory_sha, _field_sha = self.make_profile_root()
        write_json(
            profile_root / "r01" / "vadd_vv" / "human_approval.json",
            {
                "status": "approved",
                "approved_by": "unit-test-human",
                "accepted_risk_ids": ["all"],
            },
        )

        discovered = analyze.discover_approval(profile_root)

        self.assertFalse(discovered["approved"])
        self.assertEqual("absent", discovered["status"])
        self.assertIsNone(discovered["artifact_path"])
        self.assertIsNone(gate.approval_file(profile_root))


if __name__ == "__main__":
    unittest.main()
