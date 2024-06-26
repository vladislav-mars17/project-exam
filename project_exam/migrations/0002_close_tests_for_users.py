# Generated by Django 4.1.7 on 2023-04-20 09:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project_exam', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Close_tests_for_users',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unavailable_tests', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='project_exam.tests', verbose_name='Закрытый тест')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project_exam.user_role')),
            ],
        ),
    ]
