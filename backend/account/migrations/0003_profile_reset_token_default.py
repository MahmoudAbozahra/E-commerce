from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('account', '0002_rename_rest_password_expire_profile_reset_password_expire_and_more')]
    operations = [
        migrations.AlterField(
            model_name='profile',
            name='reset_password_token',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]
