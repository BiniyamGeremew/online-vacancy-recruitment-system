from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('department_head', '0003_alter_employeerequest_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='VPProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(blank=True, max_length=32)),
                ('office_location', models.CharField(blank=True, max_length=128)),
                ('bio', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='vpprofile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='VPAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('approved', 'Approved by VP'), ('rejected', 'Rejected by VP'), ('forwarded_to_hr', 'Forwarded to HR')], max_length=32)),
                ('comment', models.TextField(blank=True)),
                ('performed_at', models.DateTimeField()),
                ('performed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vp_actions', to='department_head.employeerequest')),
            ],
            options={
                'ordering': ['-performed_at'],
            },
        ),
    ]
