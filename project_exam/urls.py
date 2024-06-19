from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from .views import (
			start, 
			registration,
			choice_role,
			loginView, 
			logoutView,
			HomeUser, 
			table,
            results_table,
            open_tests,
            delete_unavailable_tests,
            get_roles,
	    	get_roles2,
            get_tests,
	    	get_tests2,
            get_questions_answers,
	    	get_questions_answers2,
            delete_question_answers,
            edit_questions, 
            test_ajax,
	    	get_users,
	    	registration_organization,
	    	test_result_analysis,
            user_history,)

urlpatterns = [
	
	path('start', start, name='start'),
	path('HomeUser/', HomeUser, name='HomeUser'),
	path('user_history/', user_history, name='user_history'),

	path('', loginView, name='login'),
	path('logout_view/', logoutView, name='logout_view'),
	path('registration/', registration, name='registration'),
	path('choice_role/', choice_role, name='choice_role'),

	path('table/', table, name='table'),

	path('results_table/', results_table, name='results_table'),
	path('open_tests/', open_tests, name='open_tests'),
	path('open_tests/delete_unavailable_tests/<int:id>/', delete_unavailable_tests, name='delete_unavailable_tests'),

	path('get_roles/', get_roles, name='get_roles'),
	path('get_roles2/', get_roles2, name='get_roles2'),
	path('get_roles/get_tests/<int:id>/', get_tests, name='get_tests'),
	path('get_roles2/get_tests2/<int:id>/', get_tests2, name='get_tests2'),

	path('get_questions_answers/<int:id>/', get_questions_answers, name='get_questions_answers'),
	path('get_questions_answers2/<int:id>/', get_questions_answers2, name='get_questions_answers2'),
	path('delete_question_answers/<int:id>/', delete_question_answers, name='delete_question_answers'),
	path('edit_questions/<int:id>/', edit_questions, name='edit_questions'),

	path('get_users/', get_users, name="get_users"),

    path('HomeUser/test/<int:id>/', test_ajax, name="test"),

	path('registration_organization/', registration_organization, name="registration_organization"),
	
	path('test_result_analysis/<int:id>/', test_result_analysis, name="test_result_analysis"),


]

urlpatterns += staticfiles_urlpatterns()
