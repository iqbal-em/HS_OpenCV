# Generated by Django 3.1.1 on 2020-10-19 08:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('streamapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PeopleCount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('waktu', models.DateTimeField()),
                ('kode_hs', models.IntegerField()),
            ],
            options={
                'db_table': 'people_count',
                'managed': False,
            },
        ),
    ]