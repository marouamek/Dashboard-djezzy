from django.shortcuts import render
from .inference import analyse_commentaire
from django.db.models import Count
from .models import CommentaireClient

# ==========================================================
# === VUE : TESTER UN COMMENTAIRE CLIENT ===================
# ==========================================================
# Permet à l'utilisateur de soumettre un commentaire via un formulaire
# et d'obtenir une analyse de sentiment, thème et score de confiance.
def tester_commentaire(request):
    resultat = None

    if request.method == "POST":
        texte = request.POST.get("commentaire")
        resultat = analyse_commentaire(texte)

    return render(request, "nps_prediction_commentaire.html", {"resultat": resultat})

# ==========================================================
# === VUE : REMPLIR ET ANALYSER LES COMMENTAIRES ===========
# ==========================================================
# Parcourt tous les commentaires en base, analyse ceux qui ne le sont pas encore,
# puis calcule des statistiques pour affichage dans le dashboard.
def remplir_commentaire(request):
    commentaires = CommentaireClient.objects.all()

    # Analyse automatique pour les commentaires non analysés
    for commentaire in commentaires:
        if not commentaire.sentiment:
            resultat = analyse_commentaire(commentaire.commentaire)
            commentaire.sentiment = resultat['sentiment']
            commentaire.theme = resultat['theme']
            commentaire.score_prediction = resultat['score']
            # nps_match : à adapter selon ta logique de correspondance NPS/sentiment
            commentaire.nps_match = (
                commentaire.nps and commentaire.sentiment.lower() == commentaire.nps.lower()
            )
            commentaire.save()

    # Statistiques pour les graphiques (répartition des sentiments et thèmes)
    sentiments = (
        CommentaireClient.objects
        .values('sentiment')
        .annotate(count=Count('id_client'))
    )

    themes = (
        CommentaireClient.objects
        .values('theme')
        .annotate(count=Count('id_client'))
    )

    return render(request, "dashboard.html", {
        "sentiments": list(sentiments),
        "themes": list(themes)
    })