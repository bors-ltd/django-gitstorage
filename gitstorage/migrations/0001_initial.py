from django.db import migrations, models
from django.conf import settings
import gitstorage.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TreeMetadata',
            fields=[
                ('id', models.CharField(verbose_name='id', editable=False, serialize=False, db_index=True, max_length=40, primary_key=True, unique=True)),
                ('mimetype', models.CharField(null=True, verbose_name='mimetype', max_length=255, blank=True)),
            ],
            options={
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='BlobMetadata',
            fields=[
                ('id', models.CharField(verbose_name='id', editable=False, serialize=False, db_index=True, max_length=40, primary_key=True, unique=True)),
                ('mimetype', models.CharField(null=True, verbose_name='mimetype', max_length=255, blank=True)),
            ],
            options={
                'verbose_name': 'blob metadata',
                'verbose_name_plural': 'blob metadata',
            },
        ),
        migrations.CreateModel(
            name='TreePermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('parent_path', models.CharField(verbose_name='parent path', max_length=2048, validators=[gitstorage.validators.path_validator], blank=True, db_index=True)),
                ('name', models.CharField(verbose_name='name', max_length=256, validators=[gitstorage.validators.name_validator], blank=True, db_index=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'tree permission',
                'verbose_name_plural': 'tree permissions',
            },
        ),
    ]
