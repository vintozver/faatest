# -*- coding: utf-8 -*-

import os.path
import datetime
import dateutil
import dateutil.relativedelta
import pytz
import json
import pickle
import random
import bson
import pymongo

import httplib

import config
import modules.templates.filesystem as mod_tmpl_fs
import modules.data.mongo as mod
import modules.data.mongo.ground_school as mod_GS
import modules.data.mongo.ground_school.logic as mod_logic


def rpc_handler(method):
	method.rpc_handler = True
	return method

from handlers.ext.paramed_cgi import HandlerError as _base_error
class HandlerError(_base_error):
	pass

from handlers.ext.paramed_cgi import Handler as _base
class Handler(_base):
	def load_state(self):
		state_obj = pickle.loads(self.req.GroundSchoolSession.get('state') or pickle.dumps(mod_logic.State()))
		if state_obj.state() == state_obj.STATE_NONE:
			state_obj._state = state_obj.STATE_CHOOSE_GROUP
		return state_obj
	def save_state(self, state_obj):
		self.req.GroundSchoolSession['state'] = pickle.dumps(state_obj)
		self.req.GroundSchoolSession.save()

	@mod.session_wrapper_context()
	def render_container(self):
		state_obj = self.load_state()
		if state_obj.state() == state_obj.STATE_CHOOSE_GROUP:
			items = mod_GS.Group.get_list()
			html = mod_tmpl_fs.TemplateFactory('asset_choose_group').render({'groups': items})
		elif state_obj.state() == state_obj.STATE_CHOOSE_TEST:
			GroupID = state_obj.group()
			try:
				group_item = mod_GS.Group.get_by_id(GroupID)
			except mod_GS.Group._ErrorNotFound:
				raise HandlerError('Groups.GroupID not found', GroupID)
			tests_items = mod_GS.Test.get_list_by_group_id(GroupID)
			html = mod_tmpl_fs.TemplateFactory('asset_choose_test').render({'group': group_item, 'tests': tests_items})
		elif state_obj.state() == state_obj.STATE_READY:
			TestID = state_obj.test()
			try:
				test_item = mod_GS.Test.get_by_id(TestID)
			except mod_GS.Test._ErrorNotFound:
				raise HandlerError('Tests.TestID not found', TestID)
			GroupID = test_item.GroupID
			try:
				group_item = mod_GS.Group.get_by_id(GroupID)
			except mod_GS.Group._ErrorNotFound:
				raise HandlerError('Groups.GroupID not found', GroupID)
			html = mod_tmpl_fs.TemplateFactory('asset_ready').render({'group': group_item, 'test': test_item})
		elif state_obj.state() == state_obj.STATE_SURVEY:
			TestID = state_obj.test()
			try:
				test_item = mod_GS.Test.get_by_id(TestID)
			except mod_GS.Test._ErrorNotFound:
				raise HandlerError('Tests.TestID not found', TestID)
			GroupID = test_item.GroupID
			try:
				group_item = mod_GS.Group.get_by_id(GroupID)
			except mod_GS.Group._ErrorNotFound:
				raise HandlerError('Groups.GroupID not found', GroupID)
			QuestionID = state_obj.survey_get_question()
			try:
				question_item = mod_GS.Question.get_by_id(QuestionID)
			except mod_GS.Question._ErrorNotFound:
				raise HandlerError('Questions.QuestionID not found', QuestionID)
			answers_items = sorted(question_item.get('Answers', []), key=lambda item: item['SortBy'])
			answers_items = map(lambda answer_item: mod_GS.Answer.create_from_data(answer_item), answers_items)
			images_items = question_item.get('Images', [])
			images_items = map(lambda image_item: mod_GS.QuestionImage.create_from_data(image_item), images_items)
			AnswerID = state_obj.questions_states.has_key(QuestionID) and \
				state_obj.questions_states[QuestionID].get('answer') or None
			if AnswerID != None:
				answer_item = filter(lambda item: item.AnswerID == AnswerID, answers_items)
				if answer_item:
					answer_item = answer_item[0]
				else:
					raise HandlerError('Questions.Answers.AnswerID not found', QuestionID, AnswerID)
			else:
				answer_item = None
			if state_obj.mix_answers() and AnswerID == None:
				random.shuffle(answers_items)
			html = mod_tmpl_fs.TemplateFactory('asset_survey').render({
				'mode': state_obj.mode() == state_obj.MODE_REAL,
				'group': group_item,
				'test': test_item,
				'question_index': state_obj.survey_get_question_index() + 1,
				'question': question_item,
				'answers': answers_items,
				'answer': answer_item,
				'images': images_items,
				'report_single': state_obj.report_single(),
			})
		elif state_obj.state() == state_obj.STATE_SURVEY_RESULTS:
			TestID = state_obj.test()
			try:
				test_item = mod_GS.Test.get_by_id(TestID)
			except mod_GS.Test._ErrorNotFound:
				raise HandlerError('Tests.TestID not found', TestID)
			GroupID = test_item.GroupID
			try:
				group_item = mod_GS.Group.get_by_id(GroupID)
			except mod_GS.Group._ErrorNotFound:
				raise HandlerError('Groups.GroupID not found', GroupID)
			results = []
			for QuestionID in state_obj.questions:
				try:
					question_item = mod_GS.Question.get_by_id(QuestionID)
				except mod_GS.Question._ErrorNotFound:
					raise HandlerError('Questions.QuestionID not found', QuestionID)
				AnswerID = state_obj.questions_states.has_key(QuestionID) and state_obj.questions_states[QuestionID].get('answer') or None
				if AnswerID != None:
					answers_items = map(lambda answer_item: mod_GS.Answer.create_from_data(answer_item), question_item.get('Answers', []))
					if answers_items:
						answer_item = answers_items[0]
					else:
						raise HandlerError('Questions.Answers.AnswerID not found', QuestionID, AnswerID)

					results.append({'question': question_item.QuestionText, 'answer': answer_item.AnswerText, 'correct': answer_item.IsCorrect})
				else:
					results.append({'question': question_item.QuestionText})
			html = mod_tmpl_fs.TemplateFactory('asset_survey_results').render({
				'mode': state_obj.mode() == state_obj.MODE_REAL,
				'group': group_item,
				'test': test_item,
				'results': results,
			})
		elif state_obj.state() == state_obj.STATE_REAL:
			html = 'REAL'
		else:
			raise HandlerError('Unexpected state', state_obj.state)
		self.save_state(state_obj)

		return html

	def render_container_obj(self):
		return {'html': self.render_container()}

	def render_result(self, result=True, message=None):
		try:
			container_obj = self.render_container_obj()
		except mod_logic.StateError, err:
			container_obj = None
			message = message and message + '\n' + err.args[0] or err.args[0]
		return {'result': result, 'message': message, 'container': container_obj}

	@rpc_handler
	def load_container(self):
		return self.render_result()
	
	@rpc_handler
	def choice_reset(self):
		state_obj = self.load_state()
		state_obj.choice_reset()
		self.save_state(state_obj)
		return self.render_result()

	@rpc_handler
	def choose_group(self):
		try:
			GroupID = self.cgi_params.param_post('GroupID')
		except self.cgi_params.NotFoundError:
			raise HandlerError('Missing mandatory parameter', 'GroupID')
		try:
			GroupID = int(GroupID)
		except TypeError:
			raise HandlerError('Invalid mandatory parameter', 'GroupID')
		except ValueError:
			raise HandlerError('Invalid mandatory parameter', 'GroupID')
		state_obj = self.load_state()
		state_obj.choose_group(GroupID)
		self.save_state(state_obj)
		return self.render_result()

	@rpc_handler
	def choose_test(self):
		try:
			TestID = self.cgi_params.param_post('TestID')
		except self.cgi_params.NotFoundError:
			raise HandlerError('Missing mandatory parameter', 'TestID')
		try:
			TestID = int(TestID)
		except TypeError:
			raise HandlerError('Invalid mandatory parameter', 'TestID')
		except ValueError:
			raise HandlerError('Invalid mandatory parameter', 'TestID')
		state_obj = self.load_state()
		state_obj.choose_test(TestID)
		self.save_state(state_obj)
		return self.render_result()

	@mod.session_wrapper_context()
	def _run(self, mode=mod_logic.State.MODE_REAL, count=50, mix_questions=True, mix_answers=True, report_single=False, deadtime=2700):
		state_obj = self.load_state()
		TestID = state_obj.test()
		items = mod_GS.QuestionTest.get_questions_by_test_id(TestID)
		try:
			questions = [item.QuestionID for item in items]
			if mix_questions:
				random.shuffle(questions)
			state_obj.survey_run(mode, questions, count, mix_questions, mix_answers, report_single)
			self.save_state(state_obj)
			result = True
			message = None
		except mod_logic.StateError, err:
			result = False
			message = err.args[0]
		return self.render_result(result, message)

	@rpc_handler
	def practice_run(self):
		try:
			count = self.cgi_params.param_post('count')
			try:
				count = int(count)
			except TypeError:
				raise HandlerError('Invalid parameter', 'count')
			except ValueError:
				raise HandlerError('Invalid parameter', 'count')
			if count == 0:
				count = None
		except self.cgi_params.NotFoundError:
			count = None
		try:
			mix_questions = self.cgi_params.param_post('mix_questions')
			try:
				mix_questions = int(mix_questions)
			except TypeError:
				raise HandlerError('Invalid parameter', 'mix_questions')
			except ValueError:
				raise HandlerError('Invalid parameter', 'mix_questions')
			mix_questions = bool(mix_questions)
		except self.cgi_params.NotFoundError:
			mix_questions = False
		try:
			mix_answers = self.cgi_params.param_post('mix_answers')
			try:
				mix_answers = int(mix_answers)
			except TypeError:
				raise HandlerError('Invalid parameter', 'mix_answers')
			except ValueError:
				raise HandlerError('Invalid parameter', 'mix_answers')
			mix_answers = bool(mix_answers)
		except self.cgi_params.NotFoundError:
			mix_answers = False
		try:
			report_single = self.cgi_params.param_post('report_single')
			try:
				report_single = int(report_single)
			except TypeError:
				raise HandlerError('Invalid parameter', 'report_single')
			except ValueError:
				raise HandlerError('Invalid parameter', 'report_single')
			report_single = bool(report_single)
		except self.cgi_params.NotFoundError:
			report_single = False
		return self._run(mod_logic.State.MODE_PRACTICE, count, mix_questions, mix_answers, report_single)

	@rpc_handler
	def real_run(self):
		return self._run()

	@rpc_handler
	def survey_choose_question(self):
		try:
			QuestionID = self.cgi_params.param_post('QuestionID')
		except self.cgi_params.NotFoundError:
			raise HandlerError('Missing mandatory parameter', 'QuestionID')
		try:
			QuestionID = int(QuestionID)
		except TypeError:
			raise HandlerError('Invalid mandatory parameter', 'QuestionID')
		except ValueError:
			raise HandlerError('Invalid mandatory parameter', 'QuestionID')
		state_obj = self.load_state()
		state_obj.survey_choose_question(QuestionID)
		self.save_state(state_obj)
		return self.render_result()
	@rpc_handler
	def survey_prev_question(self):
		state_obj = self.load_state()
		state_obj.survey_prev_question()
		self.save_state(state_obj)
		return self.render_result()
	@rpc_handler
	def survey_next_question(self):
		state_obj = self.load_state()
		state_obj.survey_next_question()
		self.save_state(state_obj)
		return self.render_result()

	@rpc_handler
	@mod.session_wrapper_context()
	def survey_show_questions(self):
		state_obj = self.load_state()
		if state_obj.state() != state_obj.STATE_SURVEY:
			raise HandlerError('Unexpected state', state_obj.state)

		TestID = state_obj.test()
		try:
			test_item = mod_GS.Test.get_by_id(TestID)
		except mod_GS.Test._ErrorNotFound:
			raise HandlerError('Tests.TestID not found', TestID)
		GroupID = test_item.GroupID
		try:
			group_item = mod_GS.Group.get_by_id(GroupID)
		except mod_GS.Group._ErrorNotFound:
			raise HandlerError('Groups.GroupID not found', GroupID)
		questions_items = [mod_GS.Question.get_by_id(QuestionID) for QuestionID in state_obj.questions]
		questions_states = [(question_item, state_obj.questions_states.get(question_item.QuestionID)) for question_item in questions_items]
		return {'result': True, 'message': None, 'container': {'html':
			mod_tmpl_fs.TemplateFactory('asset_survey_questions').render({
				'mode': state_obj.mode() == state_obj.MODE_REAL,
				'group': group_item,
				'test': test_item,
				'questions_states': questions_states,
				'report_single': state_obj.report_single(),
			})
		}}

	@rpc_handler
	@mod.session_wrapper_context()
	def survey_answer_question(self):
		state_obj = self.load_state()
		QuestionID = state_obj.survey_get_question()
		try:
			AnswerID = self.cgi_params.param_post('AnswerID')
		except self.cgi_params.NotFoundError:
			raise HandlerError('Missing mandatory parameter', 'AnswerID')
		try:
			AnswerID = int(AnswerID)
		except TypeError:
			raise HandlerError('Invalid mandatory parameter', 'AnswerID')
		except ValueError:
			raise HandlerError('Invalid mandatory parameter', 'AnswerID')

		try:
			question_item = mod_GS.Question.get_by_id(QuestionID)
		except mod_GS.Question._ErrorNotFound:
			raise HandlerError('Questions.QuestionID not found', QuestionID)
		answers_items = sorted(question_item.get('Answers', []), key=lambda item: item['SortBy'])
		answers_items = map(lambda answer_item: mod_GS.Answer.create_from_data(answer_item), answers_items)

		correct = AnswerID in map(lambda map_item: map_item.AnswerID, filter(lambda filter_item: filter_item.IsCorrect, answers_items))
		try:
			state_obj.survey_answer_question(QuestionID, AnswerID, correct)
			if not state_obj.survey_roll_question():
				state_obj.survey_finish()
			self.save_state(state_obj)

			if state_obj.report_single():
				if correct:
					message = mod_tmpl_fs.TemplateFactory('asset_notification_correct').render({})
				else:
					message = mod_tmpl_fs.TemplateFactory('asset_notification_incorrect').render({})
			else:
				message = None
			result = True
		except mod_logic.StateError, err:
			result = False
			message = err.args[0]

		return self.render_result(result, message)

	@rpc_handler
	def survey_finish(self):
		state_obj = self.load_state()
		state_obj.survey_finish()
		self.save_state(state_obj)
		return self.render_result()

	@rpc_handler
	def survey_close(self):
		state_obj = self.load_state()
		state_obj.survey_close()
		self.save_state(state_obj)
		return self.render_result()

	def __call__(self):
		try:
			action = self.cgi_params.param_get('action')
		except self.cgi_params.NotFoundError:
			raise HandlerError('Missing mandatory parameter', 'action')

		try:
			method = getattr(self, action)
		except AttributeError:
			raise HandlerError('Missing RPC handler', action)
		if hasattr(method, 'rpc_handler') and getattr(method, 'rpc_handler'):
			result = method()
		else:
			raise HandlerError('The method is not a RPC handler', action)

		content = json.dumps(result)
		self.req.setResponseCode(httplib.OK, httplib.responses[httplib.OK])
		self.req.setHeader('Cache-Control', 'public, no-cache')
		self.req.setHeader('Content-Type', 'application/json; charset=utf-8')
		self.req.write(content)

