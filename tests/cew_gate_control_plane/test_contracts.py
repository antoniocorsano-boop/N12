import unittest

from cew_gate_control_plane.contracts import (
    ControlPlaneError,
    DispatchRequest,
    PrBinding,
    load_strict_json_bytes,
    validate_dispatch_context,
    validate_pr_metadata,
)

H = "a" * 40


def metadata(*, number=148, state="open", base_repo="antoniocorsano-boop/N12", base_ref="main", head_sha=H, head_repo="fork/N12"):
    return {
        "number": number,
        "state": state,
        "base": {"repo": {"full_name": base_repo}, "ref": base_ref},
        "head": {"sha": head_sha, "repo": {"full_name": head_repo} if head_repo is not None else None},
    }


class DispatchContractTests(unittest.TestCase):
    def assert_code(self, code, fn):
        with self.assertRaises(ControlPlaneError) as ctx:
            fn()
        self.assertEqual(ctx.exception.code, code)

    def test_rejects_non_main_branch(self):
        self.assert_code("NON_CANONICAL_CONTROL_PLANE_REF", lambda: validate_dispatch_context("antoniocorsano-boop/N12", "refs/heads/dev", "branch", 148, H))

    def test_rejects_tag_ref(self):
        self.assert_code("NON_CANONICAL_CONTROL_PLANE_REF", lambda: validate_dispatch_context("antoniocorsano-boop/N12", "refs/tags/v1", "tag", 148, H))

    def test_rejects_non_positive_or_non_integral_pr_number(self):
        for value in (0, -1, 1.5, True, "148"):
            with self.subTest(value=value):
                self.assert_code("INVALID_DISPATCH_INPUT", lambda value=value: validate_dispatch_context("antoniocorsano-boop/N12", "refs/heads/main", "branch", value, H))

    def test_rejects_noncanonical_candidate_sha(self):
        for value in ("a" * 39, "A" * 40, "g" * 40, 123):
            with self.subTest(value=value):
                self.assert_code("INVALID_DISPATCH_INPUT", lambda value=value: validate_dispatch_context("antoniocorsano-boop/N12", "refs/heads/main", "branch", 148, value))

    def test_valid_main_dispatch_returns_request(self):
        self.assertEqual(validate_dispatch_context("antoniocorsano-boop/N12", "refs/heads/main", "branch", 148, H), DispatchRequest(148, H))


class PrMetadataContractTests(unittest.TestCase):
    def setUp(self):
        self.request = DispatchRequest(148, H)

    def assert_code(self, code, fn):
        with self.assertRaises(ControlPlaneError) as ctx:
            fn()
        self.assertEqual(ctx.exception.code, code)

    def test_rejects_unavailable_or_nonobject_pr_metadata(self):
        for value in (None, [], "x"):
            with self.subTest(value=value):
                self.assert_code("PR_METADATA_UNAVAILABLE", lambda value=value: validate_pr_metadata(value, self.request))

    def test_rejects_closed_pr(self):
        self.assert_code("PR_NOT_OPEN", lambda: validate_pr_metadata(metadata(state="closed"), self.request))

    def test_rejects_wrong_base_repository_or_branch(self):
        self.assert_code("PR_BASE_MISMATCH", lambda: validate_pr_metadata(metadata(base_repo="other/repo"), self.request))
        self.assert_code("PR_BASE_MISMATCH", lambda: validate_pr_metadata(metadata(base_ref="dev"), self.request))

    def test_rejects_pr_head_mismatch(self):
        self.assert_code("PR_HEAD_MISMATCH", lambda: validate_pr_metadata(metadata(head_sha="b" * 40), self.request))
        self.assert_code("PR_HEAD_MISMATCH", lambda: validate_pr_metadata(metadata(number=149), self.request))

    def test_rejects_missing_head_repository(self):
        self.assert_code("PR_METADATA_UNAVAILABLE", lambda: validate_pr_metadata(metadata(head_repo=None), self.request))
        bad = metadata(); bad["head"]["repo"] = {"full_name": ""}
        self.assert_code("PR_METADATA_UNAVAILABLE", lambda: validate_pr_metadata(bad, self.request))

    def test_rejects_duplicate_json_keys(self):
        raw = b'{"number":148,"number":149}'
        self.assert_code("PR_METADATA_UNAVAILABLE", lambda: load_strict_json_bytes(raw, label="PR_METADATA_UNAVAILABLE"))

    def test_valid_metadata_returns_binding(self):
        self.assertEqual(validate_pr_metadata(metadata(), self.request), PrBinding(148, "fork/N12", H))


if __name__ == "__main__":
    unittest.main()
