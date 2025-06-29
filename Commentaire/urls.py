from django.urls import path
from .views import tester_commentaire

# ==========================================================
# === URLS : PRÉDICTION DE SENTIMENT NPS SUR COMMENTAIRES ==
# ==========================================================
# Cette page permet de tester la prédiction du sentiment NPS
# à partir d'un commentaire client via un formulaire dédié.
urlpatterns = [
    path("nps_prediction/", tester_commentaire, name="nps_prediction_commentaire"),
]

