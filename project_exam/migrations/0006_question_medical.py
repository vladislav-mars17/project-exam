# Generated by Django 4.1.7 on 2023-05-04 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project_exam', '0005_results_answers_on_questions'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='medical',
            field=models.BooleanField(default=False),
        ),
    ]
