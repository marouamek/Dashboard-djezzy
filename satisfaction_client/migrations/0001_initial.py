# Generated by Django 5.1.4 on 2025-05-24 18:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ClientReponseSa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('survey_date', models.DateTimeField(blank=True, null=True)),
                ('id_client', models.IntegerField(blank=True, null=True)),
                ('question_number', models.IntegerField(blank=True, null=True)),
                ('question', models.CharField(blank=True, null=True)),
                ('response', models.CharField(blank=True, null=True)),
                ('nps', models.CharField(blank=True, db_column='NPS', null=True)),
                ('csat', models.CharField(blank=True, db_column='CSAT', null=True)),
                ('satis_insatis', models.CharField(blank=True, db_column='Satis_Insatis', null=True)),
                ('amelioration_generale', models.CharField(blank=True, db_column='Amelioration_Generale', null=True)),
                ('amelioration_des_passif', models.CharField(blank=True, db_column='Amelioration_des_Passif', null=True)),
                ('problems', models.CharField(blank=True, db_column='Problems', null=True)),
                ('more_amelioration', models.CharField(blank=True, db_column='More_Amelioration', null=True)),
                ('problem_appel', models.CharField(blank=True, db_column='Problem_Appel', null=True)),
                ('subscriber_type', models.CharField(blank=True, db_column='SUBSCRIBER_TYPE', null=True)),
                ('subscriber_stauts', models.CharField(blank=True, db_column='SUBSCRIBER_STAUTS', null=True)),
                ('subscriber_tech_type', models.CharField(blank=True, db_column='SUBSCRIBER_TECH_TYPE', null=True)),
                ('globale_profil', models.CharField(blank=True, db_column='GLOBALE_PROFIL', null=True)),
                ('customer_type', models.CharField(blank=True, db_column='CUSTOMER_TYPE', null=True)),
                ('city', models.CharField(blank=True, db_column='CITY', null=True)),
                ('bu', models.CharField(blank=True, db_column='BU', null=True)),
                ('wilaya', models.CharField(blank=True, db_column='WILAYA', null=True)),
                ('age_subscriber', models.CharField(blank=True, db_column='AGE_SUBSCRIBER', null=True)),
                ('age_cust', models.CharField(blank=True, db_column='AGE_CUST', null=True)),
                ('handset_brand', models.CharField(blank=True, db_column='HANDSET_BRAND', null=True)),
                ('devicetype', models.CharField(blank=True, db_column='Devicetype', null=True)),
                ('smartphone', models.CharField(blank=True, db_column='Smartphone', null=True)),
                ('handset_type', models.CharField(blank=True, db_column='HANDSET_TYPE', null=True)),
            ],
            options={
                'db_table': 'client_reponse_sa',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DimClient',
            fields=[
                ('id_client', models.IntegerField(blank=True, primary_key=True, serialize=False)),
                ('type_abonne', models.CharField(blank=True, db_column='TYPE_ABONNE', null=True)),
                ('abonne_status', models.CharField(blank=True, db_column='ABONNE_STATUS', null=True)),
                ('type_tech', models.CharField(blank=True, db_column='TYPE_TECH', null=True)),
                ('globale_profile', models.CharField(blank=True, db_column='GLOBALE_PROFILE', null=True)),
                ('type_client', models.CharField(blank=True, db_column='TYPE_CLIENT', null=True)),
                ('age_abonne', models.CharField(blank=True, db_column='AGE_ABONNE', null=True)),
                ('age_client', models.CharField(blank=True, db_column='AGE_CLIENT', null=True)),
                ('handset_brand', models.CharField(blank=True, db_column='HANDSET_BRAND', null=True)),
                ('type_tel', models.CharField(blank=True, db_column='Type_TEL', null=True)),
            ],
            options={
                'db_table': 'dim_client',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DimQuestion',
            fields=[
                ('id_question', models.IntegerField(db_column='ID_Question', primary_key=True, serialize=False)),
                ('question_number', models.IntegerField(blank=True, null=True)),
                ('question', models.CharField(blank=True, null=True)),
            ],
            options={
                'db_table': 'dim_question',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DimRegion',
            fields=[
                ('id_region', models.IntegerField(db_column='ID_Region', primary_key=True, serialize=False)),
                ('wilaya', models.CharField(blank=True, db_column='Wilaya', null=True)),
                ('bu', models.CharField(blank=True, db_column='BU', null=True)),
            ],
            options={
                'db_table': 'dim_region',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DimReponse',
            fields=[
                ('id_reponse', models.IntegerField(blank=True, primary_key=True, serialize=False)),
                ('nps_reponse', models.CharField(blank=True, db_column='NPS_Reponse', null=True)),
                ('csat_reponse', models.CharField(blank=True, db_column='CSAT_Reponse', null=True)),
                ('satis_insatis', models.CharField(blank=True, db_column='SATIS_INSATIS', null=True)),
                ('amelioraion_generale', models.CharField(blank=True, db_column='AMELIORAION_GENERALE', null=True)),
                ('amelioraion_passif', models.CharField(blank=True, db_column='AMELIORAION_PASSIF', null=True)),
                ('problemes', models.CharField(blank=True, db_column='PROBLEMES', null=True)),
                ('amelioraion_plus', models.CharField(blank=True, db_column='AMELIORAION_PLUS', null=True)),
                ('problemes_appel', models.CharField(blank=True, db_column='PROBLEMES_APPEL', null=True)),
            ],
            options={
                'db_table': 'dim_reponse',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DimTemps',
            fields=[
                ('id_date', models.IntegerField(blank=True, primary_key=True, serialize=False)),
                ('date', models.DateField(blank=True, db_column='DATE', null=True)),
                ('libjour', models.CharField(blank=True, db_column='LibJOUR', null=True)),
                ('jour', models.IntegerField(blank=True, db_column='JOUR', null=True)),
                ('libmois', models.CharField(blank=True, db_column='LibMOIS', null=True)),
                ('mois', models.IntegerField(blank=True, db_column='MOIS', null=True)),
                ('annee', models.IntegerField(blank=True, db_column='ANNEE', null=True)),
            ],
            options={
                'db_table': 'dim_temps',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='FactTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nps', models.IntegerField(blank=True, db_column='NPS', null=True)),
                ('csat', models.IntegerField(blank=True, db_column='CSAT', null=True)),
                ('non_satisfait', models.IntegerField(blank=True, db_column='Non_Satisfait', null=True)),
                ('is_promoteur', models.IntegerField(blank=True, db_column='IS_Promoteur', null=True)),
                ('is_passif', models.IntegerField(blank=True, db_column='IS_Passif', null=True)),
                ('is_detracteur', models.IntegerField(blank=True, db_column='IS_Detracteur', null=True)),
            ],
            options={
                'db_table': 'fact_table',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='LatestResponseCsat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('csat', models.IntegerField(blank=True, db_column='CSAT', null=True)),
                ('non_satisfait', models.IntegerField(blank=True, db_column='Non_Satisfait', null=True)),
                ('id_client', models.ForeignKey(blank=True, db_column='id_client', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='satisfaction_client.dimclient')),
            ],
            options={
                'db_table': 'latest_response_csat',
            },
        ),
        migrations.CreateModel(
            name='LatestResponseNps',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nps', models.IntegerField(blank=True, db_column='NPS', null=True)),
                ('is_promoteur', models.IntegerField(blank=True, db_column='IS_Promoteur', null=True)),
                ('is_passif', models.IntegerField(blank=True, db_column='IS_Passif', null=True)),
                ('is_detracteur', models.IntegerField(blank=True, db_column='IS_Detracteur', null=True)),
                ('id_client', models.ForeignKey(blank=True, db_column='id_client', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='satisfaction_client.dimclient')),
                ('id_region', models.ForeignKey(blank=True, db_column='id_region', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='satisfaction_client.dimregion')),
            ],
            options={
                'db_table': 'latest_response_nps',
            },
        ),
    ]
