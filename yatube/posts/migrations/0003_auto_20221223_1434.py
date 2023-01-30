# Generated by Django 2.2.9 on 2022-12-23 11:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20221219_1523'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='descrtiption',
            new_name='description',
        ),
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(unique=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='group', to='posts.Group'),
        ),
    ]
