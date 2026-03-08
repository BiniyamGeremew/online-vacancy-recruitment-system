from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date_submitted', models.DateTimeField(auto_now_add=True)),
                ('subject', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('closing_note', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Draft', max_length=16)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_requests_created', to=settings.AUTH_USER_MODEL)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_requests', to='organization.department')),
            ],
            options={
                'ordering': ['-date_submitted'],
                'verbose_name': 'Employee Request',
                'verbose_name_plural': 'Employee Requests',
            },
        ),
        migrations.CreateModel(
            name='EmployeeRequestItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('no', models.IntegerField(blank=True, null=True)),
                ('academic_qualification', models.CharField(max_length=255)),
                ('academic_rank', models.CharField(max_length=255)),
                ('area_of_specialization', models.CharField(max_length=255)),
                ('sex', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('A', 'Any')], default='A', max_length=1)),
                ('experience_years', models.IntegerField()),
                ('cgpa_requirement', models.DecimalField(max_digits=4, decimal_places=2)),
                ('number_of_employees', models.IntegerField()),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='department_head.employeerequest')),
            ],
            options={
                'ordering': ['request', 'no'],
                'verbose_name': 'Employee Request Item',
                'verbose_name_plural': 'Employee Request Items',
            },
        ),
    ]
