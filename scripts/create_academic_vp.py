from django.contrib.auth.models import Group, User
from django.db import transaction
from academic_vp.models import VPProfile

with transaction.atomic():
    g, g_created = Group.objects.get_or_create(name='academic_vp')

    u, u_created = User.objects.get_or_create(
        username='vp_user',
        defaults={'email': 'academicVP@gmail.com', 'is_staff': True, 'is_superuser': False}
    )

    if u_created:
        u.set_password('ww90wet873452')
        u.save()
    else:
        u.email = 'academicVP@gmail.com'
        u.is_staff = True
        u.is_superuser = False
        u.set_password('ww90wet873452')
        u.save()

    g.user_set.add(u)

    vp, vp_created = VPProfile.objects.get_or_create(user=u)

    print(f'group_created={g_created} user_created={u_created} vp_created={vp_created}')
