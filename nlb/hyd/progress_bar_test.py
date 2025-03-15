import unittest

import requests
import responses

from nlb.hyd import progress_bar


class ProgressBarTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = progress_bar.ProgressBar('Test', max_value=10)

    @responses.activate
    def test_error_code(self) -> None:
        responses.add(
            method=responses.POST,
            url=self.p._endpoint,
            body='{"error": "reason"}',
            status=401,
        )

        with self.assertRaises(requests.HTTPError):
            self.p.update_value(4)

    @responses.activate
    def test_update_value(self) -> None:
        request_payload: progress_bar.TaskProgress = {
            'label': 'Test',
            'value': 1,
            'max_value': 10,
        }

        # Assert that we return the payload on `ConnectionError`
        resp = self.p._update_hyd(request_payload)
        self.assertEqual(resp, request_payload)

        resp_payload: progress_bar.TaskProgress = {
            'id': 0,
            'label': 'Test',
            'value': 5,
            'max_value': 10,
        }

        responses.add(
            method=responses.POST,
            url=self.p._endpoint,
            json=resp_payload,
        )

        resp = self.p.update_value(4)

        self.assertEqual(resp, resp_payload)

    @responses.activate
    def test_update_status(self) -> None:
        request_payload: progress_bar.TaskProgress = {
            'label': 'Test',
            'value': 1,
            'max_value': 10,
            'status': 'new label',
        }

        # Assert that we return the payload on `ConnectionError`
        resp = self.p._update_hyd(request_payload)
        self.assertEqual(resp, request_payload)

        resp_payload: progress_bar.TaskProgress = {
            'id': 0,
            'label': 'Test',
            'value': 5,
            'max_value': 10,
            'status': 'new label',
        }

        responses.add(
            method=responses.POST,
            url=self.p._endpoint,
            json=resp_payload,
        )

        resp = self.p.update_status('new label')
        self.assertEqual(resp, resp_payload)

    @responses.activate
    def test_iter_connection_error(self) -> None:
        # No error raised on `ConnectionError`
        for _ in self.p.iter(range(10)):
            pass

        resp_payload: progress_bar.TaskProgress = {
            'id': 0,
            'label': 'Test',
            'value': 5,
            'max_value': 10,
        }
        responses.add(
            method=responses.POST,
            url=self.p._endpoint,
            json=resp_payload,
        )

        # Nominal case
        for _ in self.p.iter(range(10)):
            pass
