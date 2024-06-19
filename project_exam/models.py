from django.db import models
from django.contrib.auth.models import User


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Role(models.Model):

	text = models.TextField(verbose_name='Роль')
	
	def __str__(self):
		return self.text
	

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class User_role(models.Model):

	user_id = models.OneToOneField(User, on_delete=models.CASCADE)
	role_id = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='Роль')
	

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Tests(models.Model):

	text = models.TextField(verbose_name='Тест')
	role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='Роль',default=1)
	number_of_questions = models.DecimalField(verbose_name='Количество вопросов', default=10, decimal_places=2, max_digits=6, null=True)
	time = models.DecimalField(verbose_name='Время', default=10, decimal_places=2, max_digits=6, null=True)
	done_score = models.DecimalField(verbose_name='Пороговый балл', default=5, decimal_places=2, max_digits=6, null=True)
	
	def __str__(self):
		return self.text


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Available_tests_for_users(models.Model):

	user_id = models.ForeignKey(User, on_delete=models.CASCADE)
	unavailable_tests = models.ForeignKey(Tests, on_delete=models.CASCADE, verbose_name='Не доступный тест', default=1)
	date = models.DateTimeField(auto_now=True, verbose_name='Test date')
	
	

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Close_tests_for_users(models.Model):

	user_id = models.ForeignKey(User, on_delete=models.CASCADE)
	unavailable_tests = models.ForeignKey(Tests, on_delete=models.CASCADE, verbose_name='Закрытый тест', default=1)
	
  
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Question(models.Model):

	number_of_answers_per_question = 1
	
	tests = models.ForeignKey(Tests, on_delete=models.CASCADE, verbose_name='Тест')
	text = models.TextField(verbose_name='Текст вопроса')
	max_score = models.DecimalField(verbose_name='Количество баллов за вопрос', default=1, decimal_places=2, max_digits=6)
	medical = models.BooleanField(default=False, null=False)
	
	def __str__(self):
		return self.text


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class SelectAnswer(models.Model):

	number_of_answer_options = 4

	question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE, verbose_name='Вопрос')
	correct = models.BooleanField(verbose_name='Правильный ответ?', default=False, null=False)
	text = models.TextField(verbose_name='Текст ответа')

	def __str__(self):
		return self.text


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class AnswersOnQuestions(models.Model):
	examUser = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
	tests = models.ForeignKey(Tests, on_delete=models.CASCADE)
	question = models.ForeignKey(Question, on_delete=models.CASCADE)
	answer = models.ForeignKey(SelectAnswer, on_delete=models.CASCADE, null=True)
	correct  = models.BooleanField(verbose_name='Правильный ответ?', default=False, null=False)
	number_of_points = models.DecimalField(verbose_name='Полученный балл', default=0, decimal_places=2, max_digits=6)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class ResultsTable(models.Model):
	user_result = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Экзаменуемый')
	tests = models.ForeignKey(Tests, on_delete=models.CASCADE, verbose_name='Тест')
	number_of_points = models.DecimalField(verbose_name='Полученный балл', default=0, decimal_places=2, max_digits=6, null=True)
	test_date = models.DateTimeField(auto_now=True, verbose_name='Дата прохождения теста')
	result = models.BooleanField(default=False, null=False)
	

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Results_answers_on_questions(models.Model):
	exam_user = models.ForeignKey(User, on_delete=models.CASCADE)
	tests = models.ForeignKey(Tests, on_delete=models.CASCADE)
	question = models.ForeignKey(Question, on_delete=models.CASCADE)
	answer = models.ForeignKey(SelectAnswer, on_delete=models.CASCADE, null=True)
	test_date = models.DateTimeField(auto_now=True)
	attempt_id = models.IntegerField(default=0)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Organization(models.Model):
	name = models.TextField(verbose_name='Организация')

	def __str__(self):
		return self.text


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class User_organization(models.Model):
	user_id = models.OneToOneField(User, on_delete=models.CASCADE)
	organization_id = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name='Организация')


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Users_passwords(models.Model):
	user_id = models.OneToOneField(User, on_delete=models.CASCADE)
	password = models.TextField(verbose_name='Пароль')


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Users_reg_id(models.Model):
	user_id = models.OneToOneField(User, on_delete=models.CASCADE)
	reg_id = models.TextField(verbose_name='Identificator')
