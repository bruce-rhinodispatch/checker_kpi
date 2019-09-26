# Generated by Django 2.2.4 on 2019-08-29 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checker_kpi', '0002_auto_20190828_1256'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='corporate_id',
            field=models.SmallIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='login_name',
            field=models.CharField(max_length=35),
        ),
        migrations.AlterField(
            model_name='company',
            name='login_pass',
            field=models.CharField(max_length=35),
        ),
        migrations.AlterField(
            model_name='company',
            name='name',
            field=models.CharField(max_length=35, unique=True),
        ),
        migrations.AlterField(
            model_name='sylectususers',
            name='name',
            field=models.CharField(max_length=35),
        ),
        migrations.AddConstraint(
            model_name='emails',
            constraint=models.UniqueConstraint(fields=('company', 'email'), name='uniq user'),
        ),
        migrations.AddConstraint(
            model_name='operationsusers',
            constraint=models.UniqueConstraint(fields=('company', 'nick_name'), name='uniq user'),
        ),
        migrations.AddConstraint(
            model_name='sylectususers',
            constraint=models.UniqueConstraint(fields=('company', 'name'), name='uniq user'),
        ),
    ]