from django.test import TestCase
from nose import tools as nt
import rendering_resource_manager_service.utils.custom_logging as log
from rendering_resource_manager_service.session.views import SessionDetailsSerializer
from rendering_resource_manager_service.session.management.session_manager import SessionManager
import json

DEFAULT_USER = 'testuser'
DEFAULT_RENDERER = 'testrenderer'


class TestSessionManager(TestCase):
    def setUp(self):
        log.debug(1, 'setUp')
        sm = SessionManager()
        # Clear sessions
        status = sm.clear_sessions()
        nt.assert_true(status[0] == 200)
        # List sessions
        status = sm.resume_sessions()
        nt.assert_true(status[0] == 200)

    def tearDown(self):
        log.debug(1, 'tearDown')

    def test_create_session(self):
        log.debug(1, 'test_create_session')
        session_id = SessionManager.get_session_id()
        # Create session
        sm = SessionManager()
        status = sm.create_session(session_id, DEFAULT_USER, DEFAULT_RENDERER)
        nt.assert_true(status[0] == 201)
        # Delete new session
        status = sm.delete_session(session_id)
        nt.assert_true(status[0] == 200)

    def test_duplicate_session(self):
        log.debug(1, 'test_duplicate_session')
        session_id = SessionManager.get_session_id()
        sm = SessionManager()
        # Create session
        status = sm.create_session(session_id, DEFAULT_USER, DEFAULT_RENDERER)
        nt.assert_true(status[0] == 201)
        # Create duplicate session
        status = sm.create_session(session_id, DEFAULT_USER, DEFAULT_RENDERER)
        nt.assert_true(status[0] == 409)
        # Delete session
        status = sm.delete_session(session_id)
        nt.assert_true(status[0] == 200)

    def test_delete_invalid_session(self):
        log.debug(1, 'test_delete_invalid_session')
        session_id = SessionManager.get_session_id()
        # Delete session
        sm = SessionManager()
        status = sm.delete_session(session_id)
        nt.assert_true(status[0] == 404)

    def test_list_sessions(self):
        log.debug(1, 'test_list_sessions')
        session_id = SessionManager.get_session_id()
        sm = SessionManager()
        # Create session
        status = sm.create_session(session_id, DEFAULT_USER, DEFAULT_RENDERER)
        nt.assert_true(status[0] == 201)
        # List sessions
        sm = SessionManager()
        status = sm.list_sessions(SessionDetailsSerializer)
        nt.assert_true(status[0] == 200)

        # Decode JSON response
        decoded = json.loads(status[1].content)
        nt.assert_true(decoded[0]['owner'] == DEFAULT_USER)
        nt.assert_true(decoded[0]['renderer_id'] == DEFAULT_RENDERER)

        # Delete session
        sm = SessionManager()
        status = sm.delete_session(session_id)
        nt.assert_true(status[0] == 200)

    def test_suspend_resume_sessions(self):
        log.debug(1, 'test_suspend_resume_sessions')
        session_id = SessionManager.get_session_id()
        sm = SessionManager()
        # Suspend sessions
        status = sm.suspend_sessions()
        nt.assert_true(status[0] == 200)
        # Create session
        status = sm.create_session(session_id, DEFAULT_USER, DEFAULT_RENDERER)
        nt.assert_true(status[0] == 403)
        # List sessions
        sm = SessionManager()
        status = sm.resume_sessions()
        nt.assert_true(status[0] == 200)
        # Create session
        status = sm.create_session(session_id, DEFAULT_USER, DEFAULT_RENDERER)
        nt.assert_true(status[0] == 201)
        # Delete session
        sm = SessionManager()
        status = sm.delete_session(session_id)
        nt.assert_true(status[0] == 200)

    def test_session_status(self):
        log.debug(1, 'test_session_status')
        session_id = SessionManager.get_session_id()
        sm = SessionManager()
        # Create session
        status = sm.create_session(session_id, DEFAULT_USER, DEFAULT_RENDERER)
        nt.assert_true(status[0] == 201)
        # Check session status (must be STOPPED)
        sm = SessionManager()
        status = sm.query_status(session_id)
        js = json.loads(status[1])
        nt.assert_true(status[0] == 200)
        nt.assert_true(js['code'] == 0)
        # Delete session
        sm = SessionManager()
        status = sm.delete_session(session_id)
        nt.assert_true(status[0] == 200)
