import json
import smtplib
import ssl
import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.http import Http404, HttpResponseRedirect, JsonResponse, FileResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import RegistrationForm, UserLoginForm
from .models import Question, AnswersOnQuestions, ResultsTable, Tests, SelectAnswer, User_role, Available_tests_for_users, Role, Close_tests_for_users, Results_answers_on_questions
from .models import User_organization, Organization, Users_passwords, Users_reg_id
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Count
from django.utils import timezone
from uuid import uuid4
from pathlib import Path
from docxtpl import DocxTemplate
import os
from dotenv import load_dotenv


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
load_dotenv()
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# FOR STAFF
# ------------------------------------------------------------------------------------------------------------------------------
def open_tests(request):
	role = User_role.objects.get(user_id=request.user.id).role_id
	if role.id == 1:
		users_of_their_role = User_role.objects.filter(role_id=role).values_list('user_id', flat=True)

		available_tests = Available_tests_for_users.objects.all().select_related('unavailable_tests').select_related('user_id').\
			select_related('user_id__user_organization__organization_id').select_related('user_id__user_role__role_id').order_by('id')
		
		number_close_tests = Close_tests_for_users.objects.all().values('user_id', 'unavailable_tests').annotate(dcount=Count('unavailable_tests')).filter(dcount__gte=3)
	
		list_close_tests = []
		list_close_users = []
		for close_test in number_close_tests:
			results_table = ResultsTable.objects.filter(user_result=close_test['user_id'], tests=close_test['unavailable_tests'], result=True)
			if not results_table:
				list_close_tests.append(close_test['unavailable_tests'])
				list_close_users.append(close_test['user_id'])
			
		available_tests = available_tests.filter(unavailable_tests__in=list_close_tests, user_id__in=list_close_users)

		paginator = Paginator(available_tests, 15)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)
		
		context = {
			'available_tests': available_tests,
			'page_obj': page_obj,
			'role_id': role.id,
    		}
		return render(request, 'teacher/open_tests.html', context)
	else:
		return render(request, 'error.html')

# ------------------------------------------------------------------------------------------------------------------------------
def delete_unavailable_tests(request, id):
	try:
		available_tests = Available_tests_for_users.objects.get(id=id)
		available_tests.delete()
		return HttpResponseRedirect('/open_tests/')
	except ObjectDoesNotExist:
		return Http404

# ------------------------------------------------------------------------------------------------------------------------------
def upload_result(table_of_results, user_organization):

	results_list = []
	
	for index, result in enumerate(table_of_results):
		results_dict = dict()
		results_dict['id'] = index + 1
		results_dict['organization'] = result.user_result.user_organization.organization_id.name
		results_dict['name'] = f'{result.user_result.last_name} {result.user_result.first_name}'
		results_dict['test'] = result.tests.text
		results_dict['number_of_points'] = result.number_of_points
		results_dict['result'] = 'Зачтено' if result.result else 'Не сдано'
		results_dict['test_date'] = result.test_date.strftime('%d.%m.%Y')  # UTC timezone (+3 for Moscow)
		results_list.append(results_dict)
	
	context = {
		'today_date': datetime.datetime.now().strftime('%d.%m.%Y'), 
		'organization': user_organization.organization_id.name, 
		'table_of_results': results_list
	}
	
	file_uuid = uuid4()
	sample_path = Path(__file__).resolve().parent / 'static' / 'project_exam' / 'include' / 'sample.docx'	
	file_path = Path(__file__).resolve().parent / 'static' / 'project_exam' / 'include' / f'{file_uuid}.docx'
	
	doc = DocxTemplate(sample_path)
	doc.render(context)
	doc.save(file_path)
	
	return file_path


# ------------------------------------------------------------------------------------------------------------------------------
def results_table(request):
	role = User_role.objects.get(user_id=request.user.id).role_id
	if role.id == 1 or role.id == 3:

		user_organization = User_organization.objects.filter(user_id=request.user.id).select_related('organization_id')[0]
		user_organization_id = user_organization.organization_id.id

		all_users_current_organization = User_organization.objects.filter(organization_id=user_organization_id).values_list('user_id', flat=True)

		if role == Role.objects.get(id=1):
			table_of_results = ResultsTable.objects.all().select_related('tests').select_related('user_result').\
				select_related('user_result__user_organization__organization_id').select_related('user_result__user_role__role_id').order_by('-id')
		else:
			table_of_results = ResultsTable.objects.filter(user_result__in=all_users_current_organization).select_related('tests').select_related('user_result').\
				select_related('user_result__user_organization__organization_id').select_related('user_result__user_role__role_id').order_by('-id')
		
		name_placeholder = ''
		test_placeholder = ''
		result_placeholder = ''
	
		start_date_placeholder = 'Начиная с даты'
		end_date_placeholder = 'По дату'
		
		if request.method == 'POST':
			reset = request.POST.get('reset')
			if not reset:
				name_placeholder = request.POST.get('name')
				test_placeholder = request.POST.get('test')
				result_placeholder = request.POST.get('result')
				start_date = request.POST.get('start_date')
				end_date = request.POST.get('end_date')
				download = request.POST.get('download')
			
				if download:
					date_strp_format = '%d.%m.%Y'
				else:
					date_strp_format = '%Y-%m-%d'
			
				try:
					start_date_placeholder = datetime.datetime.strptime(start_date, date_strp_format).strftime('%d.%m.%Y')
					start_date_timezone = timezone.make_aware(datetime.datetime.strptime(start_date, date_strp_format))
				except:
					start_date_timezone = timezone.make_aware(datetime.datetime.strptime('2023-01-01', '%Y-%m-%d'))
			
				try:
					end_date_placeholder = datetime.datetime.strptime(end_date, date_strp_format).strftime('%d.%m.%Y')
					end_date_timezone = timezone.make_aware(datetime.datetime.strptime(f'{end_date} 23:59', f'{date_strp_format} %H:%M'))
				except:
					end_date_timezone = timezone.make_aware(datetime.datetime.now())
			
				table_of_results = table_of_results.filter(test_date__gte=start_date_timezone).filter(test_date__lte=end_date_timezone)

				if name_placeholder != '':
					table_of_results = table_of_results.filter(user_result__last_name__contains=name_placeholder) | table_of_results.filter(user_result__first_name__contains=name_placeholder)

				if test_placeholder != '':
					table_of_results = table_of_results.filter(tests__text__contains=test_placeholder)
			
				result_value = result_placeholder.lower().replace(' ', '')
				if result_value != '':
					if result_value in 'зачтено':
						table_of_results = table_of_results.filter(result=True)
					elif result_value in 'несдано':
						table_of_results = table_of_results.filter(result=False)
			
				if download:
					file_path = upload_result(table_of_results, user_organization)
					response = FileResponse(open(file_path, 'rb'), filename='Результаты.docx')
					return response
					
		paginator = Paginator(table_of_results, 15)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)
	
		context = {
			'table_of_results': table_of_results,
			'page_obj': page_obj,
			'role_id': role.id,
			'start_date_placeholder': start_date_placeholder,
			'end_date_placeholder': end_date_placeholder,
			'name_placeholder': name_placeholder,
			'test_placeholder': test_placeholder,
			'result_placeholder': result_placeholder,
    		}
		return render(request, 'teacher/results_table.html', context)
	else:
		return render(request, 'error.html')

# ------------------------------------------------------------------------------------------------------------------------------
def test_result_analysis(request, id):
	role = User_role.objects.get(user_id=request.user.id).role_id
	if role.id == 1 or role.id == 3:
		test_date = ResultsTable.objects.get(pk=id).test_date
		exam_user = ResultsTable.objects.get(pk=id).user_result
		test = ResultsTable.objects.get(pk=id).tests
		number_of_points = ResultsTable.objects.get(pk=id).number_of_points
		result = 'зачтено' if ResultsTable.objects.get(pk=id).result else 'не сдано'

		user_attempt = Results_answers_on_questions.objects.filter(exam_user=exam_user).filter(tests=test).filter(test_date__year=test_date.year, test_date__month=test_date.month, 
			test_date__day=test_date.day, test_date__hour=test_date.hour+3, 
			test_date__minute=test_date.minute,).order_by('-id')[0].attempt_id
		user_results = Results_answers_on_questions.objects.filter(exam_user=exam_user).filter(tests=test).filter(attempt_id=user_attempt).\
							values('question').annotate(dcount=Count('question'))

		all_questions = Question.objects.filter(pk__in=user_results.values_list('question', flat=True))
		all_answers = SelectAnswer.objects.filter(question__in=user_results.values_list('question', flat=True))
		user_answers = user_results.values_list('answer', flat=True)

		user_result_point_dict = {}
		all_correct_answers = {item.pop('question'): item for item in all_answers.filter(correct=True).values('question').annotate(dcount=Count('question'))}
		all_correct_user_results = {item.pop('question'): item for item in user_results.filter(answer__correct=True)}
		all_incorrect_user_results = {item.pop('question'): item for item in user_results.filter(answer__correct=False)}
	
		for question in all_questions:
			if question.id in all_incorrect_user_results.keys():
				user_result_point_dict[question.id] = 0
			elif question.id in all_correct_user_results.keys():
				if all_correct_answers[question.id].get('dcount') == all_correct_user_results[question.id].get('dcount'):
					user_result_point_dict[question.id] = 1
				else:
					user_result_point_dict[question.id] = 0
			else:
				user_result_point_dict[question.id] = 0
		
		context = {
			'all_questions': all_questions,
			'user_answers': user_answers,
			'all_answers': all_answers,
			'test_date': test_date,
			'exam_user': exam_user,
			'test': test,
			'user_attempt': user_attempt,
			'number_of_points': number_of_points,
			'result': result,
			'user_result_point_dict': user_result_point_dict,
			'role_id': role.id,
		}

		return render(request, 'teacher/test_result_analysis.html', context)
	else:
		return render(request, 'error.html')

# ------------------------------------------------------------------------------------------------------------------------------
def get_users(request):
	role_id_admin = User_role.objects.get(user_id=request.user.id).role_id.id
	if role_id_admin == 1 or role_id_admin == 3:

		user_organization = User_organization.objects.filter(user_id=request.user.id).select_related('organization_id')[0]
		user_organization_id = user_organization.organization_id.id
	
		if role_id_admin == 1:
			table_of_users = User_organization.objects.all().select_related('user_id').select_related('organization_id').select_related('user_id__user_role__role_id').order_by('-id')
		else:
			table_of_users = User_organization.objects.filter(organization_id=user_organization_id).select_related('user_id').select_related('organization_id').select_related('user_id__user_role__role_id').order_by('-id')
		
		last_login_placeholder = 'Последнее посещение'
		date_joined_placeholder = 'Дата регистрации'

		if request.method == 'POST':
			reset = request.POST.get('reset')
			if not reset:
				last_login = request.POST.get('last_login')
				date_joined = request.POST.get('date_joined')

				if last_login != '' and date_joined == '':
					last_login_placeholder = datetime.datetime.strptime(last_login, '%Y-%m-%d').strftime('%d.%m.%Y')
					last_login_timezone_start = timezone.make_aware(datetime.datetime.strptime(f'{last_login} 00:00', '%Y-%m-%d %H:%M'))
					last_login_timezone_end = timezone.make_aware(datetime.datetime.strptime(f'{last_login} 23:59', '%Y-%m-%d %H:%M'))
					table_of_users = table_of_users.filter(user_id__last_login__gte=last_login_timezone_start).filter(user_id__last_login__lte=last_login_timezone_end)
		
				elif last_login == '' and date_joined != '':
					date_joined_placeholder = datetime.datetime.strptime(date_joined, '%Y-%m-%d').strftime('%d.%m.%Y')
					date_joined_timezone_start = timezone.make_aware(datetime.datetime.strptime(f'{date_joined} 00:00', '%Y-%m-%d %H:%M'))
					date_joined_timezone_end = timezone.make_aware(datetime.datetime.strptime(f'{date_joined} 23:59', '%Y-%m-%d %H:%M'))
					table_of_users = table_of_users.filter(user_id__date_joined__gte=date_joined_timezone_start).filter(user_id__date_joined__lte=date_joined_timezone_end)
		
				elif last_login != '' and date_joined != '':
					last_login_placeholder = datetime.datetime.strptime(last_login, '%Y-%m-%d').strftime('%d.%m.%Y')
					date_joined_placeholder = datetime.datetime.strptime(date_joined, '%Y-%m-%d').strftime('%d.%m.%Y')

					last_login_timezone_start = timezone.make_aware(datetime.datetime.strptime(f'{last_login} 00:00', '%Y-%m-%d %H:%M'))
					last_login_timezone_end = timezone.make_aware(datetime.datetime.strptime(f'{last_login} 23:59', '%Y-%m-%d %H:%M'))

					date_joined_timezone_start = timezone.make_aware(datetime.datetime.strptime(f'{date_joined} 00:00', '%Y-%m-%d %H:%M'))
					date_joined_timezone_end = timezone.make_aware(datetime.datetime.strptime(f'{date_joined} 23:59', '%Y-%m-%d %H:%M'))

					table_of_users = table_of_users.filter(user_id__last_login__gte=last_login_timezone_start).filter(user_id__last_login__lte=last_login_timezone_end).\
							filter(user_id__date_joined__gte=date_joined_timezone_start).filter(user_id__date_joined__lte=date_joined_timezone_end)
		
		paginator = Paginator(table_of_users, 15)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)

		context = {
			'organization_name': user_organization,
			'table_of_users': table_of_users,
			'page_obj': page_obj,
			'role_id': role_id_admin,
			'last_login_placeholder': last_login_placeholder,
			'date_joined_placeholder': date_joined_placeholder,
		}

		return render(request, 'teacher/get_users.html', context)
	else:
		return render(request, 'error.html')

# ------------------------------------------------------------------------------------------------------------------------------
def get_roles(request):
	role_id_admin = User_role.objects.get(user_id=request.user.id).role_id.id
	if role_id_admin == 1:
		roles = Role.objects.all()
	
		if request.method == 'POST':
			text = request.POST.get('new_role')
		
			role = Role(text=text)
			role.save()
		
			return HttpResponseRedirect('/get_roles/')
		else:
			context = {
				'roles': roles,
				'role_id': role_id_admin,
	   		}
		
		return render(request, 'teacher/get_roles.html', context)
	else:
		return render(request, 'error.html')

# ------------------------------------------------------------------------------------------------------------------------------
def get_roles2(request):
	role_id_admin = User_role.objects.get(user_id=request.user.id).role_id.id
	if role_id_admin == 1:
		roles = Role.objects.exclude(id=1).exclude(id=3)
		
		context = {
			'roles': roles,
			'role_id': role_id_admin,
		}
		return render(request, 'teacher/get_roles2.html', context)
	else:
		return render(request, 'error.html')
	
# ------------------------------------------------------------------------------------------------------------------------------
def get_tests(request, id):
	role_id_admin = User_role.objects.get(user_id=request.user.id).role_id.id
	if role_id_admin == 1:
		tests_name = Tests.objects.filter(role=id)
		users_of_test_index = User_role.objects.filter(role_id=id).values_list('user_id', flat=True)
		users_of_test = User.objects.filter(pk__in=users_of_test_index)
	
		paginator = Paginator(users_of_test, 15)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)
	
		if request.method == 'POST':
			text = request.POST.get('new_test')
			role = Role.objects.get(id=id)
		
			test = Tests(text=text, role=role)
			test.save()
		
			return HttpResponseRedirect('/get_roles/get_tests/' + str(id) + '/')
		else:
			context = {
				'tests_name': tests_name,
				'users_of_test': users_of_test,
				'id': id,
				'page_obj': page_obj,
				'role_id': role_id_admin,
	    		}
	
		return render(request, 'teacher/get_tests.html', context)
	else:
		return render(request, 'error.html')

# ------------------------------------------------------------------------------------------------------------------------------
def get_tests2(request, id):
	role_id_admin = User_role.objects.get(user_id=request.user.id).role_id.id
	if role_id_admin == 1:
		tests_name = Tests.objects.filter(role=id)
		role = Role.objects.get(id=id)

		context = {
			'tests_name': tests_name,
			'id': id,
			'role': role.text,
			'role_id': role_id_admin,
		}

		return render(request, 'teacher/get_tests2.html', context)
	else:
		return render(request, 'error.html')

# ------------------------------------------------------------------------------------------------------------------------------
def get_questions_answers(request, id):
	role_id_admin = User_role.objects.get(user_id=request.user.id).role_id.id
	if role_id_admin == 1:
		tests_name = Tests.objects.get(id=id)
	
		if request.method == 'POST':	
			text_question = request.POST.get('question')
			max_score = request.POST.get('max_score')
		
			question = Question(text=text_question, max_score=max_score, tests=tests_name)
			question.save()

			for i in range(1, 100):
				text_answer = request.POST.get('answer' + str(i))
				if text_answer is None:
					break
			
				correct_answer = request.POST.get('correct_answer' + str(i))
				if correct_answer is None:
					correct = False
				else:
					correct = True
			
				answer = SelectAnswer(text=text_answer, correct=correct, question=question)
				answer.save()

			return HttpResponseRedirect('/get_questions_answers/' + str(tests_name.id))
	
		else:
			try:
				questions_name = Question.objects.filter(tests_id=id)
				answers_name = SelectAnswer.objects.all()
			
				paginator = Paginator(questions_name, 15)
				page_number = request.GET.get('page')
				page_obj = paginator.get_page(page_number)
			
				context = {
					'tests_name': tests_name,
		        	'questions_name': questions_name,
		        	'answers_name': answers_name,
					'page_obj': page_obj,
					'role_id': role_id_admin,
		    		}
			
				return render(request, 'teacher/get_questions_answers.html', context)
		
			except ObjectDoesNotExist:
				return Http404
	else:
		return render(request, 'error.html')
	
# ------------------------------------------------------------------------------------------------------------------------------
def get_questions_answers2(request, id):
	role_id_admin = User_role.objects.get(user_id=request.user.id).role_id.id
	if role_id_admin == 1:
		tests_name = Tests.objects.get(id=id)
		if request.method == 'POST':
			return HttpResponseRedirect('/get_questions_answers2/' + str(tests_name.id))
		else:
			try:
				questions_name = Question.objects.filter(tests_id=id)
				answers_name = SelectAnswer.objects.all()

				paginator = Paginator(questions_name, 15)
				page_number = request.GET.get('page')
				page_obj = paginator.get_page(page_number)

				context = {
					'tests_name': tests_name,
					'questions_name': questions_name,
					'answers_name': answers_name,
					'page_obj': page_obj,
					'role_id': role_id_admin,
				}

				return render(request, 'teacher/get_questions_answers2.html', context)
		
			except ObjectDoesNotExist:
				return Http404
	else:
		return render(request, 'error.html')

# ------------------------------------------------------------------------------------------------------------------------------
def edit_questions(request, id):
	try:
		question = Question.objects.get(id=id)
		tests_name = Question.objects.filter(tests_id=question.tests_id).select_related('tests')[:1]
		answers = SelectAnswer.objects.filter(question_id=id).order_by('id')
			
		if request.method == 'POST':
			question.text = request.POST.get('text')
			question.max_score = request.POST.get('max_score')
			question.save(update_fields=['max_score', 'text'])
			
			answer_count = 1
			for answer in answers:
				answer.text = request.POST.get('answer_text'+str(answer_count))
				correct_answer = request.POST.get('correct_answer'+str(answer_count))
				if correct_answer is None:
					correct = False
				else:
					correct = True
				answer.correct = correct
				answer.save(update_fields=['correct', 'text'])
				answer_count += 1
					
			return HttpResponseRedirect('/get_questions_answers/'+str(tests_name[0].tests.id))
		else:
			context = {
				'question': question,
		        'tests_name': tests_name,
                'answers': answers,
                'count_answers': answers.count(),
            }
				
			return render(request, 'teacher/edit_questions.html', context)
			
	except ObjectDoesNotExist:
		return Http404

# ------------------------------------------------------------------------------------------------------------------------------
def delete_question_answers(request, id):
	try:
		answers = SelectAnswer.objects.filter(question=id)
		answers.delete()
		question = Question.objects.get(id=id)
		test_id = question.tests_id
		question.delete()
		return HttpResponseRedirect('/get_questions_answers/' + str(test_id) + '/')
	except ObjectDoesNotExist:
		return Http404


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
def loginView(request):
	title = 'login'
	form = UserLoginForm(request.POST or None)
	valid = True
	if request.method == 'POST':
		if form.is_valid():
			username = form.cleaned_data.get("username")
			password = form.cleaned_data.get("password")
			user = authenticate(username=username, password=password)
			login(request, user)
			if user.is_staff:
				return redirect('results_table')
			else:
				return redirect('HomeUser')
		else:
			valid = False

	context = {
		'form': form,
		'title': title,
		'valid': valid,
	}

	return render(request, 'exam_user/login.html', context)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
def registration_organization(request):
	added_organization = User_organization.objects.all().values('organization_id').distinct()
	organizations = Organization.objects.all().exclude(pk__in=added_organization)

	error_text = None
	error_type = None
	valid = True
	organization_valid = True
	result_text = ''
	
	if request.method == 'POST':
		form = RegistrationForm(request.POST)
		if form.is_valid():
			organization_id = request.POST.get('organization')

			if organization_id == '':
				organization_valid = False
				result_text = 'Пользователь не добавлен'
			else:
				form.save()
				form.clean()
				valid = True
				organization_valid = True
				result_text = 'Пользователь успешно добавлен'

				user = User.objects.all().order_by('-id')[0]
				
				role_id = 3
				role = Role.objects.get(id=role_id)
				User_role(user_id=user, role_id=role).save()

				organization = Organization.objects.get(id=organization_id)
				User_organization(user_id=user, organization_id=organization).save()

				login_password = request.POST.get('password1')
				Users_passwords(user_id=user, password=login_password).save()

				user.is_staff = True
				user.save(update_fields=['is_staff'])
				
				last_name = request.POST.get('last_name')
				first_name = request.POST.get('first_name')
				receiver = request.POST.get('username')
				
				admin_user_id = 1
				try:
					send_smtp(receiver=receiver, last_name=last_name, first_name=first_name, login_username=receiver, login_password=login_password, admin_user_id=admin_user_id)
				except Exception as e:
					result_text = 'Пользователь успешно добавлен, письмо отправлено на почту представителя организации'
					log_path = str(Path(Path.cwd(), 'logs', 'log_mail.txt'))
					log_text = f"\n{datetime.datetime.now().strftime('%H:%M:%S %d.%m.%Y')}  Failed send msg to {receiver}. Exception: {e}"
					txt = open(log_path, "a")
					txt.write(log_text)
					txt.close()

				return redirect('/')
		else:
			valid = False
			result_text = 'Пользователь не добавлен'
			try:
				error_text = str(form.errors['username']).split('>')[2].split('<')[0]
				error_type = 'username'
			except:
				pass
			try:
				error_text = str(form.errors['password2']).split('>')[2].split('<')[0]
				error_type = 'password'
			except:
				pass
	else:
		form = RegistrationForm()

	context = {
		'form': form,
		'error_text': error_text,
		'error_type': error_type,
		'valid': valid,
		'organization_valid': organization_valid,
		'result_text': result_text,
		'organizations': organizations,
	}

	return render(request, 'teacher/registration_org.html', context)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
def registration(request):
	role_id_admin = User_role.objects.get(user_id=request.user.id).role_id.id
	organization_id_admin = User_organization.objects.get(user_id=request.user.id).organization_id.id

	if role_id_admin == 1:
		roles = Role.objects.all()
		organizations = Organization.objects.all()
		role_default = False
		organization_default = False
	else:
		saver_role_id = 2
		roles = Role.objects.filter(id=saver_role_id)
		organizations = Organization.objects.filter(id=organization_id_admin)
		role_default = roles[0]
		organization_default = organizations[0]

	title = 'Создать учетную запись'
	error_text = None
	error_type = None
	valid = True
	role_valid = True
	organization_valid = True
	reg_id_valid = True
	result_text = ''
	
	if request.method == 'POST':
		form = RegistrationForm(request.POST)
		if form.is_valid():
			role_id = request.POST.get('role')
			organization_id = request.POST.get('organization')
			re_cert = request.POST.get('re_cert')
			reg_id = request.POST.get('reg_id')

			if re_cert is not None and reg_id == '':
				reg_id_valid = False
			
			if role_id == 'Выберите группу' or organization_id == 'Выберите организацию' or not reg_id_valid:
				role_valid = False if role_id == 'Выберите группу' else True
				organization_valid = False if organization_id == 'Выберите организацию' else True
				result_text = 'Пользователь не добавлен'
				valid = False
			else:
				form.save()
				form.clean()
				valid = True
				role_valid = True
				organization_valid = True
				result_text = 'Пользователь успешно добавлен'
				
				user = User.objects.all().order_by('-id')[0]
				
				role = Role.objects.get(id=role_id)
				User_role(user_id=user, role_id=role).save()

				organization = Organization.objects.get(id=organization_id)
				User_organization(user_id=user, organization_id=organization).save()

				if reg_id is not None:
					Users_reg_id(user_id=user, reg_id=reg_id).save()

				login_password = request.POST.get('password1')
				Users_passwords(user_id=user, password=login_password).save()
				
				if role_id == '1' or role_id == '3':
					user.is_staff = True
					user.save(update_fields=['is_staff'])
			
				last_name = request.POST.get('last_name')
				first_name = request.POST.get('first_name')
				receiver = request.POST.get('username')
				login_password = request.POST.get('password1')
				admin_user_id = request.user.id
				try:
					send_smtp(receiver=receiver, last_name=last_name, first_name=first_name, login_username=receiver, login_password=login_password, admin_user_id=admin_user_id)
				except Exception as e:
					send_smtp(receiver=User.objects.get(id=admin_user_id).username, last_name=last_name, first_name=first_name, login_username=receiver, login_password=login_password, admin_user_id=admin_user_id)
					result_text = 'Пользователь успешно добавлен, письмо отправлено на почту представителя организации'
					user_name = User.objects.get(id = admin_user_id).username
					log_path = str(Path(Path.cwd(), 'logs', 'log_mail.txt'))
					log_text = f"\n{datetime.datetime.now().strftime('%H:%M:%S %d.%m.%Y')}  Failed send msg from {user_name} to {receiver}. Exception: {e}"
					txt = open(log_path, "a")
					txt.write(log_text)
					txt.close()
						
				#return redirect('registration')
		else:
			valid = False
			result_text = 'Пользователь не добавлен'
			try:
				error_text = str(form.errors['username']).split('>')[2].split('<')[0]
				error_type = 'username'
			except:
				pass
			try:
				error_text = str(form.errors['password2']).split('>')[2].split('<')[0]
				error_type = 'password'
			except:
				pass
	else:
		form = RegistrationForm()

	context = {
		'form': form,
		'title': title,
		'roles': roles,
		'error_text': error_text,
		'error_type': error_type,
		'valid': valid,
		'role_valid': role_valid,
		'reg_id_valid': reg_id_valid,
		'result_text': result_text,
		'organization_valid': organization_valid,
		'organizations': organizations,
		'role_default': role_default,
		'organization_default': organization_default,
		'role_id': role_id_admin,
	}

	return render(request, 'teacher/registration.html', context)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
def choice_role(request):
	roles = Role.objects.all()
	users = User.objects.all().order_by('-id')[:1]
	user = None
	for user_iter in users:
		user = user_iter
	
	if request.method == 'POST':
		role_id = request.POST.get('role')
		role = Role.objects.get(id=role_id)
		
		user_role = User_role(user_id=user, role_id=role)
		user_role.save()
		
		return redirect('/registration/')
	
	context = {
		'roles': roles,
		'user': user,
	}
	
	return render(request, 'teacher/choice_role.html', context)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
def send_smtp(receiver, last_name, first_name, login_username, login_password, admin_user_id):
	server = os.getenv('server')
	port = os.getenv('port')
	username = os.getenv('username')
	password = os.getenv('password')
	sender = os.getenv('sender')
	
	msg = MIMEMultipart()
	msg['From'] = sender
	msg['To'] = receiver
	msg['Subject'] = 'Регистрация на портале'
	
	text_of_msg = 'Добрый день, ' + last_name + ' ' + first_name + '! \n\nВы были зарегистрированы на портале Экзамен \n\nУчетные данные для доступа в личный кабинет: \n   Логин: ' + login_username + '\n   Пароль: ' + login_password + '\n\n\nЭто автоматическое сообщение, пожалуйста, не нужно отвечать на него.'
	
	msg.attach(MIMEText(text_of_msg, 'plain'))
	
	session = smtplib.SMTP(server, port)
	sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
	sslcontext.set_ciphers("AES256-SHA")
	session.starttls(context = sslcontext)
	
	session.login(username, password)
	session.send_message(msg)
	session.quit()
	
	user_name = User.objects.get(id = admin_user_id).username
	
	log_path = str(Path(Path.cwd(), 'logs', 'log_mail.txt'))
	log_text = f"\n{datetime.datetime.now().strftime('%H:%M:%S %d.%m.%Y')}  Username: {user_name}  Registered username: {login_username}"
	txt = open(log_path, "a")
	txt.write(log_text)
	txt.close()


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
def logoutView(request):
	logout(request)
	return redirect('/')


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
def start(request):
	return render(request, 'start.html')


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
def HomeUser(request):
	number_close_tests = Close_tests_for_users.objects.filter(user_id=request.user.id).values('user_id', 'unavailable_tests').annotate(dcount=Count('unavailable_tests')).order_by()
	list_close_tests = []
	for close_test in number_close_tests:
		if close_test['dcount'] >= 3:
			list_close_tests.append(close_test['unavailable_tests'])

	done_test = ResultsTable.objects.filter(user_result=request.user.id).filter(result=True).values_list('tests')
	
	date_timezone = timezone.now() - timezone.timedelta(hours=24)
	Available_tests_for_users.objects.filter(user_id=request.user.id).filter(date__lte=date_timezone).exclude(unavailable_tests__in=list_close_tests).exclude(unavailable_tests__in=done_test).delete()

	user_role = User_role.objects.get(user_id=request.user)
	available_tests = Available_tests_for_users.objects.filter(user_id=request.user.id).values_list('unavailable_tests_id', flat=True)
	tests_name = Tests.objects.filter(role=user_role.role_id).exclude(pk__in=available_tests)
	unavailable_tests_name = Tests.objects.filter(role=user_role.role_id).filter(pk__in=available_tests)
	exsist_tests = tests_name.exists()
	exsist_unavailable_tests = unavailable_tests_name.exists()
	
	table_of_results = ResultsTable.objects.filter(user_result=request.user).select_related('tests').select_related('user_result').order_by('-id')
	
	paginator = Paginator(table_of_results, 15)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	
	context = {
		'tests_name': tests_name,
		'unavailable_tests_name': unavailable_tests_name,
		'exsist_tests': exsist_tests,
		'exsist_unavailable_tests': exsist_unavailable_tests,
		'table_of_results': table_of_results,
		'page_obj': page_obj,
    }

	return render(request, 'exam_user/home2.html', context)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
def user_history(request):

	table_of_results = ResultsTable.objects.filter(user_result=request.user).select_related('tests').select_related('user_result').order_by('-id')
	
	paginator = Paginator(table_of_results, 15)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	
	context = {
		'table_of_results': table_of_results,
		'page_obj': page_obj,
    }

	return render(request, 'exam_user/user_history.html', context)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
def table(request):
	result_users = request.user
	
	try:
		test_id = AnswersOnQuestions.objects.filter(examUser=request.user.id).order_by('-id')[0].tests_id
		index_tests = Tests.objects.get(pk=test_id)
	except:
		return redirect('/HomeUser/')
	
	result_exam_users = AnswersOnQuestions.objects.filter(examUser=request.user.id).filter(tests=test_id).aggregate(Sum('number_of_points'))
	
	if result_exam_users['number_of_points__sum'] is None:
		result_exam_users['number_of_points__sum'] = 0
	
	if result_exam_users['number_of_points__sum'] >= index_tests.done_score:
		result = True
	else:
		result = False
	
	result_table = ResultsTable(user_result=request.user, tests=index_tests, number_of_points=result_exam_users['number_of_points__sum'], result=result)
	result_table.save()
	
	AnswersOnQuestions.objects.filter(examUser=request.user.id).filter(tests=test_id).delete()
	
	user_role = User_role.objects.get(user_id=request.user)
	available_tests = Available_tests_for_users(user_id=request.user, unavailable_tests=index_tests)
	available_tests.save()
	
	close_tests = Close_tests_for_users(user_id=request.user, unavailable_tests=index_tests)
	close_tests.save()
	
	counter = result_exam_users['number_of_points__sum']
	
	last_attempt_id = int(list(Results_answers_on_questions.objects.filter(exam_user=request.user.id).filter(tests=test_id).order_by('-id')[:1].values())[0]['attempt_id'])
	results_answers_on_questions = Results_answers_on_questions.objects.filter(exam_user=request.user.id).filter(tests=test_id).filter(attempt_id=last_attempt_id).order_by('id')
	question_list = []
	answer_list = []
	for i in range(len(results_answers_on_questions)):
		question_list.append(results_answers_on_questions[i].question.id)
		if results_answers_on_questions[i].answer is not None:
			answer_list.append(results_answers_on_questions[i].answer.id)
	questions_of_attempt = Question.objects.filter(pk__in=question_list)
	answers_of_attempt = SelectAnswer.objects.filter(question__in=question_list)

	context = {
		'user_exam': request.user,
		'user_score': counter,
		'done_score': index_tests.done_score,
		'number_of_questions': index_tests.number_of_questions,
		'answer_list': answer_list,
		'questions_of_attempt': questions_of_attempt,
		'answers_of_attempt': answers_of_attempt,
	}

	return render(request, 'play/table.html', context)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------

def test_ajax(request, id):
	available_tests = Available_tests_for_users.objects.filter(user_id=request.user.id, unavailable_tests=id)
	
	if not available_tests:
		limit = Tests.objects.get(id=id).number_of_questions
		limit = int(limit)
		question_limit = limit - 1
	
		timer = Tests.objects.get(id=id).time
		timer = int(timer)
	
		done_score = Tests.objects.get(id=id).done_score
		done_score = int(done_score)
	
		is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
		number_of_questions = AnswersOnQuestions.objects.filter(examUser=request.user.id).filter(tests=id)
		count = number_of_questions.count()
		questions_id_list = []
	
		if is_ajax:
			if request.method == 'GET':
			
				for question in number_of_questions:
					questions_id_list.append(question.question_id)
				
				list_question = list()
				list_answers = list()
			
				if count <= question_limit:
					if count % 5 == 0:
						question = Question.objects.filter(tests=id).filter(medical=True).exclude(pk__in=questions_id_list).order_by('?')[:1]
					else:
						question = Question.objects.filter(tests=id).filter(medical=False).exclude(pk__in=questions_id_list).order_by('?')[:1]

					list_question = list(question.values())
					index_question = Question.objects.get(pk=list_question[0]['id'])
				
					answers = SelectAnswer.objects.filter(question=list_question[0]['id']).order_by('?')
					list_answers = list(answers.values())

					exam_users = request.user
					index_tests = Tests.objects.get(pk=id)
					answers_on_questions = AnswersOnQuestions(correct=False, number_of_points=0, answer=None, examUser=exam_users, 
					      	question=index_question, tests=index_tests)
					answers_on_questions.save()
			    
				context = {
					'list_question': list_question,
					'list_answers': list_answers,
            			}
				return JsonResponse(context)
		
			if request.method == 'POST':
				data = json.load(request)
				todo = data.get('payload')
			
				question_id = None
				number_of_points = None
				if todo['question_id'] != []:
					question_id = todo['question_id'][0]
					number_of_points = Question.objects.get(id=question_id).max_score
			
				answer_id = None
				correct = None
				if todo['values'] != []:
					try:
						number_correct_answer = SelectAnswer.objects.filter(question=question_id).filter(correct=True).count()
						list_answer_id = []
						list_correct_answer = []
						for i in range(len(todo['checked'])):
							if todo['checked'][i] == True:
								answer_id = todo['values'][i]
								list_answer_id.append(answer_id)
								correct = SelectAnswer.objects.get(id=answer_id).correct
								if correct:
									list_correct_answer.append(correct)
								
						if number_correct_answer == len(list_answer_id):
							if len(list_correct_answer) == len(list_answer_id):
								number_of_points = 1
							else:
								number_of_points = 0
						else:
							number_of_points = 0					
					except ValueError:
						answer_id = None
						correct = False
						number_of_points = 0
					
				if question_id is not None and count <= question_limit+1:
					answers_on_questions = AnswersOnQuestions.objects.filter(examUser=request.user.id).get(question=question_id)
				
					if answer_id is None:
						index_answer = None
					else:
						index_answer = SelectAnswer.objects.get(pk=answer_id)
				
					answers_on_questions.number_of_points = number_of_points
					answers_on_questions.answer_id = index_answer
					answers_on_questions.save(update_fields=['number_of_points', 'answer_id'])
				
					if count == 1:
						old_results_answers_on_questions = Results_answers_on_questions.objects.filter(exam_user=request.user.id).filter(tests=id).order_by('-id')[:1].values()
						if len(old_results_answers_on_questions) == 0:
							attempt_id = 1
						else:
							attempt_id = int(list(old_results_answers_on_questions)[0]['attempt_id']) + 1
					else:
						old_results_answers_on_questions = Results_answers_on_questions.objects.filter(exam_user=request.user.id).filter(tests=id).order_by('-id')[:1].values()
						attempt_id = int(list(old_results_answers_on_questions)[0]['attempt_id'])

					for i in range(len(list_answer_id)):
						res_question = Question.objects.get(id=question_id)
						res_index_answer = SelectAnswer.objects.get(pk=list_answer_id[i])
						results_answers_on_questions = Results_answers_on_questions(exam_user=request.user, tests=res_question.tests, question=res_question, 
								 	answer=res_index_answer, attempt_id=attempt_id)
						results_answers_on_questions.save()
				
					if len(list_answer_id) == 0:
						res_question = Question.objects.get(id=question_id)
						results_answers_on_questions = Results_answers_on_questions(exam_user=request.user, tests=res_question.tests, question=res_question, 
								 	answer=None, attempt_id=attempt_id)
						results_answers_on_questions.save()
				
				return JsonResponse({'status': 'Todo added!'})
			return JsonResponse({'status': 'Invalid request'}, status=400)
		else:
			context = {
				'id': id,
				'count': count,
				'limit': limit,
				'timer': timer,
				'done_score': done_score,
            		}
			return render(request, 'play/test_new.html', context)
	else:
		return render(request, 'unavailable_test.html')

