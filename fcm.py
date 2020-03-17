# -*- coding: utf-8 -*-
import requests
import requesocks
import json
import logging
import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry


class FCMError(Exception):
    """
    PyFCM Error
    """
    pass

class AuthenticationError(FCMError):
    """
    API key not found or there was an error authenticating the sender
    """
    pass


class FCMServerError(FCMError):
    """
    Internal server error or timeout error on Firebase cloud messaging server
    """
    pass


class InvalidDataError(FCMError):
    """
    Invalid input
    """
    pass


class InternalPackageError(FCMError):
    """
    JSON parsing error, please create a new github issue describing what you're doing
    """
    pass


class RetryAfterException(Exception):
    """
    Retry-After must be handled by external logic.
    """
    def __init__(self, delay):
        self.delay = delay


#fork from pyfcm package
class FCMNotification(object):
    CONTENT_TYPE = "application/json"
    FCM_END_POINT = "https://fcm.googleapis.com/fcm/send"
    # FCM only allows up to 1000 reg ids per bulk message.
    FCM_MAX_RECIPIENTS = 1000

    #: Indicates that the push message should be sent with low priority. Low
    #: priority optimizes the client app's battery consumption, and should be used
    #: unless immediate delivery is required. For messages with low priority, the
    #: app may receive the message with unspecified delay.
    FCM_LOW_PRIORITY = 'normal'

    #: Indicates that the push message should be sent with a high priority. When a
    #: message is sent with high priority, it is sent immediately, and the app can
    #: wake a sleeping device and open a network connection to your server.
    FCM_HIGH_PRIORITY = 'high'

 
    def __init__(self, proxy_dict=None):
        
        self.requests_session = requests.Session()
        retries = Retry(backoff_factor=1, status_forcelist=[502, 503, 504],
                    method_whitelist=(Retry.DEFAULT_METHOD_WHITELIST | frozenset(['POST'])))
        self.requests_session.mount('http://', HTTPAdapter(max_retries=retries))
        self.requests_session.mount('https://', HTTPAdapter(max_retries=retries))
        self.requests_session.proxies.update(proxy_dict)
        self.send_request_responses = []        


    def do_request(self, payload, headers, timeout):
        response = self.requests_session.post(self.FCM_END_POINT, data=payload,
                                              headers=headers, timeout=timeout)
        if 'Retry-After' in response.headers and int(response.headers['Retry-After']) > 0:
            sleep_time = int(response.headers['Retry-After'])
            time.sleep(sleep_time)
            return self.do_request(payload, timeout)
        return response

    def send_request(self, payloads=None, headers=None, timeout=None):
        self.send_request_responses = []
        for payload in payloads:
            response = self.do_request(payload, headers, timeout)
            self.send_request_responses.append(response)
            

    def registration_id_chunks(self, registration_ids):
        """
        Splits registration ids in several lists of max 1000 registration ids per list

        Args:
            registration_ids (list): FCM device registration ID

        Yields:
            generator: list including lists with registration ids
        """
        try:
            xrange
        except NameError:
            xrange = range

        # Yield successive 1000-sized (max fcm recipients per request) chunks from registration_ids
        for i in xrange(0, len(registration_ids), self.FCM_MAX_RECIPIENTS):
            yield registration_ids[i:i + self.FCM_MAX_RECIPIENTS]
            

    def json_dumps(self, data):
        """
        Standardized json.dumps function with separators and sorted keys set

        Args:
            data (dict or list): data to be dumped

        Returns:
            string: json
        """
        return json.dumps(
            data, 
            separators=(',', ':'), 
        ).encode('utf8')
    

    def parse_payload(self,
                      registration_ids=None,
                      topic_name=None,
                      message_body=None,
                      message_title=None,
                      message_icon=None,
                      sound=None,
                      condition=None,
                      collapse_key=None,
                      delay_while_idle=False,
                      time_to_live=None,
                      restricted_package_name=None,
                      low_priority=False,
                      dry_run=False,
                      data_message=None,
                      click_action=None,
                      badge=None,
                      color=None,
                      tag=None,
                      body_loc_key=None,
                      body_loc_args=None,
                      title_loc_key=None,
                      title_loc_args=None,
                      content_available=None,
                      remove_notification=False,
                      android_channel_id=None,
                      extra_notification_kwargs={},
                      **extra_kwargs):
        """
        Parses parameters of FCMNotification's methods to FCM nested json

        Args:
            registration_ids (list, optional): FCM device registration IDs
            topic_name (str, optional): Name of the topic to deliver messages to
            message_body (str, optional): Message string to display in the notification tray
            message_title (str, optional): Message title to display in the notification tray
            message_icon (str, optional): Icon that apperas next to the notification
            sound (str, optional): The sound file name to play. Specify "Default" for device default sound.
            condition (str, optiona): Topic condition to deliver messages to
            collapse_key (str, optional): Identifier for a group of messages
                that can be collapsed so that only the last message gets sent
                when delivery can be resumed. Defaults to `None`.
            delay_while_idle (bool, optional): deprecated
            time_to_live (int, optional): How long (in seconds) the message
                should be kept in FCM storage if the device is offline. The
                maximum time to live supported is 4 weeks. Defaults to `None`
                which uses the FCM default of 4 weeks.
            restricted_package_name (str, optional): Name of package
            low_priority (bool, optional): Whether to send notification with
                the low priority flag. Defaults to `False`.
            dry_run (bool, optional): If `True` no message will be sent but request will be tested.
            data_message (dict, optional): Custom key-value pairs
            click_action (str, optional): Action associated with a user click on the notification
            badge (str, optional): Badge of notification
            color (str, optional): Color of the icon
            tag (str, optional): Group notification by tag
            body_loc_key (str, optional): Indicates the key to the body string for localization
            body_loc_args (list, optional): Indicates the string value to replace format
                specifiers in body string for localization
            title_loc_key (str, optional): Indicates the key to the title string for localization
            title_loc_args (list, optional): Indicates the string value to replace format
                specifiers in title string for localization
            content_available (bool, optional): Inactive client app is awoken
            remove_notification (bool, optional): Only send a data message
            android_channel_id (str, optional): Starting in Android 8.0 (API level 26),
                all notifications must be assigned to a channel. For each channel, you can set the
                visual and auditory behavior that is applied to all notifications in that channel.
                Then, users can change these settings and decide which notification channels from
                your app should be intrusive or visible at all.
            extra_notification_kwargs (dict, optional): More notification keyword arguments
            **extra_kwargs (dict, optional): More keyword arguments

        Returns:
            string: json

        Raises:
            InvalidDataError: parameters do have the wrong type or format
        """
        fcm_payload = dict()
        if registration_ids:
            if len(registration_ids) > 1:
                fcm_payload['registration_ids'] = registration_ids
            else:
                fcm_payload['to'] = registration_ids[0]
        if condition:
            fcm_payload['condition'] = condition
        else:
            # In the `to` reference at: https://firebase.google.com/docs/cloud-messaging/http-server-ref#send-downstream
            # We have `Do not set this field (to) when sending to multiple topics`
            # Which is why it's in the `else` block since `condition` is used when multiple topics are being targeted
            if topic_name:
                fcm_payload['to'] = '/topics/%s' % topic_name
        # Revert to legacy API compatible priority
        if low_priority:
            fcm_payload['priority'] = self.FCM_LOW_PRIORITY
        else:
            fcm_payload['priority'] = self.FCM_HIGH_PRIORITY

        if delay_while_idle:
            fcm_payload['delay_while_idle'] = delay_while_idle
        if collapse_key:
            fcm_payload['collapse_key'] = collapse_key
        if time_to_live:
            if isinstance(time_to_live, int):
                fcm_payload['time_to_live'] = time_to_live
            else:
                raise InvalidDataError("Provided time_to_live is not an integer")
        if restricted_package_name:
            fcm_payload['restricted_package_name'] = restricted_package_name
        if dry_run:
            fcm_payload['dry_run'] = dry_run

        if data_message:
            if isinstance(data_message, dict):
                fcm_payload['data'] = data_message
            else:
                raise InvalidDataError("Provided data_message is in the wrong format")

        fcm_payload['notification'] = {}
        if message_icon:
            fcm_payload['notification']['icon'] = message_icon
        # If body is present, use it
        if message_body:
            fcm_payload['notification']['body'] = message_body
        # Else use body_loc_key and body_loc_args for body
        else:
            if body_loc_key:
                fcm_payload['notification']['body_loc_key'] = body_loc_key
            if body_loc_args:
                if isinstance(body_loc_args, list):
                    fcm_payload['notification']['body_loc_args'] = body_loc_args
                else:
                    raise InvalidDataError('body_loc_args should be an array')
        # If title is present, use it
        if message_title:
            fcm_payload['notification']['title'] = message_title
        # Else use title_loc_key and title_loc_args for title
        else:
            if title_loc_key:
                fcm_payload['notification']['title_loc_key'] = title_loc_key
            if title_loc_args:
                if isinstance(title_loc_args, list):
                    fcm_payload['notification']['title_loc_args'] = title_loc_args
                else:
                    raise InvalidDataError('title_loc_args should be an array')

        if android_channel_id:
            fcm_payload['notification']['android_channel_id'] = android_channel_id

        # This is needed for iOS when we are sending only custom data messages
        if content_available and isinstance(content_available, bool):
            fcm_payload['content_available'] = content_available

        if click_action:
            fcm_payload['notification']['click_action'] = click_action
        if isinstance(badge, int) and badge >= 0:
            fcm_payload['notification']['badge'] = badge
        if color:
            fcm_payload['notification']['color'] = color
        if tag:
            fcm_payload['notification']['tag'] = tag
        # only add the 'sound' key if sound is not None
        # otherwise a default sound will play -- even with empty string args.
        if sound:
            fcm_payload['notification']['sound'] = sound

        if extra_kwargs:
            fcm_payload.update(extra_kwargs)

        if extra_notification_kwargs:
            fcm_payload['notification'].update(extra_notification_kwargs)

        # Do this if you only want to send a data message.
        if remove_notification:
            del fcm_payload['notification']

        return self.json_dumps(fcm_payload)

    def single_device_data_message(self,
                                   api_key,
                                   registration_id=None,
                                   condition=None,
                                   collapse_key=None,
                                   delay_while_idle=False,
                                   time_to_live=None,
                                   restricted_package_name=None,
                                   low_priority=False,
                                   dry_run=False,
                                   data_message=None,
                                   content_available=None,
                                   android_channel_id=None,
                                   timeout=5,
                                   extra_notification_kwargs=None,
                                   extra_kwargs={}):
        """
        Send push message to a single device

        Args:
            registration_id (list, optional): FCM device registration ID
            condition (str, optiona): Topic condition to deliver messages to
            collapse_key (str, optional): Identifier for a group of messages
                that can be collapsed so that only the last message gets sent
                when delivery can be resumed. Defaults to `None`.
            delay_while_idle (bool, optional): deprecated
            time_to_live (int, optional): How long (in seconds) the message
                should be kept in FCM storage if the device is offline. The
                maximum time to live supported is 4 weeks. Defaults to `None`
                which uses the FCM default of 4 weeks.
            restricted_package_name (str, optional): Name of package
            low_priority (bool, optional): Whether to send notification with
                the low priority flag. Defaults to `False`.
            dry_run (bool, optional): If `True` no message will be sent but request will be tested.
            data_message (dict, optional): Custom key-value pairs
            content_available (bool, optional): Inactive client app is awoken
            android_channel_id (str, optional): Starting in Android 8.0 (API level 26),
                all notifications must be assigned to a channel. For each channel, you can set the
                visual and auditory behavior that is applied to all notifications in that channel.
                Then, users can change these settings and decide which notification channels from
                your app should be intrusive or visible at all.
            timeout (int, optional): set time limit for the request
            extra_notification_kwargs (dict, optional): More notification keyword arguments
            extra_kwargs (dict, optional): More keyword arguments

        Returns:
            dict: Response from FCM server (`multicast_id`, `success`, `failure`, `canonical_ids`, `results`)

        Raises:
            AuthenticationError: If :attr:`api_key` is not set or provided
                or there is an error authenticating the sender.
            FCMServerError: Internal server error or timeout error on Firebase cloud messaging server
            InvalidDataError: Invalid data provided
            InternalPackageError: Mostly from changes in the response of FCM,
                contact the project owner to resolve the issue
        """
        if registration_id is None:
            raise InvalidDataError('Invalid registration ID')
        # [registration_id] cos we're sending to a single device
        payload = self.parse_payload(
            registration_ids=[registration_id],
            condition=condition,
            collapse_key=collapse_key,
            delay_while_idle=delay_while_idle,
            time_to_live=time_to_live,
            restricted_package_name=restricted_package_name,
            low_priority=low_priority,
            dry_run=dry_run,
            data_message=data_message,
            content_available=content_available,
            remove_notification=True,
            android_channel_id=android_channel_id,
            extra_notification_kwargs=extra_notification_kwargs,
            **extra_kwargs
        )

        headers =  {
            "Content-Type": self.CONTENT_TYPE,
            "Authorization": "key=" + api_key,
        }             

        self.send_request([payload], headers, timeout)
        return self.parse_responses()

    def notify_single_device(self,
                             api_key=None,
                             registration_id=None,
                             message_body=None,
                             message_title=None,
                             message_icon=None,
                             sound=None,
                             condition=None,
                             collapse_key=None,
                             delay_while_idle=False,
                             time_to_live=None,
                             restricted_package_name=None,
                             low_priority=False,
                             dry_run=False,
                             data_message=None,
                             click_action=None,
                             badge=None,
                             color=None,
                             tag=None,
                             body_loc_key=None,
                             body_loc_args=None,
                             title_loc_key=None,
                             title_loc_args=None,
                             content_available=None,
                             android_channel_id=None,
                             timeout=5,
                             extra_notification_kwargs=None,
                             extra_kwargs={}):
        """
        Send push notification to a single device

        Args:
            registration_id (list, optional): FCM device registration ID
            message_body (str, optional): Message string to display in the notification tray
            message_title (str, optional): Message title to display in the notification tray
            message_icon (str, optional): Icon that apperas next to the notification
            sound (str, optional): The sound file name to play. Specify "Default" for device default sound.
            condition (str, optiona): Topic condition to deliver messages to
            collapse_key (str, optional): Identifier for a group of messages
                that can be collapsed so that only the last message gets sent
                when delivery can be resumed. Defaults to `None`.
            delay_while_idle (bool, optional): deprecated
            time_to_live (int, optional): How long (in seconds) the message
                should be kept in FCM storage if the device is offline. The
                maximum time to live supported is 4 weeks. Defaults to `None`
                which uses the FCM default of 4 weeks.
            restricted_package_name (str, optional): Name of package
            low_priority (bool, optional): Whether to send notification with
                the low priority flag. Defaults to `False`.
            dry_run (bool, optional): If `True` no message will be sent but request will be tested.
            data_message (dict, optional): Custom key-value pairs
            click_action (str, optional): Action associated with a user click on the notification
            badge (str, optional): Badge of notification
            color (str, optional): Color of the icon
            tag (str, optional): Group notification by tag
            body_loc_key (str, optional): Indicates the key to the body string for localization
            body_loc_args (list, optional): Indicates the string value to replace format
                specifiers in body string for localization
            title_loc_key (str, optional): Indicates the key to the title string for localization
            title_loc_args (list, optional): Indicates the string value to replace format
                specifiers in title string for localization
            content_available (bool, optional): Inactive client app is awoken
            android_channel_id (str, optional): Starting in Android 8.0 (API level 26),
                all notifications must be assigned to a channel. For each channel, you can set the
                visual and auditory behavior that is applied to all notifications in that channel.
                Then, users can change these settings and decide which notification channels from
                your app should be intrusive or visible at all.
            timeout (int, optional): set time limit for the request
            extra_notification_kwargs (dict, optional): More notification keyword arguments
            extra_kwargs (dict, optional): More keyword arguments

        Returns:
            dict: Response from FCM server (`multicast_id`, `success`, `failure`, `canonical_ids`, `results`)

        Raises:
            AuthenticationError: If :attr:`api_key` is not set or provided
                or there is an error authenticating the sender.
            FCMServerError: Internal server error or timeout error on Firebase cloud messaging server
            InvalidDataError: Invalid data provided
            InternalPackageError: Mostly from changes in the response of FCM,
                contact the project owner to resolve the issue
        """
        if registration_id is None:
            raise InvalidDataError('Invalid registration ID')
        # [registration_id] cos we're sending to a single device
        payload = self.parse_payload(
            registration_ids=[registration_id],
            message_body=message_body,
            message_title=message_title,
            message_icon=message_icon,
            sound=sound,
            condition=condition,
            collapse_key=collapse_key,
            delay_while_idle=delay_while_idle,
            time_to_live=time_to_live,
            restricted_package_name=restricted_package_name,
            low_priority=low_priority,
            dry_run=dry_run, data_message=data_message, click_action=click_action,
            badge=badge,
            color=color,
            tag=tag,
            body_loc_key=body_loc_key,
            body_loc_args=body_loc_args,
            title_loc_key=title_loc_key,
            title_loc_args=title_loc_args,
            android_channel_id=android_channel_id,
            content_available=content_available,
            extra_notification_kwargs=extra_notification_kwargs,
            **extra_kwargs
        )

        headers =  {
            "Content-Type": self.CONTENT_TYPE,
            "Authorization": "key=" + api_key,
        }                    

        self.send_request([payload], headers, timeout)
        return self.parse_responses()

    
    
    def notify_multiple_devices(self,
                                api_key=None,
                                registration_ids=None,
                                message_body=None,
                                message_title=None,
                                message_icon=None,
                                sound=None,
                                condition=None,
                                collapse_key=None,
                                delay_while_idle=False,
                                time_to_live=None,
                                restricted_package_name=None,
                                low_priority=False,
                                dry_run=False,
                                data_message=None,
                                click_action=None,
                                badge=None,
                                color=None,
                                tag=None,
                                body_loc_key=None,
                                body_loc_args=None,
                                title_loc_key=None,
                                title_loc_args=None,
                                content_available=None,
                                android_channel_id=None,
                                timeout=5,
                                extra_notification_kwargs=None,
                                extra_kwargs={}):
        """
        Sends push notification to multiple devices, can send to over 1000 devices

        Args:
            registration_ids (list, optional): FCM device registration IDs
            message_body (str, optional): Message string to display in the notification tray
            message_title (str, optional): Message title to display in the notification tray
            message_icon (str, optional): Icon that apperas next to the notification
            sound (str, optional): The sound file name to play. Specify "Default" for device default sound.
            condition (str, optiona): Topic condition to deliver messages to
            collapse_key (str, optional): Identifier for a group of messages
                that can be collapsed so that only the last message gets sent
                when delivery can be resumed. Defaults to `None`.
            delay_while_idle (bool, optional): deprecated
            time_to_live (int, optional): How long (in seconds) the message
                should be kept in FCM storage if the device is offline. The
                maximum time to live supported is 4 weeks. Defaults to `None`
                which uses the FCM default of 4 weeks.
            restricted_package_name (str, optional): Name of package
            low_priority (bool, optional): Whether to send notification with
                the low priority flag. Defaults to `False`.
            dry_run (bool, optional): If `True` no message will be sent but request will be tested.
            data_message (dict, optional): Custom key-value pairs
            click_action (str, optional): Action associated with a user click on the notification
            badge (str, optional): Badge of notification
            color (str, optional): Color of the icon
            tag (str, optional): Group notification by tag
            body_loc_key (str, optional): Indicates the key to the body string for localization
            body_loc_args (list, optional): Indicates the string value to replace format
                specifiers in body string for localization
            title_loc_key (str, optional): Indicates the key to the title string for localization
            title_loc_args (list, optional): Indicates the string value to replace format
                specifiers in title string for localization
            content_available (bool, optional): Inactive client app is awoken
            android_channel_id (str, optional): Starting in Android 8.0 (API level 26),
                all notifications must be assigned to a channel. For each channel, you can set the
                visual and auditory behavior that is applied to all notifications in that channel.
                Then, users can change these settings and decide which notification channels from
                your app should be intrusive or visible at all.
            timeout (int, optional): set time limit for the request
            extra_notification_kwargs (dict, optional): More notification keyword arguments
            extra_kwargs (dict, optional): More keyword arguments

        Returns:
            dict: Response from FCM server (`multicast_id`, `success`, `failure`, `canonical_ids`, `results`)

        Raises:
            AuthenticationError: If :attr:`api_key` is not set or provided
                or there is an error authenticating the sender.
            FCMServerError: Internal server error or timeout error on Firebase cloud messaging server
            InvalidDataError: Invalid data provided
            InternalPackageError: JSON parsing error, mostly from changes in the response of FCM,
                create a new github issue to resolve it.
        """
        if not isinstance(registration_ids, list):
            raise InvalidDataError('Invalid registration IDs (should be list)')

        payloads = []

        registration_id_chunks = self.registration_id_chunks(registration_ids)
        for registration_ids in registration_id_chunks:
            # appends a payload with a chunk of registration ids here
            payloads.append(self.parse_payload(
                registration_ids=registration_ids,
                message_body=message_body,
                message_title=message_title,
                message_icon=message_icon,
                sound=sound,
                condition=condition,
                collapse_key=collapse_key,
                delay_while_idle=delay_while_idle,
                time_to_live=time_to_live,
                restricted_package_name=restricted_package_name,
                low_priority=low_priority,
                dry_run=dry_run, data_message=data_message,
                click_action=click_action,
                badge=badge,
                color=color,
                tag=tag,
                body_loc_key=body_loc_key,
                body_loc_args=body_loc_args,
                title_loc_key=title_loc_key,
                title_loc_args=title_loc_args,
                content_available=content_available,
                android_channel_id=android_channel_id,
                extra_notification_kwargs=extra_notification_kwargs,
                **extra_kwargs
            ))


        headers =  {
            "Content-Type": self.CONTENT_TYPE,
            "Authorization": "key=" + api_key,
        }            
        self.send_request(payloads, headers, timeout)
        return self.parse_responses()

    def parse_responses(self):
         """
         Parses the json response sent back by the server and tries to get out the important return variables
   
         Returns:
             dict: multicast_ids (list), success (int), failure (int), canonical_ids (int),
                 results (list) and optional topic_message_id (str but None by default)
   
         Raises:
             FCMServerError: FCM is temporary not available
             AuthenticationError: error authenticating the sender account
             InvalidDataError: data passed to FCM was incorrecly structured
         """
         response_dict = {
             'multicast_ids': [],
             'success': 0,
             'failure': 0,
             'canonical_ids': 0,
             'results': [],
             'topic_message_id': None
         }
   
         for response in self.send_request_responses:
             if response.status_code == 200:
                 if 'content-length' in response.headers and int(response.headers['content-length']) <= 0:
                     raise FCMServerError("FCM server connection error, the response is empty")
                 else:
                     parsed_response = response.json()
   
                     multicast_id = parsed_response.get('multicast_id', None)
                     success = parsed_response.get('success', 0)
                     failure = parsed_response.get('failure', 0)
                     canonical_ids = parsed_response.get('canonical_ids', 0)
                     results = parsed_response.get('results', [])
                     message_id = parsed_response.get('message_id', None)  # for topic messages
                     if message_id:
                         success = 1
                     if multicast_id:
                         response_dict['multicast_ids'].append(multicast_id)
                     response_dict['success'] += success
                     response_dict['failure'] += failure
                     response_dict['canonical_ids'] += canonical_ids
                     response_dict['results'].extend(results)
                     response_dict['topic_message_id'] = message_id
   
             elif response.status_code == 401:
                 raise AuthenticationError("There was an error authenticating the sender account")
             elif response.status_code == 400:
                 raise InvalidDataError(response.text)
             else:
                 raise FCMServerError("FCM server is temporarily unavailable")
         return response_dict
    

