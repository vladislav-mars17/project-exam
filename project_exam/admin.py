from django.contrib import admin
from .models import Question, SelectAnswer, AnswersOnQuestions, Tests, ResultsTable
from .forms import ChoiceInlineFormSet


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class TestsAdmin(admin.ModelAdmin):
	model = Tests
	list_display = ['text',]


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class ChoiceAnswerInline(admin.TabularInline):
	model = SelectAnswer
	can_delete =False
	max_num = SelectAnswer.number_of_answer_options
	min_num = SelectAnswer.number_of_answer_options
	formset = ChoiceInlineFormSet


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class QuestionAdmin(admin.ModelAdmin):
	model = Question
	inlines = (ChoiceAnswerInline, )
	list_display = ['text',]
	search_fields = ['text', 'questions__text']


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class AnswersOnQuestionsAdmin(admin.ModelAdmin):
	list_display = ['question', 'answer', 'correct', 'number_of_points']

	class Meta:
		model = AnswersOnQuestions


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class ResultsTableAdmin(admin.ModelAdmin):
	model = ResultsTable
	list_display = ['user_result', 'tests', 'number_of_points', 'test_date']
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
admin.site.register(AnswersOnQuestions)
admin.site.register(Question, QuestionAdmin)
admin.site.register(SelectAnswer)
admin.site.register(Tests, TestsAdmin)
admin.site.register(ResultsTable, ResultsTableAdmin)
