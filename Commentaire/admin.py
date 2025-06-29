from django.contrib import admin
from .models import CommentaireClient
from .inference import analyse_commentaire

# ==========================================================
# === ACTION ADMIN : ANALYSER LES COMMENTAIRES SÉLECTIONNÉS =
# ==========================================================
@admin.action(description='Analyser les commentaires sélectionnés')
def analyser_commentaires(modeladmin, request, queryset):
    for commentaire in queryset:
        commentaire.analyser()  # Remplit sentiment, thème, score_prediction et sauvegarde

# ==========================================================
# === CONFIGURATION DE L’AFFICHAGE DANS L’ADMIN DJANGO =====
# ==========================================================
@admin.register(CommentaireClient)
class CommentaireClientAdmin(admin.ModelAdmin):
    list_display = ('id_client', 'survey_date', 'nps', 'sentiment', 'theme', 'score_prediction', 'nps_match')
    actions = [analyser_commentaires]