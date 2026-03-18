from activfinancial import *
from activfinancial.constants import *

import binascii
import threading
import os

_safe_print_lock = threading.Lock()
enable_legacy = False

def connect_session(handler=None, parameters={}):
	if handler is None:
		handler = PrintSessionHandler()

	# Enable downloading of all available dictionaries, and
	# enable a CTRL handler to exit cleanly on CTRL-C/CTRL-BREAK.
	parameters[FID_ENABLE_DICTIONARY_DOWNLOAD] = True
	parameters[FID_ENABLE_CTRL_HANDLER] = True

	if not enable_legacy:
		session = Session(parameters, handler) 
	else:
		session = legacy.LegacySession(parameters, handler)

	connect_parameters = session.get_parameters()

	# The host and user credentials are picked up from the Vercel's environment variables.
	#
	# Alternatively use the environment variables:
	#   ACTIV_SESSION_HOST
	#   ACTIV_SESSION_USER_ID
	#   ACTIV_SESSION_PASSWORD

	connect_parameters[FID_HOST]     = os.environ.get('ACTIV_SESSION_HOST')
	connect_parameters[FID_USER_ID]  = os.environ.get('ACTIV_SESSION_USER_ID')
	connect_parameters[FID_PASSWORD] = os.environ.get('ACTIV_SESSION_PASSWORD')

	print(f'Connecting to {connect_parameters[FID_HOST]}...')

	session.connect(connect_parameters, 5000)

	return session

def format_message_field(name, field):
	NAME_WIDTH = 40
	filler     = '.' * (NAME_WIDTH - len(name[:NAME_WIDTH - 1]))

	if isinstance(field, Field):
		if field.is_defined():
			string = str(field)
		else:
			string = 'undefined'

		if not field.does_update_last:
			string += ' *'
	elif field is None:
		return ''
	else:
		string = str(field)

	return f'{name} {filler} {string}\n'

def print_field(name, field):
	print(format_message_field(name, field), end = '')

def _get_event_type_string(data_source, event_type):
	activ_data_source_list = [
		DATA_SOURCE_ACTIV,
		DATA_SOURCE_ACTIV_DELAYED,
		DATA_SOURCE_ACTIV_LOW_LATENCY ]

	if data_source in activ_data_source_list:
		return market_data.event_type_to_string(event_type)
	else:
		return str(event_type)

def refresh_message_to_string(msg, metadata):
	output = f"{format_message_field('DataSource',             msg.data_source_id)}"\
			 f"{format_message_field('Symbology',              msg.symbology_id)}"\
			 f"{format_message_field('Symbol',                 msg.symbol)}"\
			 f"{format_message_field('TopicType',              topic_type_to_string(msg.topic_type))}"\
			 f"{format_message_field('PermissionId',           msg.permission_id)}"\
			 f"{format_message_field('UpdateId',               msg.update_id)}"\
			 f"{format_message_field('MapKey',                 binascii.hexlify(bytearray(msg.map_key))) if msg.map_key else ''}"\
			 f"{format_message_field('TopicSubscriptionState', topic_subscription_state_to_string(msg.topic_subscription_state))}"\
			 f"{format_message_field('GatewayTimestamp',       msg.gateway_timestamp)}"\
			 f"{format_message_field('ApiTimestamp',           msg.api_timestamp)}"

	for (fid, field) in msg.fields.items():
		field_name = metadata.get_field_name(msg.data_source_id, fid)
		output += format_message_field(field_name, field)

	return output

def update_message_to_string(msg, metadata):
	output = f"{format_message_field('DataSource',             msg.data_source_id)}"\
			 f"{format_message_field('Symbology',              msg.symbology_id)}"\
			 f"{format_message_field('Symbol',                 msg.symbol)}"\
			 f"{format_message_field('TopicType',              topic_type_to_string(msg.topic_type))}"\
			 f"{format_message_field('PermissionId',           msg.permission_id)}"\
			 f"{format_message_field('UpdateId',               msg.update_id)}"\
			 f"{format_message_field('EventType',              _get_event_type_string(msg.data_source_id, msg.event_type))}"\
			 f"{format_message_field('UpdateType',             update_type_to_string(msg.update_type))}"\
			 f"{format_message_field('MapKey',                 binascii.hexlify(bytearray(msg.map_key))) if msg.map_key else ''}"\
			 f"{format_message_field('TopicSubscriptionState', topic_subscription_state_to_string(msg.topic_subscription_state))}"\
			 f"{format_message_field('SourceId',               msg.source_id)}"\
			 f"{format_message_field('SequenceNumber',         msg.sequence_number)}"\
			 f"{format_message_field('ExchangeTransTimestamp', msg.exchange_transaction_timestamp)}"\
			 f"{format_message_field('SourceTimestamp',        msg.source_timestamp)}"\
			 f"{format_message_field('GatewayTimestamp',       msg.gateway_timestamp)}"\
			 f"{format_message_field('ApiTimestamp',           msg.api_timestamp)}"

	for (fid, field) in msg.fields.items():
		field_name = metadata.get_field_name(msg.data_source_id, fid)
		output += format_message_field(field_name, field)

	return output

def topic_status_message_to_string(msg):
	output = f"{format_message_field('DataSource',             msg.data_source_id)}"\
			 f"{format_message_field('Symbology',              msg.symbology_id)}"\
			 f"{format_message_field('Symbol',                 msg.symbol)}"\
			 f"{format_message_field('TopicType',              topic_type_to_string(msg.topic_type))}"\
			 f"{format_message_field('TopicSubscriptionState', topic_subscription_state_to_string(msg.topic_subscription_state))}"

	return output

def subscription_status_message_to_string(msg):
	output = f"{format_message_field('DataSource', msg.data_source_id)}"\
			 f"{format_message_field('Symbology',  msg.symbology_id)}"\
			 f"{format_message_field('Request',    msg.request)}"\
			 f"{format_message_field('State',      subscription_state_to_string(msg.state))}"\
			 f"{format_message_field('StatusCode', msg.status_code)}"

	return output

def snapshot_message_to_string(msg, metadata):
	output = f"{format_message_field('DataSource',   msg.data_source_id)}"\
			 f"{format_message_field('Symbology',    msg.symbology_id)}"\
			 f"{format_message_field('Symbol',       msg.symbol)}"\
			 f"{format_message_field('PermissionId', msg.permission_id)}"\
			 f"{format_message_field('UpdateId',     msg.update_id)}"\
			 f"{format_message_field('Timestamp',    msg.timestamp)}"\
			 f"{format_message_field('IsComplete',   msg.complete)}"

	for (fid, field) in msg.fields.items():
		field_name = metadata.get_field_name(msg.data_source_id, fid)
		output += format_message_field(field_name, field)

	return output

def snapshot_failure_message_to_string(msg):
	output = f"{format_message_field('DataSource',   msg.data_source_id)}"\
			 f"{format_message_field('Symbology',    msg.symbology_id)}"\
			 f"{format_message_field('Symbol',       msg.symbol)}"\
			 f"{format_message_field('PermissionId', msg.permission_id)}"\
			 f"{format_message_field('StatusCode',   status_code_to_string(msg.status_code))}"\
			 f"{format_message_field('IsComplete',   msg.complete)}"

	return output

def time_series_message_to_string(msg, metadata):
	output = f"{format_message_field('DataSource',   msg.data_source_id)}"\
			 f"{format_message_field('Symbology',    msg.symbology_id)}"\
			 f"{format_message_field('Symbol',       msg.symbol)}"\
			 f"{format_message_field('PermissionId', msg.permission_id)}"\
			 f"{format_message_field('Type',         time_series_type_to_string(msg.type))}"\
			 f"{format_message_field('IsComplete',   msg.complete)}"

	for (fid, field) in msg.fields.items():
		field_name = metadata.get_field_name(msg.data_source_id, fid)
		output += format_message_field(field_name, field)

	return output

def time_series_failure_message_to_string(msg):
	output = f"{format_message_field('DataSource',   msg.data_source_id)}"\
			 f"{format_message_field('Symbology',    msg.symbology_id)}"\
			 f"{format_message_field('Symbol',       msg.symbol)}"\
			 f"{format_message_field('PermissionId', msg.permission_id)}"\
			 f"{format_message_field('StatusCode',   status_code_to_string(msg.status_code))}"\
			 f"{format_message_field('IsComplete',   msg.complete)}"

	return output

def safe_print(msg):
	_safe_print_lock.acquire()
	try:
		print(msg)
	finally:
		_safe_print_lock.release()

class PrintSessionHandler:
	def on_session_connect(self, session):
		# Called for reconnects.
		print('on_session_connect')

	def on_session_disconnect(self, session):
		# Called when a graceful disconnect has completed.
		print('on_session_disconnect')

	def on_session_error(self, session, status_code):
		print('on_session_error:')
		print_field('StatusCode', status_code_to_string(status_code))

	def on_session_log_message(self, session, log_type, message):
		# Only print errors and warnings.
		if log_type == LOG_TYPE_ERROR or log_type == LOG_TYPE_WARNING:
			print('on_session_log_message:')
			print_field('LogType', log_type_to_string(log_type))
			print_field('Message', message)
		else:
			pass

class PrintSubscriptionHandler:
	def __init__(self):
		self.error = False

	def on_subscription_refresh(self, msg, context):
		print(f'REFRESH received for {msg.symbol}')
		print(refresh_message_to_string(msg, context.session.metadata))

	def on_subscription_update(self, msg, context):
		print(f'UPDATE received for {msg.symbol}')
		print(update_message_to_string(msg, context.session.metadata))

	def on_subscription_topic_status(self, msg, context):
		print(f'TOPIC STATUS received for {msg.symbol}')
		print(topic_status_message_to_string(msg))

	def on_subscription_status(self, msg, context):
		self.error = msg.is_error()
		print(f'SUBSCRIPTION STATUS received for {msg.request}')
		print(subscription_status_message_to_string(msg))
