# Generated by Django 2.2.9 on 2021-03-01 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=70)),
                ('slug', models.SlugField(max_length=70, unique=True)),
                ('description', models.TextField(max_length=150)),
            ],
        ),
        migrations.AddField(
            model_name='post',
            name='group',
            field=models.CharField(blank=True, max_length=70, null=True),
        ),
    ]
