from django.db import migrations, models


def forwards_update_draft(apps, schema_editor):
    EmployeeRequest = apps.get_model('department_head', 'EmployeeRequest')
    # Update any existing 'Draft' statuses to 'Submitted'
    EmployeeRequest.objects.filter(status='Draft').update(status='Submitted')


def reverse_noop(apps, schema_editor):
    # No reverse operation: cannot reliably restore previous draft status
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('department_head', '0002_alter_employeerequestitem_sex'),
    ]

    operations = [
        migrations.RunPython(forwards_update_draft, reverse_noop),
        migrations.AlterField(
            model_name='employeerequest',
            name='status',
            field=models.CharField(max_length=32, choices=[('Submitted', 'Submitted'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Forwarded to VP', 'Forwarded to VP')], default='Submitted'),
        ),
    ]
