# Generated by Django 4.1.2 on 2022-12-02 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0008_alter_buyer_city_alter_buyer_name_alter_buyer_phone_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='buyer',
            name='pic1',
            field=models.ImageField(blank=True, default=None, null=True, upload_to='images/'),
        ),
        migrations.AddField(
            model_name='seller',
            name='pic1',
            field=models.ImageField(blank=True, default=None, null=True, upload_to='images/'),
        ),
    ]
