# Copyright (c) 2023, wns and contributors
# For license information, please see license.txt
import os
import json
import time
import asyncio

import frappe
from frappe.model.document import Document

from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, ResultReason, AudioConfig, CancellationReason
import openai
from pydub import AudioSegment

class NEXUS(Document):
	pass

subscription_key = 'cdf26bd3a5f2443f91a103c36f4f9dd3'
service_region = 'eastus'

openai.api_type = "azure"
openai.api_version = "2023-05-15" 
openai.api_base = "https://wts-cis-openai-gpt4.openai.azure.com/"  # Your Azure OpenAI resource's endpoint value.
openai.api_key = "1303dd742d1c4f0b97053efe25a22a06"

BASE_FILE_PATH = './opex.wns.com'

def make_score_json_system_prompt(score_headers):
	hardcoded_fields = {
		'feedback': {
			'type': 'string',
			'description': 'feedback given to the custom service executive'
		},
		'call_category': {
			'type': 'string',
			'description': 'categorization of the call or interaction'
		},
		'escalation_due': {
			'type': 'boolean',
			'description': 'is escalation required or not'
		}
	}
	schema = {
        "type": "object",
        "properties": {},
        "required": []
    }

	for key in score_headers:
		schema["properties"][key] = {
			"type": "number"  # You can change the type as needed
		}
		schema["required"].append(key)

	for key in hardcoded_fields:
		schema["properties"][key] = hardcoded_fields[key]
		schema["required"].append(key)


	return """
Answer the users question as best as possible.
You must format your output as a JSON value that adheres to a given "JSON Schema" instance.

"JSON Schema" is a declarative language that allows you to annotate and validate JSON documents.

For example, the example "JSON Schema" instance {{"properties": {{"foo": {{"description": "a list of test words", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}}}
would match an object with one required property, "foo". The "type" property specifies "foo" must be an "array", and the "description" property semantically describes it as "a list of test words". The items within "foo" must be strings.
Thus, the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of this example "JSON Schema". The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.

Your output will be parsed and type-checked according to the provided schema instance, so make sure all fields in your output match the schema exactly and there are no trailing commas!

Here is the JSON Schema instance your output must adhere to:
""" + json.dumps(schema)

def make_score_json_user_prompt(prev_ai_response):
	return "Extract numeric score values from the text given below.\n\nTEXT:\n" + prev_ai_response


# def get_json_response(score_headers, prev_ai_response):
async def get_json_response(score_headers, prev_ai_response):
	response = openai.ChatCompletion.create(
		engine="gpt-4", # The deployment name you chose when you deployed the GPT-35-Turbo or GPT-4 model.
		messages = [
			{"role": "system", "content": make_score_json_system_prompt(score_headers)},
			{"role": "user", "content": make_score_json_user_prompt(prev_ai_response)}
		]
	)

	response_chat = response.choices[0].message["content"]

	return response_chat

def getTranscription(mp3_file_path):
	speech_config = SpeechConfig(subscription=subscription_key, region=service_region)
	audio_config = AudioConfig(filename=mp3_file_path)

	# Initialize the Speech Recognizer
	speech_recognizer = SpeechRecognizer(
		speech_config=speech_config,
		audio_config=audio_config
	)

	done = False
	recognized_lines = []

	def on_utterance_recognized(evt):
		recognized_lines.append(evt.result.text)

	def stop_cb(evt):
		"""callback that stops continuous recognition upon receiving an event `evt`"""

		print('CLOSING on {}'.format(evt))
		speech_recognizer.stop_continuous_recognition()
		nonlocal done
		done = True

	def on_cancellation(evt):
		result = evt.result
		if result.reason == ResultReason.Canceled:
			cancellation_details = result.cancellation_details
			print("Speech Recognition canceled: {}".format(cancellation_details.reason))
			
			if cancellation_details.reason == CancellationReason.Error:
				print("Error details: {}".format(cancellation_details.error_details))

	# Connect callbacks to the events fired by the speech recognizer
	# speech_recognizer.recognized.connect(lambda evt: print('RECOGNIZED: {}'.format(evt)))
	speech_recognizer.recognized.connect(on_utterance_recognized)
	speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
	speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
	speech_recognizer.canceled.connect(on_cancellation)
	# stop continuous recognition on either session stopped or canceled events
	speech_recognizer.session_stopped.connect(stop_cb)
	speech_recognizer.canceled.connect(stop_cb)

	# Start continuous speech recognition
	speech_recognizer.start_continuous_recognition()
	while not done:
		time.sleep(.5)
	
	print("RECOGNIZED TEXT:::::::")
	print(recognized_lines)

	
	return ' '.join(recognized_lines)

def get_all_attachment_paths(docname):
	files = frappe.get_all('File', filters={'attached_to_doctype': 'NEXUS', 'attached_to_name': docname}, fields=['file_url'])

	return {'files': [file['file_url'] for file in files]}

def get_wav_from_mp3(file_path):
	audio = AudioSegment.from_mp3(file_path)

	output_format = "wav"

	output_wav_file = file_path.replace(".mp3", f".{output_format}")

	audio.export(output_wav_file, format=output_format)

	print("CONVERTED FILE NAME:", output_wav_file)

	return output_wav_file

# def transcribe(file_path):
async def transcribe(file_path):
	full_file_path = BASE_FILE_PATH + file_path

	if os.path.exists(full_file_path):
		print("FOUND MP3 FILE")
	else:
		print("DID NOT FIND FILE")


	print("FILENAME: ", full_file_path)

	if full_file_path.endswith('.mp3'):
		full_file_path = get_wav_from_mp3(full_file_path)
	
	# Set up the Speech Configuration
	transcription = getTranscription(full_file_path)
	return transcription

# def send_to_ai(transcription, prompt):
async def send_to_ai(transcription, prompt):
	response = openai.ChatCompletion.create(
		engine="gpt-4", # The deployment name you chose when you deployed the GPT-35-Turbo or GPT-4 model.
		messages = [
			{"role": "system", "content": prompt},
			{"role": "user", "content": transcription}
		]
	)

	response_chat = response.choices[0].message["content"]
	print(response_chat)
	return response_chat

@frappe.whitelist(allow_guest=True)
def get_results():
	if 'docname' not in frappe.form_dict:
		frappe.msgprint("No docname provided")
		return "No docname provided", 400
	
	if 'prompt' not in frappe.form_dict:
		frappe.msgprint("No prompt provided")
		return "No prompt provided", 400
	
	if 'scores' not in frappe.form_dict:
		frappe.msgprint("No scores provided")
		return "No scores provided", 400

	docname = frappe.form_dict.get('docname')
	prompt = frappe.form_dict.get('prompt')
	score_headers = json.loads(frappe.form_dict.get('scores'))

	files = get_all_attachment_paths(docname)['files']

	print("FILES::", files)
	# return

	document = frappe.get_doc('NEXUS', docname)

	# for file in files:
	# 	frappe.enqueue(process_file, timeout=3000, file=file, document=document, prompt=prompt)

	try:
		loop = asyncio.get_event_loop()
	except RuntimeError as e:
		if str(e).startswith('There is no current event loop in thread'):
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
		else:
			raise

	asyncio.set_event_loop(loop)

	print("starting event loop")
	loop.run_until_complete(process_files_wrapper(files, document, prompt, score_headers))

	return


async def process_files_wrapper(files, document, prompt,score_headers):
	tasks = [process_file(file, document, prompt, score_headers) for file in files]
	# tasks = [process_file(files[1], document, prompt, score_headers)]
	await asyncio.gather(*tasks)

# def process_file(file, document, prompt):
async def process_file(file, document, prompt, score_headers):
	row = document.append('output')

	row.status = 'Not Done'
	row.assessment_label = file
	# document._dirty = True
	document.save()

	try:
		# transcription = transcribe(file)
		transcription = await transcribe(file)
		row.score = transcription
		# document._dirty = Truee
		document.save()

		# ai_response = send_to_ai(transcription, prompt)
		ai_response = await send_to_ai(transcription, prompt)
		row.result = ai_response
		# document._dirty = True
		document.save()

		# json_response = get_json_response(score_headers, ai_response)
		json_response = await get_json_response(score_headers, ai_response)
		print("JSON AI RESPONSE::", json_response)
		json_dict = json.loads(json_response)
		print("JSON DICT::", json_dict)

		if 'escalation_due' in json_dict:
			json_dict['escalation_due'] = 'Yes' if json_dict['escalation_due'] else 'No'

		row.update(json_dict)
		# for score_key in score_headers:
		# 	row[score_key] = json_dict[score_key]

		row.status = 'Done'
		# document._dirty = True
		document.save()

	except Exception as e:
		row.status = 'Error'
		document.save()
