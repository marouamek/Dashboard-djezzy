from django.db import models

class CommentaireClient(models.Model):
    # ================================
    # === CHAMPS DE LA TABLE =========
    # ================================
    survey_date = models.DateField(null=True, verbose_name="Date du sondage")
    id_client = models.IntegerField(primary_key=True, verbose_name="ID Client")
    nps = models.CharField(max_length=20, null=True, verbose_name="NPS")
    commentaire = models.TextField(verbose_name="Commentaire")
    sentiment = models.CharField(max_length=20, null=True, verbose_name="Sentiment")
    theme = models.CharField(max_length=50, null=True, verbose_name="Thème")
    score_prediction = models.FloatField(null=True, verbose_name="Confiance")
    nps_match = models.CharField(null=True, verbose_name="Correspondance NPS")

    # ==========================================================
    # === MÉTHODE : ANALYSER LE COMMENTAIRE ET REMPLIR LES CHAMPS
    # ==========================================================
   # ==========================================================
    # === MÉTHODE : ANALYSER LE COMMENTAIRE ET REMPLIR LES CHAMPS
    # ==========================================================
    def analyser(self):
        from .inference import analyse_commentaire
        
        resultat = analyse_commentaire(self.commentaire)
        self.sentiment = resultat['sentiment']
        self.theme = resultat['theme']
        self.score_prediction = resultat['score']
        self.nps_match = self._compare_nps_sentiment()
        self.save()
        
    # ==========================================================
    # === MÉTHODE : COMPARER NPS ET SENTIMENT POUR LA COHÉRENCE
    # ==========================================================
    def _compare_nps_sentiment(self):
        try:
            nps_value = int(self.nps)
        except (ValueError, TypeError):
            nps_value = None

        sentiment = self.sentiment.upper() if self.sentiment else ""
        if nps_value is not None:
            if nps_value in [9, 10] and sentiment == "POSITIF":
                return True
            elif nps_value in [0, 1, 2, 3, 4, 5, 6] and sentiment == "NEGATIF":
                return True
            elif nps_value in [7, 8] and sentiment == "NEUTRE":
                return True
        return False
        
    class Meta:
        managed = False
        db_table = 'commentaire_client'

