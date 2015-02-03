# -*- coding: utf-8 -*-

import time

class StateError(Exception):
	pass

class State(object):
	STATE_NONE = None
	STATE_CHOOSE_GROUP = 'choose_group'
	STATE_CHOOSE_TEST = 'choose_test'
	STATE_READY = 'ready'
	STATE_SURVEY = 'survey'
	STATE_SURVEY_RESULTS = 'survey_results'
	MODE_PRACTICE = 'practice'
	MODE_REAL = 'real'

	def __init__(self):
		self._state = None

	def __getstate__(self):
		dump = {}
		dump['state'] = self._state
		try:
			dump['group'] = self._group
		except AttributeError:
			dump['group'] = None
		try:
			dump['test'] = self._test
		except AttributeError:
			dump['test'] = None
		if self._state in (self.STATE_SURVEY, self.STATE_SURVEY_RESULTS):
			dump['mode'] = self._mode
			dump['questions_index'] = self.questions_index
			dump['questions'] = self.questions
			dump['questions_states'] = self.questions_states
			dump['mix_questions'] = self._mix_questions
			dump['mix_answers'] = self._mix_answers
			dump['report_single'] = self._report_single
			dump['deadline'] = self._deadline
		return dump

	def __setstate__(self, dump):
		self._state = dump['state']
		if dump.get('group') != None:
			self._group = dump['group']
		if dump.get('test') != None:
			self._test = dump['test']
		if self._state in (self.STATE_SURVEY, self.STATE_SURVEY_RESULTS):
			self._mode = dump['mode']
			self.questions_index = dump['questions_index']
			self.questions = dump['questions']
			self.questions_states = dump['questions_states']
			self._mix_questions = dump['mix_questions']
			self._mix_answers = dump['mix_answers']
			self._report_single = dump['report_single']
			self._deadline = dump['deadline']

	def state(self):
		return self._state

	def choice_reset(self):
		assert self._state in (self.STATE_CHOOSE_GROUP, self.STATE_CHOOSE_TEST, self.STATE_READY), 'Unexpected current state "%s"' % self._state
		self._state = self.STATE_NONE
		try:
			del self._group
		except AttributeError:
			pass
		try:
			del self._test
		except AttributeError:
			pass

	def group(self):
		try:
			return self._group
		except AttributeError:
			return None
	def choose_group(self, group):
		assert self._state in (self.STATE_CHOOSE_GROUP, self.STATE_CHOOSE_TEST, self.STATE_READY), 'Unexpected current state "%s"' % self._state
		self._state = self.STATE_CHOOSE_TEST
		self._group = group
		try:
			del self._test
		except AttributeError:
			pass

	def test(self):
		try:
			return self._test
		except AttributeError:
			return None
	def choose_test(self, test):
		assert self._state in (self.STATE_CHOOSE_GROUP, self.STATE_CHOOSE_TEST, self.STATE_READY), 'Unexpected current state "%s"' % self._state
		self._state = self.STATE_READY
		try:
			del self._group
		except AttributeError:
			pass
		self._test = test

	def _ready_check(self):
		try:
			assert self._state in (self.STATE_READY, ), 'Unexpected current state "%s"' % self._state
		except AssertionError, err:
			raise StateError(*err.args)
	def _ready_survey_check(self):
		try:
			assert self._state in (self.STATE_READY, self.STATE_SURVEY), 'Unexpected current state "%s"' % self._state
		except AssertionError, err:
			raise StateError(*err.args)

	def mode(self):
		return self._mode
	def mix_questions(self):
		self._survey_check()
		return self._mix_questions
	def mix_answers(self):
		self._survey_check()
		return self._mix_answers
	def report_single(self):
		self._survey_check()
		return self._report_single
	def deadline(self):
		self._survey_check()
		return self._deadline
	def check_deadline(self):
		self._survey_check()
		if self.deadline == None:
			return True
		return self.deadline > int(time.time())
	def survey_run(self, mode, questions, limit=None, mix_questions=False, mix_answers=False, report_single=True, deadtime=None):
		try:
			assert self._state in (self.STATE_READY, ), 'Unexpected current state "%s"' % self._state
		except AssertionError, err:
			raise StateError(*err.args)
		try:
			assert len(questions), 'There are no questions available for the survey'
		except AssertionError, err:
			raise StateError(*err.args)
		try:
			if limit != None:
				assert limit > 0, 'Limit value is invalid'
				self.questions = questions[:limit]
			else:
				self.questions = questions[:]
			self.questions_index = -1
			self.questions_states = {}
		except AssertionError, err:
			raise StateError(*err.args)
		self._state = self.STATE_SURVEY
		self._mode = mode
		self._mix_questions = mix_questions
		self._mix_answers = mix_answers
		self._report_single = report_single
		if deadtime != None:
			self._deadline = int(time.time()) + deadtime
		else:
			self._deadline = None

	def _survey_check(self):
		try:
			assert self._state in (self.STATE_SURVEY, ), 'Unexpected current state "%s"' % self._state
		except AssertionError, err:
			raise StateError(*err.args)

	def survey_get_question_index(self):
		self._survey_check()
		if self.questions_index < 0:
			self.questions_index = 0
		if self.questions_index >= len(self.questions):
			self.questions_index = len(self.questions) - 1
		if self.questions_index != -1:
			return self.questions_index
		else:
			raise StateError('There are no questions available for the survey')
	def survey_get_question(self):
		return self.questions[self.survey_get_question_index()]

	def survey_choose_question(self, question):
		self._survey_check()
		try:
			self.questions_index = self.questions.index(question)
		except ValueError:
			self.questions_index = -1
	def survey_prev_question(self):
		self._survey_check()
		self.questions_index = (self.questions_index - 1) % len(self.questions)
	def survey_next_question(self):
		self._survey_check()
		self.questions_index = (self.questions_index + 1) % len(self.questions)

	def survey_answer_question(self, question, answer, correct):
		self._survey_check()
		if self.questions_states.has_key(question):
			raise StateError('Question "%s" is already answered' % str(question))
		self.questions_states[question] = {'answer': answer, 'correct': correct}

	def survey_roll_question(self):
		self._survey_check()
		if set(self.questions_states.keys()).issuperset(set(self.questions)):
			return False
		shift = 0
		while shift < len(self.questions):
			questions_index = (self.questions_index + shift) % len(self.questions)
			if self.questions_states.get(self.questions[questions_index]) == None:
				self.questions_index = questions_index
				return True
			else:
				shift = shift + 1
		return False

	def survey_finish(self):
		self._survey_check()
		self._state = self.STATE_SURVEY_RESULTS
		self.questions_index = None

	def survey_close(self):
		try:
			assert self._state in (self.STATE_SURVEY_RESULTS, ), 'Unexpected current state "%s"' % self._state
		except AssertionError, err:
			raise StateError(*err.args)
		self._state = self.STATE_NONE
		del self.questions_index
		del self.questions
		del self.questions_states

	def run_real(self):
		self._state = self.STATE_REAL

