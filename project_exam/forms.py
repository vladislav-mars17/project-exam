from django import forms
from .models import  Question
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, get_user_model


User = get_user_model()


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class ChoiceInlineFormSet(forms.BaseInlineFormSet):
	def clean(self):
		super(ChoiceInlineFormSet, self).clean()

		correct_answer = 0
		for form in self.forms:
			if not form.is_valid():
				return

			if form.cleaned_data and form.cleaned_data.get('correct') is True:
				correct_answer += 1

		try:
			assert correct_answer == Question.number_of_answers_per_question
		except AssertionError:
			raise forms.ValidationError('Допускается только 1 правильный ответ')


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class UserLoginForm(forms.Form):
	username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
	password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}))

	def clean(self, *args, **kwargs):
		username = self.cleaned_data.get("username")
		password = self.cleaned_data.get("password")

		if username and password:
			user = authenticate(username=username, password=password)
			if not user:
				raise forms.ValidationError("Этот пользователь не существует")
			if not user.check_password(password):
				raise forms.ValidationError("Неверный пароль")
			if not user.is_active:
				raise forms.ValidationError("Этот пользователь не активен")

		return super(UserLoginForm, self).clean(*args, **kwargs)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class RegistrationForm(UserCreationForm):
	# email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control rounded-3'}))
	first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
	last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
	
	username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control rounded-3'}))
	password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}))
	password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}))

	class Meta:
		model = User 

		fields = [
			'first_name',
			'last_name',
			'username',
			'password1',
			'password2'
		]
		