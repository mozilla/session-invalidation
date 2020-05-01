import unittest

import requests_mock

import mozdef_session_invalidation.session_invalidation as sesinv


class TestSessionInvalidators(unittest.TestCase):
    def test_terminate_sso_error_handling(self):
        with requests_mock.Mocker() as mock:
            mock.post('www.test.com/endpoint', status_code=400)

            terminate = sesinv.terminate_sso(
                'testtoken',
                'http://test.com/endpoint/{}',
            )

            result = terminate('testuser@mozilla.com')

            history = mock.request_history
            assert len(history) == 1

            e_url = 'http://www.test.com/endpoint/ad%7CMozilla-LDAP%7Ctestuser'
            assert history[0].url == e_url

            assert result.error is not None
            assert result.new_state == sesinv.TerminationState.ERROR
    
    def test_terminate_sso_success_case(self):
        with requests_mock.Mocker() as mock:
            mock.post('www.test.com/endpoint', status_code=204)

            terminate = sesinv.terminate_sso(
                'testtoken',
                'http://test.com/endpoint/{}',
            )

            result = terminate('testuser@mozilla.com')

            history = mock.request_history
            assert len(history) == 1

            e_url = 'http://www.test.com/endpoint/ad%7CMozilla-LDAP%7Ctestuser'
            assert history[0].url == e_url

            assert result.error is None
            assert result.new_state == sesinv.TerminationState.TERMINATED
