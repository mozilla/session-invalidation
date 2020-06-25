from datetime import datetime, timedelta
import unittest
from unittest.mock import patch

import requests_mock

import sesinv.sessions as sessions
import sesinv.authentication as auth


class GsuiteCredentialsMock:
    def __init__(self):
        self.subject = None

    def with_subject(self, subject):
        self.subject = subject

        return self


class GsuiteServiceMock:
    class Executor:
        def __init__(self, result):
            self._result = result

        def execute(self):
            return self._result


    class UsersAPI:
        def __init__(self, service, result):
            self._service = service
            self._result = result

        def patch(self, userKey='', body=None):
            self._service.calls.append({
                'userKey': userKey,
                'body': body,
            })

            return GsuiteServiceMock.Executor(self._result)


    def __init__(self, call_results):
        self.calls = []

        self._results = call_results

    def users(self):
        result = self._results[len(self.calls) % len(self._results)]

        return GsuiteServiceMock.UsersAPI(self, result)


class TestSessionInvalidators(unittest.TestCase):
    def test_terminate_sso_error_handling(self):
        mock_creds = auth.SSOCreds(
            client_id='test_id',
            client_secret='test_secret',
            auth_url='test.website.com',
            audience='audience',
            grant_type='grant',
            _token='testtoken',
            _expires=datetime.now() + timedelta(hours=1),
        )

        with requests_mock.Mocker() as mock:
            mock.post(requests_mock.ANY, status_code=400)

            terminate = sessions.terminate_sso(
                mock_creds,
                'ad|Mozilla-LDAP|{}',
                'http://test.com/endpoint/{}',
            )

            result = terminate('testuser@mozilla.com')

            history = mock.request_history
            assert len(history) == 1

            e_url = 'test.com/endpoint/ad%7CMozilla-LDAP%7Ctestuser'
            assert history[0].url.endswith(e_url)

            assert result.error is not None
            assert 'Status 400' in result.error
            assert result.new_state == sessions.TerminationState.ERROR
    
    def test_terminate_sso_success_case(self):
        mock_creds = auth.SSOCreds(
            client_id='test_id',
            client_secret='test_secret',
            auth_url='test.website.com',
            audience='audience',
            grant_type='grant',
            _token='testtoken',
            _expires=datetime.now() + timedelta(hours=1),
        )

        with requests_mock.Mocker() as mock:
            mock.post(requests_mock.ANY, status_code=204)

            terminate = sessions.terminate_sso(
                mock_creds,
                'ad|Mozilla-LDAP|{}',
                'http://test.com/endpoint/{}',
            )

            result = terminate('testuser@mozilla.com')

            history = mock.request_history
            assert len(history) == 1

            e_url = 'test.com/endpoint/ad%7CMozilla-LDAP%7Ctestuser'
            assert history[0].url.endswith(e_url)

            assert result.error is None
            assert result.new_state == sessions.TerminationState.TERMINATED

    @patch('googleapiclient.discovery.build')
    @patch('google.oauth2.service_account.Credentials.from_service_account_info')
    def test_terminate_gsuite_success_case(
        self,
        service_account_mock,
        discovery_mock,
    ):
        discovery = GsuiteServiceMock([
            {
                'changePasswordAtNextLogin': True,
            },
            {
                'changePasswordAtNextLogin': False,
            }
        ])

        discovery_mock.return_value = discovery

        credentials = GsuiteCredentialsMock()

        service_account_mock.return_value = credentials

        terminate = sessions.terminate_gsuite(
            {
                'private_key': 'fake',
            },
            'subject@test.com',
        )

        result = terminate('testuser@mozilla.com')

        assert result.new_state == sessions.TerminationState.TERMINATED

        assert credentials.subject == 'subject@test.com'

        assert len(discovery.calls) == 2
        assert discovery.calls[0] == {
            'userKey': 'testuser@mozilla.com',
            'body': {
                'changePasswordAtNextLogin': True,
            },
        }
        assert discovery.calls[1] == {
            'userKey': 'testuser@mozilla.com',
            'body': {
                'changePasswordAtNextLogin': False,
            },
        }

    @patch('googleapiclient.discovery')
    @patch('google.oauth2.service_account')
    def test_terminate_gsuite_error_handling_1(
        self,
        service_account_mock,
        discovery_mock,
    ):
        discovery = GsuiteServiceMock([
            {
                'missingExpectedKey': True,
            },
        ])

        discovery_mock.return_value = discovery

        credentials = GsuiteCredentialsMock()

        service_account_mock.return_value = credentials

        terminate = sessions.terminate_gsuite(
            {
                'private_key': 'fake',
            },
            'subject@test.com',
        )

        result = terminate('testuser@mozilla.com')

        assert result.new_state == sessions.TerminationState.ERROR
        assert result.error is not None

    @patch('googleapiclient.discovery')
    @patch('google.oauth2.service_account')
    def test_terminate_gsuite_error_handling_2(
        self,
        service_account_mock,
        discovery_mock,
    ):
        discovery = GsuiteServiceMock([
            {
                'changePasswordAtNextLogin': True,
            },
            {
                'changePasswordAtNextLogin': True,
            }
        ])

        discovery_mock.return_value = discovery

        credentials = GsuiteCredentialsMock()

        service_account_mock.return_value = credentials

        terminate = sessions.terminate_gsuite(
            {
                'private_key': 'fake',
            },
            'subject@test.com',
        )

        result = terminate('testuser@mozilla.com')

        assert result.new_state == sessions.TerminationState.ERROR
        assert result.error is not None

    def test_terminate_slack_failed_user_lookup(self):
        with requests_mock.Mocker() as mock:
            mock.post(
                'http://test.com/lookupuser',
                status_code=400,
                json={
                    'ok': False,
                    'error': 'users_not_found',
                },
            )

            mock.patch(requests_mock.ANY, status_code=400)

            terminate = sessions.terminate_slack(
                'testtoken',
                'http://test.com/lookupuser',
                'http://test.com/updateuser',
            )

            result = terminate('testuser@mozilla.com')

            history = mock.request_history

            assert len(history) == 1
            assert history[0].text == 'email=testuser%40mozilla.com'

            assert result.error is not None
            assert 'users_not_found' in result.error
            assert result.new_state == sessions.TerminationState.ERROR

    def test_terminate_slack_error_handling(self):
        with requests_mock.Mocker() as mock:
            mock.post(
                'http://test.com/lookupuser',
                status_code=200,
                json={
                    'ok': True,
                    'user': {
                        'id': 'testid123',
                    },
                },
            )

            mock.patch(
                'http://test.com/updateuser/testid123',
                status_code=400,
                json={'error': 'test error'},
            )

            terminate = sessions.terminate_slack(
                'testtoken',
                'http://test.com/lookupuser',
                'http://test.com/updateuser',
            )

            result = terminate('testuser@mozilla.com')

            history = mock.request_history
            assert len(history) == 3

            assert history[1].json()['active'] is False
            assert history[2].json()['active'] is True

            assert result.error is not None
            assert 'Status 400' in result.error
            assert result.new_state == sessions.TerminationState.ERROR

    def test_terminate_slack_success_case(self):
        with requests_mock.Mocker() as mock:
            mock.post(
                'http://test.com/lookupuser',
                json={
                    'ok': True,
                    'user': {
                        'id': 'testid123',
                    },
                },
            )

            mock.patch(
                'http://test.com/updateuser/testid123',
                status_code=204,
                json={},
            )

            terminate = sessions.terminate_slack(
                'testtoken',
                'http://test.com/lookupuser',
                'http://test.com/updateuser',
            )

            result = terminate('testuser@mozilla.com')

            history = mock.request_history
            assert len(history) == 3

            assert history[1].json()['active'] is False
            assert history[2].json()['active'] is True

            assert result.error is None
            assert result.new_state == sessions.TerminationState.TERMINATED
