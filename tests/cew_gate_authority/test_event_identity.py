from __future__ import annotations

import unittest

from cew_gate_authority.event_identity import candidate_from_pull_request_target_event, control_plane_from_pull_request_target_event, verify_dispatch_candidate


def event(head="d"*40, base="a"*40):
    return {"repository":{"full_name":"antoniocorsano-boop/N12"},"pull_request":{"number":148,"base":{"sha":base,"repo":{"full_name":"antoniocorsano-boop/N12"}},"head":{"sha":head,"repo":{"full_name":"antoniocorsano-boop/N12"}}}}


class EventIdentityTests(unittest.TestCase):
    def test_pull_request_target_derives_b_from_base_and_h_from_pr_head(self):
        e=event(); b=control_plane_from_pull_request_target_event(e); h=candidate_from_pull_request_target_event(e)
        self.assertEqual(b.base_commit_sha,"a"*40); self.assertEqual(h.head_sha,"d"*40); self.assertEqual(h.pr_number,148); self.assertEqual(h.head_repository,"antoniocorsano-boop/N12")

    def test_dispatch_requires_requested_sha_to_equal_current_pr_head(self):
        metadata=event()["pull_request"]
        identity=verify_dispatch_candidate(metadata,"d"*40,base_repository="antoniocorsano-boop/N12")
        self.assertEqual(identity.head_sha,"d"*40)
        with self.assertRaises(ValueError): verify_dispatch_candidate(metadata,"e"*40,base_repository="antoniocorsano-boop/N12")

    def test_missing_or_invalid_event_identity_fails_closed(self):
        with self.assertRaises(ValueError): candidate_from_pull_request_target_event({})
        bad=event(head="short")
        with self.assertRaises(ValueError): candidate_from_pull_request_target_event(bad)


if __name__=="__main__": unittest.main()
