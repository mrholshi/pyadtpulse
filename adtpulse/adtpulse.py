"""
Interfaces with portal.adtpulse.com.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/alarm_control_panel.adtpulse/
"""

import os
import pickle
from bs4 import BeautifulSoup
import requests
from requests.auth import AuthBase

import logging

_LOGGER = logging.getLogger(__name__)


def authenticated(function):
        """Re-authenticate if session expired."""
        def wrapped(*args):
            """Wrap function."""
            try:
                return function(*args)
            except LoginException:
                self = args[0]
                self._login(self.session,
                            os.getenv("ADT_PULSE_USERNAME"),
                            os.getenv("ADT_PULSE_PASSWORD"))
                return function(*args)
        return wrapped


class LoginException(Exception):
    """
    Raise when we are unable to log in to portal.adtpulse.com
    """
    pass


class SystemArmedError(Exception):
    """
    Raise when the system is already armed and an attempt to arm it again is
    made.
    """
    pass


class SystemDisarmingError(Exception):
    """
    Raise when there is an exception during system disarming
    """
    pass


class SystemArmingError(Exception):
    """
    Raise when there is an exception during system arming
    """
    pass


class SystemDisarmedError(Exception):
    """
    Raise when the system is already disamred and an attempt to disarm
    the system is made.
    """
    pass


class ElementException(Exception):
    """
    Raise when we are unable to locate an element on the page.
    """
    pass


class Adtpulse(object):
    """
    Access to ADT Pulse partners and accounts.
    This class is used to interface with the options available through
    portal.adtpulse.com. The basic functions of checking system status and
    arming and disarming the system are possible.
    """

    """
    ADT Pulse constants
    """
    COOKIE_PATH = '/tmp/adtpulse_cookies.pickle'
    ADTPULSE_JSON_PREAMBLE_SIZE = 18
    DEFAULT_LOCALE = 'en_US'
    HTML_PARSER = 'html.parser'
    ERROR_FIND_TAG = 'div'
    ERROR_FIND_ATTR = {'id': 'warnMsgContents'}
    VALUE_ATTR = 'value'
    ATTRIBUTION = 'Information provided by portal.adtpulse.com'

    # ADT Pulse baseURL
    ADTPULSE_DOMAIN = 'https://portal.adtpulse.com'
    ADTPULSE_LOGIN_URL = 'https://portal.adtpulse.com/myhome/access/signin.jsp'

    """
    Determine the current code version used on portal.adtpulse.com
    """
    def adtpulse_version(self):
        """Determine current ADT Pulse version"""
        resp = requests.get(self.ADTPULSE_LOGIN_URL, allow_redirects=False)
        # resp.headers['Location'] = /myhome/9.6.0-610/access/signin.jsp
        return resp.headers['Location'].rsplit('/', 2)[0]

    @staticmethod
    def _save_cookies(requests_cookiejar, filename):
        """Save cookies to a file."""
        with open(filename, 'wb') as handle:
            pickle.dump(requests_cookiejar.get_dict(),
                        handle)

    @staticmethod
    def _load_cookies(filename):
        """Load cookies from a file."""
        with open(filename, 'rb') as handle:
            return requests.utils.cookiejar_from_dict(pickle.load(handle))

    def __init__(self):
        self.ADTPULSE_CONTEXT_PATH = self.adtpulse_version()
        self.LOGIN_URL = (
            self.ADTPULSE_DOMAIN + self.ADTPULSE_CONTEXT_PATH
            + '/access/signin.jsp'
        )

        self.SUMMARY_URL = (
            self.ADTPULSE_DOMAIN + self.ADTPULSE_CONTEXT_PATH +
            '/summary/summary.jsp'
        )

        self.ARM_DISARM_HANDLER = (
            self.ADTPULSE_DOMAIN + self.ADTPULSE_CONTEXT_PATH +
            '/quickcontrol/armDisarm.jsp'
        )
        self._session = None

    def get_session(self, username, password, cookie_path=COOKIE_PATH):
        """Get ADTPULSE HTTP session."""
        class ADTPULSEAuth(AuthBase):  # pylint: disable=too-few-public-methods
            """ADTPULSE authorization storage."""

            def __init__(self, username, password, cookie_path):
                """Init."""
                self.username = username
                self.password = password
                self.cookie_path = cookie_path

            def __call__(self, r):
                """Call is no-op."""
                return r

        session = requests.session()
        session.auth = ADTPULSEAuth(username, password, cookie_path)
        if os.path.exists(cookie_path):
            session.cookies = self._load_cookies(cookie_path)
        else:
            self._login(session, username, password, cookie_path)
        return session

    @property
    def session(self):
        if not self._session:
            self._session = self.get_session(
                username=os.getenv("ADT_PULSE_USERNAME"),
                password=os.getenv("ADT_PULSE_PASSWORD"))
        return self._session

    def _login(self, session, username, password, cookie_path=COOKIE_PATH):
        """Login to ADTPULSE."""
        resp = session.post(self.LOGIN_URL, {
            'usernameForm': username,
            'passwordForm': password,
        })
        parsed = BeautifulSoup(resp.text, self.HTML_PARSER)
        error = parsed.find(self.ERROR_FIND_TAG,
                            self.ERROR_FIND_ATTR)
        if error:
            error_string = error.text
            raise LoginException(error_string.strip())
        self._save_cookies(session.cookies, cookie_path)

    @authenticated
    def get_alarmstatus(self):
        """Get alarm status."""
        resp = self.session.get(self.SUMMARY_URL)
        parsed = BeautifulSoup(resp.content, self.HTML_PARSER)
        alarm_status = parsed.find('span', 'p_boldNormalTextLarge')
        if not alarm_status:
            raise LoginException("Cannot find alarm state information")
        for string in alarm_status.strings:
            if "." in string:
                param, _ = string.split(".", 1)
            adtpulse_alarmstatus = param
            state = adtpulse_alarmstatus
        return(state)

    @property
    def alarm_state(self):
        alarm_status_string_arry = self.get_alarmstatus().split(" ")
        if len(alarm_status_string_arry) > 1:
            return alarm_status_string_arry[1].lower()
        else:
            return alarm_status_string_arry[0].lower()

    @authenticated
    def disarm(self):
        try:
            resp = self.session.get(
                self.ARM_DISARM_HANDLER,
                params={
                    'href': 'rest/adt/ui/client/security/setArmState',
                    'armstate': self.alarm_state,
                    'arm': 'off'
                }
            )
        except Exception as e:
            raise SystemDisarmingError("Error disarming system, error: %s"
                                       % str(e))
        if not resp.ok:
            raise SystemDisarmingError("Error disarming system")

    @authenticated
    def arm(self, arm_type='stay'):
        try:
            resp = self.session.get(
                self.ARM_DISARM_HANDLER,
                params={
                    'href': 'rest/adt/ui/client/security/setArmState',
                    'armstate': self.alarm_state,
                    'arm': arm_type
                }
            )
        except Exception as e:
            raise SystemDisarmingError("Error arming system, error: %s"
                                       % str(e))
        if not resp.ok:
            raise SystemDisarmingError("Error arming system")
