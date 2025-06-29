# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has on_delete set to the desired behavior
#   * Remove managed = False lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class ClientReponseSa(models.Model):
    survey_date = models.DateTimeField(blank=True, null=True)
    id_client = models.IntegerField(blank=True, null=True)
    question_number = models.IntegerField(blank=True, null=True)
    question = models.CharField(blank=True, null=True)
    response = models.CharField(blank=True, null=True)
    nps = models.CharField(db_column='NPS', blank=True, null=True)  # Field name made lowercase.
    csat = models.CharField(db_column='CSAT', blank=True, null=True)  # Field name made lowercase.
    satis_insatis = models.CharField(db_column='Satis_Insatis', blank=True, null=True)  # Field name made lowercase.
    amelioration_generale = models.CharField(db_column='Amelioration_Generale', blank=True, null=True)  # Field name made lowercase.
    amelioration_des_passif = models.CharField(db_column='Amelioration_des_Passif', blank=True, null=True)  # Field name made lowercase.
    problems = models.CharField(db_column='Problems', blank=True, null=True)  # Field name made lowercase.
    more_amelioration = models.CharField(db_column='More_Amelioration', blank=True, null=True)  # Field name made lowercase.
    problem_appel = models.CharField(db_column='Problem_Appel', blank=True, null=True)  # Field name made lowercase.
    subscriber_type = models.CharField(db_column='SUBSCRIBER_TYPE', blank=True, null=True)  # Field name made lowercase.
    subscriber_stauts = models.CharField(db_column='SUBSCRIBER_STAUTS', blank=True, null=True)  # Field name made lowercase.
    subscriber_tech_type = models.CharField(db_column='SUBSCRIBER_TECH_TYPE', blank=True, null=True)  # Field name made lowercase.
    globale_profil = models.CharField(db_column='GLOBALE_PROFIL', blank=True, null=True)  # Field name made lowercase.
    customer_type = models.CharField(db_column='CUSTOMER_TYPE', blank=True, null=True)  # Field name made lowercase.
    city = models.CharField(db_column='CITY', blank=True, null=True)  # Field name made lowercase.
    bu = models.CharField(db_column='BU', blank=True, null=True)  # Field name made lowercase.
    wilaya = models.CharField(db_column='WILAYA', blank=True, null=True)  # Field name made lowercase.
    age_subscriber = models.CharField(db_column='AGE_SUBSCRIBER', blank=True, null=True)  # Field name made lowercase.
    age_cust = models.CharField(db_column='AGE_CUST', blank=True, null=True)  # Field name made lowercase.
    handset_brand = models.CharField(db_column='HANDSET_BRAND', blank=True, null=True)  # Field name made lowercase.
    devicetype = models.CharField(db_column='Devicetype', blank=True, null=True)  # Field name made lowercase.
    smartphone = models.CharField(db_column='Smartphone', blank=True, null=True)  # Field name made lowercase.
    handset_type = models.CharField(db_column='HANDSET_TYPE', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'client_reponse_sa'


class DimClient(models.Model):
    id_client = models.IntegerField(blank=True, null=False , primary_key=True )
    type_abonne = models.CharField(db_column='TYPE_ABONNE', blank=True, null=True)  # Field name made lowercase.
    abonne_status = models.CharField(db_column='ABONNE_STATUS', blank=True, null=True)  # Field name made lowercase.
    type_tech = models.CharField(db_column='TYPE_TECH', blank=True, null=True)  # Field name made lowercase.
    globale_profile = models.CharField(db_column='GLOBALE_PROFILE', blank=True, null=True)  # Field name made lowercase.
    type_client = models.CharField(db_column='TYPE_CLIENT', blank=True, null=True)  # Field name made lowercase.
    age_abonne = models.CharField(db_column='AGE_ABONNE', blank=True, null=True)  # Field name made lowercase.
    age_client = models.CharField(db_column='AGE_CLIENT', blank=True, null=True)  # Field name made lowercase.
    handset_brand = models.CharField(db_column='HANDSET_BRAND', blank=True, null=True)  # Field name made lowercase.
    type_tel = models.CharField(db_column='Type_TEL', blank=True, null=True)  # Field name made lowercase.
    
    class Meta:
        managed = False
        db_table = 'dim_client'


class DimQuestion(models.Model):
    id_question = models.IntegerField(db_column='ID_Question', null=False , primary_key=True ) # Field name made lowercase.
    question_number = models.IntegerField(blank=True, null=True)
    question = models.CharField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'dim_question'


class DimRegion(models.Model):
    id_region = models.IntegerField(db_column='ID_Region', null=False , primary_key=True )  # Field name made lowercase.
    wilaya = models.CharField(db_column='Wilaya', blank=True, null=True)  # Field name made lowercase.
    bu = models.CharField(db_column='BU', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'dim_region'


class DimReponse(models.Model):
    id_reponse = models.IntegerField(blank=True,null=False , primary_key=True )
    nps_reponse = models.CharField(db_column='NPS_Reponse', blank=True, null=True)  # Field name made lowercase.
    csat_reponse = models.CharField(db_column='CSAT_Reponse', blank=True, null=True)  # Field name made lowercase.
    satis_insatis = models.CharField(db_column='SATIS_INSATIS', blank=True, null=True)  # Field name made lowercase.
    amelioraion_generale = models.CharField(db_column='AMELIORAION_GENERALE', blank=True, null=True)  # Field name made lowercase.
    amelioraion_passif = models.CharField(db_column='AMELIORAION_PASSIF', blank=True, null=True)  # Field name made lowercase.
    problemes = models.CharField(db_column='PROBLEMES', blank=True, null=True)  # Field name made lowercase.
    amelioraion_plus = models.CharField(db_column='AMELIORAION_PLUS', blank=True, null=True)  # Field name made lowercase.
    problemes_appel = models.CharField(db_column='PROBLEMES_APPEL', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'dim_reponse'


class DimTemps(models.Model):
    id_date = models.IntegerField(blank=True,null=False , primary_key=True )
    date = models.DateField(db_column='DATE', blank=True, null=True)  # Field name made lowercase.
    libjour = models.CharField(db_column='LibJOUR', blank=True, null=True)  # Field name made lowercase.
    jour = models.IntegerField(db_column='JOUR', blank=True, null=True)  # Field name made lowercase.
    libmois = models.CharField(db_column='LibMOIS', blank=True, null=True)  # Field name made lowercase.
    mois = models.IntegerField(db_column='MOIS', blank=True, null=True)  # Field name made lowercase.
    annee = models.IntegerField(db_column='ANNEE', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'dim_temps'




class FactTable(models.Model):
    id_date = models.ForeignKey(
        'DimTemps',
        db_column='id_date',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True
    )
    id_client = models.ForeignKey(
        'DimClient',
        db_column='id_client',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True
    )
    id_reponse = models.ForeignKey(
        'DimReponse',
        db_column='id_reponse',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True
    )
    id_question = models.ForeignKey(
        'DimQuestion',
        db_column='id_question',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True
    )
    id_region = models.ForeignKey(
        'DimRegion',
        db_column='id_region',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True
    )
    nps = models.IntegerField(db_column='NPS', blank=True, null=True)  # Field name made lowercase.
    csat = models.IntegerField(db_column='CSAT', blank=True, null=True)  # Field name made lowercase.
    non_satisfait = models.IntegerField(db_column='Non_Satisfait', blank=True, null=True)  # Field name made lowercase.
    is_promoteur = models.IntegerField(db_column='IS_Promoteur', blank=True, null=True)  # Field name made lowercase.
    is_passif = models.IntegerField(db_column='IS_Passif', blank=True, null=True)  # Field name made lowercase.
    is_detracteur = models.IntegerField(db_column='IS_Detracteur', blank=True, null=True)  # Field name made lowercase.


    class Meta:
        managed = False  # Pour éviter que Django ne gère cette table
        db_table = 'fact_table'
        # Déclare la combinaison de plusieurs champs comme unique
        unique_together = ('id_date', 'id_client', 'id_reponse', 'id_question', 'id_region')

    # Optionnellement, vous pouvez définir une méthode __str__ pour mieux représenter l'objet
    def __str__(self):
        return f"FactTable({self.id_date}, {self.id_client}, {self.id_reponse}, {self.id_question}, {self.id_region})"
    


    
class LatestResponseCsat(models.Model):
    id_client = models.ForeignKey(
        'DimClient',
        db_column='id_client',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True
    )
    csat = models.IntegerField(db_column='CSAT', blank=True, null=True)
    non_satisfait = models.IntegerField(db_column='Non_Satisfait', blank=True, null=True)

    class Meta:
        db_table = "latest_response_csat" 



class LatestResponseNps(models.Model):
    id_client = models.ForeignKey(
        'DimClient',
        db_column='id_client',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True
    )
    id_region = models.ForeignKey(
        'DimRegion',
        db_column='id_region',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True
    )
    nps = models.IntegerField(db_column='NPS', blank=True, null=True)
    is_promoteur = models.IntegerField(db_column='IS_Promoteur', blank=True, null=True)
    is_passif = models.IntegerField(db_column='IS_Passif', blank=True, null=True)
    is_detracteur = models.IntegerField(db_column='IS_Detracteur', blank=True, null=True)

    class Meta:
        db_table = 'latest_response_nps'




class CommentaireClient(models.Model):
    survey_date = models.DateTimeField()
    id_client = models.IntegerField(primary_key=True)  # Set as primary key
    nps = models.CharField(max_length=255)
    commentaire = models.CharField(max_length=255)
    sentiment = models.CharField(max_length=255)
    theme = models.CharField(max_length=255)
    score_prediction = models.FloatField()
    nps_match = models.CharField(max_length=255)

    class Meta:
        db_table = 'commentaire_client'
        managed = False
        unique_together = ('survey_date', 'id_client')  # Add this line