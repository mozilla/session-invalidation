import unittest

import requests_mock

import mozilla_session_invalidation.session_invalidation as sesinv


class TestSessionInvalidators(unittest.TestCase):
    def test_terminate_sso_error_handling(self):
        with requests_mock.Mocker() as mock:
            mock.post(requests_mock.ANY, status_code=400)

            terminate = sesinv.terminate_sso(
                'testtoken',
                'http://test.com/endpoint/{}',
            )

            result = terminate('testuser@mozilla.com')

            history = mock.request_history
            assert len(history) == 1

            e_url = 'test.com/endpoint/ad%7CMozilla-LDAP%7Ctestuser'
            assert history[0].url.endswith(e_url)

            assert result.error is not None
            assert 'Status 400' in result.error
            assert result.new_state == sesinv.TerminationState.ERROR
    
    def test_terminate_sso_success_case(self):
        with requests_mock.Mocker() as mock:
            mock.post(requests_mock.ANY, status_code=204)

            terminate = sesinv.terminate_sso(
                'testtoken',
                'http://test.com/endpoint/{}',
            )

            result = terminate('testuser@mozilla.com')

            history = mock.request_history
            assert len(history) == 1

            e_url = 'test.com/endpoint/ad%7CMozilla-LDAP%7Ctestuser'
            assert history[0].url.endswith(e_url)

            assert result.error is None
            assert result.new_state == sesinv.TerminationState.TERMINATED

    def test_terminate_gsuite_error_handling(self):
        with requests_mock.Mocker() as mock:
            mock.patch(requests_mock.ANY, status_code=400)

            terminate = sesinv.terminate_gsuite(
                'testtoken',
                'http://test.com/endpoint/{}',
            )

            result = terminate('testuser@mozilla.com')

            history = mock.request_history
            assert len(history) == 2

            e_url = 'test.com/endpoint/testuser@mozilla.com'
            assert history[0].url.endswith(e_url)
            assert history[1].url.endswith(e_url)

            assert history[0].json()['changePasswordAtNextLogin'] is True
            assert history[1].json()['changePasswordAtNextLogin'] is False

            assert result.error is not None
            assert 'Status 400' in result.error
            assert result.new_state == sesinv.TerminationState.ERROR

    def test_terminate_gsuite_success_case(self):
        with requests_mock.Mocker() as mock:
            mock.patch(requests_mock.ANY, status_code=200)

            terminate = sesinv.terminate_gsuite(
                'testtoken',
                'http://test.com/endpoint/{}',
            )

            result = terminate('testuser@mozilla.com')

            history = mock.request_history
            assert len(history) == 2

            e_url = 'test.com/endpoint/testuser@mozilla.com'
            assert history[0].url.endswith(e_url)
            assert history[1].url.endswith(e_url)

            assert history[0].json()['changePasswordAtNextLogin'] is True
            assert history[1].json()['changePasswordAtNextLogin'] is False

            assert result.error is None
            assert result.new_state == sesinv.TerminationState.TERMINATED
